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
from typing import Callable, Dict, List, Tuple, Union

import structlog
from structlog.stdlib import BoundLogger

from dioptra import pyplugs
from dioptra.sdk.exceptions import TensorflowDependencyError
from dioptra.sdk.utilities.decorators import require_package

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    from tensorflow.keras.layers import (
        BatchNormalization,
        Conv2D,
        Dense,
        Dropout,
        Flatten,
        MaxPooling2D,
    )
    from tensorflow.keras.metrics import Metric
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.optimizers import Optimizer

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


@pyplugs.register
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def init_classifier(
    model_architecture: str,
    optimizer: Optimizer,
    metrics: List[Union[Metric, FunctionType]],
    input_shape: Tuple[int, int, int],
    n_classes: int,
    loss: str = "categorical_crossentropy",
) -> Sequential:
    """Initializes an untrained neural network image classifier for Tensorflow/Keras.

    The `model_architecture` argument is used to select a neural network architecture
    from the architecture registry. The string passed to `model_architecture` must match
    one of the following,

    - `"shallow_net"` - A shallow neural network architecture.
    - `"le_net"` - The LeNet-5 convolutional neural network architecture.
    - `"alex_net"` - The AlexNet convolutional neural network architecture.

    Args:
        model_architecture: The neural network architecture to use.
        optimizer: A Keras :py:class:`~tf.keras.optimizers.Optimizer` providing an
            algorithm to use to train the estimator, such as
            :py:class:`~tf.keras.optimizers.SGD` and
            :py:class:`~tf.keras.optimizers.Adam`.
        metrics: A list of metrics to be evaluated by the model during training and
            testing.
        input_shape: A shape tuple of integers, not including the batch size, specifying
            the dimensions of the image data. The shape tuple for all classifiers in the
            architecture registry follows the convention `(height, width, channels)`.
        n_classes: The number of target labels in the dataset.
        loss: A string specifying the loss function to be minimized during training. The
            string must match the name of one of the loss functions in the
            :py:mod:`tf.keras.losses` module. The default is
            `"categorical_crossentropy"`.

    Returns:
        A compiled :py:class:`~tf.keras.Sequential` object.

    See Also:
        - :py:mod:`tf.keras.losses`
        - :py:mod:`tf.keras.optimizers`
        - :py:class:`tf.keras.Sequential`
    """
    classifier: Sequential = KERAS_CLASSIFIERS_REGISTRY[model_architecture](
        input_shape,
        n_classes,
    )
    classifier.compile(loss=loss, optimizer=optimizer, metrics=metrics)

    return classifier


def shallow_net(input_shape: Tuple[int, int, int], n_classes: int) -> Sequential:
    """Builds an untrained shallow neural network architecture for Tensorflow/Keras.

    Args:
        input_shape: A shape tuple of integers, not including the batch size, specifying
            the dimensions of the image data. The shape tuple for all classifiers in the
            architecture registry follows the convention `(height, width, channels)`.
        n_classes: The number of target labels in the dataset.

    Returns:
        A :py:class:`~tf.keras.Sequential` object.

    See Also:
        - :py:class:`tf.keras.Sequential`
    """
    model = Sequential()

    # Flatten inputs
    model.add(Flatten(input_shape=input_shape))

    # single hidden layer:
    model.add(Dense(32, activation="sigmoid"))

    # output layer:
    model.add(Dense(n_classes, activation="softmax"))

    return model


def le_net(input_shape: Tuple[int, int, int], n_classes: int) -> Sequential:
    """Builds an untrained LeNet-5 neural network architecture for Tensorflow/Keras.

    Args:
        input_shape: A shape tuple of integers, not including the batch size, specifying
            the dimensions of the image data. The shape tuple for all classifiers in the
            architecture registry follows the convention `(height, width, channels)`.
        n_classes: The number of target labels in the dataset.

    Returns:
        A :py:class:`~tf.keras.Sequential` object.

    See Also:
        - :py:class:`tf.keras.Sequential`
    """
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


def alex_net(input_shape: Tuple[int, int, int], n_classes: int) -> Sequential:
    """Builds an untrained AlexNet neural network architecture for Tensorflow/Keras.

    Args:
        input_shape: A shape tuple of integers, not including the batch size, specifying
            the dimensions of the image data. The shape tuple for all classifiers in the
            architecture registry follows the convention `(height, width, channels)`.
        n_classes: The number of target labels in the dataset.

    Returns:
        A :py:class:`~tf.keras.Sequential` object.

    See Also:
        - :py:class:`tf.keras.Sequential`
    """
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


KERAS_CLASSIFIERS_REGISTRY: Dict[
    str, Callable[[Tuple[int, int, int], int], Sequential]
] = dict(shallow_net=shallow_net, le_net=le_net, alex_net=alex_net)
