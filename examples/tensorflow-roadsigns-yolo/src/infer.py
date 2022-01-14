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
    "--model-name",
    type=click.STRING,
    help="Name of model to load from registry",
)
@click.option(
    "--model-version",
    type=click.STRING,
    help="Version of model to load from registry",
)
@click.option(
    "--batch-size",
    type=click.INT,
    help="Batch size to use when training a single epoch",
    default=32,
)
@click.option(
    "--seed",
    type=click.INT,
    help="Set the entry point rng seed",
    default=-1,
)
def infer(
    data_dir,
    image_size,
    model_name,
    model_version,
    batch_size,
    seed,
):
    LOGGER.info(
        "Execute MLFlow entry point",
        entry_point="infer",
        data_dir=data_dir,
        image_size=image_size,
        model_name=model_name,
        model_version=model_version,
        batch_size=batch_size,
        seed=seed,
    )

    with mlflow.start_run() as active_run:
        flow: Flow = init_infer_flow()
        state = flow.run(
            parameters=dict(
                training_dir=data_dir,
                image_size=image_size,
                model_name=model_name,
                model_version=model_version,
                batch_size=batch_size,
                seed=seed,
            )
        )

    return state


def init_infer_flow() -> Flow:
    with Flow("Train Model") as flow:
        (
            training_dir,
            image_size,
            model_name,
            model_version,
            batch_size,
            seed,
        ) = (
            Parameter("training_dir"),
            Parameter("image_size"),
            Parameter("model_name"),
            Parameter("model_version"),
            Parameter("batch_size"),
            Parameter("seed"),
        )
        seed, rng = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.random", "rng", "init_rng", seed=seed
        )
        tensorflow_global_seed = pyplugs.call_task(
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
            ),
        )
        testing_ds, n_classes = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.roadsigns_yolo_estimators",
            "data",
            "create_object_detection_testing_dataset",
            root_directory=training_dir,
            image_size=image_size,
            batch_size=batch_size,
            upstream_tasks=[init_tensorflow_results],
        )
        object_detector = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.registry",
            "mlflow",
            "load_tensorflow_keras_classifier",
            name=model_name,
            version=model_version,
            upstream_tasks=[init_tensorflow_results],
        )
        predictions = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.estimators",
            "methods",
            "predict",
            estimator=object_detector,
            x=testing_ds,
        )
        boxes, scores, classes, nums = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.roadsigns_yolo_estimators",
            "methods",
            "post_process_tensor_output",
            pred_tensor_output=predictions,
            n_classes=n_classes,
        )
        predictions_serialized = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.roadsigns_yolo_estimators",
            "data",
            "serialize_array_to_npy",
            array=predictions,
            output_dir="object_detection_predictions",
            output_filename="predictions.npy",
        )
        boxes_serialized = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.roadsigns_yolo_estimators",
            "data",
            "serialize_tensor_to_npy",
            tensor=boxes,
            output_dir="object_detection_predictions",
            output_filename="boxes.npy",
        )
        scores_serialized = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.roadsigns_yolo_estimators",
            "data",
            "serialize_tensor_to_npy",
            tensor=scores,
            output_dir="object_detection_predictions",
            output_filename="scores.npy",
        )
        classes_serialized = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.roadsigns_yolo_estimators",
            "data",
            "serialize_tensor_to_npy",
            tensor=classes,
            output_dir="object_detection_predictions",
            output_filename="classes.npy",
        )
        nums_serialized = pyplugs.call_task(
            f"{_CUSTOM_PLUGINS_IMPORT_PATH}.roadsigns_yolo_estimators",
            "data",
            "serialize_tensor_to_npy",
            tensor=nums,
            output_dir="object_detection_predictions",
            output_filename="nums.npy",
        )
        upload_directory_results = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.artifacts",
            "mlflow",
            "upload_directory_as_tarball_artifact",
            source_dir="object_detection_predictions",
            tarball_filename="object_detection_predictions.tar.gz",
            upstream_tasks=[
                predictions_serialized,
                boxes_serialized,
                scores_serialized,
                classes_serialized,
                nums_serialized,
            ],
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
        _ = infer()
