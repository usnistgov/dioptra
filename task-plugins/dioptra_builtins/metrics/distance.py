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
"""A task plugin module for getting functions from a distance metric registry.

.. |Linf| replace:: L\\ :sub:`∞`
.. |L1| replace:: L\\ :sub:`1`
.. |L2| replace:: L\\ :sub:`2`
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import structlog
from scipy.stats import wasserstein_distance
from sklearn.metrics.pairwise import paired_distances
from structlog.stdlib import BoundLogger

from dioptra import pyplugs

from .exceptions import UnknownDistanceMetricError

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pyplugs.register
def get_distance_metric_list(
    request: List[Dict[str, str]]
) -> List[Tuple[str, Callable[..., np.ndarray]]]:
    """Gets multiple distance metric functions from the registry.

    The following metrics are available in the registry,

    - `l_inf_norm`
    - `l_1_norm`
    - `l_2_norm`
    - `paired_cosine_similarities`
    - `paired_euclidean_distances`
    - `paired_manhattan_distances`
    - `paired_wasserstein_distances`

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
    distance_metrics_list: List[Tuple[str, Callable[..., np.ndarray]]] = []

    for metric in request:
        metric_callable: Optional[Callable[..., np.ndarray]] = (
            DISTANCE_METRICS_REGISTRY.get(metric["func"])
        )

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
    """Gets a distance metric function from the registry.

    The following metrics are available in the registry,

    - `l_inf_norm`
    - `l_1_norm`
    - `l_2_norm`
    - `paired_cosine_similarities`
    - `paired_euclidean_distances`
    - `paired_manhattan_distances`
    - `paired_wasserstein_distances`

    Args:
        func: A string that identifies the distance metric to return from the registry.
            The string must match one of the names of the metrics in the registry.

    Returns:
        A callable distance metric function.
    """
    metric_callable: Optional[Callable[..., np.ndarray]] = (
        DISTANCE_METRICS_REGISTRY.get(func)
    )

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
    """Calculates the |Linf| norm between a batch of two matrices.

    Args:
        y_true: A batch of matrices containing the original or target values.
        y_pred: A batch of matrices containing the perturbed or predicted values.

    Returns:
        A :py:class:`numpy.ndarray` containing a batch of |Linf| norms.
    """
    metric: np.ndarray = _matrix_difference_l_norm(
        y_true=y_true, y_pred=y_pred, order=np.inf
    )
    return metric


def l_1_norm(y_true, y_pred) -> np.ndarray:
    """Calculates the |L1| norm between a batch of two matrices.

    Args:
        y_true: A batch of matrices containing the original or target values.
        y_pred: A batch of matrices containing the perturbed or predicted values.

    Returns:
        A :py:class:`numpy.ndarray` containing a batch of |L1| norms.
    """
    metric: np.ndarray = _matrix_difference_l_norm(
        y_true=y_true, y_pred=y_pred, order=1
    )
    return metric


def l_2_norm(y_true, y_pred) -> np.ndarray:
    """Calculates the |L2| norm between a batch of two matrices.

    Args:
        y_true: A batch of matrices containing the original or target values.
        y_pred: A batch of matrices containing the perturbed or predicted values.

    Returns:
        A :py:class:`numpy.ndarray` containing a batch of |L2| norms.
    """
    metric: np.ndarray = _matrix_difference_l_norm(
        y_true=y_true, y_pred=y_pred, order=2
    )
    return metric


def paired_cosine_similarities(y_true, y_pred) -> np.ndarray:
    """Calculates the cosine similarity between a batch of two matrices.

    Args:
        y_true: A batch of matrices containing the original or target values.
        y_pred: A batch of matrices containing the perturbed or predicted values.

    Returns:
        A :py:class:`numpy.ndarray` containing a batch of cosine similarities.
    """
    y_true_normalized: np.ndarray = _normalize_batch(_flatten_batch(y_true), order=2)
    y_pred_normalized: np.ndarray = _normalize_batch(_flatten_batch(y_pred), order=2)
    metric: np.ndarray = np.sum(y_true_normalized * y_pred_normalized, axis=1)
    return metric


