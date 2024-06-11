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

import math
from typing import cast

import structlog
from structlog.stdlib import BoundLogger

from dioptra.sdk.object_detection.bounding_boxes.coordinates import (
    TensorflowBoundingBoxesBatchedGrid,
)
from dioptra.sdk.object_detection.bounding_boxes.postprocessing.bounding_boxes_postprocessing import (  # noqa: B950
    BoundingBoxesYOLOV1PostProcessing,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    import tensorflow as tf
    from tensorflow import Tensor
    from tensorflow.image import combined_non_max_suppression

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


class TensorflowBoundingBoxesYOLOV1NMS(BoundingBoxesYOLOV1PostProcessing):
    def __init__(
        self,
        bounding_boxes_batched_grid: TensorflowBoundingBoxesBatchedGrid,
        max_output_size_per_class: int,
        max_total_size: int,
        iou_threshold: float,
        score_threshold: float,
    ) -> None:
        self._bbox_batched_grid = bounding_boxes_batched_grid
        self._max_output_size_per_class = max_output_size_per_class
        self._max_total_size = max_total_size
        self._iou_threshold = iou_threshold
        self._score_threshold = score_threshold

    @classmethod
    def on_grid_shape(
        cls,
        grid_shape: tuple[int, int],
        max_output_size_per_class: int = 20,
        iou_threshold: float = 0.5,
        score_threshold: float = 0.5,
    ) -> TensorflowBoundingBoxesYOLOV1NMS:
        return cls(
            bounding_boxes_batched_grid=(
                TensorflowBoundingBoxesBatchedGrid.on_grid_shape(grid_shape=grid_shape)
            ),
            max_output_size_per_class=max_output_size_per_class,
            max_total_size=math.prod(grid_shape),
            iou_threshold=iou_threshold,
            score_threshold=score_threshold,
        )

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def postprocess(
        self, bboxes_cell_xywh: Tensor, bboxes_conf: Tensor, bboxes_labels: Tensor
    ) -> tuple[Tensor, Tensor, Tensor, Tensor]:
        batch_size = tf.cast(tf.shape(bboxes_cell_xywh)[0], tf.int32)
        num_boxes = tf.cast(tf.reduce_prod(tf.shape(bboxes_cell_xywh)[1:4]), tf.int32)
        num_labels = tf.cast(tf.shape(bboxes_labels)[-1], tf.int32)

        boxes = tf.reshape(
            self._from_cell_xywh_to_corner(bboxes_cell_xywh=bboxes_cell_xywh),
            shape=(batch_size, num_boxes, 1, 4),
        )
        scores = tf.reshape(
            self._calculate_prediction_scores(
                bboxes_conf=bboxes_conf, bboxes_labels=bboxes_labels
            ),
            shape=(batch_size, num_boxes, num_labels),
        )

        return cast(
            tuple[Tensor, Tensor, Tensor, Tensor],
            combined_non_max_suppression(
                boxes=boxes,
                scores=scores,
                max_output_size_per_class=self._max_output_size_per_class,
                max_total_size=self._max_total_size,
                iou_threshold=self._iou_threshold,
                score_threshold=self._score_threshold,
            ),
        )

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.int32),
            tf.TensorSpec(None, tf.int32),
        ]
    )
    def embed(
        self, bboxes_corner: Tensor, bboxes_labels: Tensor, n_classes: Tensor
    ) -> tuple[Tensor, Tensor, Tensor, Tensor]:
        return cast(
            tuple[Tensor, Tensor, Tensor, Tensor],
            self._bbox_batched_grid.embed(
                bboxes_corner=bboxes_corner,
                bboxes_labels=bboxes_labels,
                n_classes=n_classes,
            ),
        )

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def _from_cell_xywh_to_corner(self, bboxes_cell_xywh: Tensor) -> Tensor:
        n_bounding_boxes = tf.cast(tf.shape(bboxes_cell_xywh)[-2], tf.int32)
        bboxes_corner = self._bbox_batched_grid.from_cell_xywh_to_corner(
            bboxes_cell_xywh=bboxes_cell_xywh,
            n_bounding_boxes=n_bounding_boxes,
        )

        return tf.gather(bboxes_corner, [1, 0, 3, 2], axis=-1)

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def _calculate_prediction_scores(
        self, bboxes_conf: Tensor, bboxes_labels: Tensor
    ) -> Tensor:
        n_bounding_boxes = tf.cast(tf.shape(bboxes_conf)[-1], tf.int32)
        bboxes_labels = tf.tile(
            tf.expand_dims(bboxes_labels, axis=-2),
            multiples=(1, 1, 1, n_bounding_boxes, 1),
        )

        return tf.expand_dims(bboxes_conf, axis=-1) * bboxes_labels
