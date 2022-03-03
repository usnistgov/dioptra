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
from typing import Any, Dict, List

import click
import mlflow
import structlog
from prefect import Flow, Parameter
from prefect.utilities.logging import get_logger as get_prefect_logger
from structlog.stdlib import BoundLogger

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
_CUSTOM_PLUGINS_IMPORT_PATH: str = "securingai_custom"
CALLBACKS: List[Dict[str, Any]] = [
    {
        "name": "CSVLogger",
        "parameters": {
            "filename": "training_log.csv",
        },
    },
    {
        "name": "EarlyStopping",
        "parameters": {
            "monitor": "val_loss",
            "min_delta": 1e-2,
            "patience": 40,
            "restore_best_weights": True,
        },
    },
    {
        "name": "ReduceLROnPlateau",
        "parameters": {
            "monitor": "val_loss",
            "factor": 0.1,
            "cooldown": 5,
            "patience": 10,
            "min_lr": 0,
        },
    },
]
FINETUNE_CALLBACKS: List[Dict[str, Any]] = [
    {
        "name": "CSVLogger",
        "parameters": {
            "filename": "finetune_training_log.csv",
        },
    },
    {
        "name": "EarlyStopping",
        "parameters": {
            "monitor": "val_loss",
            "min_delta": 1e-2,
            "patience": 40,
            "restore_best_weights": True,
        },
    },
    {
        "name": "ReduceLROnPlateau",
        "parameters": {
            "monitor": "val_loss",
            "factor": 0.1,
            "cooldown": 5,
            "patience": 10,
            "min_lr": 0,
        },
    },
]
LOGGER: BoundLogger = structlog.stdlib.get_logger()


def _coerce_comma_separated_ints(ctx, param, value):
    return tuple(int(x.strip()) for x in value.split(","))


def _coerce_str_to_bool(ctx, param, value):
    return value.lower() == "true"


