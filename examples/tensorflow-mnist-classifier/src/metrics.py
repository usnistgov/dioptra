import warnings

warnings.filterwarnings("ignore")

import numpy as np
from scipy.stats import wasserstein_distance
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.metrics.pairwise import paired_distances


def accuracy(y_true, y_pred, **kwargs) -> float:
    metric: float = accuracy_score(y_true=y_true, y_pred=y_pred, **kwargs)
    return metric


def auc(y_true, y_pred, **kwargs) -> float:
    metric: float = roc_auc_score(y_true=y_true, y_score=y_pred, **kwargs)
    return metric


def f1(y_true, y_pred, **kwargs) -> float:
    metric: float = f1_score(y_true=y_true, y_pred=y_pred, **kwargs)
    return metric


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


def precision(y_true, y_pred, **kwargs) -> float:
    metric: float = precision_score(y_true=y_true, y_pred=y_pred, **kwargs)
    return metric


def recall(y_true, y_pred, **kwargs) -> float:
    metric: float = recall_score(y_true=y_true, y_pred=y_pred, **kwargs)
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
