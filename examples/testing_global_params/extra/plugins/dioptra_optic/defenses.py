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
from typing import Any

import structlog
import tensorflow as tf
from art.defences.preprocessor import (
    GaussianAugmentation,
    JpegCompression,
    SpatialSmoothing,
)
from keras import ops

from dioptra import pyplugs

from .data import create_transformed_dataset

LOGGER = structlog.get_logger()


@pyplugs.register
def preprocessing(
    dataset: tf.data.Dataset,
    defense_name: str = "spatial_smoothing",
    defense_options: dict[str, Any] | None = None,
    save_dataset: bool = False,
) -> tf.data.Dataset:
    """
    Apply a preprocessing defense to a dataset.

    Args:
        dataset: The tf.data.Dataset to apply the defense to.
        defense_name: The name of the defense.
        defense_options: Options passed to the defense as kwargs.

    Returns:
        The defended dataset.
    """
    defense_options = defense_options or {}

    clip_values = (0.0, 255.0) if ops.max(next(iter(dataset))[0]) > 1.0 else (0.0, 1.0)

    method = {
        "spatial_smoothing": SpatialSmoothing,
        "jpeg_compression": JpegCompression,
        "gaussian_augmentation": GaussianAugmentation,
    }.get(defense_name, None)

    if method is None:
        raise ValueError(f"No such defense method: '{defense_name}'")

    defense = method(clip_values=clip_values, **defense_options)

    @tf.numpy_function(Tout=(tf.float32, tf.float32))
    def defend_fn(x, y):
        return defense(x, y)

    return create_transformed_dataset(dataset, defend_fn, save_dataset)
