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

from mitre.securingai import pyplugs

from .exceptions import UnknownPerformanceMetricError

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pyplugs.register
def get_performance_metric_list(
    request: List[Dict[str, str]]
) -> List[Tuple[str, Callable[..., float]]]:
    performance_metrics_list: List[Tuple[str, Callable[..., float]]] = []

    for metric in request:
        metric_callable: Optional[
            Callable[..., float]
        ] = PERFORMANCE_METRICS_REGISTRY.get(metric["func"])

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
    metric: float = accuracy_score(y_true=y_true, y_pred=y_pred, **kwargs)
    return metric


def roc_auc(y_true, y_pred, **kwargs) -> float:
    metric: float = roc_auc_score(y_true=y_true, y_score=y_pred, **kwargs)
    return metric


def categorical_accuracy(y_true, y_pred) -> float:
    if len(y_true.shape) > 1 and len(y_pred.shape) > 1:
        label_comparison: np.ndarray = np.argmax(y_true, axis=-1) == np.argmax(
            y_pred, axis=-1
        )

    else:
        label_comparison = y_true == y_pred

    metric: float = float(np.mean(label_comparison))

    return metric


def mcc(y_true, y_pred, **kwargs) -> float:
    metric: float = matthews_corrcoef(y_true=y_true, y_score=y_pred, **kwargs)
    return metric


def f1(y_true, y_pred, **kwargs) -> float:
    metric: float = f1_score(y_true=y_true, y_pred=y_pred, **kwargs)
    return metric


def precision(y_true, y_pred, **kwargs) -> float:
    metric: float = precision_score(y_true=y_true, y_pred=y_pred, **kwargs)
    return metric


def recall(y_true, y_pred, **kwargs) -> float:
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
