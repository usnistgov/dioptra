from __future__ import annotations

from typing import Optional, Tuple

import structlog
from prefect import task
from structlog.stdlib import BoundLogger
from tensorflow.keras.applications.imagenet_utils import preprocess_input

from mitre.securingai import pyplugs
from mitre.securingai.sdk.exceptions import TensorflowDependencyError
from mitre.securingai.sdk.utilities.decorators import require_package

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
@task
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
