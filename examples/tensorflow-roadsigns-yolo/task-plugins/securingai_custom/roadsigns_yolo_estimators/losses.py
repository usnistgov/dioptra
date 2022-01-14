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
import tensorflow as tf
from tensorflow.keras.losses import Loss


# source: https://github.com/GiaKhangLuu/YOLOv1_from_scratch
class YOLOLoss(Loss):
    def call(self, y_true, y_pred):
        n_bounding_boxes = self._get_n_bounding_boxes(y_pred)
        grid_shape = self._get_grid_shape(y_pred)

        # Get ground truth
        true_cellbox = self._get_true_cellbox(y_true, n_bounding_boxes)
        true_obj = self._get_true_obj(y_true, n_bounding_boxes)
        true_cls = self._get_true_cls(y_true, n_bounding_boxes)

        # Get predictions
        pred_cellboxes = self._get_pred_cellboxes(y_pred)
        pred_objs = self._get_pred_objs(y_pred)
        pred_cls = self._get_pred_cls(y_pred)

        # Convert cell box to corner bbox to compute iou
        true_corner_bbox = self._convert_cellbox_to_corner_bbox_masked(
            true_cellbox, grid_shape, true_obj
        )
        pred_corner_bboxes = self._convert_cellbox_to_corner_bbox(
            pred_cellboxes, grid_shape
        )

        # Get the highest iou
        ious = self._iou(pred_corner_bboxes, true_corner_bbox)
        pred_responsible_cellboxes_mask = self._get_pred_responsible_cellboxes_mask(
            ious, n_bounding_boxes
        )

        # Build the 1obj_ij mask
        obj_responsible_cellboxes_mask = true_obj * pred_responsible_cellboxes_mask

        # Build the 1noobj_ij mask
        no_obj_responsible_cellboxes_mask = (
            1 - true_obj
        ) * pred_responsible_cellboxes_mask

        # Compute xy and wh losses
        xy_loss = self._compute_xy_loss(
            true_cellbox[..., :2],
            pred_cellboxes[..., :2],
            obj_responsible_cellboxes_mask,
        )
        wh_loss = self._compute_wh_loss(
            true_cellbox[..., 2:],
            pred_cellboxes[..., 2:],
            obj_responsible_cellboxes_mask,
        )

        # Compute obj. loss
        obj_loss = self._compute_obj_loss(
            true_obj, pred_objs, obj_responsible_cellboxes_mask
        )

        # Compute no obj. loss
        no_obj_loss = self._compute_no_obj_loss(
            true_obj, pred_objs, no_obj_responsible_cellboxes_mask
        )

        # Compute class distribution loss
        cls_loss = self._compute_class_dist_loss(
            true_cls, pred_cls, obj_responsible_cellboxes_mask
        )

        COORD_WEIGHT = 5.0
        NOOBJ_WEIGHT = 0.5

        yolo_loss = (
            COORD_WEIGHT * (xy_loss + wh_loss)
            + obj_loss
            + NOOBJ_WEIGHT * no_obj_loss
            + cls_loss
        )

        return yolo_loss

    def _convert_cellbox_to_corner_bbox(self, cellbox, grid_shape):
        bbox = self._convert_cellbox_to_xywh(cellbox, grid_shape)
        x = bbox[..., 0]
        y = bbox[..., 1]
        w = bbox[..., 2]
        h = bbox[..., 3]

        x_min = x - (w / 2.0)
        y_min = y - (h / 2.0)
        x_max = x + (w / 2.0)
        y_max = y + (h / 2.0)

        corner_box = tf.stack([x_min, y_min, x_max, y_max], axis=-1)

        return corner_box

    def _convert_cellbox_to_corner_bbox_masked(self, cellbox, grid_shape, mask):
        bbox = self._convert_cellbox_to_xywh_masked(cellbox, grid_shape, mask)
        x = bbox[..., 0]
        y = bbox[..., 1]
        w = bbox[..., 2]
        h = bbox[..., 3]

        x_min = x - (w / 2.0)
        y_min = y - (h / 2.0)
        x_max = x + (w / 2.0)
        y_max = y + (h / 2.0)

        corner_box = tf.stack([x_min, y_min, x_max, y_max], axis=-1)

        return corner_box

    @staticmethod
    def _convert_cellbox_to_xywh(cellbox, grid_shape):
        x_offset = cellbox[..., 0]
        y_offset = cellbox[..., 1]
        w_h = cellbox[..., 2:]

        num_w_cells = grid_shape[1]
        num_h_cells = grid_shape[0]

        # w_cell_indices: [[0, 1, 2, ...], [0, 1, 2, ...], ...]
        # Use w_cell_indices to convert x_offset of a particular grid cell
        # location to x_center
        w_cell_indices = tf.range(num_w_cells)
        w_cell_indices = tf.reshape(
            tf.repeat(w_cell_indices, num_h_cells, 0), grid_shape
        )
        w_cell_indices = tf.broadcast_to(
            w_cell_indices, tf.roll(tf.shape(x_offset), axis=-1, shift=1)
        )
        w_cell_indices = tf.transpose(
            w_cell_indices,
            tf.roll(tf.range(tf.size(tf.shape(w_cell_indices))), axis=-1, shift=-1),
        )
        w_cell_indices = tf.cast(w_cell_indices, dtype=tf.float32)

        # h_cell_indices: [[0, 0, 0, ...], [1, 1, 1, ...], [2, 2, 2, ...], ....]
        # Use h_cell_indices to convert y_offset of a particular grid cell
        # location to y_center
        h_cell_indices = tf.range(num_h_cells)
        h_cell_indices = tf.broadcast_to(
            h_cell_indices, tf.roll(tf.shape(x_offset), axis=-1, shift=1)
        )
        h_cell_indices = tf.transpose(
            h_cell_indices,
            tf.roll(tf.range(tf.size(tf.shape(h_cell_indices))), axis=-1, shift=-1),
        )
        h_cell_indices = tf.cast(h_cell_indices, dtype=tf.float32)

        x_center = (x_offset + w_cell_indices) / tf.cast(num_w_cells, dtype=tf.float32)
        y_center = (y_offset + h_cell_indices) / tf.cast(num_h_cells, dtype=tf.float32)

        x_y = tf.stack([x_center, y_center], axis=-1)

        bbox = tf.concat([x_y, w_h], axis=-1)

        return bbox

    @staticmethod
    def _convert_cellbox_to_xywh_masked(cellbox, grid_shape, mask):
        x_offset = cellbox[..., 0]
        y_offset = cellbox[..., 1]
        w_h = cellbox[..., 2:]

        num_w_cells = grid_shape[1]
        num_h_cells = grid_shape[0]

        # w_cell_indices: [[0, 1, 2, ...], [0, 1, 2, ...], ...]
        # Use w_cell_indices to convert x_offset of a particular grid cell
        # location to x_center
        w_cell_indices = tf.range(num_w_cells)
        w_cell_indices = tf.reshape(
            tf.repeat(w_cell_indices, num_h_cells, 0), grid_shape
        )
        w_cell_indices = tf.broadcast_to(
            w_cell_indices, tf.roll(tf.shape(x_offset), axis=-1, shift=1)
        )
        w_cell_indices = tf.transpose(
            w_cell_indices,
            tf.roll(tf.range(tf.size(tf.shape(w_cell_indices))), axis=-1, shift=-1),
        )
        w_cell_indices = tf.cast(w_cell_indices, dtype=tf.float32)

        # h_cell_indices: [[0, 0, 0, ...], [1, 1, 1, ...], [2, 2, 2, ...], ....]
        # Use h_cell_indices to convert y_offset of a particular grid cell
        # location to y_center
        h_cell_indices = tf.range(num_h_cells)
        h_cell_indices = tf.broadcast_to(
            h_cell_indices, tf.roll(tf.shape(x_offset), axis=-1, shift=1)
        )
        h_cell_indices = tf.transpose(
            h_cell_indices,
            tf.roll(tf.range(tf.size(tf.shape(h_cell_indices))), axis=-1, shift=-1),
        )
        h_cell_indices = tf.cast(h_cell_indices, dtype=tf.float32)

        x_center = (x_offset + w_cell_indices) / tf.cast(num_w_cells, dtype=tf.float32)
        y_center = (y_offset + h_cell_indices) / tf.cast(num_h_cells, dtype=tf.float32)

        x_center *= mask
        y_center *= mask

        x_y = tf.stack([x_center, y_center], axis=-1)

        bbox = tf.concat([x_y, w_h], axis=-1)

        return bbox

    @staticmethod
    def _compute_xy_loss(target_xy, boxes_xy, mask):
        sse_xy = tf.reduce_sum(tf.square(target_xy - boxes_xy), axis=-1)
        xy_predictor = tf.reduce_sum(mask * sse_xy, axis=-1)
        xy_predictor_shape_indices = tf.range(tf.size(tf.shape(xy_predictor)))
        xy_loss = tf.reduce_mean(
            tf.reduce_sum(xy_predictor, axis=xy_predictor_shape_indices[-2:])
        )

        return xy_loss

    @staticmethod
    def _compute_wh_loss(target_wh, boxes_wh, mask):
        target_wh = tf.sqrt(target_wh)
        boxes_wh = tf.sqrt(tf.abs(boxes_wh))

        sse_wh = tf.reduce_sum(tf.square(target_wh - boxes_wh), axis=-1)
        wh_predictor = tf.reduce_sum(mask * sse_wh, axis=-1)
        wh_predictor_shape_indices = tf.range(tf.size(tf.shape(wh_predictor)))
        wh_loss = tf.reduce_mean(
            tf.reduce_sum(wh_predictor, axis=wh_predictor_shape_indices[-2:])
        )

        return wh_loss

    @staticmethod
    def _compute_obj_loss(target_obj, pred_obj, mask):
        sqrt_err_obj = tf.reduce_sum(mask * tf.square(target_obj - pred_obj), axis=-1)
        sqrt_err_obj_shape_indices = tf.range(tf.size(tf.shape(sqrt_err_obj)))
        obj_loss = tf.reduce_mean(
            tf.reduce_sum(sqrt_err_obj, axis=sqrt_err_obj_shape_indices[-2:])
        )

        return obj_loss

    @staticmethod
    def _compute_no_obj_loss(target_obj, pred_obj, mask):
        sqrt_err_no_obj = tf.reduce_sum(
            mask * tf.square(target_obj - pred_obj), axis=-1
        )
        sqrt_err_no_obj_shape_indices = tf.range(tf.size(tf.shape(sqrt_err_no_obj)))
        no_obj_loss = tf.reduce_mean(
            tf.reduce_sum(sqrt_err_no_obj, axis=sqrt_err_no_obj_shape_indices[-2:])
        )

        return no_obj_loss

    @staticmethod
    def _compute_class_dist_loss(target_cls, pred_cls, mask):
        sse_cls = mask * tf.reduce_sum(tf.square(target_cls - pred_cls), axis=-1)
        sse_cls_shape_indices = tf.range(tf.size(tf.shape(sse_cls)))
        cls_loss = tf.reduce_mean(
            tf.reduce_sum(sse_cls, axis=sse_cls_shape_indices[-2:])
        )

        return cls_loss

    @staticmethod
    def _iou(box_1, box_2):
        # Find the intersection coordinate
        x1 = tf.maximum(box_1[..., 0], box_2[..., 0])
        y1 = tf.maximum(box_1[..., 1], box_2[..., 1])
        x2 = tf.minimum(box_1[..., 2], box_2[..., 2])
        y2 = tf.minimum(box_1[..., 3], box_2[..., 3])

        # Compute area
        inter_area = tf.maximum(0.0, x2 - x1) * tf.maximum(0.0, y2 - y1)
        box_1_area = tf.abs(
            (box_1[..., 2] - box_1[..., 0]) * (box_1[..., 3] - box_1[..., 1])
        )
        box_2_area = tf.abs(
            (box_2[..., 2] - box_1[..., 0]) * (box_2[..., 3] - box_1[..., 1])
        )

        return inter_area / (box_1_area + box_2_area - inter_area)

    @staticmethod
    def _get_n_classes(tensor):
        return tf.cast(tf.shape(tensor)[-1] - 5, dtype=tf.int32)

    @staticmethod
    def _get_n_bounding_boxes(tensor):
        return tf.cast(tf.shape(tensor)[-2], dtype=tf.int32)

    @staticmethod
    def _get_grid_shape(tensor):
        return tf.cast(tf.shape(tensor)[-4:-2], dtype=tf.int32)

    @staticmethod
    def _get_true_cellbox(tensor, n_bounding_boxes):
        true_cellbox = tensor[..., :4]
        true_cellbox_shape = tf.cast(tf.shape(true_cellbox), dtype=tf.int32)
        true_cellbox_shape_indices = (
            tf.range(tf.size(true_cellbox_shape), dtype=tf.int32) + 1
        )
        return tf.transpose(
            tf.broadcast_to(
                true_cellbox,
                tf.concat([[n_bounding_boxes], true_cellbox_shape], axis=-1),
            ),
            tf.concat(
                [true_cellbox_shape_indices[:-1], [0], true_cellbox_shape_indices[-1:]],
                axis=-1,
            ),
        )

    @staticmethod
    def _get_true_obj(tensor, n_bounding_boxes):
        true_obj = tensor[..., 4]
        true_obj_shape = tf.cast(tf.shape(true_obj), dtype=tf.int32)
        true_obj_shape_indices = tf.range(tf.size(true_obj_shape), dtype=tf.int32) + 1
        return tf.transpose(
            tf.broadcast_to(
                true_obj,
                tf.concat([[n_bounding_boxes], true_obj_shape], axis=-1),
            ),
            tf.concat([true_obj_shape_indices, [0]], axis=-1),
        )

    @staticmethod
    def _get_true_cls(tensor, n_bounding_boxes):
        true_cls = tensor[..., 5:]
        true_cls_shape = tf.cast(tf.shape(true_cls), dtype=tf.int32)
        true_cls_shape_indices = tf.range(tf.size(true_cls_shape), dtype=tf.int32) + 1
        return tf.transpose(
            tf.broadcast_to(
                true_cls,
                tf.concat([[n_bounding_boxes], true_cls_shape], axis=-1),
            ),
            tf.concat(
                [true_cls_shape_indices[:-1], [0], true_cls_shape_indices[-1:]], axis=-1
            ),
        )

    @staticmethod
    def _get_pred_cellboxes(tensor):
        return tensor[..., :4]

    @staticmethod
    def _get_pred_objs(tensor):
        return tensor[..., 4]

    @staticmethod
    def _get_pred_cls(tensor):
        return tensor[..., 5:]

    @staticmethod
    def _get_best_iou(ious, n_bounding_boxes):
        best_iou = tf.cast(tf.math.argmax(ious, axis=-1), dtype=tf.int32)

        best_iou_shape = tf.cast(tf.shape(best_iou), dtype=tf.int32)
        best_iou_indices = tf.range(tf.size(best_iou_shape) + 1, dtype=tf.int32)

        return tf.transpose(
            tf.broadcast_to(
                best_iou, tf.concat([[n_bounding_boxes], best_iou_shape], axis=-1)
            ),
            tf.roll(best_iou_indices, axis=-1, shift=-1),
        )

    @staticmethod
    def _get_bounding_box_indices(n_bounding_boxes, shape):
        return tf.broadcast_to(tf.range(n_bounding_boxes, dtype=tf.int32), shape)

    def _get_pred_responsible_cellboxes_mask(self, ious, n_bounding_boxes):
        best_iou = self._get_best_iou(ious, n_bounding_boxes)
        bounding_box_indices = self._get_bounding_box_indices(
            n_bounding_boxes, tf.cast(tf.shape(best_iou), dtype=tf.int32)
        )

        return tf.cast(bounding_box_indices == best_iou, dtype=tf.float32)
