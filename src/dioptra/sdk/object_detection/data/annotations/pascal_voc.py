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
from typing import Dict, Iterable, List, Tuple, Union, cast
from xml.etree import ElementTree

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
    ) -> Tuple[list[list[float]], list[int]]:
        # Load and parse the file
        filepath = filepath.decode() if isinstance(filepath, bytes) else str(filepath)
        tree: ElementTree.ElementTree = ElementTree.parse(filepath)

        # Get the root of the document
        root = tree.getroot()
        boxes: List[List[float]] = list()
        classes: List[int] = list()

        # Get width and height of an image
        width_element: ElementTree.Element | None = root.find(".//size/width")
        height_element: ElementTree.Element | None = root.find(".//size/height")
        width: int = (
            int(cast(str, width_element.text)) if width_element is not None else -1
        )
        height: int = (
            int(cast(str, height_element.text)) if height_element is not None else -1
        )

        # Extract each bounding box
        for box in root.findall(".//object"):
            class_name_element: ElementTree.Element | None = box.find("name")
            class_name: str = (
                cast(str, class_name_element.text)
                if class_name_element is not None
                else ""
            )
            class_id = self._labels[class_name]
            xmin_element: ElementTree.Element | None = box.find("bndbox/xmin")
            ymin_element: ElementTree.Element | None = box.find("bndbox/ymin")
            xmax_element: ElementTree.Element | None = box.find("bndbox/xmax")
            ymax_element: ElementTree.Element | None = box.find("bndbox/ymax")
            xmin = int(cast(str, xmin_element.text)) if xmin_element is not None else -1
            ymin = int(cast(str, ymin_element.text)) if ymin_element is not None else -1
            xmax = int(cast(str, xmax_element.text)) if xmax_element is not None else -1
            ymax = int(cast(str, ymax_element.text)) if ymax_element is not None else -1
            coordinates = [xmin / width, ymin / height, xmax / width, ymax / height]
            boxes.append(coordinates)
            classes.append(class_id)

        return boxes, classes
