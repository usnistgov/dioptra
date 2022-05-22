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

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    import tensorflow as tf
    from tensorflow.keras import Model
    from tensorflow.keras.applications.efficientnet import (
        EfficientNetB0,
        EfficientNetB1,
        EfficientNetB2,
        EfficientNetB3,
        EfficientNetB4,
        EfficientNetB5,
        EfficientNetB6,
        EfficientNetB7,
    )
    from tensorflow.keras.applications.efficientnet import (
        preprocess_input as efficient_net_preprocess_input,
    )
    from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2
    from tensorflow.keras.applications.mobilenet_v2 import (
        preprocess_input as mobilenet_v2_preprocess_input,
    )
    from tensorflow.keras.layers import InputLayer

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


class EfficientNetBackbone(Model):
    def __init__(
        self,
        flavor: str = "B4",
        input_shape: Optional[Tuple[int, int, int]] = None,
        weights: str = "imagenet",
        input_tensor: Optional[InputLayer] = None,
        pooling: Optional[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        efficient_net_registry = dict(
            b0=EfficientNetB0,
            b1=EfficientNetB1,
            b2=EfficientNetB2,
            b3=EfficientNetB3,
            b4=EfficientNetB4,
            b5=EfficientNetB5,
            b6=EfficientNetB6,
            b7=EfficientNetB7,
        )
        self.model = efficient_net_registry[flavor.strip().lower()](
            include_top=False,
            weights=weights,
            input_tensor=input_tensor,
            input_shape=input_shape,
            pooling=pooling,
        )
        self.model.trainable = False

    @property
    def output_grid_shape(self):
        return (self.model.output_shape[1], self.model.output_shape[2])

    def call(self, inputs):
        x = self.normalize(inputs)
        return self.model(x, training=False)

    @staticmethod
    def normalize(inputs):
        x = tf.cast(inputs, tf.float32)
        return efficient_net_preprocess_input(x)


class MobileNetV2Backbone(Model):
    def __init__(
        self,
        input_shape: Optional[Tuple[int, int, int]] = None,
        alpha: float = 1.0,
        weights: str = "imagenet",
        input_tensor: Optional[InputLayer] = None,
        pooling: Optional[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.model = MobileNetV2(
            input_shape=input_shape,
            alpha=alpha,
            include_top=False,
            weights=weights,
            input_tensor=input_tensor,
            pooling=pooling,
        )
        self.model.trainable = False

    @property
    def output_grid_shape(self):
        return (self.model.output_shape[1], self.model.output_shape[2])

    def call(self, inputs):
        x = self.normalize(inputs)
        return self.model(x, training=False)

    @staticmethod
    def normalize(inputs):
        x = tf.cast(inputs, tf.float32)
        return mobilenet_v2_preprocess_input(x)
