# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
from __future__ import annotations

from types import FunctionType
from typing import Callable, Dict, List, Tuple, Union

import structlog
from prefect import task
from structlog.stdlib import BoundLogger

from mitre.securingai import pyplugs
from mitre.securingai.sdk.exceptions import TensorflowDependencyError
from mitre.securingai.sdk.utilities.decorators import require_package

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    from tensorflow.keras.applications import ResNet50
    from tensorflow.keras.applications.vgg16 import VGG16
    from tensorflow.keras.layers import (
        BatchNormalization,
        Conv2D,
        Dense,
        Dropout,
        Flatten,
        GlobalAveragePooling2D,
        MaxPooling2D,
    )
    from tensorflow.keras.metrics import Metric
    from tensorflow.keras.models import Model, Sequential
    from tensorflow.keras.optimizers import Optimizer

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


@task
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def init_classifier(
    model_architecture: str,
    optimizer: Optimizer,
    metrics: List[Union[Metric, FunctionType]],
    input_shape: Tuple[int, int, int],
    n_classes: int,
    loss: str = "categorical_crossentropy",
    training: bool = True,
) -> Sequential:
    classifier: Sequential = KERAS_CLASSIFIERS_REGISTRY[model_architecture](
        input_shape,
        n_classes,
        training,
    )

    classifier.compile(loss=loss, optimizer=optimizer, metrics=metrics)

    return classifier


def shallow_net(
    input_shape: Tuple[int, int, int], n_classes: int, training: bool
) -> Sequential:
    model = Sequential()

    # Flatten inputs
    model.add(Flatten(input_shape=input_shape))

    # single hidden layer:
    model.add(Dense(32, activation="sigmoid"))

    # output layer:
    model.add(Dense(n_classes, activation="softmax"))

    return model


def le_net(
    input_shape: Tuple[int, int, int], n_classes: int, training: bool
) -> Sequential:
    model = Sequential()

    # first convolutional layer:
    model.add(
        Conv2D(32, kernel_size=(3, 3), activation="relu", input_shape=input_shape)
    )

    # second conv layer, with pooling and dropout:
    model.add(Conv2D(64, kernel_size=(3, 3), activation="relu"))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.25))
    model.add(Flatten())

    # dense hidden layer, with dropout:
    model.add(Dense(128, activation="relu"))
    model.add(Dropout(0.5))

    # output layer:
    model.add(Dense(n_classes, activation="softmax"))

    return model


def alex_net(
    input_shape: Tuple[int, int, int], n_classes: int, training: bool
) -> Sequential:
    model = Sequential()

    # first conv-pool block:
    model.add(
        Conv2D(
            96,
            kernel_size=(11, 11),
            strides=(4, 4),
            activation="relu",
            input_shape=input_shape,
        )
    )
    model.add(MaxPooling2D(pool_size=(3, 3), strides=(2, 2)))
    model.add(BatchNormalization())

    # second conv-pool block:
    model.add(Conv2D(256, kernel_size=(5, 5), activation="relu"))
    model.add(MaxPooling2D(pool_size=(3, 3), strides=(2, 2)))
    model.add(BatchNormalization())

    # third conv-pool block:
    model.add(Conv2D(256, kernel_size=(3, 3), activation="relu"))
    model.add(Conv2D(384, kernel_size=(3, 3), activation="relu"))
    model.add(Conv2D(384, kernel_size=(3, 3), activation="relu"))
    model.add(MaxPooling2D(pool_size=(3, 3), strides=(2, 2)))
    model.add(BatchNormalization())

    # dense layers:
    model.add(Flatten())
    model.add(Dense(4096, activation="tanh"))
    model.add(Dropout(0.5))
    model.add(Dense(4096, activation="tanh"))
    model.add(Dropout(0.5))

    # output layer:
    model.add(Dense(n_classes, activation="softmax"))

    return model


def resnet50(
    input_shape: Tuple[int, int, int], n_classes: int, training: bool
) -> Sequential:
    if training:
        base_model = ResNet50(
            weights="imagenet", input_shape=input_shape, include_top=False
        )
        top = base_model.output
        top = GlobalAveragePooling2D()(top)
        top = Dense(1024, activation="relu")(top)
        predictions = Dense(n_classes, activation="softmax")(top)
        model = Model(inputs=base_model.input, outputs=predictions)

        for layer in base_model.layers:
            layer.trainable = False
    else:
        model = ResNet50(weights="imagenet", input_shape=input_shape)
    return model


def vgg16(
    input_shape: Tuple[int, int, int], n_classes: int, training: bool
) -> Sequential:
    if training:
        base_model = VGG16(
            weights="imagenet", input_shape=input_shape, include_top=False
        )
        top = base_model.output
        top = GlobalAveragePooling2D()(top)
        top = Dense(1024, activation="relu")(top)
        predictions = Dense(n_classes, activation="softmax")(top)
        model = Model(inputs=base_model.input, outputs=predictions)

        for layer in base_model.layers:
            layer.trainable = False
    else:
        model = VGG16(weights="imagenet", input_shape=input_shape)
    return model


KERAS_CLASSIFIERS_REGISTRY: Dict[
    str, Callable[[Tuple[int, int, int], int, bool], Sequential]
] = dict(
    shallow_net=shallow_net,
    le_net=le_net,
    alex_net=alex_net,
    resnet50=resnet50,
    vgg16=vgg16,
)
