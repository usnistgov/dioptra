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
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import click
import mlflow
import structlog
from prefect import Flow, Parameter
from prefect.utilities.logging import get_logger as get_prefect_logger
from structlog.stdlib import BoundLogger

from dioptra import pyplugs
from dioptra.sdk.utilities.contexts import plugin_dirs
from dioptra.sdk.utilities.logging import (
    StderrLogStream,
    StdoutLogStream,
    attach_stdout_stream_handler,
    clear_logger_handlers,
    configure_structlog,
    set_logging_level,
)

_PLUGINS_IMPORT_PATH: str = "dioptra_builtins"
_CUSTOM_PLUGINS_IMPORT_PATH: str = "dioptra_custom"
CALLBACKS: list[dict[str, Any]] = [
    {
        "name": "ModelCheckpoint",
        "parameters": {
            "filepath": "/".join(
                [
                    str(Path.cwd() / "checkpoints"),
                    "weights.hdf5",
                ]
            ),
            "monitor": "val_loss",
            "mode": "min",
            "save_best_only": True,
            "save_weights_only": True,
        },
    },
    {
        "name": "CSVLogger",
        "parameters": {
            "filename": "train_log.csv",
        },
    },
    {
        "name": "TerminateOnNaN",
        "parameters": {},
    },
]
LOGGER: BoundLogger = structlog.stdlib.get_logger()


def _coerce_string_none_to_none_obj(ctx, param, value):
    if value.strip().lower() == "none":
        return None

    return value.strip().lower()


def _coerce_comma_separated_ints(ctx, param, value):
    return tuple(int(x.strip()) for x in value.split(","))


def _coerce_comma_separated_list_of_strings(ctx, param, value):
    return [str(x.strip()) for x in value.split(",")]


@click.command()
@click.option(
    "--training-dir",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, resolve_path=True, readable=True
    ),
    help=(
        "Training data directory for object detection dataset in PASCAL VOC format "
        "(in container)"
    ),
)
@click.option(
    "--validation-dir",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, resolve_path=True, readable=True
    ),
    help=(
        "Validation data directory for object detection dataset in PASCAL VOC format "
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
    "--augmentations",
    type=click.Choice(["imgaug_minimal", "imgaug_light", "imgaug_heavy", "none"], case_sensitive=False),
    help="Apply a data augmentation pipeline to the training images.",
    callback=_coerce_string_none_to_none_obj,
    default="none",
)
@click.option(
    "--model-architecture",
    type=click.Choice(["yolo_v1"], case_sensitive=False),
    default="yolo_v1",
    help="Model architecture",
)
@click.option(
    "--backbone",
    type=click.Choice(["efficientnetb0", "efficientnetb1", "efficientnetb2", "efficientnetb3", "efficientnetb4", "efficientnetb5", "efficientnetb6", "efficientnetb7", "mobilenetv2"], case_sensitive=False),
    default="efficientnetb1",
    help="YOLO Backbone architecture",
)
@click.option(
    "--detector",
    type=click.Choice(["original", "shallow", "two_headed"], case_sensitive=False),
    default="two_headed",
    help="YOLO Detector architecture",
)
@click.option(
    "--wh-loss",
    type=click.Choice(["sq_relative_diff", "sq_diff_sqrt"], case_sensitive=False),
    default="sq_relative_diff",
    help="For the localization loss, controls how the width/height term is calculated.",
)
@click.option(
    "--classification-loss",
    type=click.Choice(["categorical_crossentropy", "binary_crossentropy", "original"], case_sensitive=False),
    default="categorical_crossentropy",
    help="Classification loss",
)
@click.option(
    "--epochs",
    type=click.INT,
    help="Number of epochs to train model",
    default=30,
)
@click.option(
    "--labels",
    type=click.STRING,
    callback=_coerce_comma_separated_list_of_strings,
    help="The full list of labels used in the dataset",
    default="crosswalk,speedlimit,stop,trafficlight",
)
@click.option(
    "--n-bounding-boxes",
    type=click.INT,
    help=(
        "Number of bounding boxes to use per grid square. YOLO v1 paper uses a value "
        "of 2."
    ),
    default=2,
)
@click.option(
    "--n-classes",
    type=click.INT,
    help="Number of label classes in the dataset.",
    default=4,
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
    "--learning-rate", type=click.FLOAT, help="Model learning rate", default=3e-5
)
@click.option(
    "--optimizer",
    type=click.Choice(["Adam", "Adagrad", "RMSprop", "SGD"], case_sensitive=True),
    help="Optimizer to use to train the model",
    default="Adam",
)
@click.option(
    "--seed",
    type=click.INT,
    help="Set the entry point rng seed",
    default=-1,
)
def train(
    training_dir,
    validation_dir,
    image_size,
    augmentations,
    model_architecture,
    backbone,
    detector,
    wh_loss,
    classification_loss,
    epochs,
    labels,
    n_bounding_boxes,
    n_classes,
    batch_size,
    register_model_name,
    learning_rate,
    optimizer,
    seed,
):
    LOGGER.info(
        "Execute MLFlow entry point",
        entry_point="transfer_learn",
        training_dir=training_dir,
        validation_dir=validation_dir,
        image_size=image_size,
        augmentations=augmentations,
        model_architecture=model_architecture,
        backbone=backbone,
        detector=detector,
        wh_loss=wh_loss,
        classification_loss=classification_loss,
        epochs=epochs,
        labels=labels,
        n_bounding_boxes=n_bounding_boxes,
        n_classes=n_classes,
        batch_size=batch_size,
        register_model_name=register_model_name,
        learning_rate=learning_rate,
        optimizer=optimizer,
        seed=seed,
    )
    (Path.cwd() / "checkpoints").mkdir(mode=0o777, parents=True, exist_ok=True)

    with mlflow.start_run() as active_run:
        flow: Flow = init_train_flow()
        state = flow.run(
            parameters=dict(
                active_run=active_run,
                training_dir=training_dir,
                validation_dir=validation_dir,
                image_size=image_size,
                augmentations=augmentations,
                model_architecture=model_architecture,
                backbone=backbone,
                detector=detector,
                wh_loss=wh_loss,
                classification_loss=classification_loss,
                epochs=epochs,
                labels=labels,
                n_bounding_boxes=n_bounding_boxes,
                n_classes=n_classes,
                batch_size=batch_size,
                register_model_name=register_model_name,
                learning_rate=learning_rate,
                optimizer_name=optimizer,
                seed=seed,
            )
        )

    return state


