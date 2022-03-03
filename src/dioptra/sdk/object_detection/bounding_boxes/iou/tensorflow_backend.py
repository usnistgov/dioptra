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

from typing import Tuple

import structlog
from structlog.stdlib import BoundLogger

from dioptra.sdk.object_detection.bounding_boxes.coordinates import (
    TensorflowBoundingBoxesBatchedGrid,
)

from .bounding_boxes_iou import BoundingBoxesBatchedGridIOU, BoundingBoxesIOU

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    import tensorflow as tf
    from tensorflow import Tensor

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


class TensorflowBoundingBoxesIOU(BoundingBoxesIOU):
    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def iou(self, bbox_corner1, bbox_corner2):
        x1 = tf.maximum(bbox_corner1[..., 0], bbox_corner2[..., 0])
        y1 = tf.maximum(bbox_corner1[..., 1], bbox_corner2[..., 1])
        x2 = tf.minimum(bbox_corner1[..., 2], bbox_corner2[..., 2])
        y2 = tf.minimum(bbox_corner1[..., 3], bbox_corner2[..., 3])

        intersection_area = tf.maximum(0.0, (x2 - x1)) * tf.maximum(0.0, (y2 - y1))
        box_1_area = (bbox_corner1[..., 2] - bbox_corner1[..., 0]) * (
            bbox_corner1[..., 3] - bbox_corner1[..., 1]
        )
        box_2_area = (bbox_corner2[..., 2] - bbox_corner2[..., 0]) * (
            bbox_corner2[..., 3] - bbox_corner2[..., 1]
        )
        union_area = box_1_area + box_2_area - intersection_area

        return intersection_area / union_area


