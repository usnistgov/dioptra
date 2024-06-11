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

from typing import cast

import numpy as np
import numpy.typing as npt
import structlog
from structlog.stdlib import BoundLogger

from .bounding_box_coordinates import BoundingBoxCoordinates, BoundingBoxesBatchedGrid

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    import tensorflow as tf
    from tensorflow import Tensor

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


class TensorflowBoundingBoxCoordinates(BoundingBoxCoordinates):
    def __init__(self, grid_shape: tuple[int, int]) -> None:
        self._grid_shape = grid_shape
        self._cell_height = 1 / self._grid_shape[0]
        self._cell_width = 1 / self._grid_shape[1]
        self._cell_ncol = self._grid_shape[1]
        self._cell_nrow = self._grid_shape[0]

    @property
    def cell_height(self) -> float:
        return self._cell_height

    @property
    def cell_width(self) -> float:
        return self._cell_width

    @property
    def cell_ncol(self) -> int:
        return self._cell_ncol

    @property
    def cell_nrow(self) -> int:
        return self._cell_nrow

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.int32),
            tf.TensorSpec(None, tf.int32),
        ]
    )
    def apply_constraint_one_object_per_cell(
        self,
        bboxes_cell_xywh: Tensor,
        bboxes_cell_ij: Tensor,
        bboxes_labels: Tensor,
    ) -> tuple[Tensor, Tensor, Tensor]:
        return cast(
            tuple[Tensor, Tensor, Tensor],
            tf.numpy_function(
                self._apply_constraint_one_object_per_cell,
                [bboxes_cell_xywh, bboxes_cell_ij, bboxes_labels],
                [tf.float32, tf.int32, tf.int32],
            ),
        )

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.int32),
        ]
    )
    def find_no_obj_cell_ij(self, bboxes_cell_ij: Tensor) -> Tensor:
        i_range = tf.range(self.cell_nrow, dtype=tf.int32)
        j_range = tf.range(self.cell_ncol, dtype=tf.int32)

        return tf.numpy_function(
            self._find_no_obj_cell_ij, [bboxes_cell_ij, i_range, j_range], [tf.int32]
        )

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def find_bbox_cell_ij(self, x_center: Tensor, y_center: Tensor) -> Tensor:
        cell_h = tf.cast(self.cell_height, tf.float32)
        cell_w = tf.cast(self.cell_width, tf.float32)
        max_i = tf.cast(
            tf.fill(dims=tf.shape(y_center), value=self.cell_nrow), tf.int32
        )
        max_j = tf.cast(
            tf.fill(dims=tf.shape(x_center), value=self.cell_ncol), tf.int32
        )

        i = tf.reduce_min(
            tf.stack(
                [
                    tf.cast(y_center / cell_h, tf.int32),
                    max_i,
                ],
                axis=-1,
            ),
            axis=-1,
        )
        j = tf.reduce_min(
            tf.stack(
                [
                    tf.cast(x_center / cell_w, tf.int32),
                    max_j,
                ],
                axis=-1,
            ),
            axis=-1,
        )

        return tf.cast(tf.stack([i, j], axis=-1), tf.int32)

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.int32),
        ]
    )
    def find_bbox_cell_xy(
        self, x_center: Tensor, y_center: Tensor, bboxes_cell_ij: Tensor
    ) -> Tensor:
        cell_h = tf.cast(self.cell_height, tf.float32)
        cell_w = tf.cast(self.cell_width, tf.float32)

        x_center_shape = tf.shape(x_center)
        y_center_shape = tf.shape(y_center)

        cell_x = tf.reduce_min(
            tf.stack(
                [
                    tf.cast(x_center / cell_w, tf.float32)
                    - tf.cast(bboxes_cell_ij[..., 1], tf.float32),
                    tf.ones(shape=x_center_shape, dtype=tf.float32),
                ],
                axis=-1,
            ),
            axis=-1,
        )
        cell_y = tf.reduce_min(
            tf.stack(
                [
                    tf.cast(y_center / cell_h, tf.float32)
                    - tf.cast(bboxes_cell_ij[..., 0], tf.float32),
                    tf.ones(shape=y_center_shape, dtype=tf.float32),
                ],
                axis=-1,
            ),
            axis=-1,
        )

        return cell_x, cell_y

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def from_corner_to_image_xywh(self, bboxes_corner: Tensor) -> Tensor:
        xmin = bboxes_corner[..., 0]
        ymin = bboxes_corner[..., 1]
        xmax = bboxes_corner[..., 2]
        ymax = bboxes_corner[..., 3]

        x = (xmin + xmax) / 2.0
        y = (ymin + ymax) / 2.0
        w = xmax - xmin
        h = ymax - ymin

        return tf.stack([x, y, w, h], axis=-1)

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def from_image_to_cell_xywh(
        self, bboxes_image_xywh: Tensor
    ) -> tuple[Tensor, Tensor]:
        x_center = bboxes_image_xywh[..., 0]
        y_center = bboxes_image_xywh[..., 1]

        bboxes_cell_ij = self.find_bbox_cell_ij(x_center=x_center, y_center=y_center)
        cell_x, cell_y = self.find_bbox_cell_xy(
            x_center=x_center, y_center=y_center, bboxes_cell_ij=bboxes_cell_ij
        )
        bboxes_cell_xywh = tf.stack(
            [cell_x, cell_y, bboxes_image_xywh[..., 2], bboxes_image_xywh[..., 3]],
            axis=-1,
        )

        return tf.cast(bboxes_cell_xywh, tf.float32), tf.cast(bboxes_cell_ij, tf.int32)

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def from_corner_to_cell_xywh(self, bboxes_corner: Tensor) -> tuple[Tensor, Tensor]:
        bboxes_image_xywh = self.from_corner_to_image_xywh(bboxes_corner=bboxes_corner)
        bboxes_cell_xywh, bboxes_cell_ij = self.from_image_to_cell_xywh(
            bboxes_image_xywh=bboxes_image_xywh
        )

        return bboxes_cell_xywh, bboxes_cell_ij

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.int32),
        ]
    )
    def from_cell_xywh_to_image_xywh(
        self, bboxes_cell_xywh: Tensor, bboxes_cell_ij: Tensor
    ) -> Tensor:
        num_cells_wh = tf.concat(
            [tf.cast(self.cell_ncol, tf.float32), tf.cast(self.cell_nrow, tf.float32)],
            axis=0,
        )
        bboxes_image_xy = (
            bboxes_cell_xywh[..., :2]
            + tf.cast(tf.gather(bboxes_cell_ij, indices=[1, 0], axis=-1), tf.float32)
        ) / num_cells_wh
        bboxes_image_wh = bboxes_cell_xywh[..., 2:4]

        return tf.concat([bboxes_image_xy, bboxes_image_wh], axis=-1)

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def from_image_xywh_to_corner(self, bboxes_image_xywh: Tensor) -> Tensor:
        x = bboxes_image_xywh[..., 0]
        y = bboxes_image_xywh[..., 1]
        w = bboxes_image_xywh[..., 2]
        h = bboxes_image_xywh[..., 3]

        x1 = x - (w / 2)
        x2 = x + (w / 2)
        y1 = y - (h / 2)
        y2 = y + (h / 2)

        return tf.stack([x1, y1, x2, y2], axis=-1)

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.int32),
        ]
    )
    def from_cell_xywh_to_corner(
        self, bboxes_cell_xywh: Tensor, bboxes_cell_ij: Tensor
    ) -> Tensor:
        bboxes_image_xywh = self.from_cell_xywh_to_image_xywh(
            bboxes_cell_xywh=bboxes_cell_xywh, bboxes_cell_ij=bboxes_cell_ij
        )
        bboxes_corner = self.from_image_xywh_to_corner(
            bboxes_image_xywh=bboxes_image_xywh
        )

        return bboxes_corner

    def _apply_constraint_one_object_per_cell(
        self,
        bboxes_cell_xywh: npt.NDArray,
        bboxes_cell_ij: npt.NDArray,
        bboxes_labels: npt.NDArray,
    ) -> tuple[npt.NDArray, npt.NDArray, npt.NDArray]:
        pruned_bboxes_cell_ij, pruning_indices = np.unique(
            bboxes_cell_ij, return_index=True, axis=0
        )
        pruned_bboxes_cell_xywh = bboxes_cell_xywh[pruning_indices]
        pruned_bboxes_labels = bboxes_labels[pruning_indices]

        return (
            pruned_bboxes_cell_xywh.astype("float32"),
            pruned_bboxes_cell_ij.astype("int32"),
            pruned_bboxes_labels.astype("int32"),
        )

    def _find_no_obj_cell_ij(
        self, bboxes_cell_ij: npt.NDArray, i_range: npt.NDArray, j_range: npt.NDArray
    ) -> npt.NDArray:
        cell_ij_set: set[tuple[npt.ArrayLike, npt.ArrayLike]] = set(
            [(i, j) for i in i_range for j in j_range]
        )
        cell_ij_seen: set[tuple[npt.ArrayLike, npt.ArrayLike]] = set(
            [(x[0], x[1]) for x in bboxes_cell_ij.tolist()]
        )
        no_obj_cell_ij: list[tuple[npt.ArrayLike, npt.ArrayLike]] = sorted(
            list(cell_ij_set - cell_ij_seen)
        )

        return np.array(no_obj_cell_ij, dtype="int32")


