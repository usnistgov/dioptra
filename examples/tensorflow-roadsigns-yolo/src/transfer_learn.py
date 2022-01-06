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
            "patience": 20,
            "restore_best_weights": True,
        },
    },
]
LOGGER: BoundLogger = structlog.stdlib.get_logger()


def _coerce_comma_separated_ints(ctx, param, value):
    return tuple(int(x.strip()) for x in value.split(","))


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
    "--model-architecture",
    type=click.Choice(["mobilenet_v2", "tiny_yolo"], case_sensitive=False),
    default="mobilenet_v2",
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
        training_ds, validation_ds, n_classes = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.roadsigns_yolo_estimators",
            "data",
            "create_object_detection_dataset",
            root_directory=training_dir,
            image_size=image_size,
            seed=dataset_seed,
            validation_split=validation_split,
            batch_size=batch_size,
            upstream_tasks=[init_tensorflow_results],
        )
        object_detector = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.roadsigns_yolo_estimators",
            "keras_object_detectors",
            "init_object_detector",
            model_architecture=model_architecture,
            optimizer=optimizer,
            n_classes=n_classes,
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
        logged_tensorflow_keras_estimator = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.tracking",
            "mlflow",
            "log_tensorflow_keras_estimator",
            estimator=object_detector,
            model_dir="model",
            upstream_tasks=[history],
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
