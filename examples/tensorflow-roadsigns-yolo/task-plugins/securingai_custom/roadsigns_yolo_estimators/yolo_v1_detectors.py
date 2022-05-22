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
"""Neural network object detectors implemented in Tensorflow/Keras."""

from __future__ import annotations

from types import FunctionType
from typing import Dict, List, Optional, Tuple, Union

import structlog
from structlog.stdlib import BoundLogger

from mitre.securingai import pyplugs
from mitre.securingai.sdk.exceptions import TensorflowDependencyError
from mitre.securingai.sdk.utilities.decorators import require_package
from mitre.securingai.sdk.object_detection.architectures import (
    MobileNetV2YOLOV1Detector,
    MobileNetV2SimpleYOLOV1Detector,
    MobileNetV2TwoHeadedYOLOV1Detector,
)
from mitre.securingai.sdk.object_detection.losses import YOLOV1Loss

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    from tensorflow.keras import Model
    from tensorflow.keras.metrics import Metric
    from tensorflow.keras.optimizers import Optimizer

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


@pyplugs.register
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def init_yolo_v1_detectors(
    model_architecture: str,
    optimizer: Optimizer,
    n_bounding_boxes: int,
    n_classes: int,
    loss: str = "yolo_v1_loss",
    metrics: Optional[List[Union[Metric, FunctionType]]] = None,
    input_shape: Optional[Tuple[int, int, int]] = None,
) -> Model:
    object_detector: Model = YOLO_V1_DETECTORS_REGISTRY[model_architecture](
        input_shape=input_shape,
        n_bounding_boxes=n_bounding_boxes,
        n_classes=n_classes,
    )
    object_detector_loss = YOLOV1Loss() if loss == "yolo_v1_loss" else loss
    object_detector.compile(
        loss=object_detector_loss,
        optimizer=optimizer,
        metrics=metrics if metrics else None,
    )

    return object_detector


YOLO_V1_DETECTORS_REGISTRY: Dict[str, Model] = dict(
    mobilenetv2_yolo_v1_detector=MobileNetV2YOLOV1Detector,
    mobilenetv2_simple_yolo_v1_detector=MobileNetV2SimpleYOLOV1Detector,
    mobilenetv2_two_headed_yolo_v1_detector=MobileNetV2TwoHeadedYOLOV1Detector,
)
