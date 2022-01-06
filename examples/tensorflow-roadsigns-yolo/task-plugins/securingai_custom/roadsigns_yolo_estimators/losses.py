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

from .utils import convert_cellbox_to_corner_bbox

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    import tensorflow as tf

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


COORD_WEIGHT = 5
NOOBJ_WEIGHT = 0.5

# source: https://github.com/GiaKhangLuu/YOLOv1_from_scratch
@tf.function
def yolo_loss(y_true, y_pred):
    y_true = tf.Variable(y_true)
    y_pred = tf.Variable(y_pred)

    # Get xywh, cfd, class
    true_cellbox = y_true[:, :, :, :4]
    true_obj = y_true[:, :, :, 4]
    true_cls = y_true[:, :, :, 5:]

    n_classes = tf.cast(tf.shape(true_cls)[-1], dtype=tf.int32)
    n_bounding_boxes = tf.cast((tf.shape(y_pred)[-1] - n_classes) / 5, dtype=tf.int32)
    elems_range = tf.range(n_bounding_boxes, dtype=tf.float32)

    # pred_cellboxes = []
    # pred_objs = []

    # pred_cellboxes = tf.TensorArray(tf.float32, size=n_bounding_boxes)
    # pred_objs = tf.TensorArray(tf.float32, size=n_bounding_boxes)

    # for i in range(n_bounding_boxes):
    #     pred_cellboxes.append(y_pred[:, :, :, (5 * i) : (5 * i + 4)])
    #     pred_objs.append(y_pred[:, :, :, (5 * i + 4)])

    # for i in tf.range(n_bounding_boxes):
    #     pred_cellboxes.write(i, y_pred[:, :, :, (5 * i) : (5 * i + 4)])
    #     pred_objs.write(i, y_pred[:, :, :, (5 * i + 4)])

    # tf.map_fn(fn=lambda i: pred_cellboxes.write(i, y_pred[:, :, :, (5 * i) : (5 * i + 4)]), elems=tf.range(n_bounding_boxes))
    # tf.map_fn(fn=lambda i: pred_objs.write(i, y_pred[:, :, :, (5 * i + 4)]), elems=tf.range(n_bounding_boxes))

    # pred_cellboxes = pred_cellboxes.stack()
    # pred_objs = pred_objs.stack()

    pred_cellboxes = tf.map_fn(
        fn=lambda i: y_pred[
            :,
            :,
            :,
            (5 * tf.cast(i, dtype=tf.int32)) : (5 * tf.cast(i, dtype=tf.int32) + 4),
        ],
        elems=elems_range,
    )
    pred_objs = tf.map_fn(
        fn=lambda i: y_pred[:, :, :, (5 * tf.cast(i, dtype=tf.int32) + 4)],
        elems=elems_range,
    )

    pred_cls = y_pred[:, :, :, (5 * n_bounding_boxes) :]

    # Convert cell box to corner bbox to compute iou
    true_corner_bbox = convert_cellbox_to_corner_bbox(true_cellbox, true_obj)

    # pred_corner_bboxes = []
    # for pred_cellbox in pred_cellboxes:
    #     pred_corner_bboxes.append(convert_cellbox_to_corner_bbox(pred_cellbox))

    # pred_corner_bboxes = tf.TensorArray(tf.float32, size=n_bounding_boxes)
    # for i in tf.range(n_bounding_boxes):
    #     pred_corner_bboxes.write(i, convert_cellbox_to_corner_bbox(pred_cellboxes[i]))

    # pred_corner_bboxes = pred_corner_bboxes.stack()

    # tf.map_fn(fn=lambda i: pred_corner_bboxes.write(i, convert_cellbox_to_corner_bbox(pred_cellboxes[i])), elems=tf.range(n_bounding_boxes))
    pred_corner_bboxes = tf.map_fn(
        fn=lambda i: convert_cellbox_to_corner_bbox(
            pred_cellboxes[tf.cast(i, dtype=tf.int32)]
        ),
        elems=elems_range,
    )

    # Compute iou
    # iou_boxes = []
    # for pred_corner_bbox in pred_corner_bboxes:
    #     iou_boxes.append(iou(pred_corner_bbox, true_corner_bbox))
    # iou_boxes = tf.TensorArray(tf.float32, size=n_bounding_boxes)
    # for i in tf.range(n_bounding_boxes):
    #     iou_boxes.write(i, iou(pred_corner_bboxes[i], true_corner_bbox))

    # tf.map_fn(fn=lambda i: iou_boxes.write(i, iou(pred_corner_bboxes[i], true_corner_bbox)), elems=tf.range(n_bounding_boxes))
    # iou_boxes = iou_boxes.stack()

    iou_boxes = tf.map_fn(
        fn=lambda i: iou(
            pred_corner_bboxes[tf.cast(i, dtype=tf.int32)], true_corner_bbox
        ),
        elems=elems_range,
    )

    # Get the highest iou
    ious = tf.transpose(iou_boxes, [1, 2, 3, 0])
    # ious = tf.stack(iou_boxes.stack(), axis=-1)

    best_iou = tf.cast(tf.math.argmax(ious, axis=-1), dtype=tf.float32)

    # Compute xy and wh losses
    xy_loss = compute_xy_loss(
        true_cellbox[:, :, :, :2],
        pred_cellboxes[0, :, :, :, :2],
        pred_cellboxes[1, :, :, :, :2],
        true_obj,
        best_iou,
    )
    wh_loss = compute_wh_loss(
        true_cellbox[:, :, :, 2:],
        pred_cellboxes[0, :, :, :, :2],
        pred_cellboxes[1, :, :, :, :2],
        true_obj,
        best_iou,
    )

    # Compute obj. loss
    obj_loss = compute_obj_loss(true_obj, pred_objs[0], pred_objs[1], best_iou)

    # Compute no obj. loss
    no_obj_loss = compute_no_obj_loss(true_obj, pred_objs[0], pred_objs[1])

    # Compute class distribution loss
    cls_loss = compute_class_dist_loss(true_cls, pred_cls, true_obj)

    yolo_loss = (
        COORD_WEIGHT * (xy_loss + wh_loss)
        + obj_loss
        + NOOBJ_WEIGHT * no_obj_loss
        + cls_loss
    )

    return yolo_loss


