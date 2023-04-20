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
from typing import Any, Dict, List, Union

import structlog
from structlog.stdlib import BoundLogger

from dioptra import pyplugs
from dioptra.sdk.exceptions import TensorflowDependencyError
from dioptra.sdk.utilities.decorators import require_package

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
