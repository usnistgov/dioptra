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

import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import mlflow
import structlog
from structlog.stdlib import BoundLogger

from dioptra import pyplugs
from dioptra.sdk.object_detection.architectures import YOLOV1ObjectDetector
from dioptra.sdk.object_detection.data import TensorflowObjectDetectionData
from dioptra.sdk.object_detection.losses import YOLOV1Loss

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    from tensorflow.keras.optimizers import Optimizer

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


@pyplugs.register
def yolo_train(
    estimator: YOLOV1ObjectDetector,
    optimizer: Optimizer,
    loss: YOLOV1Loss,
    data: TensorflowObjectDetectionData,
    fit_kwargs: Optional[Dict[str, Any]] = None,
) -> Any:
    fit_kwargs = fit_kwargs or {}

    estimator.backbone.model.trainable = False
    estimator.compile(optimizer=optimizer, loss=loss)

    time_start: datetime.datetime = datetime.datetime.now()

    LOGGER.info(
        "Begin estimator training",
        timestamp=time_start.isoformat(),
    )

    estimator_fit_result: Any = estimator.fit(
        x=data.training_dataset,
        validation_data=data.validation_dataset,
        **fit_kwargs,
    )

    time_end: datetime.datetime = datetime.datetime.now()

    total_seconds: float = (time_end - time_start).total_seconds()
    total_minutes: float = total_seconds / 60

    mlflow.log_metric("training_time_in_minutes", total_minutes)
    LOGGER.info(
        "Estimator training complete",
        timestamp=time_end.isoformat(),
        total_minutes=total_minutes,
    )

    return estimator_fit_result


@pyplugs.register
def yolo_finetune(
    estimator: YOLOV1ObjectDetector,
    optimizer: Optimizer,
    loss: YOLOV1Loss,
    data: TensorflowObjectDetectionData,
    fit_kwargs: Optional[Dict[str, Any]] = None,
) -> Any:
    fit_kwargs = fit_kwargs or {}

    estimator.backbone.model.trainable = True
    estimator.compile(optimizer=optimizer, loss=loss)

    time_start: datetime.datetime = datetime.datetime.now()

    LOGGER.info(
        "Begin estimator finetuning",
        timestamp=time_start.isoformat(),
    )

    estimator_fit_result: Any = estimator.fit(
        x=data.training_dataset,
        validation_data=data.validation_dataset,
        **fit_kwargs,
    )

    time_end: datetime.datetime = datetime.datetime.now()

    total_seconds: float = (time_end - time_start).total_seconds()
    total_minutes: float = total_seconds / 60

    mlflow.log_metric("finetuning_time_in_minutes", total_minutes)
    LOGGER.info(
        "Estimator finetuning complete",
        timestamp=time_end.isoformat(),
        total_minutes=total_minutes,
    )

    return estimator_fit_result


@pyplugs.register
def yolo_load_best_checkpoint(
    estimator: YOLOV1ObjectDetector,
    checkpoints_dir: Path | str,
    weights_file_name: str = "weights.hdf5",
) -> None:
    weights_file_path = Path(checkpoints_dir).resolve() / weights_file_name

    if weights_file_path.exists():
        LOGGER.info(
            "Checkpoint found, loading model weights.",
            checkpoints_dir=str(checkpoints_dir),
            weights_file_name=weights_file_name,
        )
        estimator.load_weights(str(weights_file_path))

    else:
        LOGGER.info(
            "No checkpoint found, model weights will not change.",
            checkpoints_dir=str(checkpoints_dir),
            weights_file_name=weights_file_name,
        )
