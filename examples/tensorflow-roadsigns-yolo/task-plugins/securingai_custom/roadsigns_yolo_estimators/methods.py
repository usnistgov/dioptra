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

import structlog
from structlog.stdlib import BoundLogger

from mitre.securingai import pyplugs
from mitre.securingai.sdk.exceptions import TensorflowDependencyError
from mitre.securingai.sdk.utilities.decorators import require_package

from .utils import convert_cellbox_to_corner_bbox

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    import tensorflow as tf
    from tensorflow.image import combined_non_max_suppression

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


# source: https://github.com/GiaKhangLuu/YOLOv1_from_scratch
@pyplugs.register
@pyplugs.task_nout(4)
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def post_process_tensor_output(pred_tensor_output, n_classes):
    pred_box_1 = pred_tensor_output[..., :4]
    pred_cfd_1 = pred_tensor_output[..., 4]
    pred_box_2 = pred_tensor_output[..., 5:9]
    pred_cfd_2 = pred_tensor_output[..., 9]
    pred_cls_dist = pred_tensor_output[..., 10:]

    pred_corner_bbox_1 = convert_cellbox_to_corner_bbox(pred_box_1)
    pred_corner_bbox_2 = convert_cellbox_to_corner_bbox(pred_box_2)

    # To use combined_nms() method from TF we must change
    # [x1, y1, x2, y2] to [y1, x1, y2, x2]
    box1 = tf.reshape(
        tf.gather(pred_corner_bbox_1, [1, 0, 3, 2], axis=-1), shape=(-1, 7 * 7, 1, 4)
    )
    box2 = tf.reshape(
        tf.gather(pred_corner_bbox_2, [1, 0, 3, 2], axis=-1), shape=(-1, 7 * 7, 1, 4)
    )
    boxes = tf.concat([box1, box2], axis=1)

    scores1 = tf.reshape(
        tf.expand_dims(pred_cfd_1, axis=-1) * pred_cls_dist,
        shape=(-1, 7 * 7, n_classes),
    )
    scores2 = tf.reshape(
        tf.expand_dims(pred_cfd_2, axis=-1) * pred_cls_dist,
        shape=(-1, 7 * 7, n_classes),
    )
    scores = tf.concat([scores1, scores2], axis=1)

    boxes, scores, classes, nums = combined_non_max_suppression(
        boxes,
        scores,
        max_output_size_per_class=10,
        max_total_size=49,
        iou_threshold=0.5,
        score_threshold=0.5,
    )

    return boxes, scores, classes, nums
