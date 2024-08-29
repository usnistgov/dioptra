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
"""A task plugin module for preparing Tensorflow-specific dataset iterators.

.. |flow_from_directory| replace:: :py:meth:`tensorflow.keras.preprocessing.image\\
   .ImageDataGenerator.flow_from_directory`
.. |directory_iterator| replace:: :py:class:`~tensorflow.keras.preprocessing.image\\
   .DirectoryIterator`
"""

from __future__ import annotations

from typing import Optional, Tuple

import structlog
from structlog.stdlib import BoundLogger

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
) -> DirectoryIterator:
    """Yields an iterator for generating batches of real-time augmented image data.

    Args:
        data_dir: The directory containing the image dataset.
        subset: The subset of data (`"training"` or `"validation"`) to use if
            `validation_split` is not `None`. If `None`, then `validation_split` must
            also be `None`.
        image_size: A tuple of integers `(height, width, channels)` used to preprocess
            the images so that they all have the same dimensions and number of color
            channels. `channels=3` means RGB color images and `channels=1` means
            grayscale images. Images with different dimensions will be resized. If
            `channels=1`, color images will be converted into grayscale.
        seed: Sets the random seed used for shuffling and transformations.
        rescale: The rescaling factor for the pixel vectors. If `None` or `0`, no
            rescaling is applied, otherwise multiply the data by the value provided
            (after applying all other transformations). The default is `1.0 / 255`.
        validation_split: The fraction of the data to set aside for validation. If not
            `None`, the value given here must be between `0` and `1`. If `None`, then
            there is no validation set. The default is `0.2`.
        batch_size: The size of the batch on which adversarial samples are generated.
            The default is `32`.
        label_mode: Determines how the label arrays for the dataset will be returned.
            The available choices are: `"categorical"`, `"binary"`, `"sparse"`,
            `"input"`, `None`. For information on the meaning of each choice, see
            the documentation for |flow_from_directory|. The default is `"categorical"`.

    Returns:
        A :py:class:`~tensorflow.keras.preprocessing.image.DirectoryIterator` object.

    See Also:
        - |flow_from_directory|
        - :py:class:`~tensorflow.keras.preprocessing.image.DirectoryIterator`
    """
    color_mode: str = (
        "rgb" if image_size[2] == 3 else "rgba" if image_size[2] == 4 else "grayscale"
    )
    target_size: Tuple[int, int] = image_size[:2]

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
    """Returns the number of unique labels found by the |directory_iterator|.

    Args:
        ds: A |directory_iterator| object.

    Returns:
        The number of unique labels in the dataset.
    """
    return len(ds.class_indices)