def paired_euclidean_distances(y_true, y_pred) -> np.ndarray:
    """Calculates the Euclidean distance between a batch of two matrices.

    The Euclidean distance is equivalent to the |L2| norm.

    Args:
        y_true: A batch of matrices containing the original or target values.
        y_pred: A batch of matrices containing the perturbed or predicted values.

    Returns:
        A :py:class:`numpy.ndarray` containing a batch of euclidean distances.
    """
    metric: np.ndarray = l_2_norm(y_true=y_true, y_pred=y_pred)
    return metric


def paired_manhattan_distances(y_true, y_pred) -> np.ndarray:
    """Calculates the Manhattan distance between a batch of two matrices.

    The Manhattan distance is equivalent to the |L1| norm.

    Args:
        y_true: A batch of matrices containing the original or target values.
        y_pred: A batch of matrices containing the perturbed or predicted values.

    Returns:
        A :py:class:`numpy.ndarray` containing a batch of Manhattan distances.
    """
    metric: np.ndarray = l_1_norm(y_true=y_true, y_pred=y_pred)
    return metric


def paired_wasserstein_distances(y_true, y_pred, **kwargs) -> np.ndarray:
    """Calculates the Wasserstein distance between a batch of two matrices.

    Args:
        y_true: A batch of matrices containing the original or target values.
        y_pred: A batch of matrices containing the perturbed or predicted values.

    Returns:
        A :py:class:`numpy.ndarray` containing a batch of Wasserstein distances.

    See Also:
        - :py:func:`scipy.stats.wasserstein_distance`
    """

    def wrapped_metric(X, Y):
        return wasserstein_distance(u_values=X, v_values=Y, **kwargs)

    metric: np.ndarray = paired_distances(
        X=_flatten_batch(y_true), Y=_flatten_batch(y_pred), metric=wrapped_metric
    )
    return metric


def _flatten_batch(X: np.ndarray) -> np.ndarray:
    """Flattens each of the matrices in a batch into a one-dimensional array.

    Args:
        X: A batch of matrices.

    Returns:
        A :py:class:`numpy.ndarray` containing a batch of one-dimensional arrays.
    """
    num_samples: int = X.shape[0]
    num_matrix_elements: int = int(np.prod(X.shape[1:]))
    return X.reshape((num_samples, num_matrix_elements))


def _matrix_difference_l_norm(y_true, y_pred, order) -> np.ndarray:
    """Calculates a batch of norms of the difference between two matrices.

    Args:
        y_true: A batch of matrices containing the original or target values.
        y_pred: A batch of matrices containing the perturbed or predicted values.
        order: The order of the norm, see :py:func:`numpy.linalg.norm` for the full list
            of norms that can be calculated.

    Returns:
        A :py:class:`numpy.ndarray` containing a batch of norms.

    See Also:
        - :py:func:`numpy.linalg.norm`
    """
    y_diff: np.ndarray = _flatten_batch(y_true - y_pred)
    y_diff_l_norm: np.ndarray = np.linalg.norm(y_diff, axis=1, ord=order)
    return y_diff_l_norm


def _normalize_batch(X: np.ndarray, order: int) -> np.ndarray:
    """Normalizes a batch of matrices by their norms.

    Args:
        X: A batch of matrices to be normalized.
        order: The order of the norm used for normalization, see
            :py:func:`numpy.linalg.norm` for the full list of available norms.

    Returns:
        A :py:class:`numpy.ndarray` containing a batch of normalized matrices.

    See Also:
        - :py:func:`numpy.linalg.norm`
    """
    X_l_norm: np.ndarray = np.linalg.norm(X, axis=1, ord=order)
    num_samples: int = X_l_norm.shape[0]
    normalized_batch: np.ndarray = X / X_l_norm.reshape((num_samples, 1))
    return normalized_batch


DISTANCE_METRICS_REGISTRY: Dict[str, Callable[..., Any]] = dict(
    l_inf_norm=l_inf_norm,
    l_1_norm=l_1_norm,
    l_2_norm=l_2_norm,
    paired_cosine_similarities=paired_cosine_similarities,
    paired_euclidean_distances=paired_euclidean_distances,
    paired_manhattan_distances=paired_manhattan_distances,
    paired_wasserstein_distances=paired_wasserstein_distances,
)
