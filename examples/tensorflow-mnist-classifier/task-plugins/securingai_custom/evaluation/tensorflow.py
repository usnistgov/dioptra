from __future__ import annotations

from types import FunctionType
from typing import Any, Dict, List, Union

import structlog
from structlog.stdlib import BoundLogger

from mitre.securingai import pyplugs
from mitre.securingai.sdk.exceptions import TensorflowDependencyError
from mitre.securingai.sdk.utilities.decorators import require_package

from . import import_keras

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


@pyplugs.register
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def evaluate_metrics_tensorflow(classifier, dataset) -> Dict[str, float]:
    result = classifier.evaluate(dataset, verbose=0)
    return dict(zip(classifier.metrics_names, result))


@pyplugs.register
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def get_optimizer(optimizer: str, learning_rate: float) -> Optimizer:
    return import_keras.get_optimizer(optimizer)(learning_rate)


@pyplugs.register
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def get_model_callbacks(callbacks_list: List[Dict[str, Any]]) -> List[Callback]:
    return [
        import_keras.get_callback(callback["name"])(**callback.get("parameters", {}))
        for callback in callbacks_list
    ]


@pyplugs.register
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def get_performance_metrics(
    metrics_list: List[Dict[str, Any]]
) -> List[Union[Metric, FunctionType]]:
    performance_metrics: List[Metric] = []

    for metric in metrics_list:
        new_metric: Union[Metric, FunctionType] = import_keras.get_metric(
            metric["name"]
        )
        performance_metrics.append(
            new_metric(**metric.get("parameters"))
            if not isinstance(new_metric, FunctionType) and metric.get("parameters")
            else new_metric
        )

    return performance_metrics
