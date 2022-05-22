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

def membership_guess_accuracy(y_true, y_pred, **kwargs):
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
