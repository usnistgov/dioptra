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
from typing import Sequence

import structlog
from structlog.stdlib import BoundLogger

from dioptra import pyplugs
from dioptra.sdk.exceptions import TensorflowDependencyError
from dioptra.sdk.utilities.decorators import require_package
from dioptra.sdk.object_detection.architectures import YOLOV1ObjectDetector
from dioptra.sdk.object_detection.data import TensorflowObjectDetectionData

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pyplugs.register
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def create_object_detection_dataset(
    image_size: tuple[int, int, int],
    grid_shape: tuple[int, int] | YOLOV1ObjectDetector,
    labels: Sequence[str],
    training_directory: Path | str | None = None,
    validation_directory: Path | str | None = None,
    testing_directory: Path | str | None = None,
    annotation_format: str = "pascal_voc",
    augmentations: str | None = None,
    batch_size: int | None = 16,
    shuffle_training_data: bool = True,
    images_dirname: str = "images",
    annotations_dirname: str = "annotations",
    augmentations_seed: int | None = None,
    shuffle_seed: int | None = None,
) -> TensorflowObjectDetectionData:
    if isinstance(grid_shape, YOLOV1ObjectDetector):
        grid_shape = grid_shape.output_grid_shape

    return TensorflowObjectDetectionData.create(
        image_dimensions=image_size,
        grid_shape=grid_shape,
        labels=labels,
        training_directory=training_directory,
        validation_directory=validation_directory,
        testing_directory=testing_directory,
        annotation_format=annotation_format,
        augmentations=augmentations,
        batch_size=batch_size,
        shuffle_training_data=shuffle_training_data,
        images_dirname=images_dirname,
        annotations_dirname=annotations_dirname,
        augmentations_seed=augmentations_seed,
        shuffle_seed=shuffle_seed,
    )
