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

from abc import ABCMeta, abstractmethod


class BoundingBoxCoordinates(metaclass=ABCMeta):
    @property
    @abstractmethod
    def cell_height(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def cell_width(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def cell_ncol(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def cell_nrow(self):
        raise NotImplementedError

    @abstractmethod
    def apply_constraint_one_object_per_cell(
        self, bboxes_cell_xywh, bboxes_cell_ij, bboxes_labels
    ):
        raise NotImplementedError

    @abstractmethod
    def from_corner_to_image_xywh(self, bboxes_corner):
        raise NotImplementedError

    @abstractmethod
    def from_image_to_cell_xywh(self, bboxes_image_xywh):
        raise NotImplementedError

    @abstractmethod
    def from_corner_to_cell_xywh(self, bboxes_corner):
        raise NotImplementedError

    @abstractmethod
    def from_cell_xywh_to_image_xywh(self, bboxes_cell_xywh, bboxes_cell_ij):
        raise NotImplementedError

    @abstractmethod
    def from_image_xywh_to_corner(self, bboxes_image_xywh):
        raise NotImplementedError

    @abstractmethod
    def from_cell_xywh_to_corner(self, bboxes_cell_xywh, bboxes_cell_ij):
        raise NotImplementedError


class BoundingBoxesBatchedGrid(metaclass=ABCMeta):
    @property
    @abstractmethod
    def cell_height(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def cell_width(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def cell_ncol(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def cell_nrow(self):
        raise NotImplementedError

    @abstractmethod
    def embed(self, bboxes_corner, bboxes_labels, n_classes):
        raise NotImplementedError

    @abstractmethod
    def extract_using_mask(self, bboxes_grid, labels_grid, cell_mask):
        raise NotImplementedError

    @abstractmethod
    def from_corner_to_image_xywh(self, bboxes_corner):
        raise NotImplementedError

    @abstractmethod
    def from_image_to_cell_xywh(self, bboxes_image_xywh):
        raise NotImplementedError

    @abstractmethod
    def from_corner_to_cell_xywh(self, bboxes_corner):
        raise NotImplementedError

    @abstractmethod
    def from_cell_xywh_to_image_xywh(self, bboxes_cell_xywh, n_bounding_boxes):
        raise NotImplementedError

    @abstractmethod
    def from_image_xywh_to_corner(self, bboxes_image_xywh):
        raise NotImplementedError

    @abstractmethod
    def from_cell_xywh_to_corner(self, bboxes_cell_xywh, n_bounding_boxes):
        raise NotImplementedError
