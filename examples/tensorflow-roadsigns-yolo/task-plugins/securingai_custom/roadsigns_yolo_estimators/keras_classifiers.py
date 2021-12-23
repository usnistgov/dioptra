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
"""Neural network image classifiers implemented in Tensorflow/Keras."""

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
from .output_layers import attach_classifier_output_layers

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    from tensorflow.keras import Input, Model
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
def init_classifier(
    model_architecture: str,
    optimizer: Optimizer,
    n_classes: int,
    metrics: Optional[List[Union[Metric, FunctionType]]] = None,
    loss: str = "categorical_crossentropy",
) -> Model:
    classifier: Model = KERAS_CLASSIFIERS_REGISTRY[model_architecture](
        n_classes=n_classes,
    )
    classifier.compile(
        loss=loss,
        optimizer=optimizer,
        metrics=metrics if metrics else None,
    )

    return classifier


def mobilenet_v2(
    n_classes: int,
    alpha: float = 1.0,
    weights: Optional[str] = "imagenet",
    pooling: Optional[str] = None,
):
    conv_layer_specs = []
    dense_layer_specs = []

    input_shape: Tuple[int, int, int] = (224, 224, 3)
    inputs = Input(shape=input_shape)
    x = mobilenet_v2_feature_extraction_layers(
        input_shape=input_shape,
        inputs=inputs,
        alpha=alpha,
        weights=weights,
        pooling=pooling,
    )
    outputs = attach_classifier_output_layers(
        x,
        n_classes=n_classes,
        dense_layer_specs=dense_layer_specs,
        input_shape=x.shape[1:],
        conv_layer_specs=conv_layer_specs,
        transition_strategy="avgpool",
    )
    model = Model(inputs, outputs)

    return model


def tiny_yolo(n_classes: int) -> Model:
    conv_layer_specs = [{"strides": (1, 1), "pooling": "avgpool", "dropout": 0.5}]
    dense_layer_specs = []

    input_shape: Tuple[int, int, int] = (224, 224, 3)
    inputs = Input(shape=input_shape)
    x = tiny_yolo_feature_extraction_layers(inputs=inputs)
    outputs = attach_classifier_output_layers(
        x,
        n_classes=n_classes,
        dense_layer_specs=dense_layer_specs,
        input_shape=x.shape[1:],
        conv_layer_specs=conv_layer_specs,
        output_layer_spec={"activation": "leaky"},
        transition_strategy="flatten",
    )
    model = Model(inputs, outputs)

    return model


KERAS_CLASSIFIERS_REGISTRY: Dict[
    str, Callable[[Tuple[int, int, int], int], Model]
] = dict(mobilenet_v2=mobilenet_v2, tiny_yolo=tiny_yolo)
