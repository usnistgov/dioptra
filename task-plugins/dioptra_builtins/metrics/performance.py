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
"""A task plugin module for getting functions from a performance metric registry."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import structlog
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
)
from structlog.stdlib import BoundLogger

from dioptra import pyplugs

from .exceptions import UnknownPerformanceMetricError

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pyplugs.register
def get_performance_metric_list(
    request: List[Dict[str, str]]
) -> List[Tuple[str, Callable[..., float]]]:
    """Gets multiple performance metric functions from the registry.

    The following metrics are available in the registry,

    - `accuracy`
    - `roc_auc`
    - `categorical_accuracy`
    - `mcc`
    - `f1`
    - `precision`
    - `recall`

    Args:
        request: A list of dictionaries with the keys `name` and `func`. The `func` key
            is used to lookup the metric function in the registry and must match one of
            the metric names listed above. The `name` key is human-readable label for
            the metric function.

    Returns:
        A list of tuples with two elements. The first element of each tuple is the label
        from the `name` key of `request`, and the second element is the callable metric
        function.
    """
    performance_metrics_list: List[Tuple[str, Callable[..., float]]] = []

    for metric in request:
        metric_callable: Optional[Callable[..., float]] = (
            PERFORMANCE_METRICS_REGISTRY.get(metric["func"])
        )

        if metric_callable is not None:
            performance_metrics_list.append((metric["name"], metric_callable))

        else:
            LOGGER.warn(
                "Performance metric not in registry, skipping...",
                name=metric["name"],
                func=metric["func"],
            )

    return performance_metrics_list


@pyplugs.register
def get_performance_metric(func: str) -> Callable[..., float]:
    """Gets a performance metric function from the registry.

    The following metrics are available in the registry,

    - `accuracy`
    - `roc_auc`
    - `categorical_accuracy`
    - `mcc`
    - `f1`
    - `precision`
    - `recall`

    Args:
        func: A string that identifies the performance metric to return from the
            registry. The string must match one of the names of the metrics in the
            registry.

    Returns:
        A callable performance metric function.
    """
    metric_callable: Optional[Callable[..., float]] = PERFORMANCE_METRICS_REGISTRY.get(
        func
    )

    if metric_callable is None:
        LOGGER.error(
            "Performance metric not in registry",
            func=func,
        )
        raise UnknownPerformanceMetricError(
            f"Could not find any performance metric named {func!r} in the metrics "
            "plugin collection. Check spelling and try again."
        )

    return metric_callable


def accuracy(y_true, y_pred, **kwargs) -> float:
    """Calculates the accuracy score.

    Args:
        y_true: A 1d array-like, or label indicator array containing the ground truth
            labels.
        y_pred: A 1d array-like, or label indicator array containing the predicted
            labels, as returned by a classifier.

    Returns:
        The fraction of correctly classified samples.

    See Also:
        - :py:func:`sklearn.metrics.accuracy_score`
    """
    metric: float = accuracy_score(y_true=y_true, y_pred=y_pred, **kwargs)
    return metric


def roc_auc(y_true, y_pred, **kwargs) -> float:
    """Calculates the Area Under the Receiver Operating Characteristic Curve (ROC AUC).

    Args:
        y_true: An array-like of shape `(n_samples,)` or `(n_samples, n_classes)`
            containing the ground truth labels.
        y_pred: An array-like of shape `(n_samples,)` or `(n_samples, n_classes)`
            containing the predicted labels, as returned by a classifier.

    Returns:
        The ROC AUC.

    See Also:
        - :py:func:`sklearn.metrics.roc_auc_score`
    """
    metric: float = roc_auc_score(y_true=y_true, y_score=y_pred, **kwargs)
    return metric


def categorical_accuracy(y_true, y_pred) -> float:
    """Calculates the categorical accuracy.

    This function is a port of the Keras metric
    :py:class:`~tf.keras.metrics.CategoricalAccuracy`.

    Args:
        y_true: A 1d array-like, or label indicator array containing the ground truth
            labels.
        y_pred: A 1d array-like, or label indicator array containing the predicted
            labels, as returned by a classifier.

    Returns:
        The fraction of correctly classified samples.
    """
    if len(y_true.shape) > 1 and len(y_pred.shape) > 1:
        label_comparison: np.ndarray = np.argmax(y_true, axis=-1) == np.argmax(
            y_pred, axis=-1
        )

    else:
        label_comparison = y_true == y_pred

    metric: float = float(np.mean(label_comparison))

    return metric


def mcc(y_true, y_pred, **kwargs) -> float:
    """Calculates the Matthews correlation coefficient.

    Args:
        y_true: A 1d array containing the ground truth labels.
        y_pred: A 1d array containing the predicted labels, as returned by a classifier.

    Returns:
        The Matthews correlation coefficient (`+1` represents a perfect prediction, `0`
        an average random prediction and `-1` and inverse prediction).

    See Also:
        - :py:func:`sklearn.metrics.matthews_corrcoef`
    """
    metric: float = matthews_corrcoef(y_true=y_true, y_pred=y_pred, **kwargs)
    return metric


def f1(y_true, y_pred, **kwargs) -> float:
    """Calculates the F1 score.

    Args:
        y_true: A 1d array-like, or label indicator array containing the ground truth
            labels.
        y_pred: A 1d array-like, or label indicator array containing the predicted
            labels, as returned by a classifier.

    Returns:
        The F1 score of the positive class in binary classification or the weighted
        average of the F1 scores of each class for the multiclass task.

    See Also:
        - :py:func:`sklearn.metrics.f1_score`
    """
    metric: float = f1_score(y_true=y_true, y_pred=y_pred, **kwargs)
    return metric


def precision(y_true, y_pred, **kwargs) -> float:
    """Calculates the precision score.

    Args:
        y_true: A 1d array-like, or label indicator array containing the ground truth
            labels.
        y_pred: A 1d array-like, or label indicator array containing the predicted
            labels, as returned by a classifier.

    Returns:
        The precision of the positive class in binary classification or the weighted
        average of the precision of each class for the multiclass task.

    See Also:
        - :py:func:`sklearn.metrics.precision_score`
    """
    metric: float = precision_score(y_true=y_true, y_pred=y_pred, **kwargs)
    return metric


def recall(y_true, y_pred, **kwargs) -> float:
    """Calculates the recall score.

    Args:
        y_true: A 1d array-like, or label indicator array containing the ground truth
            labels.
        y_pred: A 1d array-like, or label indicator array containing the predicted
            labels, as returned by a classifier.

    Returns:
        The recall of the positive class in binary classification or the weighted
        average of the recall of each class for the multiclass task.

    See Also:
        - :py:func:`sklearn.metrics.recall_score`
    """
    metric: float = recall_score(y_true=y_true, y_pred=y_pred, **kwargs)
    return metric


PERFORMANCE_METRICS_REGISTRY: Dict[str, Callable[..., Any]] = dict(
    accuracy=accuracy,
    roc_auc=roc_auc,
    categorical_accuracy=categorical_accuracy,
    mcc=mcc,
    f1=f1,
    precision=precision,
    recall=recall,
)
