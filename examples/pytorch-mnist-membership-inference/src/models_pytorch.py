# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
import warnings
from typing import Callable

warnings.filterwarnings("ignore")

import mlflow.keras
import structlog
from mlflow.entities import Run as MlflowRun
from mlflow.entities.model_registry import ModelVersion
from mlflow.tracking import MlflowClient
from torch import nn
from torch.nn import (
    Conv2d,
    Flatten,
    Linear,
    MaxPool2d,
    ReLU,
    Sequential,
    Softmax,
)

LOGGER = structlog.get_logger()


def load_model_in_registry(model: str):
    model_uri: str = f"models:/{model}"
    LOGGER.info("load registered model", model_uri=model_uri)
    return mlflow.pytorch.load_model(model_uri=f"models:/{model}")


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


def le_net(
    input_shape: Tuple[int, int, int] = (28, 28, 1), n_classes: int = 10
) -> Sequential:
    model = Sequential(
        # first convolutional layer:
        Conv2d(1, 20, 5, 1),
        ReLU(),
        MaxPool2d(2, 2),
        # second conv layer, with pooling and dropout:
        Conv2d(20, 50, 5, 1),
        ReLU(),
        MaxPool2d(2, 2),
        Flatten(),
        # dense hidden layer, with dropout:
        Linear(4 * 4 * 50, 500),
        ReLU(),
        # output layer:
        Linear(500, 10),
        Softmax(),
    )
    return model
