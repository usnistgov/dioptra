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
from typing import Iterable, Optional, Tuple

import numpy as np
import structlog
from structlog.stdlib import BoundLogger

from mitre.securingai import pyplugs
from mitre.securingai.sdk.exceptions import TensorflowDependencyError
from mitre.securingai.sdk.utilities.decorators import require_package
from mitre.securingai.sdk.object_detection.data import TensorflowObjectDetectionData

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pyplugs.register
@pyplugs.task_nout(3)
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def create_object_detection_dataset(
    image_size: Tuple[int, int, int],
    grid_shape: Tuple[int, int],
    labels: Iterable[str],
    training_directory: Optional[str] = None,
    validation_directory: Optional[str] = None,
    testing_directory: Optional[str] = None,
    annotation_format: str = "pascal_voc",
    augmentations: Optional[str] = None,
    batch_size: Optional[int] = 16,
    shuffle_training_data: bool = True,
    images_dirname: str = "images",
    annotations_dirname: str = "annotations",
    augmentations_seed: Optional[int] = None,
    shuffle_seed: Optional[int] = None,
) -> TensorflowObjectDetectionData:
    object_detection_datasets = TensorflowObjectDetectionData.create(
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

    training_dataset = object_detection_datasets.training_dataset
    validation_dataset = object_detection_datasets.validation_dataset
    testing_dataset = object_detection_datasets.testing_dataset

    return training_dataset, validation_dataset, testing_dataset


@pyplugs.register
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def serialize_tensor_to_npy(tensor, output_dir, output_filename, working_dir=None):
    if working_dir is None:
        working_dir = Path.cwd()

    output_dir = Path(output_dir)
    working_dir = Path(working_dir)
    output_dirpath = working_dir / output_dir
    output_filepath = output_dirpath / output_filename

    output_dirpath.mkdir(parents=True, exist_ok=True)

    data = tensor.numpy()

    np.save(file=output_filepath, arr=data, allow_pickle=False)


@pyplugs.register
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def serialize_array_to_npy(array, output_dir, output_filename, working_dir=None):
    if working_dir is None:
        working_dir = Path.cwd()

    output_dir = Path(output_dir)
    working_dir = Path(working_dir)
    output_dirpath = working_dir / output_dir
    output_filepath = output_dirpath / output_filename

    output_dirpath.mkdir(parents=True, exist_ok=True)

    np.save(file=output_filepath, arr=array, allow_pickle=False)