def compute_xy_loss(target_xy, box1_xy, box2_xy, mask, best_iou):
    sse_xy_1 = tf.reduce_sum(tf.square(target_xy - box1_xy), axis=-1)
    sse_xy_2 = tf.reduce_sum(tf.square(target_xy - box2_xy), axis=-1)

    xy_predictor_1 = sse_xy_1 * mask * (1 - best_iou)
    xy_predictor_2 = sse_xy_2 * mask * best_iou
    xy_predictor = xy_predictor_1 + xy_predictor_2

    xy_loss = tf.reduce_mean(tf.reduce_sum(xy_predictor, axis=(1, 2)))

    return xy_loss


def compute_wh_loss(target_wh, box1_wh, box2_wh, mask, best_iou):
    target_wh = tf.sqrt(target_wh)
    box1_wh, box2_wh = tf.sqrt(tf.abs(box1_wh)), tf.sqrt(tf.abs(box2_wh))

    sse_wh_1 = tf.reduce_sum(tf.square(target_wh - box1_wh), axis=-1)
    sse_wh_2 = tf.reduce_sum(tf.square(target_wh - box2_wh), axis=-1)

    wh_predictor_1 = sse_wh_1 * mask * (1 - best_iou)
    wh_predictor_2 = sse_wh_2 * mask * best_iou
    wh_predictor = wh_predictor_1 + wh_predictor_2

    wh_loss = tf.reduce_mean(tf.reduce_sum(wh_predictor, axis=(1, 2)))

    return wh_loss


def compute_obj_loss(target_obj, box1_obj, box2_obj, best_iou):
    pred_obj_1 = box1_obj * target_obj * (1 - best_iou)
    pred_obj_2 = box2_obj * target_obj * best_iou
    pred_obj = pred_obj_1 + pred_obj_2

    sqrt_err_obj = tf.square(target_obj - pred_obj)

    obj_loss = tf.reduce_mean(tf.reduce_sum(sqrt_err_obj, axis=(1, 2)))

    return obj_loss


def compute_no_obj_loss(target_obj, box1_obj, box2_obj):
    target_no_obj_mask = 1 - target_obj

    pred_no_obj_1 = box1_obj * target_no_obj_mask
    pred_no_obj_2 = box2_obj * target_no_obj_mask

    sqr_err_no_obj_1 = tf.square((target_obj * target_no_obj_mask) - pred_no_obj_1)
    sqr_err_no_obj_2 = tf.square((target_obj * target_no_obj_mask) - pred_no_obj_2)
    sqr_err_no_obj = sqr_err_no_obj_1 + sqr_err_no_obj_2

    no_obj_loss = tf.reduce_mean(tf.reduce_sum(sqr_err_no_obj, axis=(1, 2)))

    return no_obj_loss


def compute_class_dist_loss(target_cls, pred_cls, mask):
    sse_cls = tf.reduce_sum(tf.square(target_cls - pred_cls), axis=-1)
    sse_cls = sse_cls * mask

    cls_loss = tf.reduce_mean(tf.reduce_sum(sse_cls, axis=(1, 2)))

    return cls_loss


def iou(box_1, box_2):
    # Find the intersection coordinate
    x1 = tf.maximum(box_1[:, :, :, 0], box_2[:, :, :, 0])
    y1 = tf.maximum(box_1[:, :, :, 1], box_2[:, :, :, 1])
    x2 = tf.minimum(box_1[:, :, :, 2], box_2[:, :, :, 2])
    y2 = tf.minimum(box_1[:, :, :, 3], box_2[:, :, :, 3])

    # Compute area
    inter_area = tf.maximum(0.0, x2 - x1) * tf.maximum(0.0, y2 - y1)
    box_1_area = tf.abs(
        (box_1[:, :, :, 2] - box_1[:, :, :, 0])
        * (box_1[:, :, :, 3] - box_1[:, :, :, 1])
    )
    box_2_area = tf.abs(
        (box_2[:, :, :, 2] - box_1[:, :, :, 0])
        * (box_2[:, :, :, 3] - box_1[:, :, :, 1])
    )

    return inter_area / (box_1_area + box_2_area - inter_area)
