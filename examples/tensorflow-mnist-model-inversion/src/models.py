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
import warnings
from typing import Callable, Tuple

warnings.filterwarnings("ignore")

import tensorflow as tf

tf.compat.v1.disable_eager_execution()

import mlflow.keras
import structlog
from mlflow.entities import Run as MlflowRun
from mlflow.entities.model_registry import ModelVersion
from mlflow.tracking import MlflowClient
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import (
    BatchNormalization,
    Conv2D,
    Dense,
    Dropout,
    Flatten,
    MaxPooling2D,
)


LOGGER = structlog.get_logger()


def load_model_in_registry(model: str):
    model_uri: str = f"models:/{model}"
    LOGGER.info("load registered model", model_uri=model_uri)
    return mlflow.keras.load_model(model_uri=f"models:/{model}")


def make_model_register(
    active_run: MlflowRun, name: str
) -> Callable[[str], ModelVersion]:
    LOGGER.info("create model register")
    run_id: str = active_run.info.run_id
    artifact_uri: str = active_run.info.artifact_uri
    registered_models = [x.name for x in MlflowClient().list_registered_models()]

    if name not in registered_models:
        LOGGER.info("create registered model", name=name)
        MlflowClient().create_registered_model(name=name)

    def inner_func(model_dir: str) -> ModelVersion:
        source: str = f"{artifact_uri}/{model_dir}"
        LOGGER.info("create model version", name=name, source=source, run_id=run_id)
        return MlflowClient().create_model_version(
            name=name, source=source, run_id=run_id
        )

    return inner_func


def shallow_net(
    input_shape: Tuple[int, int, int] = (28, 28, 1), n_classes: int = 10
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
