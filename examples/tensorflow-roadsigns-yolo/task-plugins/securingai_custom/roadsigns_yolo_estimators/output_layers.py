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
"""Neural network output layers implemented in Tensorflow/Keras."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import structlog
from structlog.stdlib import BoundLogger

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    from tensorflow.keras.layers import (
        Activation,
        AveragePooling2D,
        BatchNormalization,
        Conv2D,
        Dense,
        Dropout,
        Flatten,
        GlobalAveragePooling2D,
        GlobalMaxPool2D,
        LeakyReLU,
        MaxPooling2D,
        Softmax,
    )

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


# source: https://github.com/GiaKhangLuu/YOLOv1_from_scratch
# source: https://github.com/experiencor/keras-yolo2


# darknet classifier output: https://github.com/pjreddie/darknet/blob/eaf033c0570308dfcd381ed61d274c7f5add7cfc/cfg/darknet.cfg
def attach_classifier_output_layers(
    x,
    n_classes: int,
    dense_layer_specs: List[Dict[str, Any]],
    input_shape: Optional[Tuple[int, int, int]] = None,
    conv_layer_specs: Optional[List[Dict[str, Any]]] = None,
    output_layer_spec: Optional[List[Dict[str, Any]]] = None,
    transition_strategy: Optional[str] = "flatten",
):
    if conv_layer_specs is None:
        conv_layer_specs = []

    if output_layer_spec is None:
        output_layer_spec = {}

    # additional conv block layers
    for idx, spec in enumerate(conv_layer_specs, start=1):
        conv_2d_params = dict(
            filters=spec.get("filters", 1024),
            kernel_size=spec.get("kernel_size", (3, 3)),
            strides=spec["strides"],
            padding=spec.get("padding", "same"),
            name=f"classification_output_conv_{idx}",
            use_bias=spec.get("use_bias", True),
        )

        if idx == 1 and input_shape is not None:
            conv_2d_params["input_shape"] = input_shape

        x = Conv2D(**conv_2d_params)(x)
        x = BatchNormalization(name=f"classification_output_norm_{idx}")(x)
        x = LeakyReLU(alpha=0.1)(x)

        if spec.get("pooling") == "avgpool":
            x = AveragePooling2D(pool_size=(2, 2), padding="same")(x)

        elif spec.get("pooling") == "maxpool":
            x = MaxPooling2D(pool_size=(2, 2), padding="same")(x)

        if spec.get("dropout", 0) > 0:
            x = Dropout(rate=spec["dropout"])(x)

    if transition_strategy is not None:
        transition_layers = dict(
            avgpool=GlobalAveragePooling2D(),
            flatten=Flatten(),
            maxpool=GlobalMaxPool2D(),
        )
        x = transition_layers[transition_strategy.lower()](x)

        # dense layers:
        for idx, spec in enumerate(dense_layer_specs, start=1):
            activation = (
                LeakyReLU(alpha=0.1)
                if spec.get("activation") == "leaky"
                else spec.get("activation")
            )
            x = Dense(
                units=spec["units"],
                activation=activation,
                name=f"classification_output_dense_{idx}",
            )(x)

            if spec.get("dropout", 0) > 0:
                x = Dropout(rate=spec["dropout"])(x)

        # output layer:
        x = Dense(n_classes, name="classification_predictions")(x)

    if output_layer_spec.get("activation") is not None:
        activation = (
            LeakyReLU(alpha=0.1)
            if output_layer_spec.get["activation"] == "leaky"
            else Activation(output_layer_spec["activation"])
        )
        x = activation(x)

    return x


def attach_yolo_v1_object_detector_layers(
    x,
    input_shape: Tuple[int, int, int],
    dense_layer_specs: List[Dict[str, Any]],
    n_classes: int,
    n_bounding_boxes: int = 2,
    grid_size: int = 7,
    conv_layer_specs: Optional[List[Dict[str, Any]]] = None,
    output_layer_spec: Optional[List[Dict[str, Any]]] = None,
    transition_strategy: Optional[str] = "flatten",
):
    if conv_layer_specs is None:
        conv_layer_specs = []

    if output_layer_spec is None:
        output_layer_spec = {}

    # conv block layers
    for idx, spec in enumerate(conv_layer_specs, start=1):
        conv_2d_params = dict(
            filters=spec.get("filters", 1024),
            kernel_size=spec.get("kernel_size", (3, 3)),
            strides=spec["strides"],
            padding=spec.get("padding", "same"),
            name=f"bbox_output_conv_{idx}",
            use_bias=spec.get("use_bias", True),
        )

        if idx == 1:
            conv_2d_params["input_shape"] = input_shape

        x = Conv2D(**conv_2d_params)(x)
        x = BatchNormalization(name=f"bbox_output_norm_{idx}")(x)
        x = LeakyReLU(alpha=0.1)(x)

        if spec.get("pooling") == "avgpool":
            x = AveragePooling2D(pool_size=(2, 2), padding="same")(x)

        elif spec.get("pooling") == "maxpool":
            x = MaxPooling2D(pool_size=(2, 2), padding="same")(x)

        if spec.get("dropout", 0) > 0:
            x = Dropout(rate=spec["dropout"])(x)

    # dense layers:
    if transition_strategy is not None:
        transition_layers = dict(
            avgpool=GlobalAveragePooling2D(),
            flatten=Flatten(),
            maxpool=GlobalMaxPool2D(),
        )

        x = transition_layers[transition_strategy.lower()](x)

        for idx, spec in enumerate(dense_layer_specs, start=1):
            activation = (
                LeakyReLU(alpha=0.1)
                if spec.get("activation") == "leaky"
                else spec.get("activation")
            )
            x = Dense(
                units=spec["units"],
                activation=activation,
                name=f"bbox_output_dense_{idx}",
            )(x)

            if spec.get("dropout", 0) > 0:
                x = Dropout(rate=spec["dropout"])(x)

        # output layer:
        x = Dense(
            grid_size * grid_size * (n_bounding_boxes * 5 + n_classes),
            name="bbox_predictions",
        )(x)

    if output_layer_spec.get("activation") is not None:
        activation = (
            LeakyReLU(alpha=0.1)
            if output_layer_spec["activation"] == "leaky"
            else Activation(output_layer_spec["activation"])
        )
        x = activation(x)

    return x