class TensorflowBoundingBoxesBatchedGrid(BoundingBoxesBatchedGrid):
    def __init__(
        self,
        bounding_box_coordinates: TensorflowBoundingBoxCoordinates,
    ) -> None:
        self._bbox_coord = bounding_box_coordinates
        self._wh_grid_indices = self._generate_wh_grid_indices(
            grid_shape=(
                bounding_box_coordinates.cell_nrow,
                bounding_box_coordinates.cell_ncol,
            )
        )
        self._num_wh_grid_indices = self._generate_num_wh_grid_indices(
            grid_shape=(
                bounding_box_coordinates.cell_nrow,
                bounding_box_coordinates.cell_ncol,
            )
        )

    @classmethod
    def on_grid_shape(
        cls, grid_shape: tuple[int, int]
    ) -> TensorflowBoundingBoxesBatchedGrid:
        return cls(
            bounding_box_coordinates=TensorflowBoundingBoxCoordinates(
                grid_shape=grid_shape
            ),
        )

    @property
    def cell_height(self) -> float:
        return self._bbox_coord.cell_height

    @property
    def cell_width(self) -> float:
        return self._bbox_coord.cell_width

    @property
    def cell_ncol(self) -> int:
        return self._bbox_coord.cell_ncol

    @property
    def cell_nrow(self) -> int:
        return self._bbox_coord.cell_nrow

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
        (
            bboxes_cell_xywh_grid,
            bboxes_labels_grid,
            bboxes_object_mask,
            bboxes_no_object_mask,
        ) = tf.py_function(
            self._gen_embed_tensors,
            [n_classes],
            [tf.float32, tf.float32, tf.float32, tf.float32],
        )
        bboxes_cell_xywh, bboxes_cell_ij = self._bbox_coord.from_corner_to_cell_xywh(
            bboxes_corner=bboxes_corner
        )
        xywh, ij, labels = self._bbox_coord.apply_constraint_one_object_per_cell(
            bboxes_cell_xywh=bboxes_cell_xywh,
            bboxes_cell_ij=bboxes_cell_ij,
            bboxes_labels=bboxes_labels,
        )

        return cast(
            tuple[Tensor, Tensor, Tensor, Tensor],
            tf.numpy_function(
                self._embed,
                [
                    xywh,
                    ij,
                    labels,
                    bboxes_cell_xywh_grid,
                    bboxes_labels_grid,
                    bboxes_object_mask,
                    bboxes_no_object_mask,
                ],
                [tf.float32, tf.float32, tf.float32, tf.float32],
            ),
        )

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def extract_using_mask(
        self,
        bboxes_grid: Tensor,
        labels_grid: Tensor,
        cell_mask: Tensor,
    ) -> tuple[Tensor, Tensor, Tensor]:
        bboxes_cell_ij = tf.where(cell_mask)
        bboxes = tf.gather_nd(params=bboxes_grid, indices=bboxes_cell_ij)
        labels = tf.gather_nd(params=labels_grid, indices=bboxes_cell_ij)

        return bboxes, bboxes_cell_ij, labels

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def from_corner_to_image_xywh(self, bboxes_corner: Tensor) -> Tensor:
        return self._bbox_coord.from_corner_to_image_xywh(bboxes_corner=bboxes_corner)

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def from_image_to_cell_xywh(self, bboxes_image_xywh: Tensor) -> Tensor:
        bboxes_cell_xywh, _ = self._bbox_coord.from_image_to_cell_xywh(
            bboxes_image_xywh=bboxes_image_xywh
        )

        return bboxes_cell_xywh

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def from_corner_to_cell_xywh(self, bboxes_corner: Tensor) -> Tensor:
        bboxes_image_xywh: npt.NDArray = self.from_corner_to_image_xywh(
            bboxes_corner=bboxes_corner
        )
        bboxes_cell_xywh: npt.NDArray = self.from_image_to_cell_xywh(
            bboxes_image_xywh=bboxes_image_xywh
        )

        return bboxes_cell_xywh

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.int32),
        ]
    )
    def from_cell_xywh_to_image_xywh(
        self, bboxes_cell_xywh: Tensor, n_bounding_boxes: Tensor
    ) -> Tensor:
        batch_size = tf.shape(bboxes_cell_xywh)[0]

        wh_grid = tf.tile(
            tf.cast(self._wh_grid_indices, tf.float32),
            multiples=[batch_size, 1, 1, n_bounding_boxes, 1],
        )
        num_wh_grid = tf.tile(
            tf.cast(self._num_wh_grid_indices, tf.float32),
            multiples=[batch_size, 1, 1, n_bounding_boxes, 1],
        )

        bboxes_image_xy = (bboxes_cell_xywh[..., :2] + wh_grid) / num_wh_grid
        bboxes_image_wh = bboxes_cell_xywh[..., 2:4]

        return tf.concat([bboxes_image_xy, bboxes_image_wh], axis=-1)

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
        ]
    )
    def from_image_xywh_to_corner(self, bboxes_image_xywh: Tensor) -> Tensor:
        return self._bbox_coord.from_image_xywh_to_corner(
            bboxes_image_xywh=bboxes_image_xywh
        )

    @tf.function(
        input_signature=[
            tf.TensorSpec(None, tf.float32),
            tf.TensorSpec(None, tf.int32),
        ]
    )
    def from_cell_xywh_to_corner(
        self, bboxes_cell_xywh: Tensor, n_bounding_boxes: Tensor
    ) -> Tensor:
        bboxes_image_xywh = self.from_cell_xywh_to_image_xywh(
            bboxes_cell_xywh=bboxes_cell_xywh,
            n_bounding_boxes=n_bounding_boxes,
        )
        bboxes_corner = self.from_image_xywh_to_corner(
            bboxes_image_xywh=bboxes_image_xywh
        )

        return bboxes_corner

    def _embed(
        self,
        xywh: npt.NDArray,
        ij: npt.NDArray,
        labels: npt.NDArray,
        bboxes_cell_xywh_grid: npt.NDArray,
        bboxes_labels_grid: npt.NDArray,
        bboxes_object_mask: npt.NDArray,
        bboxes_no_object_mask: npt.NDArray,
    ) -> tuple[npt.NDArray, npt.NDArray, npt.NDArray, npt.NDArray]:
        grid_i = np.transpose(ij)[0]
        grid_j = np.transpose(ij)[1]

        bboxes_cell_xywh_grid[grid_i, grid_j] = xywh
        bboxes_labels_grid[grid_i, grid_j, labels] = 1.0
        bboxes_object_mask[grid_i, grid_j] = 1.0
        bboxes_no_object_mask[grid_i, grid_j] = 0.0

        bboxes_cell_xywh_grid = np.expand_dims(bboxes_cell_xywh_grid, axis=-2)

        return (
            bboxes_cell_xywh_grid,
            bboxes_labels_grid,
            bboxes_object_mask,
            bboxes_no_object_mask,
        )

    def _gen_embed_tensors(
        self, n_classes: Tensor
    ) -> tuple[Tensor, Tensor, Tensor, Tensor]:
        bboxes_cell_xywh_grid = tf.zeros(
            shape=(self.cell_nrow, self.cell_ncol, 4),
            dtype=tf.float32,
        )
        bboxes_labels_grid = tf.zeros(
            shape=(self.cell_nrow, self.cell_ncol, n_classes),
            dtype=tf.float32,
        )
        bboxes_object_mask = tf.zeros(
            shape=(self.cell_nrow, self.cell_ncol),
            dtype=tf.float32,
        )
        bboxes_no_object_mask = tf.ones(
            shape=(self.cell_nrow, self.cell_ncol),
            dtype=tf.float32,
        )

        return (
            bboxes_cell_xywh_grid,
            bboxes_labels_grid,
            bboxes_object_mask,
            bboxes_no_object_mask,
        )

    @staticmethod
    def _generate_wh_grid_indices(grid_shape: tuple[int, int]) -> Tensor:
        w_grid_indices = tf.tile(
            tf.expand_dims(tf.range(grid_shape[1], dtype=tf.int32), axis=0),
            multiples=[grid_shape[0], 1],
        )
        w_grid_indices = tf.reshape(
            w_grid_indices, (1, grid_shape[0], grid_shape[1], 1, 1)
        )

        h_grid_indices = tf.transpose(
            tf.tile(
                tf.expand_dims(tf.range(grid_shape[0], dtype=tf.int32), axis=0),
                multiples=[grid_shape[1], 1],
            )
        )
        h_grid_indices = tf.reshape(
            h_grid_indices, (1, grid_shape[0], grid_shape[1], 1, 1)
        )

        return tf.cast(tf.concat([w_grid_indices, h_grid_indices], axis=-1), tf.float32)

    @staticmethod
    def _generate_num_wh_grid_indices(grid_shape: tuple[int, int]) -> Tensor:
        num_w_grid_indices = tf.constant(
            value=grid_shape[1],
            shape=(1, grid_shape[0], grid_shape[1], 1, 1),
            dtype=tf.int32,
        )
        num_h_grid_indices = tf.constant(
            value=grid_shape[0],
            shape=(1, grid_shape[0], grid_shape[1], 1, 1),
            dtype=tf.int32,
        )

        return tf.cast(
            tf.concat([num_w_grid_indices, num_h_grid_indices], axis=-1), tf.float32
        )
