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

from dioptra.sdk.object_detection.bounding_boxes.iou import (
    TensorflowBoundingBoxesBatchedGridIOU,
)

from .classification import YOLOV1ClassificationLoss
from .localization import YOLOV1LocalizationLoss

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    import tensorflow as tf
    from tensorflow import Tensor
    from tensorflow.keras.losses import Loss

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


class YOLOV1Loss(Loss):
    def __init__(
        self,
        bbox_grid_iou: TensorflowBoundingBoxesBatchedGridIOU,
        coord_weight: float = 5.0,
        object_weight: float = 5.0,
        no_object_weight: float = 1.0,
        labels_weight: float = 1.0,
        wh_loss_type: str = "sq_relative_diff",
        classification_loss_type: str = "categorical_crossentropy",
        name: str = "yolov1_loss",
        **kwargs,
    ) -> None:
        super().__init__(name=name, **kwargs)
        self._bbox_grid_iou = bbox_grid_iou
        self._coord_weight = coord_weight
        self._object_weight = object_weight
        self._no_object_weight = no_object_weight
        self._labels_weight = labels_weight
        self._wh_loss_type = wh_loss_type
        self._classification_loss_type = classification_loss_type

        self._classification_loss = YOLOV1ClassificationLoss(
            labels_weight=labels_weight, loss_type=classification_loss_type
        )
        self._localization_loss = YOLOV1LocalizationLoss(
            coord_weight=coord_weight,
            object_weight=object_weight,
            no_object_weight=no_object_weight,
            wh_loss_type=wh_loss_type,
        )

    def call(self, y_true, y_pred):
        true_bboxes_cell_xywh = y_true[0]
        true_labels = y_true[1]
        true_object = y_true[2]
        true_no_object = y_true[3]

        pred_bboxes_cell_xywh = y_pred[0]
        pred_object_conf = y_pred[1]
        pred_labels = y_pred[2]

        (
            responsible_pred_bboxes_cell_xywh,
            responsible_pred_object_conf,
            not_responsible_pred_object_conf,
        ) = self._select_responsible_bboxes(
            true_bboxes_cell_xywh=true_bboxes_cell_xywh,
            pred_bboxes_cell_xywh=pred_bboxes_cell_xywh,
            pred_object_conf=pred_object_conf,
        )
        true_object_conf = self._compute_true_object_conf(
            true_bboxes_cell_xywh=true_bboxes_cell_xywh,
            pred_bboxes_cell_xywh=pred_bboxes_cell_xywh,
            true_object=true_object,
        )

        # Compute localization loss
        localization_loss = self._localization_loss(
            responsible_pred_bboxes_cell_xywh=responsible_pred_bboxes_cell_xywh,
            pred_object_conf=pred_object_conf,
            responsible_pred_object_conf=responsible_pred_object_conf,
            not_responsible_pred_object_conf=not_responsible_pred_object_conf,
            true_bboxes_cell_xywh=true_bboxes_cell_xywh,
            true_object_conf=true_object_conf,
            true_object=true_object,
            true_no_object=true_no_object,
        )

        # Compute classification loss
        classification_loss = self._classification_loss(
            pred_labels=pred_labels,
            true_labels=true_labels,
            true_object=true_object,
        )

        # Compute total loss
        yolo_loss = localization_loss + classification_loss

        return yolo_loss

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def _compute_true_object_conf(
        self,
        true_bboxes_cell_xywh: Tensor,
        pred_bboxes_cell_xywh: Tensor,
        true_object: Tensor,
    ) -> Tensor:
        pred_bbox_max_iou = self._bbox_grid_iou.max_iou(
            bboxes_cell_xywh1=pred_bboxes_cell_xywh,
            bboxes_cell_xywh2=true_bboxes_cell_xywh,
        )

        return pred_bbox_max_iou * true_object

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def _select_responsible_bboxes(
        self,
        true_bboxes_cell_xywh: Tensor,
        pred_bboxes_cell_xywh: Tensor,
        pred_object_conf: Tensor,
    ) -> Tuple[Tensor, Tensor, Tensor]:
        (
            responsible_pred_bboxes_cell_xywh,
            responsible_pred_object_conf,
            not_responsible_pred_object_conf,
        ) = self._bbox_grid_iou.select_max_iou_bboxes(
            bboxes_cell_xywh=pred_bboxes_cell_xywh,
            bboxes_conf=pred_object_conf,
            bboxes_cell_xywh_ground_truth=true_bboxes_cell_xywh,
        )
        responsible_pred_bboxes_cell_xywh = tf.expand_dims(
            responsible_pred_bboxes_cell_xywh, axis=-2
        )

        return (
            responsible_pred_bboxes_cell_xywh,
            responsible_pred_object_conf,
            not_responsible_pred_object_conf,
        )
