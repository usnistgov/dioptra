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
import numpy.typing as npt

from .bounding_box_coordinates import BoundingBoxCoordinates, BoundingBoxesBatchedGrid


class NumpyBoundingBoxCoordinates(BoundingBoxCoordinates):
    def __init__(self, grid_shape: tuple[int, int]) -> None:
        self._grid_shape = grid_shape

    @property
    def cell_height(self) -> float:
        return 1 / self._grid_shape[0]

    @property
    def cell_width(self) -> float:
        return 1 / self._grid_shape[1]

    @property
    def cell_ncol(self) -> int:
        return self._grid_shape[1]

    @property
    def cell_nrow(self) -> int:
        return self._grid_shape[0]

    def apply_constraint_one_object_per_cell(
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

    def find_no_obj_cell_ij(self, bboxes_cell_ij: npt.NDArray) -> npt.NDArray:
        cell_ij_set: set[tuple[int, int]] = set(
            [(i, j) for i in range(self.cell_nrow) for j in range(self.cell_ncol)]
        )
        cell_ij_seen: set[tuple[int, int]] = set(
            [(int(x[0]), int(x[1])) for x in bboxes_cell_ij.tolist()]
        )
        no_obj_cell_ij = sorted(list(cell_ij_set - cell_ij_seen))

        return np.array(no_obj_cell_ij, dtype="int32")

    def find_bbox_cell_ij(
        self, x_center: npt.NDArray, y_center: npt.NDArray
    ) -> npt.NDArray:
        cell_h: float = self.cell_height
        cell_w: float = self.cell_width
        max_i: int = self.cell_nrow
        max_j: int = self.cell_ncol

        i: npt.NDArray = np.min(
            np.stack(
                [
                    (y_center / cell_h).astype("int32"),
                    np.full(shape=y_center.shape, fill_value=max_i, dtype="int32"),
                ],
                axis=-1,
            ),
            axis=-1,
        )
        j: npt.NDArray = np.min(
            np.stack(
                [
                    (x_center / cell_w).astype("int32"),
                    np.full(shape=x_center.shape, fill_value=max_j, dtype="int32"),
                ],
                axis=-1,
            ),
            axis=-1,
        )

        bbox_cell_ij: npt.NDArray = np.stack([i, j], axis=-1).astype("int32")

        return bbox_cell_ij

    def find_bbox_cell_xy(
        self, x_center: npt.NDArray, y_center: npt.NDArray, bboxes_cell_ij: npt.NDArray
    ) -> tuple[npt.NDArray, npt.NDArray]:
        cell_h: float = self.cell_height
        cell_w: float = self.cell_width

        cell_x: npt.NDArray = np.min(
            np.stack(
                [
                    (x_center / cell_w).astype("float32")
                    - bboxes_cell_ij[..., 1].astype("float32"),
                    np.full(shape=x_center.shape, fill_value=1.0, dtype="float32"),
                ],
                axis=-1,
            ),
            axis=-1,
        )
        cell_y: npt.NDArray = np.min(
            np.stack(
                [
                    (y_center / cell_h).astype("float32")
                    - bboxes_cell_ij[..., 0].astype("float32"),
                    np.full(shape=y_center.shape, fill_value=1.0, dtype="float32"),
                ],
                axis=-1,
            ),
            axis=-1,
        )

        return cell_x, cell_y

    def from_corner_to_image_xywh(self, bboxes_corner: npt.NDArray) -> npt.NDArray:
        xmin = bboxes_corner[..., 0]
        ymin = bboxes_corner[..., 1]
        xmax = bboxes_corner[..., 2]
        ymax = bboxes_corner[..., 3]

        x = (xmin + xmax) / 2.0
        y = (ymin + ymax) / 2.0
        w = xmax - xmin
        h = ymax - ymin

        return np.stack([x, y, w, h], axis=-1)

    def from_image_to_cell_xywh(
        self, bboxes_image_xywh: npt.NDArray
    ) -> tuple[npt.NDArray, npt.NDArray]:
        x_center = bboxes_image_xywh[..., 0]
        y_center = bboxes_image_xywh[..., 1]

        bboxes_cell_ij = self.find_bbox_cell_ij(x_center=x_center, y_center=y_center)
        cell_x, cell_y = self.find_bbox_cell_xy(
            x_center=x_center, y_center=y_center, bboxes_cell_ij=bboxes_cell_ij
        )
        bboxes_cell_xywh = np.stack(
            [cell_x, cell_y, bboxes_image_xywh[..., 2], bboxes_image_xywh[..., 3]],
            axis=-1,
        )

        return bboxes_cell_xywh.astype("float32"), bboxes_cell_ij.astype("int32")

    def from_corner_to_cell_xywh(
        self, bboxes_corner: npt.NDArray
    ) -> tuple[npt.NDArray, npt.NDArray]:
        bboxes_image_xywh: npt.NDArray = self.from_corner_to_image_xywh(
            bboxes_corner=bboxes_corner
        )
        bboxes_cell_xywh, bboxes_cell_ij = self.from_image_to_cell_xywh(
            bboxes_image_xywh=bboxes_image_xywh
        )

        return bboxes_cell_xywh, bboxes_cell_ij

    def from_cell_xywh_to_image_xywh(
        self, bboxes_cell_xywh: npt.NDArray, bboxes_cell_ij: npt.NDArray
    ) -> npt.NDArray:
        num_cells_wh = np.array([self.cell_ncol, self.cell_nrow], dtype="float32")
        bboxes_image_xywh = bboxes_cell_xywh.copy()
        bboxes_image_xywh[..., :2] = (
            bboxes_cell_xywh[..., :2] + bboxes_cell_ij[:, [1, 0]].astype("float32")
        ) / num_cells_wh

        return bboxes_image_xywh

    def from_image_xywh_to_corner(self, bboxes_image_xywh: npt.NDArray) -> npt.NDArray:
        x = bboxes_image_xywh[..., 0]
        y = bboxes_image_xywh[..., 1]
        w = bboxes_image_xywh[..., 2]
        h = bboxes_image_xywh[..., 3]

        x1 = x - (w / 2)
        x2 = x + (w / 2)
        y1 = y - (h / 2)
        y2 = y + (h / 2)

        return np.stack([x1, y1, x2, y2], axis=-1)

    def from_cell_xywh_to_corner(
        self, bboxes_cell_xywh: npt.NDArray, bboxes_cell_ij: npt.NDArray
    ) -> npt.NDArray:
        bboxes_image_xywh = self.from_cell_xywh_to_image_xywh(
            bboxes_cell_xywh=bboxes_cell_xywh, bboxes_cell_ij=bboxes_cell_ij
        )
        bboxes_corner = self.from_image_xywh_to_corner(
            bboxes_image_xywh=bboxes_image_xywh
        )

        return bboxes_corner


class NumpyBoundingBoxesBatchedGrid(BoundingBoxesBatchedGrid):
    def __init__(
        self,
        bounding_box_coordinates: NumpyBoundingBoxCoordinates,
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
    ) -> NumpyBoundingBoxesBatchedGrid:
        bbox_coord: NumpyBoundingBoxCoordinates = NumpyBoundingBoxCoordinates(
            grid_shape=grid_shape
        )

        return cls(bounding_box_coordinates=bbox_coord)

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

    def embed(
        self, bboxes_corner: npt.NDArray, bboxes_labels: npt.NDArray, n_classes: int
    ) -> tuple[npt.NDArray, npt.NDArray, npt.NDArray, npt.NDArray]:
        bboxes_cell_xywh_grid: npt.NDArray = np.zeros(
            shape=(self.cell_nrow, self.cell_ncol, 4),
            dtype="float32",
        )
        bboxes_labels_grid: npt.NDArray = np.zeros(
            shape=(self.cell_nrow, self.cell_ncol, n_classes),
            dtype="float32",
        )
        bboxes_object_mask: npt.NDArray = np.zeros(
            shape=(self.cell_nrow, self.cell_ncol),
            dtype="float32",
        )
        bboxes_no_object_mask: npt.NDArray = np.ones(
            shape=(self.cell_nrow, self.cell_ncol),
            dtype="float32",
        )

        bboxes_cell_xywh, bboxes_cell_ij = self._bbox_coord.from_corner_to_cell_xywh(
            bboxes_corner=bboxes_corner
        )
        xywh, ij, labels = self._bbox_coord.apply_constraint_one_object_per_cell(
            bboxes_cell_xywh=bboxes_cell_xywh,
            bboxes_cell_ij=bboxes_cell_ij,
            bboxes_labels=bboxes_labels,
        )

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

    def from_corner_to_image_xywh(self, bboxes_corner: npt.NDArray) -> npt.NDArray:
        return self._bbox_coord.from_corner_to_image_xywh(bboxes_corner=bboxes_corner)

    def from_image_to_cell_xywh(self, bboxes_image_xywh: npt.NDArray) -> npt.NDArray:
        bboxes_cell_xywh, _ = self._bbox_coord.from_image_to_cell_xywh(
            bboxes_image_xywh=bboxes_image_xywh
        )

        return bboxes_cell_xywh

    def from_corner_to_cell_xywh(self, bboxes_corner: npt.NDArray) -> npt.NDArray:
        bboxes_image_xywh: npt.NDArray = self.from_corner_to_image_xywh(
            bboxes_corner=bboxes_corner
        )
        bboxes_cell_xywh: npt.NDArray = self.from_image_to_cell_xywh(
            bboxes_image_xywh=bboxes_image_xywh
        )

        return bboxes_cell_xywh

    def from_cell_xywh_to_image_xywh(
        self, bboxes_cell_xywh: npt.NDArray, n_bounding_boxes: int
    ) -> npt.NDArray:
        batch_size: int = int(np.shape(bboxes_cell_xywh)[0])

        wh_grid = np.tile(
            self._wh_grid_indices.astype("float32"),
            reps=[batch_size, 1, 1, n_bounding_boxes, 1],
        )
        num_wh_grid = np.tile(
            self._num_wh_grid_indices.astype("float32"),
            reps=[batch_size, 1, 1, n_bounding_boxes, 1],
        )

        bboxes_image_xywh = bboxes_cell_xywh.copy()
        bboxes_image_xywh[..., :2] = (bboxes_cell_xywh[..., :2] + wh_grid) / num_wh_grid

        return bboxes_image_xywh

    def from_image_xywh_to_corner(self, bboxes_image_xywh: npt.NDArray) -> npt.NDArray:
        return self._bbox_coord.from_image_xywh_to_corner(
            bboxes_image_xywh=bboxes_image_xywh
        )

    def from_cell_xywh_to_corner(
        self, bboxes_cell_xywh: npt.NDArray, n_bounding_boxes: int
    ) -> npt.NDArray:
        bboxes_image_xywh = self.from_cell_xywh_to_image_xywh(
            bboxes_cell_xywh=bboxes_cell_xywh,
            n_bounding_boxes=n_bounding_boxes,
        )
        bboxes_corner = self.from_image_xywh_to_corner(
            bboxes_image_xywh=bboxes_image_xywh
        )

        return bboxes_corner

    @staticmethod
    def _generate_wh_grid_indices(grid_shape: tuple[int, int]) -> npt.NDArray:
        w_grid_indices = np.tile(
            np.expand_dims(np.arange(grid_shape[1], dtype="int32"), axis=0),
            reps=[grid_shape[0], 1],
        )
        w_grid_indices = np.reshape(
            w_grid_indices, (1, grid_shape[0], grid_shape[1], 1, 1)
        )

        h_grid_indices = np.transpose(
            np.tile(
                np.expand_dims(np.arange(grid_shape[0], dtype="int32"), axis=0),
                reps=[grid_shape[1], 1],
            )
        )
        h_grid_indices = np.reshape(
            h_grid_indices, (1, grid_shape[0], grid_shape[1], 1, 1)
        )

        wh_grid_indices: npt.NDArray = np.concatenate(
            [w_grid_indices, h_grid_indices],
            axis=-1,
        ).astype("float32")

        return wh_grid_indices

    @staticmethod
    def _generate_num_wh_grid_indices(grid_shape: tuple[int, int]) -> npt.NDArray:
        num_w_grid_indices = np.full(
            shape=(1, grid_shape[0], grid_shape[1], 1, 1),
            fill_value=grid_shape[1],
            dtype="int32",
        )
        num_h_grid_indices = np.full(
            shape=(1, grid_shape[0], grid_shape[1], 1, 1),
            fill_value=grid_shape[0],
            dtype="int32",
        )

        num_wh_grid_indices: npt.NDArray = np.concatenate(
            [num_w_grid_indices, num_h_grid_indices],
            axis=-1,
        ).astype("float32")

        return num_wh_grid_indices
