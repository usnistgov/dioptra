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

from typing import Any

import structlog
from structlog.stdlib import BoundLogger

from dioptra import pyplugs
from dioptra.sdk.exceptions import TensorflowDependencyError
from dioptra.sdk.utilities.decorators import require_package
from dioptra.sdk.object_detection.architectures import YOLOV1ObjectDetector
from dioptra.sdk.object_detection.bounding_boxes.iou import (
    TensorflowBoundingBoxesBatchedGridIOU,
)
from dioptra.sdk.object_detection.bounding_boxes.postprocessing import (
    BoundingBoxesYOLOV1PostProcessing,
    TensorflowBoundingBoxesYOLOV1NMS,
    TensorflowBoundingBoxesYOLOV1Confluence,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pyplugs.register
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def init_bbox_iou(
    grid_shape: tuple[int, int] | YOLOV1ObjectDetector,
) -> TensorflowBoundingBoxesBatchedGridIOU:
    if isinstance(grid_shape, YOLOV1ObjectDetector):
        grid_shape = grid_shape.output_grid_shape

    return TensorflowBoundingBoxesBatchedGridIOU.on_grid_shape(grid_shape)


@pyplugs.register
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def init_bbox_postprocessor(
    postprocessor: str,
    grid_shape: tuple[int, int] | YOLOV1ObjectDetector,
    postprocessor_kwargs: dict[str, Any] | None = None
) -> BoundingBoxesYOLOV1PostProcessing:
    if isinstance(grid_shape, YOLOV1ObjectDetector):
        grid_shape = grid_shape.output_grid_shape

    postprocessor_kwargs = postprocessor_kwargs or {}
    bbox_postprocessor: BoundingBoxesYOLOV1PostProcessing = (
        BBOX_POSTPROCESSING_REGISTRY[postprocessor].on_grid_shape(
            grid_shape=grid_shape,
            **postprocessor_kwargs
        )
    )
    return bbox_postprocessor


BBOX_POSTPROCESSING_REGISTRY: dict[str, BoundingBoxesYOLOV1PostProcessing] = dict(
    nms=TensorflowBoundingBoxesYOLOV1NMS,
    confluence=TensorflowBoundingBoxesYOLOV1Confluence,
)