@click.command()
@click.option(
    "--data-dir",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, resolve_path=True, readable=True
    ),
    help=(
        "Root directory for object detection dataset in PASCAL VOC format "
        "(in container)"
    ),
)
@click.option(
    "--image-size",
    type=click.STRING,
    callback=_coerce_comma_separated_ints,
    help="Dimensions for the input images",
)
@click.option(
    "--grid-size",
    type=click.INT,
    help="Grid resolution to use for object detector.",
    default=7,
)
@click.option(
    "--skip-finetune",
    type=click.Choice(["True", "False"], case_sensitive=False),
    callback=_coerce_str_to_bool,
    help="Skip finetuning the pre-trained model weights after transfer learning.",
    default="True",
)
@click.option(
    "--augment",
    type=click.Choice(["True", "False"], case_sensitive=False),
    callback=_coerce_str_to_bool,
    help="Apply the data augmentation pipeline to the training images.",
    default="True",
)
@click.option(
    "--model-architecture",
    type=click.Choice(["mobilenetv2", "tiny_yolo"], case_sensitive=False),
    default="mobilenetv2",
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
    type=click.INT,
    help=(
        "Set the stride size for creating the validation dataset. For example, if "
        "value is 5, then every fifth image in dataset stream will be reserved for the "
        "validation dataset."
    ),
    default=5,
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
    grid_size,
    skip_finetune,
    augment,
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
        entry_point="transfer_learn",
        data_dir=data_dir,
        image_size=image_size,
        grid_size=grid_size,
        skip_finetune=skip_finetune,
        augment=augment,
        model_architecture=model_architecture,
        epochs=epochs,
        batch_size=batch_size,
        register_model_name=register_model_name,
        learning_rate=learning_rate,
        optimizer=optimizer,
        validation_split=validation_split,
        seed=seed,
    )

    with mlflow.start_run() as active_run:
        flow: Flow = init_train_flow()
        state = flow.run(
            parameters=dict(
                active_run=active_run,
                training_dir=data_dir,
                image_size=image_size,
                grid_size=grid_size,
                skip_finetune=skip_finetune,
                augment=augment,
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
            image_size,
            grid_size,
            skip_finetune,
            augment,
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
            Parameter("image_size"),
            Parameter("grid_size"),
            Parameter("skip_finetune"),
            Parameter("augment"),
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
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.backend_configs",
            # f"{_PLUGINS_IMPORT_PATH}.backend_configs",
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
        optimizer = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.evaluation",
            "tensorflow",
            "get_optimizer",
            optimizer=optimizer_name,
            learning_rate=learning_rate,
            upstream_tasks=[init_tensorflow_results],
        )
        callbacks_list = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.evaluation",
            "tensorflow",
            "get_model_callbacks",
            callbacks_list=CALLBACKS,
            upstream_tasks=[init_tensorflow_results],
        )
        training_ds, validation_ds, testing_ds = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.roadsigns_yolo_estimators",
            "data",
            "create_object_detection_dataset",
            image_size=image_size,
            grid_shape=grid_shape,
            labels=label,
            training_directory=training_dir,
            validation_directory=validation_dir,
            annotation_format=annotation_format,
            batch_size=batch_size,
            shuffle_seed=dataset_seed,
            upstream_tasks=[init_tensorflow_results],
        )
        object_detector = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.roadsigns_yolo_estimators",
            "keras_object_detectors",
            "init_object_detector",
            model_architecture=model_architecture,
            optimizer=optimizer,
            n_classes=n_classes,
            grid_size=grid_size,
            upstream_tasks=[init_tensorflow_results],
        )
        history = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.estimators",
            "methods",
            "fit",
            estimator=object_detector,
            x=training_ds,
            fit_kwargs=dict(
                nb_epochs=epochs,
                validation_data=validation_ds,
                callbacks=callbacks_list,
                verbose=2,
            ),
        )
        finetune_optimizer = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.evaluation",
            "tensorflow",
            "get_optimizer",
            optimizer=optimizer_name,
            learning_rate=1e-5,
            upstream_tasks=[history],
        )
        finetune_callbacks_list = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.evaluation",
            "tensorflow",
            "get_model_callbacks",
            callbacks_list=FINETUNE_CALLBACKS,
            upstream_tasks=[history],
        )
        finetune_history = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.roadsigns_yolo_estimators",
            "finetuning",
            "finetune",
            estimator=object_detector,
            model_architecture=model_architecture,
            optimizer=finetune_optimizer,
            skip=skip_finetune,
            x=training_ds,
            fit_kwargs=dict(
                nb_epochs=epochs,
                validation_data=validation_ds,
                callbacks=finetune_callbacks_list,
                verbose=2,
            ),
            upstream_tasks=[history],
        )
        logged_tensorflow_keras_estimator = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.tracking",
            "mlflow",
            "log_tensorflow_keras_estimator",
            estimator=object_detector,
            model_dir="model",
            log_model_kwargs={"custom_objects": {"YOLOLoss": object_detector}},
            upstream_tasks=[finetune_history],
        )
        model_version = pyplugs.call_task(  # noqa: F841
            f"{_PLUGINS_IMPORT_PATH}.registry",
            "mlflow",
            "add_model_to_registry",
            active_run=active_run,
            name=register_model_name,
            model_dir="model",
            upstream_tasks=[logged_tensorflow_keras_estimator],
        )
        log_training_csv = pyplugs.call_task(  # noqa: F841
            f"{_PLUGINS_IMPORT_PATH}.artifacts",
            "mlflow",
            "upload_file_as_artifact",
            artifact_path="training_log.csv",
            upstream_tasks=[history],
        )
        log_finetune_training_csv = pyplugs.call_task(  # noqa: F841
            f"{_PLUGINS_IMPORT_PATH}.artifacts",
            "mlflow",
            "upload_file_as_artifact",
            artifact_path="finetune_training_log.csv",
            upstream_tasks=[finetune_history],
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
