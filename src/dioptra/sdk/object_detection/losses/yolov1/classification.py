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
    from tensorflow.keras.losses import BinaryCrossentropy, CategoricalCrossentropy

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


class ComputeLabelsLossFn(Protocol):
    def __call__(
        self,
        true_labels: Tensor,
        pred_labels: Tensor,
        true_object: Tensor,
    ) -> Tensor:
        pass


class YOLOV1ClassificationLoss(object):
    def __init__(
        self,
        labels_weight: float = 1.0,
        loss_type: str = "categorical_crossentropy",
    ) -> None:
        self._labels_weight = labels_weight
        self._loss_type = loss_type
        self._compute_labels_loss = self._get_loss_fn(loss_type=loss_type)
        self._binary_crossentropy = BinaryCrossentropy(
            reduction=tf.keras.losses.Reduction.NONE
        )
        self._categorical_crossentropy = CategoricalCrossentropy(
            reduction=tf.keras.losses.Reduction.NONE
        )

    def __call__(self, *args, **kwargs) -> Tensor:
        return self.call(*args, **kwargs)

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def call(
        self, pred_labels: Tensor, true_labels: Tensor, true_object: Tensor
    ) -> Tensor:
        labels_loss = self._compute_labels_loss(
            true_labels=true_labels,
            pred_labels=pred_labels,
            true_object=true_object,
        )

        return self._labels_weight * labels_loss

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def _compute_original_loss(
        self,
        true_labels: Tensor,
        pred_labels: Tensor,
        true_object: Tensor,
    ) -> Tensor:
        sse_labels = tf.reduce_sum(tf.square(true_labels - pred_labels), axis=-1)
        reduction_axes = tf.range(tf.rank(sse_labels), dtype=tf.int32)[1:]
        sse_labels = tf.reduce_sum(true_object * sse_labels, axis=reduction_axes)

        # Count the number of bounding boxes in cells with an object that are
        # responsible for prediction
        num_obj_reduction_axes = tf.range(tf.rank(true_object), dtype=tf.int32)[1:]
        num_obj = tf.reduce_sum(
            tf.cast(true_object > 0, tf.float32), axis=num_obj_reduction_axes
        )

        return sse_labels / (num_obj + 1e-6)

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def _compute_categorical_crossentropy_loss(
        self,
        true_labels: Tensor,
        pred_labels: Tensor,
        true_object: Tensor,
    ) -> Tensor:
        cce_labels = self._categorical_crossentropy(
            y_true=true_labels, y_pred=pred_labels
        )
        reduction_axes = tf.range(tf.rank(cce_labels), dtype=tf.int32)[1:]
        cce_labels = tf.reduce_sum(true_object * cce_labels, axis=reduction_axes)

        # Count the number of bounding boxes in cells with an object that are
        # responsible for prediction
        num_obj_reduction_axes = tf.range(tf.rank(true_object), dtype=tf.int32)[1:]
        num_obj = tf.reduce_sum(
            tf.cast(true_object > 0, tf.float32), axis=num_obj_reduction_axes
        )

        return cce_labels / (num_obj + 1e-6)

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def _compute_binary_crossentropy_loss(
        self,
        true_labels: Tensor,
        pred_labels: Tensor,
        true_object: Tensor,
    ) -> Tensor:
        cce_labels = self._binary_crossentropy(y_true=true_labels, y_pred=pred_labels)
        reduction_axes = tf.range(tf.rank(cce_labels), dtype=tf.int32)[1:]
        cce_labels = tf.reduce_sum(true_object * cce_labels, axis=reduction_axes)

        # Count the number of bounding boxes in cells with an object that are
        # responsible for prediction
        num_obj_reduction_axes = tf.range(tf.rank(true_object), dtype=tf.int32)[1:]
        num_obj = tf.reduce_sum(
            tf.cast(true_object > 0, tf.float32), axis=num_obj_reduction_axes
        )

        return cce_labels / (num_obj + 1e-6)

    def _get_loss_fn(self, loss_type: str) -> ComputeLabelsLossFn:
        loss_fn_registry: dict[str, ComputeLabelsLossFn] = {
            "categorical_crossentropy": self._compute_categorical_crossentropy_loss,
            "binary_crossentropy": self._compute_binary_crossentropy_loss,
            "original": self._compute_original_loss,
        }
        loss_fn: ComputeLabelsLossFn | None = loss_fn_registry.get(loss_type)

        if loss_fn is None:
            raise KeyError(
                f"The loss type '{loss_type}' is not supported. The following types "
                f"are currently available: {list(loss_fn_registry.keys())}"
            )

        return loss_fn
