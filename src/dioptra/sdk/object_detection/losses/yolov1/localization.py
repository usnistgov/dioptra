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

from typing import Protocol

import structlog
from structlog.stdlib import BoundLogger

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    import tensorflow as tf
    from tensorflow import Tensor

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


class ComputeWhLossFn(Protocol):
    def __call__(
        self,
        true_bboxes_cell_wh: Tensor,
        pred_bboxes_cell_wh: Tensor,
        true_object: Tensor,
    ) -> Tensor:
        pass


class YOLOV1LocalizationLoss(object):
    def __init__(
        self,
        coord_weight: float = 5.0,
        object_weight: float = 5.0,
        no_object_weight: float = 1.0,
        wh_loss_type: str = "sq_relative_diff",
    ) -> None:
        self._coord_weight = coord_weight
        self._object_weight = object_weight
        self._no_object_weight = no_object_weight
        self._wh_loss_type = wh_loss_type
        self._compute_wh_loss = self._get_wh_loss_fn(wh_loss_type=wh_loss_type)

    def __call__(self, *args, **kwargs) -> Tensor:
        return self.call(*args, **kwargs)

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def call(
        self,
        responsible_pred_bboxes_cell_xywh: Tensor,
        pred_object_conf: Tensor,
        responsible_pred_object_conf: Tensor,
        not_responsible_pred_object_conf: Tensor,
        true_bboxes_cell_xywh: Tensor,
        true_object_conf: Tensor,
        true_object: Tensor,
        true_no_object: Tensor,
    ) -> Tensor:
        # Compute xy and wh losses
        xy_loss = self._compute_xy_loss(
            true_bboxes_cell_xy=true_bboxes_cell_xywh[..., :2],
            pred_bboxes_cell_xy=responsible_pred_bboxes_cell_xywh[..., :2],
            true_object=true_object,
        )
        wh_loss = self._compute_wh_loss(
            true_bboxes_cell_wh=true_bboxes_cell_xywh[..., 2:],
            pred_bboxes_cell_wh=responsible_pred_bboxes_cell_xywh[..., 2:],
            true_object=true_object,
        )

        # Compute obj. loss
        obj_loss = self._compute_obj_loss(
            true_object_conf=true_object_conf,
            pred_object_conf=responsible_pred_object_conf,
            true_object=true_object,
        )

        # Compute no obj. loss
        no_obj_loss = self._compute_no_obj_loss(
            pred_object_conf=pred_object_conf,
            not_responsible_pred_object_conf=not_responsible_pred_object_conf,
            true_object=true_object,
            true_no_object=true_no_object,
        )

        return (
            self._coord_weight * (xy_loss + wh_loss)
            + self._object_weight * obj_loss
            + self._no_object_weight * no_obj_loss
        )

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def _compute_xy_loss(
        self,
        true_bboxes_cell_xy: Tensor,
        pred_bboxes_cell_xy: Tensor,
        true_object: Tensor,
    ) -> Tensor:
        sse_xy = tf.reduce_sum(
            tf.square(true_bboxes_cell_xy - pred_bboxes_cell_xy), axis=-1
        )
        reduction_axes = tf.range(tf.rank(sse_xy), dtype=tf.int32)[1:]
        sse_xy = tf.reduce_sum(
            tf.expand_dims(true_object, axis=-1) * sse_xy, axis=reduction_axes
        )

        # Count the number of bounding boxes in cells with an object that are
        # responsible for prediction
        num_obj_reduction_axes = tf.range(tf.rank(true_object), dtype=tf.int32)[1:]
        num_obj = tf.reduce_sum(
            tf.cast(true_object > 0, tf.float32), axis=num_obj_reduction_axes
        )

        return sse_xy / (num_obj + 1e-6) / 2

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def _compute_wh_square_diff_sqrt_loss(
        self,
        true_bboxes_cell_wh: Tensor,
        pred_bboxes_cell_wh: Tensor,
        true_object: Tensor,
    ) -> Tensor:
        sse_wh = tf.reduce_sum(
            tf.square(tf.sqrt(true_bboxes_cell_wh) - tf.sqrt(pred_bboxes_cell_wh)),
            axis=-1,
        )
        reduction_axes = tf.range(tf.rank(sse_wh), dtype=tf.int32)[1:]
        sse_wh = tf.reduce_sum(
            tf.expand_dims(true_object, axis=-1) * sse_wh, axis=reduction_axes
        )

        # Count the number of bounding boxes in cells with an object that are
        # responsible for prediction
        num_obj_reduction_axes = tf.range(tf.rank(true_object), dtype=tf.int32)[1:]
        num_obj = tf.reduce_sum(
            tf.cast(true_object > 0, tf.float32), axis=num_obj_reduction_axes
        )

        return sse_wh / (num_obj + 1e-6) / 2

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def _compute_wh_square_relative_diff_loss(
        self,
        true_bboxes_cell_wh: Tensor,
        pred_bboxes_cell_wh: Tensor,
        true_object: Tensor,
    ) -> Tensor:
        sse_wh = tf.reduce_sum(
            tf.square(
                (true_bboxes_cell_wh - pred_bboxes_cell_wh)
                / (true_bboxes_cell_wh + 1e-6)
            ),
            axis=-1,
        )
        reduction_axes = tf.range(tf.rank(sse_wh), dtype=tf.int32)[1:]
        sse_wh = tf.reduce_sum(
            tf.expand_dims(true_object, axis=-1) * sse_wh, axis=reduction_axes
        )

        # Count the number of bounding boxes in cells with an object that are
        # responsible for prediction
        num_obj_reduction_axes = tf.range(tf.rank(true_object), dtype=tf.int32)[1:]
        num_obj = tf.reduce_sum(
            tf.cast(true_object > 0, tf.float32), axis=num_obj_reduction_axes
        )

        return sse_wh / (num_obj + 1e-6) / 2

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def _compute_obj_loss(
        self,
        true_object_conf: Tensor,
        pred_object_conf: Tensor,
        true_object: Tensor,
    ) -> Tensor:
        sq_diff_obj = tf.square(true_object_conf - pred_object_conf)
        reduction_axes = tf.range(tf.rank(sq_diff_obj), dtype=tf.int32)[1:]
        sum_sq_diff_obj_cells = tf.reduce_sum(
            true_object * sq_diff_obj, axis=reduction_axes
        )

        # Count the number of bounding boxes in cells with an object that are
        # responsible for prediction
        num_boxes_from_obj_cells_reduction_axes = tf.range(
            tf.rank(true_object), dtype=tf.int32
        )[1:]
        num_boxes_from_obj_cells = tf.reduce_sum(
            tf.cast(true_object > 0, tf.float32),
            axis=num_boxes_from_obj_cells_reduction_axes,
        )

        return sum_sq_diff_obj_cells / (num_boxes_from_obj_cells + 1e-6) / 2

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def _compute_no_obj_loss(
        self,
        pred_object_conf: Tensor,
        not_responsible_pred_object_conf: Tensor,
        true_object: Tensor,
        true_no_object: Tensor,
    ) -> Tensor:
        n_bounding_boxes = tf.cast(tf.shape(pred_object_conf)[-1], tf.float32)

        # Confidence sum of squares for bounding boxes in cells without an object
        sq_diff_boxes_from_no_obj_cells = tf.square(pred_object_conf)
        no_obj_cells_reduction_axes = tf.range(
            tf.rank(sq_diff_boxes_from_no_obj_cells), dtype=tf.int32
        )[1:]
        sum_sq_diff_boxes_from_no_obj_cells = tf.reduce_sum(
            tf.expand_dims(true_no_object, axis=-1) * sq_diff_boxes_from_no_obj_cells,
            axis=no_obj_cells_reduction_axes,
        )

        # Confidence sum of squares for bounding boxes in cells with an object that
        # are not responsible for prediction
        sq_diff_extra_boxes_from_obj_cells = tf.square(not_responsible_pred_object_conf)
        obj_cells_reduction_axes = tf.range(
            tf.rank(sq_diff_extra_boxes_from_obj_cells), dtype=tf.int32
        )[1:]
        sum_sq_diff_extra_boxes_from_obj_cells = tf.reduce_sum(
            tf.expand_dims(true_object, axis=-1) * sq_diff_extra_boxes_from_obj_cells,
            axis=obj_cells_reduction_axes,
        )

        # Count the number of bounding boxes in cells without an object
        num_boxes_from_obj_cells_reduction_axes = tf.range(
            tf.rank(true_object),
            dtype=tf.int32,
        )[1:]
        num_boxes_from_obj_cells = (n_bounding_boxes - 1) * tf.reduce_sum(
            tf.cast(true_object > 0, tf.float32),
            axis=num_boxes_from_obj_cells_reduction_axes,
        )

        # Count the number of bounding boxes in cells with an object that are not
        # responsible for prediction
        num_boxes_from_no_obj_cells_reduction_axes = tf.range(
            tf.rank(true_no_object),
            dtype=tf.int32,
        )[1:]
        num_boxes_from_no_obj_cells = n_bounding_boxes * tf.reduce_sum(
            tf.cast(true_no_object > 0, tf.float32),
            axis=num_boxes_from_no_obj_cells_reduction_axes,
        )

        return (
            (
                sum_sq_diff_boxes_from_no_obj_cells
                + sum_sq_diff_extra_boxes_from_obj_cells
            )
            / (num_boxes_from_obj_cells + num_boxes_from_no_obj_cells + 1e-6)
            / 2
        )

    def _get_wh_loss_fn(self, wh_loss_type: str) -> ComputeWhLossFn:
        wh_loss_fn_registry: dict[str, ComputeWhLossFn] = {
            "sq_relative_diff": self._compute_wh_square_relative_diff_loss,
            "sq_diff_sqrt": self._compute_wh_square_diff_sqrt_loss,
        }
        wh_loss_fn: ComputeWhLossFn | None = wh_loss_fn_registry.get(wh_loss_type)

        if wh_loss_fn is None:
            raise KeyError(
                f"The wh loss type '{wh_loss_type}' is not supported. The following "
                f"types are currently available: {list(wh_loss_fn_registry.keys())}"
            )

        return wh_loss_fn