def init_train_flow() -> Flow:
    with Flow("Train Model") as flow:
        (
            active_run,
            training_dir,
            validation_dir,
            image_size,
            augmentations,
            model_architecture,
            backbone,
            detector,
            wh_loss,
            classification_loss,
            epochs,
            labels,
            n_bounding_boxes,
            n_classes,
            batch_size,
            register_model_name,
            learning_rate,
            optimizer_name,
            seed,
        ) = (
            Parameter("active_run"),
            Parameter("training_dir"),
            Parameter("validation_dir"),
            Parameter("image_size"),
            Parameter("augmentations"),
            Parameter("model_architecture"),
            Parameter("backbone"),
            Parameter("detector"),
            Parameter("wh_loss"),
            Parameter("classification_loss"),
            Parameter("epochs"),
            Parameter("labels"),
            Parameter("n_bounding_boxes"),
            Parameter("n_classes"),
            Parameter("batch_size"),
            Parameter("register_model_name"),
            Parameter("learning_rate"),
            Parameter("optimizer_name"),
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
        object_detector = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.roadsigns_yolo",
            "yolo_detectors",
            "init_yolo_detectors",
            model_architecture=model_architecture,
            input_shape=image_size,
            n_bounding_boxes=n_bounding_boxes,
            n_classes=n_classes,
            backbone=backbone,
            detector=detector,
            upstream_tasks=[init_tensorflow_results],
        )
        data = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.roadsigns_yolo",
            "data",
            "create_object_detection_dataset",
            image_size=image_size,
            grid_shape=object_detector,
            labels=labels,
            training_directory=training_dir,
            validation_directory=validation_dir,
            augmentations=augmentations,
            batch_size=batch_size,
            shuffle_seed=dataset_seed,
        )
        bbox_iou = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.roadsigns_yolo",
            "bbox",
            "init_bbox_iou",
            grid_shape=object_detector,
        )
        loss = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.roadsigns_yolo",
            "loss",
            "init_yolo_v1_loss",
            bbox_iou=bbox_iou,
            wh_loss=wh_loss,
            classification_loss=classification_loss,
        )
        history = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.roadsigns_yolo",
            "yolo_train",
            "yolo_train",
            estimator=object_detector,
            optimizer=optimizer,
            loss=loss,
            data=data,
            fit_kwargs=dict(
                epochs=epochs,
                callbacks=callbacks_list,
                verbose=2,
            ),
        )
        yolo_load_best_checkpoint = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.roadsigns_yolo",
            "yolo_train",
            "yolo_load_best_checkpoint",
            estimator=object_detector,
            checkpoints_dir="checkpoints",
            weights_file_name="weights.hdf5",
            upstream_tasks=[history],
        )
        logged_tensorflow_keras_estimator = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.tracking",
            "mlflow",
            "log_tensorflow_keras_estimator",
            estimator=object_detector,
            model_dir="model",
            upstream_tasks=[yolo_load_best_checkpoint],
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
            artifact_path="train_log.csv",
            upstream_tasks=[history],
        )

    return flow


if __name__ == "__main__":
    log_level: str = os.getenv("DIOPTRA_JOB_LOG_LEVEL", default="INFO")
    as_json: bool = True if os.getenv("DIOPTRA_JOB_LOG_AS_JSON") else False

    clear_logger_handlers(get_prefect_logger())
    attach_stdout_stream_handler(as_json)
    set_logging_level(log_level)
    configure_structlog()

    with plugin_dirs(), StdoutLogStream(as_json), StderrLogStream(as_json):
        _ = train()
