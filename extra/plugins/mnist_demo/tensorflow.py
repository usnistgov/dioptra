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

from types import FunctionType
from typing import Any, Dict, List, Union, Optional

import datetime
import structlog
import tensorflow as tf

from structlog.stdlib import BoundLogger

from dioptra import pyplugs
from dioptra.sdk.exceptions import TensorflowDependencyError
from dioptra.sdk.utilities.decorators import require_package

from . import import_keras
from .restapi import post_metrics
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
def init_tensorflow(seed: int) -> None:
    """Initializes Tensorflow to ensure reproducibility.

    This task plugin **must** be run before any other features from Tensorflow are used
    to ensure reproducibility.

    Args:
        seed: The seed to use for Tensorflow's random number generator.
    """
    tf.random.set_seed(seed)


@pyplugs.register
def fit_tensorflow(
    estimator: Any,
    x: Any = None,
    y: Any = None,
    fit_kwargs: Optional[Dict[str, Any]] = None,
) -> Any:
    fit_kwargs = fit_kwargs or {}
    time_start: datetime.datetime = datetime.datetime.now()

    LOGGER.info(
        "Begin estimator fit",
        timestamp=time_start.isoformat(),
    )
    try:
        estimator_fit_result: Any = estimator.fit(x, y, **fit_kwargs)

    except AttributeError:
        LOGGER.exception("Estimator does not have a fit method")
        raise

    time_end: datetime.datetime = datetime.datetime.now()

    total_seconds: float = (time_end - time_start).total_seconds()
    total_minutes: float = total_seconds / 60

    post_metrics(metric_name="training_time_in_minutes", metric_value=total_minutes)
    
    LOGGER.info(
        "Estimator fit complete",
        timestamp=time_end.isoformat(),
        total_minutes=total_minutes,
    )

    return estimator_fit_result


@pyplugs.register
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def evaluate_metrics_tensorflow(classifier, dataset) -> Dict[str, float]:
    result = classifier.evaluate(dataset, verbose=0, return_dict=True)
    return result

@pyplugs.register
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def predict_tensorflow(classifier, dataset) -> Dict[str, float]:
    result = classifier.predict(dataset)
    return result

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
