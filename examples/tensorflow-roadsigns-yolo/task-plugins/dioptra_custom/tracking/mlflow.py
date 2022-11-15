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
"""A task plugin module for using the MLFlow Tracking service."""

from __future__ import annotations

from typing import Any, Dict, Optional

import mlflow
import structlog
from structlog.stdlib import BoundLogger

from dioptra import pyplugs
from dioptra.sdk.exceptions import TensorflowDependencyError
from dioptra.sdk.object_detection.architectures import YOLOV1ObjectDetector
from dioptra.sdk.utilities.decorators import require_package

from .yolo_v1 import log_model as log_yolo_v1_model

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    from tensorflow.keras.models import Model

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


@pyplugs.register
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def log_tensorflow_keras_estimator(
    estimator: Model,
    model_dir: str,
    log_model_kwargs: Optional[Dict[str, Any]] = None,
) -> None:
    """Logs a Keras estimator trained during the current run to the MLFlow registry.

    Args:
        estimator: A trained Keras estimator.
        model_dir: The relative artifact directory where MLFlow should save the
            model.
    """
    if log_model_kwargs is None:
        log_model_kwargs = {}

    if isinstance(estimator, YOLOV1ObjectDetector):
        log_yolo_v1_model(model=estimator, artifact_path=model_dir, **log_model_kwargs)

    else:
        mlflow.keras.log_model(
            keras_model=estimator, artifact_path=model_dir, **log_model_kwargs
        )

    LOGGER.info(
        "Tensorflow Keras model logged to tracking server",
        model_dir=model_dir,
    )
