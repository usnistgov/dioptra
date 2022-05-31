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
from __future__ import annotations

import importlib
from types import FunctionType, ModuleType
from typing import Union

import structlog
from structlog.stdlib import BoundLogger

from dioptra.sdk.exceptions import TensorflowDependencyError
from dioptra.sdk.utilities.decorators import require_package

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
