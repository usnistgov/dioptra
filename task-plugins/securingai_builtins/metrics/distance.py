from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import structlog
from scipy.stats import wasserstein_distance
from sklearn.metrics.pairwise import paired_distances
from structlog.stdlib import BoundLogger

from mitre.securingai import pyplugs

from .exceptions import UnknownDistanceMetricError

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pyplugs.register
def get_distance_metric_list(
    request: List[Dict[str, str]]
) -> List[Tuple[str, Callable[..., np.ndarray]]]:
    distance_metrics_list: List[Tuple[str, Callable[..., np.ndarray]]] = []

    for metric in request:
        metric_callable: Optional[
            Callable[..., np.ndarray]
        ] = DISTANCE_METRICS_REGISTRY.get(metric["func"])

        if metric_callable is not None:
            distance_metrics_list.append((metric["name"], metric_callable))

        else:
            LOGGER.warn(
                "Distance metric not in registry, skipping...",
                name=metric["name"],
                func=metric["func"],
            )

    return distance_metrics_list


@pyplugs.register
def get_distance_metric(func: str) -> Callable[..., np.ndarray]:
    metric_callable: Optional[
        Callable[..., np.ndarray]
    ] = DISTANCE_METRICS_REGISTRY.get(func)

    if metric_callable is None:
        LOGGER.error(
            "Distance metric not in registry",
            func=func,
        )
        raise UnknownDistanceMetricError(
            f"Could not find any distance metric named {func!r} in the metrics "
            "plugin collection. Check spelling and try again."
        )

    return metric_callable


def l_inf_norm(y_true, y_pred) -> np.ndarray:
    metric: np.ndarray = _matrix_difference_l_norm(
        y_true=y_true, y_pred=y_pred, order=np.inf
    )
    return metric


def l_1_norm(y_true, y_pred) -> np.ndarray:
    metric: np.ndarray = _matrix_difference_l_norm(
        y_true=y_true, y_pred=y_pred, order=1
    )
    return metric


def l_2_norm(y_true, y_pred) -> np.ndarray:
    metric: np.ndarray = _matrix_difference_l_norm(
        y_true=y_true, y_pred=y_pred, order=2
    )
    return metric


def paired_cosine_similarities(y_true, y_pred) -> np.ndarray:
    y_true_normalized: np.ndarray = _normalize_batch(_flatten_batch(y_true), order=2)
    y_pred_normalized: np.ndarray = _normalize_batch(_flatten_batch(y_pred), order=2)
    metric: np.ndarray = np.sum(y_true_normalized * y_pred_normalized, axis=1)
    return metric


def paired_euclidean_distances(y_true, y_pred) -> np.ndarray:
    metric: np.ndarray = l_2_norm(y_true=y_true, y_pred=y_pred)
    return metric


def paired_manhattan_distances(y_true, y_pred) -> np.ndarray:
    metric: np.ndarray = l_1_norm(y_true=y_true, y_pred=y_pred)
    return metric


def paired_wasserstein_distances(y_true, y_pred, **kwargs) -> np.ndarray:
    def wrapped_metric(X, Y):
        return wasserstein_distance(u_values=X, v_values=Y, **kwargs)

    metric: np.ndarray = paired_distances(
        X=_flatten_batch(y_true), Y=_flatten_batch(y_pred), metric=wrapped_metric
    )
    return metric


def _flatten_batch(X: np.ndarray) -> np.ndarray:
    num_samples = X.shape[0]
    num_matrix_elements = np.prod(X.shape[1:])
    return X.reshape((num_samples, num_matrix_elements))


def _matrix_difference_l_norm(y_true, y_pred, order) -> np.ndarray:
    y_diff: np.ndarray = _flatten_batch(y_true - y_pred)
    y_diff_l_norm: float = np.linalg.norm(y_diff, axis=1, ord=order)
    return y_diff_l_norm


def _normalize_batch(X: np.ndarray, order: int) -> np.ndarray:
    X_l_norm = np.linalg.norm(X, axis=1, ord=order)
    num_samples = X_l_norm.shape[0]

    return X / X_l_norm.reshape((num_samples, 1))


DISTANCE_METRICS_REGISTRY: Dict[str, Callable[..., Any]] = dict(
    l_inf_norm=l_inf_norm,
    l_1_norm=l_1_norm,
    l_2_norm=l_2_norm,
    paired_cosine_similarities=paired_cosine_similarities,
    paired_euclidean_distances=paired_euclidean_distances,
    paired_manhattan_distances=paired_manhattan_distances,
    paired_wasserstein_distances=paired_wasserstein_distances,
)
