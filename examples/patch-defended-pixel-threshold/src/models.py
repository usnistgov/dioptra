import warnings
from typing import Tuple

warnings.filterwarnings("ignore")

import tensorflow as tf

tf.compat.v1.disable_eager_execution()

import mlflow.keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import (
    BatchNormalization,
    Conv2D,
    Dense,
    Dropout,
    Flatten,
    MaxPooling2D,
)


def load_model_in_registry(model: str):
    return mlflow.keras.load_model(model_uri=f"models:/{model}")


def le_net(
    input_shape: Tuple[int, int, int] = (28, 28, 1), n_classes: int = 10
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
    input_shape: Tuple[int, int, int] = (224, 224, 1), n_classes: int = 10
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
