#!/usr/bin/env python
# This Software (Dioptra) is being made available as a public service by the
# National Institute of Standards and Technology (NIST), an Agency of the United
# States Department of Commerce. This software was developed in part by employees of
# NIST and in part by NIST contractors. Copyright in portions of this software that
# were developed by NIST contractors has been licensed or assigned to NIST. Pursuant
# to Title 17 United States Code Section 105, works of NIST employees are not
# subject to copyright protection in the United States. However, NIST may hold
# international copyright in software created by its employees and domestic
# copyright (or licensing rights) in portions of software that were assigned or
# licensed to NIST. To the extent that NIST holds copyright in this software, it is
# being made available under the Creative Commons Attribution 4.0 International
# license (CC BY 4.0). The disclaimers of the CC BY 4.0 license apply to all parts
# of the software developed or licensed by NIST.
#
# ACCESS THE FULL CC BY 4.0 LICENSE HERE:
# https://creativecommons.org/licenses/by/4.0/legalcode

import os
from pathlib import Path
from typing import Any, Dict, List

import click
import mlflow
import structlog
from prefect import Flow, Parameter
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
    "--data-dir",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, resolve_path=True, readable=True
    ),
    help="Root directory for NFS mounted datasets (in container)",
)
@click.option(
    "--image-size",
    type=click.STRING,
    callback=_coerce_comma_separated_ints,
    help="Dimensions for the input images",
)
@click.option(
    "--model-architecture",
    type=click.Choice(["shallow_net", "le_net", "alex_net"], case_sensitive=False),
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
    "--seed",
    type=click.INT,
    help="Set the entry point rng seed",
    default=-1,
)
def train(
    data_dir,
    image_size,
    model_architecture,
    epochs,
    batch_size,
    register_model_name,
    learning_rate,
    optimizer,
    validation_split,
    seed,
):
    LOGGER.info(
        "Execute MLFlow entry point",
        entry_point="train",
        data_dir=data_dir,
        image_size=image_size,
        model_architecture=model_architecture,
        epochs=epochs,
        batch_size=batch_size,
        register_model_name=register_model_name,
        learning_rate=learning_rate,
        optimizer=optimizer,
        validation_split=validation_split,
        seed=seed,
    )

    mlflow.autolog()

    with mlflow.start_run() as active_run:
        flow: Flow = init_train_flow()
        state = flow.run(
            parameters=dict(
                active_run=active_run,
                training_dir=Path(data_dir) / "training",
                testing_dir=Path(data_dir) / "testing",
                image_size=image_size,
                model_architecture=model_architecture,
                epochs=epochs,
                batch_size=batch_size,
                register_model_name=register_model_name,
                learning_rate=learning_rate,
                optimizer_name=optimizer,
                validation_split=validation_split,
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
            register_model_name,
            learning_rate,
            optimizer_name,
            validation_split,
            seed,
        ) = (
            Parameter("active_run"),
            Parameter("training_dir"),
            Parameter("testing_dir"),
            Parameter("image_size"),
            Parameter("model_architecture"),
            Parameter("epochs"),
            Parameter("batch_size"),
            Parameter("register_model_name"),
            Parameter("learning_rate"),
            Parameter("optimizer_name"),
            Parameter("validation_split"),
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
        training_ds = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.data",
            "tensorflow",
            "create_image_dataset",
            data_dir=training_dir,
            subset="training",
            image_size=image_size,
            seed=dataset_seed,
            validation_split=validation_split,
            batch_size=batch_size,
            upstream_tasks=[init_tensorflow_results],
        )
        validation_ds = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.data",
            "tensorflow",
            "create_image_dataset",
            data_dir=training_dir,
            subset="validation",
            image_size=image_size,
            seed=dataset_seed,
            validation_split=validation_split,
            batch_size=batch_size,
            upstream_tasks=[init_tensorflow_results],
        )
        testing_ds = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.data",
            "tensorflow",
            "create_image_dataset",
            data_dir=testing_dir,
            subset=None,
            image_size=image_size,
            seed=dataset_seed + 1,
            validation_split=None,
            batch_size=batch_size,
            upstream_tasks=[init_tensorflow_results],
        )
        n_classes = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.data",
            "tensorflow",
            "get_n_classes_from_directory_iterator",
            ds=training_ds,
        )
        classifier = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.estimators",
            "keras_classifiers",
            "init_classifier",
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


if __name__ == "__main__":
    log_level: str = os.getenv("AI_JOB_LOG_LEVEL", default="INFO")
    as_json: bool = True if os.getenv("AI_JOB_LOG_AS_JSON") else False

    clear_logger_handlers(get_prefect_logger())
    attach_stdout_stream_handler(as_json)
    set_logging_level(log_level)
    configure_structlog()

    with plugin_dirs(), StdoutLogStream(as_json), StderrLogStream(as_json):
        _ = train()
