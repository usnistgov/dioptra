#!/usr/bin/env python
# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.

import os
import tarfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import mlflow
import structlog
from data_tensorflow_updated import create_image_dataset
from estimators_keras_classifiers_updated import init_classifier
from mlflow.tracking import MlflowClient
from prefect import Flow, Parameter, case
from prefect.utilities.logging import get_logger as get_prefect_logger
from structlog.stdlib import BoundLogger
from tasks import (
    evaluate_metrics_tensorflow,
    get_model_callbacks,
    get_optimizer,
    get_performance_metrics,
)

from mitre.securingai import pyplugs
from mitre.securingai.sdk.utilities.contexts import plugin_dirs
from mitre.securingai.sdk.utilities.logging import (
    StderrLogStream,
    StdoutLogStream,
    attach_stdout_stream_handler,
    clear_logger_handlers,
    configure_structlog,
    set_logging_level,
)

_PLUGINS_IMPORT_PATH: str = "securingai_builtins"
CALLBACKS: List[Dict[str, Any]] = [
    {
        "name": "EarlyStopping",
        "parameters": {
            "monitor": "val_loss",
            "min_delta": 1e-2,
            "patience": 5,
            "restore_best_weights": True,
        },
    },
]
LOGGER: BoundLogger = structlog.stdlib.get_logger()
PERFORMANCE_METRICS: List[Dict[str, Any]] = [
    {"name": "CategoricalAccuracy", "parameters": {"name": "accuracy"}},
    {"name": "Precision", "parameters": {"name": "precision"}},
    {"name": "Recall", "parameters": {"name": "recall"}},
    {"name": "AUC", "parameters": {"name": "auc"}},
]


def _coerce_comma_separated_ints(ctx, param, value):
    return tuple(int(x.strip()) for x in value.split(","))


