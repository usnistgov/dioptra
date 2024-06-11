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

from typing import Optional, Tuple

import structlog
from structlog.stdlib import BoundLogger
from tensorflow.keras.applications.imagenet_utils import preprocess_input

from dioptra import pyplugs
from dioptra.sdk.exceptions import TensorflowDependencyError
from dioptra.sdk.utilities.decorators import require_package

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    from tensorflow.keras.preprocessing.image import (
        DirectoryIterator,
        ImageDataGenerator,
    )

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )

# Adding imagenet preprocessing option for pre-trained Imagenet estimators.
@pyplugs.register
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def create_image_dataset(
    data_dir: str,
    subset: Optional[str],
    image_size: Tuple[int, int, int],
    seed: int,
    rescale: float = 1.0 / 255,
    validation_split: Optional[float] = 0.2,
    batch_size: int = 32,
    label_mode: str = "categorical",
    imagenet_preprocessing: bool = False,
) -> DirectoryIterator:
    color_mode: str = "rgb" if image_size[2] == 3 else "grayscale"
    target_size: Tuple[int, int] = image_size[:2]

    if imagenet_preprocessing:
        data_generator: ImageDataGenerator = ImageDataGenerator(
            rescale=rescale,
            validation_split=validation_split,
            preprocessing_function=preprocess_input,
        )
    else:
        data_generator: ImageDataGenerator = ImageDataGenerator(
            rescale=rescale,
            validation_split=validation_split,
        )

    return data_generator.flow_from_directory(
        directory=data_dir,
        target_size=target_size,
        color_mode=color_mode,
        class_mode=label_mode,
        batch_size=batch_size,
        seed=seed,
        subset=subset,
    )


@pyplugs.register
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def get_n_classes_from_directory_iterator(ds: DirectoryIterator) -> int:
    return len(ds.class_indices)
