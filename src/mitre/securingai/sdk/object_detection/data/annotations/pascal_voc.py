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

from pathlib import Path
from typing import Dict, Iterable, List, Tuple, Union
from xml.etree import ElementTree

import numpy as np
import structlog
from structlog.stdlib import BoundLogger

from .annotation_data import AnnotationData
from .encodings import AnnotationEncoding, BoxesType, LabelsType

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class PascalVOCAnnotationData(AnnotationData):
    def __init__(
        self,
        labels: Iterable[str],
        encoding: AnnotationEncoding,
    ) -> None:
        self._labels = {x: idx for idx, x in enumerate(labels)}
        self._encoding = encoding

    @property
    def labels(self) -> Dict[str, int]:
        return self._labels

    def get(self, y: Union[Path, bytes, str]) -> Tuple[BoxesType, LabelsType]:
        boxes, classes = self.read_file(filepath=y)
        encoded_boxes, encoded_classes = self._encoding.encode(boxes, classes)

        return encoded_boxes, encoded_classes

    def read_file(
        self, filepath: Union[Path, bytes, str]
    ) -> Tuple[List[List[float]], List[int]]:
        # Load and parse the file
        filepath: str = (
            filepath.decode() if isinstance(filepath, bytes) else str(filepath)
        )
        tree: ElementTree = ElementTree.parse(filepath)

        # Get the root of the document
        root = tree.getroot()
        boxes: List[List[float]] = list()
        classes: List[int] = list()

        # Get width and height of an image
        width = int(root.find(".//size/width").text)
        height = int(root.find(".//size/height").text)

        # Extract each bounding box
        for box in root.findall(".//object"):
            class_name = box.find("name").text
            class_id = self._labels[class_name]
            xmin = int(box.find("bndbox/xmin").text)
            ymin = int(box.find("bndbox/ymin").text)
            xmax = int(box.find("bndbox/xmax").text)
            ymax = int(box.find("bndbox/ymax").text)
            coordinates = [xmin / width, ymin / height, xmax / width, ymax / height]
            boxes.append(coordinates)
            classes.append(class_id)

        return np.array(boxes, dtype="float32"), np.array(classes, dtype="int32")
