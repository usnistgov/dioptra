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

import numpy as np
import structlog
from structlog.stdlib import BoundLogger

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    import tensorflow as tf

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


# source: https://github.com/GiaKhangLuu/YOLOv1_from_scratch
def convert_cellbox_to_corner_bbox(cellbox, mask=None):
    bbox = convert_cellbox_to_xywh(cellbox, mask)
    x = bbox[:, :, :, 0]
    y = bbox[:, :, :, 1]
    w = bbox[:, :, :, 2]
    h = bbox[:, :, :, 3]

    x_min = x - (w / 2)
    y_min = y - (h / 2)
    x_max = x + (w / 2)
    y_max = y + (h / 2)

    corner_box = tf.stack([x_min, y_min, x_max, y_max], axis=-1)

    return corner_box


def convert_cellbox_to_xywh(cellbox, mask=None):
    x_offset = cellbox[:, :, :, 0]
    y_offset = cellbox[:, :, :, 1]
    w_h = cellbox[:, :, :, 2:]

    num_w_cells = x_offset.shape[-1]
    num_h_cells = x_offset.shape[-2]

    # w_cell_indices: [[0, 1, 2, ...], [0, 1, 2, ...], ...]
    # Use w_cell_indices to convert x_offset of a particular grid cell
    # location to x_center
    w_cell_indices = np.array(range(num_w_cells))
    w_cell_indices = np.broadcast_to(w_cell_indices, x_offset.shape[-2:])

    # h_cell_indices: [[0, 0, 0, ...], [1, 1, 1, ...], [2, 2, 2, ...], ....]
    # Use h_cell_indices to convert y_offset of a particular grid cell
    # location to y_center
    h_cell_indices = np.array(range(num_h_cells))
    h_cell_indices = np.repeat(h_cell_indices, 7, 0).reshape(x_offset.shape[-2:])
    # h_cell_indices = np.broadcast_to(h_cell_indices, x_offset.shape)

    x_center = (x_offset + w_cell_indices) / num_w_cells
    y_center = (y_offset + h_cell_indices) / num_h_cells

    if mask is not None:
        x_center *= mask
        y_center *= mask

    x_y = tf.stack([x_center, y_center], axis=-1)

    bbox = tf.concat([x_y, w_h], axis=-1)

    return bbox


def convert_to_xywh(bboxes):
    boxes = list()
    for box in bboxes:
        xmin, ymin, xmax, ymax = box

        # Compute width and height of box
        box_width = xmax - xmin
        box_height = ymax - ymin

        # Compute x, y center
        x_center = int(xmin + (box_width / 2))
        y_center = int(ymin + (box_height / 2))

        boxes.append((x_center, y_center, box_width, box_height))

    return boxes


def convert_bboxes_to_tensor(
    bboxes, classes, img_width, img_height, n_classes, grid_size=7
):
    target = np.zeros(shape=(grid_size, grid_size, 5 + n_classes), dtype=np.float32)

    for idx, bbox in enumerate(bboxes):
        x_center, y_center, width, height = bbox

        # Compute size of each cell in grid
        cell_w = img_width / grid_size
        cell_h = img_height / grid_size

        # Determine cell i, j of bounding box
        i = int(y_center // cell_h)
        j = int(x_center // cell_w)

        # Compute value of x_center and y_center in cell
        x = (x_center / cell_w) - j
        y = (y_center / cell_h) - i

        # Normalize width and height of bounding box
        w_norm = width / img_width
        h_norm = height / img_height

        # Add bounding box to tensor
        # Set x, y, w, h
        target[i, j, :4] += (x, y, w_norm, h_norm)
        # Set obj score
        target[i, j, 4] = 1.0
        # Set class dist.
        target[i, j, 5 + classes[idx]] = 1.0

    return target.tolist()
