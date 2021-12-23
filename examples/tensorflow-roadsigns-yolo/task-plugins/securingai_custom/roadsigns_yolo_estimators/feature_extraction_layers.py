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
"""Neural network feature extraction layers implemented in Tensorflow/Keras."""

from __future__ import annotations

from typing import Optional, Tuple

import structlog
from structlog.stdlib import BoundLogger

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    from tensorflow import cast as tf_cast
    from tensorflow import float32 as tf_float32
    from tensorflow.keras import Input
    from tensorflow.keras.applications import mobilenet_v2 as tf_mobilenet_v2
    from tensorflow.keras.layers import (
        BatchNormalization,
        Conv2D,
        LeakyReLU,
        MaxPooling2D,
    )

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )

# source: https://github.com/GiaKhangLuu/YOLOv1_from_scratch
# source: https://github.com/experiencor/keras-yolo2


def mobilenet_v2_feature_extraction_layers(
    input_shape: Tuple[int, int, int],
    inputs: Input,
    alpha: float = 1.0,
    weights: Optional[str] = "imagenet",
    pooling: Optional[str] = None,
):
    base_model = tf_mobilenet_v2.MobileNetV2(
        input_shape=input_shape,
        alpha=alpha,
        include_top=False,
        weights=weights,
        pooling=pooling,
    )
    base_model.trainable = False

    x = tf_cast(inputs, tf_float32)
    x = tf_mobilenet_v2.preprocess_input(x)
    x = base_model(x, training=False)

    return x


# Source: https://github.com/pjreddie/darknet/blob/eaf033c0570308dfcd381ed61d274c7f5add7cfc/cfg/yolo-tiny.cfg
def tiny_yolo_feature_extraction_layers(inputs: Input):
    # first conv-pool block:
    x = Conv2D(
        16,
        kernel_size=(3, 3),
        strides=(1, 1),
        padding="same",
        name="conv_1",
        use_bias=False,
    )(inputs)
    x = BatchNormalization(name="norm_1")(x)
    x = LeakyReLU(alpha=0.1)(x)
    x = MaxPooling2D(pool_size=(2, 2))(x)

    # second conv-pool block:
    x = Conv2D(
        32,
        kernel_size=(3, 3),
        strides=(1, 1),
        padding="same",
        name=f"conv_2",
        use_bias=False,
    )(x)
    x = BatchNormalization(name="norm_2")(x)
    x = LeakyReLU(alpha=0.1)(x)
    x = MaxPooling2D(pool_size=(2, 2))(x)

    # third conv-pool block:
    x = Conv2D(
        64,
        kernel_size=(3, 3),
        strides=(1, 1),
        padding="same",
        name=f"conv_3",
        use_bias=False,
    )(x)
    x = BatchNormalization(name="norm_3")(x)
    x = LeakyReLU(alpha=0.1)(x)
    x = MaxPooling2D(pool_size=(2, 2))(x)

    # fourth conv-pool block:
    x = Conv2D(
        128,
        kernel_size=(3, 3),
        strides=(1, 1),
        padding="same",
        name=f"conv_4",
        use_bias=False,
    )(x)
    x = BatchNormalization(name="norm_4")(x)
    x = LeakyReLU(alpha=0.1)(x)
    x = MaxPooling2D(pool_size=(2, 2))(x)

    # fifth conv-pool block:
    x = Conv2D(
        256,
        kernel_size=(3, 3),
        strides=(1, 1),
        padding="same",
        name=f"conv_5",
        use_bias=False,
    )(x)
    x = BatchNormalization(name="norm_5")(x)
    x = LeakyReLU(alpha=0.1)(x)
    x = MaxPooling2D(pool_size=(2, 2))(x)

    # sixth conv-pool block:
    x = Conv2D(
        512,
        kernel_size=(3, 3),
        strides=(1, 1),
        padding="same",
        name="conv_6",
        use_bias=False,
    )(x)
    x = BatchNormalization(name="norm_6")(x)
    x = LeakyReLU(alpha=0.1)(x)
    x = MaxPooling2D(pool_size=(2, 2))(x)

    return x
