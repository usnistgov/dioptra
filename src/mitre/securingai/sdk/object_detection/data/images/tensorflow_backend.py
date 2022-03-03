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

import structlog
from structlog.stdlib import BoundLogger

from .image_data import ImageData

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    import tensorflow as tf
    from tensorflow import DType, Tensor
    from tensorflow.image import ResizeMethod

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


class TensorflowImageData(ImageData):
    def __init__(
        self,
        num_channels: int,
        expand_animations: bool = False,
        resize_method: str = ResizeMethod.BILINEAR,
        resize_preserve_aspect_ratio: bool = False,
        resize_antialias: bool = False,
        dtype: DType = tf.float32,
    ):
        self._num_channels = num_channels
        self._expand_animations = expand_animations
        self._resize_method = resize_method
        self._resize_preserve_aspect_ratio = resize_preserve_aspect_ratio
        self._resize_antialias = resize_antialias
        self._dtype = dtype

    def read_file(self, filepath: Tensor) -> Tensor:
        image = tf.io.read_file(filename=filepath)
        image = tf.io.decode_image(
            contents=image,
            channels=self._num_channels,
            expand_animations=self._expand_animations,
        )

        return tf.cast(image, self._dtype)

    def resize(self, images: Tensor, size: Tensor) -> Tensor:
        return tf.image.resize(
            images=images,
            size=size,
            method=self._resize_method,
            preserve_aspect_ratio=self._resize_preserve_aspect_ratio,
            antialias=self._resize_antialias,
        )
