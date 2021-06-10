# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
import warnings

warnings.filterwarnings("ignore")

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    roc_auc_score,
    precision_score,
    recall_score,
)
from sklearn.metrics.pairwise import paired_distances
from scipy.stats import wasserstein_distance


def accuracy(y_true, y_pred, **kwargs):
    return accuracy_score(y_true=y_true, y_pred=y_pred, **kwargs)


def auc(y_true, y_pred, **kwargs):
    return roc_auc_score(y_true=y_true, y_score=y_pred, **kwargs)


def f1(y_true, y_pred, **kwargs):
    return f1_score(y_true=y_true, y_pred=y_pred, **kwargs)


def l_inf_norm(y_true, y_pred):
    return _matrix_difference_l_norm(y_true=y_true, y_pred=y_pred, order=np.inf)


def l_1_norm(y_true, y_pred):
    return _matrix_difference_l_norm(y_true=y_true, y_pred=y_pred, order=1)


def l_2_norm(y_true, y_pred):
    return _matrix_difference_l_norm(y_true=y_true, y_pred=y_pred, order=2)


def paired_cosine_similarities(y_true, y_pred):
    y_true_normalized = _normalize_batch(_flatten_batch(y_true), order=2)
    y_pred_normalized = _normalize_batch(_flatten_batch(y_pred), order=2)
    return np.sum(y_true_normalized * y_pred_normalized, axis=1)


def paired_euclidean_distances(y_true, y_pred):
    return l_2_norm(y_true=y_true, y_pred=y_pred)


def paired_manhattan_distances(y_true, y_pred):
    return l_1_norm(y_true=y_true, y_pred=y_pred)


def paired_wasserstein_distances(y_true, y_pred, **kwargs):
    def wrapped_metric(X, Y):
        return wasserstein_distance(u_values=X, v_values=Y, **kwargs)

    return paired_distances(
        X=_flatten_batch(y_true), Y=_flatten_batch(y_pred), metric=wrapped_metric
    )


def precision(y_true, y_pred, **kwargs):
    return precision_score(y_true=y_true, y_pred=y_pred, **kwargs)


def recall(y_true, y_pred, **kwargs):
    return recall_score(y_true=y_true, y_pred=y_pred, **kwargs)


def _flatten_batch(X):
    num_samples = X.shape[0]
    num_matrix_elements = np.prod(X.shape[1:])
    return X.reshape((num_samples, num_matrix_elements))


def _matrix_difference_l_norm(y_true, y_pred, order):
    y_diff = _flatten_batch(y_true - y_pred)
    y_diff_l_norm = np.linalg.norm(y_diff, axis=1, ord=order)
    return y_diff_l_norm


def _normalize_batch(X, order):
    X_l_norm = np.linalg.norm(X, axis=1, ord=order)
    num_samples = X_l_norm.shape[0]

    return X / X_l_norm.reshape((num_samples, 1))
