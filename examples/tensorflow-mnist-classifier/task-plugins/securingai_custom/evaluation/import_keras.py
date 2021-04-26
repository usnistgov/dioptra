from __future__ import annotations

import importlib
from types import FunctionType, ModuleType
from typing import Union

import structlog
from structlog.stdlib import BoundLogger

from mitre.securingai.sdk.exceptions import TensorflowDependencyError
from mitre.securingai.sdk.utilities.decorators import require_package

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    from tensorflow.keras.callbacks import Callback
    from tensorflow.keras.metrics import Metric
    from tensorflow.keras.optimizers import Optimizer

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )

KERAS_CALLBACKS: str = "tensorflow.keras.callbacks"
KERAS_METRICS: str = "tensorflow.keras.metrics"
KERAS_OPTIMIZERS: str = "tensorflow.keras.optimizers"


@require_package("tensorflow", exc_type=TensorflowDependencyError)
def get_callback(callback_name: str) -> Callback:
    keras_callbacks: ModuleType = importlib.import_module(KERAS_CALLBACKS)
    callback: Callback = getattr(keras_callbacks, callback_name)
    return callback


@require_package("tensorflow", exc_type=TensorflowDependencyError)
def get_metric(metric_name: str) -> Union[Metric, FunctionType]:
    keras_metrics: ModuleType = importlib.import_module(KERAS_METRICS)
    metric: Metric = getattr(keras_metrics, metric_name)
    return metric


@require_package("tensorflow", exc_type=TensorflowDependencyError)
def get_optimizer(optimizer_name: str) -> Optimizer:
    keras_optimizers: ModuleType = importlib.import_module(KERAS_OPTIMIZERS)
    optimizer: Optimizer = getattr(keras_optimizers, optimizer_name)
    return optimizer