@click.command()
@click.option(
    "--data-dir-training",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, resolve_path=True, readable=True
    ),
    help="Root directory for NFS mounted training dataset (in container)",
)
@click.option(
    "--data-dir-testing",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, resolve_path=True, readable=True
    ),
    help="Root directory for NFS mounted test dataset (in container)",
)
@click.option(
    "--image-size",
    type=click.STRING,
    callback=_coerce_comma_separated_ints,
    help="Dimensions for the input images",
)
@click.option(
    "--model-architecture",
    type=click.Choice(
        ["shallow_net", "le_net", "alex_net", "resnet50", "vgg16"], case_sensitive=False
    ),
    default="le_net",
    help="Model architecture",
)
@click.option(
    "--epochs",
    type=click.INT,
    help="Number of epochs to train model",
    default=30,
)
@click.option(
    "--batch-size",
    type=click.INT,
    help="Batch size to use when training a single epoch",
    default=32,
)
@click.option(
    "--register-model-name",
    type=click.STRING,
    default="",
    help=(
        "Register the trained model under the provided name. If an empty string, "
        "then the trained model will not be registered."
    ),
)
@click.option(
    "--learning-rate", type=click.FLOAT, help="Model learning rate", default=0.001
)
@click.option(
    "--optimizer",
    type=click.Choice(["Adam", "Adagrad", "RMSprop", "SGD"], case_sensitive=True),
    help="Optimizer to use to train the model",
    default="Adam",
)
@click.option(
    "--validation-split",
    type=click.FLOAT,
    help="Fraction of training dataset to use for validation",
    default=0.2,
)
@click.option(
    "--imagenet-preprocessing",
    type=click.BOOL,
    help="If true, initializes model with Imagenet image preprocessing settings.",
    default=False,
)
@click.option(
    "--load-dataset-from-mlruns",
    type=click.BOOL,
    help="If set to true, instead loads the training and test datasets from a previous patch mlruns.",
    default=False,
)
@click.option(
    "--dataset-run-id-testing",
    type=click.STRING,
    help="MLFlow Run ID of a successful patch attack on a test dataset.",
    default="None",
)
@click.option(
    "--dataset-run-id-training",
    type=click.STRING,
    help="MLFlow Run ID of a successful patch attack on a training dataset.",
    default="None",
)
@click.option(
    "--adv-tar-name",
    type=click.STRING,
    default="adversarial_patch_dataset.tar.gz",
    help="Name of tarfile artifact containing images",
)
@click.option(
    "--adv-data-dir",
    type=click.STRING,
    default="adv_patch_dataset",
    help="Directory in tarfile containing images",
)
@click.option(
    "--seed",
    type=click.INT,
    help="Set the entry point rng seed",
    default=-1,
)
def train(
    data_dir_testing,
    data_dir_training,
    image_size,
    model_architecture,
    epochs,
    batch_size,
    register_model_name,
    learning_rate,
    optimizer,
    validation_split,
    imagenet_preprocessing,
    load_dataset_from_mlruns,
    dataset_run_id_testing,
    dataset_run_id_training,
    adv_tar_name,
    adv_data_dir,
    seed,
):
    LOGGER.info(
        "Execute MLFlow entry point",
        entry_point="train",
        data_dir_testing=data_dir_testing,
        data_dir_training=data_dir_training,
        image_size=image_size,
        model_architecture=model_architecture,
        epochs=epochs,
        batch_size=batch_size,
        register_model_name=register_model_name,
        learning_rate=learning_rate,
        optimizer=optimizer,
        validation_split=validation_split,
        imagenet_preprocessing=imagenet_preprocessing,
        load_dataset_from_mlruns=load_dataset_from_mlruns,
        dataset_run_id_testing=dataset_run_id_testing,
        dataset_run_id_training=dataset_run_id_training,
        seed=seed,
    )

    mlflow.autolog()
    if imagenet_preprocessing:
        rescale = 1.0
    else:
        rescale = 1.0 / 255

    if load_dataset_from_mlruns:
        if len(dataset_run_id_testing) > 0:
            data_dir_testing = Path.cwd() / "testing" / adv_data_dir
            data_test_tar_name = adv_tar_name
            adv_testing_tar_path = download_image_archive(
                run_id=dataset_run_id_testing, archive_path=data_test_tar_name
            )
            with tarfile.open(adv_testing_tar_path, "r:gz") as f:
                f.extractall(path=(Path.cwd() / "testing"))
        else:
            LOGGER.info(
                "No test run_id provided, defaulting to original test directory.",
            )
        data_dir_training = Path.cwd() / "training" / adv_data_dir
        data_train_tar_name = adv_tar_name
        adv_training_tar_path = download_image_archive(
            run_id=dataset_run_id_training, archive_path=data_train_tar_name
        )
        with tarfile.open(adv_training_tar_path, "r:gz") as f:
            f.extractall(path=(Path.cwd() / "training"))

    with mlflow.start_run() as active_run:
        flow: Flow = init_train_flow()
        state = flow.run(
            parameters=dict(
                active_run=active_run,
                training_dir=Path(data_dir_training),
                testing_dir=Path(data_dir_testing),
                image_size=image_size,
                model_architecture=model_architecture,
                epochs=epochs,
                batch_size=batch_size,
                rescale=rescale,
                register_model_name=register_model_name,
                learning_rate=learning_rate,
                optimizer_name=optimizer,
                validation_split=validation_split,
                imagenet_preprocessing=imagenet_preprocessing,
                seed=seed,
            )
        )
    return state


