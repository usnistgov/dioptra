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
"""Neural network object detectors implemented in Tensorflow/Keras."""

from __future__ import annotations

from types import FunctionType
from typing import Callable, Dict, List, Optional, Tuple, Union

import structlog
from structlog.stdlib import BoundLogger

from mitre.securingai import pyplugs
from mitre.securingai.sdk.exceptions import TensorflowDependencyError
from mitre.securingai.sdk.utilities.decorators import require_package

from .feature_extraction_layers import (
    mobilenet_v2_feature_extraction_layers,
    tiny_yolo_feature_extraction_layers,
)
from .losses import YOLOLoss
from .output_layers import (
    attach_classifier_output_layers,
    attach_yolo_v1_object_detector_layers,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    from tensorflow.keras import Input, Model
    from tensorflow.keras.layers import Concatenate, MaxPooling2D, Reshape
    from tensorflow.keras.metrics import Metric
    from tensorflow.keras.optimizers import Optimizer

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


# source: https://github.com/GiaKhangLuu/YOLOv1_from_scratch
# source: https://github.com/experiencor/keras-yolo2


@pyplugs.register
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def init_object_detector(
    model_architecture: str,
    optimizer: Optimizer,
    n_classes: int,
    metrics: Optional[List[Union[Metric, FunctionType]]] = None,
    n_bounding_boxes: int = 2,
    grid_size: int = 7,
    loss: str = "yolo_loss",
    bbox_transition_strategy: Optional[str] = None,
    classification_transition_strategy: Optional[str] = None,
) -> Model:
    object_detector: Model = KERAS_ATTACH_OBJECT_DETECTORS_REGISTRY[model_architecture](
        n_classes=n_classes,
        n_bounding_boxes=n_bounding_boxes,
        grid_size=grid_size,
        bbox_transition_strategy=bbox_transition_strategy,
        classification_transition_strategy=classification_transition_strategy,
    )
    object_detector_loss = YOLOLoss() if loss == "yolo_loss" else loss
    object_detector.compile(
        loss=object_detector_loss,
        optimizer=optimizer,
        metrics=metrics if metrics else None,
    )

    return object_detector


def mobilenet_v2(
    n_classes: int,
    alpha: float = 1.0,
    weights: Optional[str] = "imagenet",
    pooling: Optional[str] = None,
    n_bounding_boxes: int = 2,
    grid_size: int = 7,
    bbox_transition_strategy: Optional[str] = None,
    classification_transition_strategy: Optional[str] = None,
):
    # conv_layer_specs = [{"strides": (1, 1), "filters": 1280}]
    # dense_layer_specs = [
    #     {"units": 256, "activation": "linear"},
    #     {"units": 4096, "activation": "leaky", "dropout": 0.5},
    # ]
    bbox_conv_layer_specs = [
        {
            "kernel_size": (1, 1),
            "strides": (1, 1),
            "filters": 1024,
            "padding": "valid",
            "use_bias": False,
            "dropout": 0.5,
        },
        {
            "kernel_size": (1, 1),
            "strides": (1, 1),
            "filters": 512,
            "padding": "valid",
            "use_bias": False,
            "dropout": 0.5,
        },
        {
            "kernel_size": (1, 1),
            "strides": (1, 1),
            "filters": 4 * n_bounding_boxes,
            "padding": "valid",
            "use_bias": True,
        },
    ]
    classification_conv_layer_specs = [
        {
            "kernel_size": (1, 1),
            "strides": (1, 1),
            "filters": 1024,
            "padding": "valid",
            "use_bias": False,
            "dropout": 0.5,
        },
        {
            "kernel_size": (1, 1),
            "strides": (1, 1),
            "filters": 512,
            "padding": "valid",
            "use_bias": False,
            "dropout": 0.5,
        },
        {
            "kernel_size": (1, 1),
            "strides": (1, 1),
            "filters": n_bounding_boxes * (n_classes + 1),
            "padding": "valid",
            "use_bias": True,
        },
    ]
    bbox_dense_layer_specs = []
    classification_dense_layer_specs = []

    input_shape: Tuple[int, int, int] = (448, 448, 3)
    inputs = Input(shape=input_shape)
    x = mobilenet_v2_feature_extraction_layers(
        input_shape=input_shape,
        inputs=inputs,
        alpha=alpha,
        weights=weights,
        pooling=pooling,
    )
    # x = MaxPooling2D(pool_size=(2, 2), padding="same")(x)
    # x = attach_yolo_v1_object_detector_layers(
    #     x,
    #     input_shape=x.shape[1:],
    #     dense_layer_specs=dense_layer_specs,
    #     n_classes=n_classes,
    #     n_bounding_boxes=n_bounding_boxes,
    #     grid_size=grid_size,
    #     conv_layer_specs=conv_layer_specs,
    #     transition_strategy=transition_strategy,
    # )
    bbox_detector = attach_yolo_v1_object_detector_layers(
        x,
        input_shape=x.shape[1:],
        dense_layer_specs=bbox_dense_layer_specs,
        n_classes=n_classes,
        n_bounding_boxes=n_bounding_boxes,
        grid_size=grid_size,
        conv_layer_specs=bbox_conv_layer_specs,
        output_layer_spec={"activation": "sigmoid"},
        transition_strategy=bbox_transition_strategy,
    )
    classification_detector = attach_classifier_output_layers(
        x,
        n_classes=n_classes,
        dense_layer_specs=classification_dense_layer_specs,
        input_shape=x.shape[1:],
        conv_layer_specs=classification_conv_layer_specs,
        transition_strategy=classification_transition_strategy,
    )
    bbox_detector = Reshape((14, 14, n_bounding_boxes, 4))(bbox_detector)
    classification_detector = Reshape((14, 14, n_bounding_boxes, n_classes + 1))(
        classification_detector
    )
    outputs = Concatenate(axis=-1)([bbox_detector, classification_detector])
    # outputs = Reshape((grid_size, grid_size, 5 * n_bounding_boxes + n_classes))(x)
    model = Model(inputs, outputs)

    return model


def tiny_yolo(
    n_classes: int,
    n_bounding_boxes: int = 2,
    grid_size: int = 7,
    transition_strategy: str = "flatten",
) -> Model:
    conv_layer_specs = [{"strides": (1, 1)}, {"strides": (1, 1)}, {"strides": (1, 1)}]
    dense_layer_specs = [
        {"units": 256, "activation": "linear"},
        {"units": 4096, "activation": "leaky", "dropout": 0.5},
    ]

    input_shape: Tuple[int, int, int] = (448, 448, 3)
    inputs = Input(shape=input_shape)
    x = tiny_yolo_feature_extraction_layers(inputs=inputs)
    x = attach_yolo_v1_object_detector_layers(
        x,
        input_shape=x.shape[1:],
        dense_layer_specs=dense_layer_specs,
        n_classes=n_classes,
        n_bounding_boxes=n_bounding_boxes,
        grid_size=grid_size,
        conv_layer_specs=conv_layer_specs,
        transition_strategy=transition_strategy,
    )
    outputs = Reshape((grid_size, grid_size, 5 * n_bounding_boxes + n_classes))(x)
    model = Model(inputs, outputs)

    return model


KERAS_ATTACH_OBJECT_DETECTORS_REGISTRY: Dict[
    str, Callable[[Tuple[int, int, int], int], Model]
] = dict(mobilenetv2=mobilenet_v2)
# ] = dict(mobilenetv2=mobilenet_v2, tiny_yolo=tiny_yolo)
