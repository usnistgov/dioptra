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
from typing import List, Tuple

import numpy as np
import numpy.typing as npt
import structlog
from structlog.stdlib import BoundLogger

LOGGER: BoundLogger = structlog.stdlib.get_logger()


BoxesType = npt.NDArray
LabelsType = npt.NDArray


class AnnotationEncoding(metaclass=ABCMeta):
    @abstractmethod
    def decode(
        self, boxes: BoxesType, labels: LabelsType
    ) -> Tuple[List[List[float]], List[int]]:
        raise NotImplementedError

    @abstractmethod
    def encode(
        self, boxes: List[List[float]], labels: List[int]
    ) -> Tuple[BoxesType, LabelsType]:
        raise NotImplementedError


class NumpyAnnotationEncoding(AnnotationEncoding):
    def __init__(
        self, boxes_dtype: str = "float32", labels_dtype: str = "int32"
    ) -> None:
        self._boxes_dtype = boxes_dtype
        self._labels_dtype = labels_dtype

    def decode(
        self, boxes: npt.NDArray, labels: npt.NDArray
    ) -> Tuple[List[List[float]], List[int]]:
        decoded_boxes: List[List[float]] = [
            [float(coord) for coord in x] for x in boxes.tolist()
        ]
        decoded_labels: List[int] = [int(x) for x in labels.tolist()]

        return decoded_boxes, decoded_labels

    def encode(
        self, boxes: List[List[float]], labels: List[int]
    ) -> Tuple[npt.NDArray, npt.NDArray]:
        return np.array(boxes, dtype=self._boxes_dtype), np.array(
            labels, dtype=self._labels_dtype
        )