def init_train_flow() -> Flow:
    with Flow("Train Model") as flow:
        (
            active_run,
            training_dir,
            testing_dir,
            image_size,
            model_architecture,
            epochs,
            batch_size,
            rescale,
            register_model_name,
            learning_rate,
            optimizer_name,
            validation_split,
            imagenet_preprocessing,
            seed,
        ) = (
            Parameter("active_run"),
            Parameter("training_dir"),
            Parameter("testing_dir"),
            Parameter("image_size"),
            Parameter("model_architecture"),
            Parameter("epochs"),
            Parameter("batch_size"),
            Parameter("rescale"),
            Parameter("register_model_name"),
            Parameter("learning_rate"),
            Parameter("optimizer_name"),
            Parameter("validation_split"),
            Parameter("imagenet_preprocessing"),
            Parameter("seed"),
        )
        seed, rng = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.random", "rng", "init_rng", seed=seed
        )
        tensorflow_global_seed = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.random", "sample", "draw_random_integer", rng=rng
        )
        dataset_seed = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.random", "sample", "draw_random_integer", rng=rng
        )
        init_tensorflow_results = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.backend_configs",
            "tensorflow",
            "init_tensorflow",
            seed=tensorflow_global_seed,
        )
        log_mlflow_params_result = pyplugs.call_task(  # noqa: F841
            f"{_PLUGINS_IMPORT_PATH}.tracking",
            "mlflow",
            "log_parameters",
            parameters=dict(
                entry_point_seed=seed,
                tensorflow_global_seed=tensorflow_global_seed,
                dataset_seed=dataset_seed,
            ),
        )
        optimizer = get_optimizer(
            optimizer_name,
            learning_rate=learning_rate,
            upstream_tasks=[init_tensorflow_results],
        )
        metrics = get_performance_metrics(
            PERFORMANCE_METRICS, upstream_tasks=[init_tensorflow_results]
        )
        callbacks_list = get_model_callbacks(
            CALLBACKS, upstream_tasks=[init_tensorflow_results]
        )

        training_ds = create_image_dataset(
            data_dir=training_dir,
            subset="training",
            image_size=image_size,
            seed=dataset_seed,
            validation_split=validation_split,
            batch_size=batch_size,
            upstream_tasks=[init_tensorflow_results],
            rescale=rescale,
            imagenet_preprocessing=imagenet_preprocessing,
        )
        validation_ds = create_image_dataset(
            data_dir=training_dir,
            subset="validation",
            image_size=image_size,
            seed=dataset_seed,
            validation_split=validation_split,
            batch_size=batch_size,
            upstream_tasks=[init_tensorflow_results],
            rescale=rescale,
            imagenet_preprocessing=imagenet_preprocessing,
        )
        testing_ds = create_image_dataset(
            data_dir=testing_dir,
            subset=None,
            image_size=image_size,
            seed=dataset_seed + 1,
            validation_split=None,
            batch_size=batch_size,
            upstream_tasks=[init_tensorflow_results],
            rescale=rescale,
            imagenet_preprocessing=imagenet_preprocessing,
        )
        n_classes = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.data",
            "tensorflow",
            "get_n_classes_from_directory_iterator",
            ds=training_ds,
        )
        # TODO: Swap to pyplugs in next update.
        classifier = init_classifier(
            model_architecture=model_architecture,
            optimizer=optimizer,
            metrics=metrics,
            input_shape=image_size,
            n_classes=n_classes,
            upstream_tasks=[init_tensorflow_results],
        )
        history = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.estimators",
            "methods",
            "fit",
            estimator=classifier,
            x=training_ds,
            fit_kwargs=dict(
                nb_epochs=epochs,
                validation_data=validation_ds,
                callbacks=callbacks_list,
                verbose=2,
            ),
        )
        classifier_performance_metrics = evaluate_metrics_tensorflow(
            classifier=classifier, dataset=testing_ds, upstream_tasks=[history]
        )
        log_classifier_performance_metrics_result = pyplugs.call_task(  # noqa: F841
            f"{_PLUGINS_IMPORT_PATH}.tracking",
            "mlflow",
            "log_metrics",
            metrics=classifier_performance_metrics,
        )
        model_version = pyplugs.call_task(  # noqa: F841
            f"{_PLUGINS_IMPORT_PATH}.registry",
            "mlflow",
            "add_model_to_registry",
            active_run=active_run,
            name=register_model_name,
            model_dir="model",
            upstream_tasks=[history],
        )

    return flow


# Update data dir path if user is applying defense over image artifacts.
def download_image_archive(
    run_id: str, archive_path: str, destination_path: Optional[str] = None
) -> str:
    client: MlflowClient = MlflowClient()
    image_archive_path: str = client.download_artifacts(
        run_id=run_id, path=archive_path, dst_path=destination_path
    )
    LOGGER.info(
        "Image archive downloaded",
        run_id=run_id,
        storage_path=archive_path,
        dst_path=image_archive_path,
    )
    return image_archive_path


if __name__ == "__main__":
    log_level: str = os.getenv("AI_JOB_LOG_LEVEL", default="INFO")
    as_json: bool = True if os.getenv("AI_JOB_LOG_AS_JSON") else False

    clear_logger_handlers(get_prefect_logger())
    attach_stdout_stream_handler(as_json)
    set_logging_level(log_level)
    configure_structlog()

    with plugin_dirs(), StdoutLogStream(as_json), StderrLogStream(as_json):
        _ = train()