class TensorflowBoundingBoxesBatchedGridIOU(BoundingBoxesBatchedGridIOU):
    def __init__(
        self,
        bounding_boxes_iou: TensorflowBoundingBoxesIOU,
        bounding_boxes_batched_grid: TensorflowBoundingBoxesBatchedGrid,
    ) -> None:
        self._bounding_boxes_iou = bounding_boxes_iou
        self._bbox_batched_grid = bounding_boxes_batched_grid

    @classmethod
    def on_grid_shape(
        cls, grid_shape: Tuple[int, int]
    ) -> TensorflowBoundingBoxesBatchedGridIOU:
        return cls(
            bounding_boxes_iou=TensorflowBoundingBoxesIOU(),
            bounding_boxes_batched_grid=(
                TensorflowBoundingBoxesBatchedGrid.on_grid_shape(grid_shape=grid_shape)
            ),
        )

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def iou(self, bboxes_cell_xywh1: Tensor, bboxes_cell_xywh2: Tensor) -> Tensor:
        n_bounding_boxes1 = tf.cast(tf.shape(bboxes_cell_xywh1)[-2], tf.int32)
        n_bounding_boxes2 = tf.cast(tf.shape(bboxes_cell_xywh2)[-2], tf.int32)
        max_n_bounding_boxes = tf.cast(n_bounding_boxes1 * n_bounding_boxes2, tf.int32)

        bboxes_corner1 = self._bbox_batched_grid.from_cell_xywh_to_corner(
            bboxes_cell_xywh=bboxes_cell_xywh1, n_bounding_boxes=n_bounding_boxes1
        )
        bboxes_corner2 = self._bbox_batched_grid.from_cell_xywh_to_corner(
            bboxes_cell_xywh=bboxes_cell_xywh2, n_bounding_boxes=n_bounding_boxes2
        )

        tiled_bboxes_corner1 = tf.cond(
            pred=tf.math.greater(max_n_bounding_boxes, n_bounding_boxes1),
            true_fn=lambda: tf.tile(
                bboxes_corner1, multiples=(1, 1, 1, n_bounding_boxes2, 1)
            ),
            false_fn=lambda: bboxes_corner1,
        )
        tiled_bboxes_corner2 = tf.cond(
            pred=tf.math.greater(max_n_bounding_boxes, n_bounding_boxes2),
            true_fn=lambda: tf.tile(
                bboxes_corner2, multiples=(1, 1, 1, n_bounding_boxes1, 1)
            ),
            false_fn=lambda: bboxes_corner2,
        )

        return self._bounding_boxes_iou.iou(tiled_bboxes_corner1, tiled_bboxes_corner2)

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def max_iou(self, bboxes_cell_xywh1: Tensor, bboxes_cell_xywh2: Tensor) -> Tensor:
        iou_areas = self.iou(bboxes_cell_xywh1, bboxes_cell_xywh2)

        return tf.reduce_max(iou_areas, axis=-1)

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def select_max_iou_bboxes(
        self,
        bboxes_cell_xywh: Tensor,
        bboxes_conf: Tensor,
        bboxes_cell_xywh_ground_truth: Tensor,
    ) -> Tuple[Tensor, Tensor, Tensor]:
        batch_size = tf.cast(tf.shape(bboxes_cell_xywh)[0], tf.int32)
        n_bounding_boxes = tf.cast(tf.shape(bboxes_cell_xywh)[-2], tf.int32)
        bboxes_corner = self._bbox_batched_grid.from_cell_xywh_to_corner(
            bboxes_cell_xywh=bboxes_cell_xywh, n_bounding_boxes=n_bounding_boxes
        )
        bboxes_corner_ground_truth = self._bbox_batched_grid.from_cell_xywh_to_corner(
            bboxes_cell_xywh=bboxes_cell_xywh_ground_truth, n_bounding_boxes=1
        )

        iou_areas = self.iou(bboxes_corner, bboxes_corner_ground_truth)

        batch_indices = self._generate_flattened_batch_indices(batch_size=batch_size)
        dim_i_indices = self._generate_flattened_dim_i_indices(batch_size=batch_size)
        dim_j_indices = self._generate_flattened_dim_j_indices(batch_size=batch_size)

        sorted_iou_indices = tf.math.top_k(iou_areas, k=n_bounding_boxes).indices
        max_iou_indices = tf.reshape(
            sorted_iou_indices[..., :1],
            (
                batch_size,
                self._bbox_batched_grid.cell_nrow * self._bbox_batched_grid.cell_ncol,
                1,
            ),
        )
        non_max_iou_indices = tf.reshape(
            sorted_iou_indices[..., 1:],
            (
                batch_size,
                self._bbox_batched_grid.cell_nrow
                * self._bbox_batched_grid.cell_ncol
                * (n_bounding_boxes - 1),
                1,
            ),
        )

        bboxes_gather_indices = self._prepare_gather_indices(
            batch_size=batch_size,
            n_bounding_boxes=1,
            batch_indices=batch_indices,
            dim_i_indices=dim_i_indices,
            dim_j_indices=dim_j_indices,
            bbox_indices=max_iou_indices,
        )
        no_bboxes_gather_indices = self._prepare_gather_indices(
            batch_size=batch_size,
            n_bounding_boxes=n_bounding_boxes - 1,
            batch_indices=batch_indices,
            dim_i_indices=dim_i_indices,
            dim_j_indices=dim_j_indices,
            bbox_indices=non_max_iou_indices,
        )

        selected_bboxes = tf.reshape(
            tf.gather_nd(params=bboxes_cell_xywh, indices=bboxes_gather_indices),
            shape=(
                batch_size,
                self._bbox_batched_grid.cell_nrow,
                self._bbox_batched_grid.cell_ncol,
                4,
            ),
        )
        selected_bboxes_conf = tf.reshape(
            tf.gather_nd(params=bboxes_conf, indices=bboxes_gather_indices),
            shape=(
                batch_size,
                self._bbox_batched_grid.cell_nrow,
                self._bbox_batched_grid.cell_ncol,
            ),
        )
        selected_no_bboxes_conf = tf.reshape(
            tf.gather_nd(params=bboxes_conf, indices=no_bboxes_gather_indices),
            shape=(
                batch_size,
                self._bbox_batched_grid.cell_nrow,
                self._bbox_batched_grid.cell_ncol,
                n_bounding_boxes - 1,
            ),
        )

        return selected_bboxes, selected_bboxes_conf, selected_no_bboxes_conf

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.int32),
        ]
    )
    def _generate_flattened_batch_indices(self, batch_size: Tensor) -> Tensor:
        batch_indices = tf.repeat(
            tf.range(batch_size),
            repeats=self._bbox_batched_grid.cell_nrow
            * self._bbox_batched_grid.cell_ncol,
        )
        batch_indices = tf.reshape(
            batch_indices,
            shape=(
                batch_size,
                self._bbox_batched_grid.cell_nrow * self._bbox_batched_grid.cell_ncol,
                1,
            ),
        )

        return tf.cast(batch_indices, tf.int32)

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.int32),
        ]
    )
    def _generate_flattened_dim_i_indices(self, batch_size: Tensor) -> Tensor:
        dim_i_indices = tf.transpose(
            tf.tile(
                tf.expand_dims(
                    tf.range(self._bbox_batched_grid.cell_nrow, dtype=tf.int32), axis=0
                ),
                multiples=[self._bbox_batched_grid.cell_ncol, 1],
            )
        )
        dim_i_indices = tf.reshape(
            dim_i_indices,
            (self._bbox_batched_grid.cell_nrow * self._bbox_batched_grid.cell_ncol, 1),
        )
        dim_i_indices = tf.broadcast_to(
            dim_i_indices,
            shape=(
                batch_size,
                self._bbox_batched_grid.cell_nrow * self._bbox_batched_grid.cell_ncol,
                1,
            ),
        )

        return tf.cast(dim_i_indices, tf.int32)

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.int32),
        ]
    )
    def _generate_flattened_dim_j_indices(self, batch_size: Tensor) -> Tensor:
        dim_j_indices = tf.tile(
            tf.expand_dims(
                tf.range(self._bbox_batched_grid.cell_ncol, dtype=tf.int32), axis=0
            ),
            multiples=[self._bbox_batched_grid.cell_nrow, 1],
        )
        dim_j_indices = tf.reshape(
            dim_j_indices,
            (self._bbox_batched_grid.cell_nrow * self._bbox_batched_grid.cell_ncol, 1),
        )
        dim_j_indices = tf.broadcast_to(
            dim_j_indices,
            shape=(
                batch_size,
                self._bbox_batched_grid.cell_nrow * self._bbox_batched_grid.cell_ncol,
                1,
            ),
        )

        return tf.cast(dim_j_indices, tf.int32)

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.int32),
            tf.TensorSpec(None, tf.int32),
            tf.TensorSpec(None, tf.int32),
            tf.TensorSpec(None, tf.int32),
            tf.TensorSpec(None, tf.int32),
            tf.TensorSpec(None, tf.int32),
        ]
    )
    def _prepare_gather_indices(
        self,
        batch_size: Tensor,
        n_bounding_boxes: Tensor,
        batch_indices: Tensor,
        dim_i_indices: Tensor,
        dim_j_indices: Tensor,
        bbox_indices: Tensor,
    ) -> Tensor:
        batch_indices = tf.reshape(
            tf.tile(batch_indices, multiples=(1, 1, n_bounding_boxes)),
            shape=(
                batch_size,
                self._bbox_batched_grid.cell_nrow
                * self._bbox_batched_grid.cell_ncol
                * n_bounding_boxes,
                1,
            ),
        )
        dim_i_indices = tf.reshape(
            tf.tile(dim_i_indices, multiples=(1, 1, n_bounding_boxes)),
            shape=(
                batch_size,
                self._bbox_batched_grid.cell_nrow
                * self._bbox_batched_grid.cell_ncol
                * n_bounding_boxes,
                1,
            ),
        )
        dim_j_indices = tf.reshape(
            tf.tile(dim_j_indices, multiples=(1, 1, n_bounding_boxes)),
            shape=(
                batch_size,
                self._bbox_batched_grid.cell_nrow
                * self._bbox_batched_grid.cell_ncol
                * n_bounding_boxes,
                1,
            ),
        )

        return tf.concat(
            [batch_indices, dim_i_indices, dim_j_indices, bbox_indices], axis=2
        )
