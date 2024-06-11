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

import numpy as np
import pytest


@pytest.mark.parametrize(
    "request_",
    [
        [],
        [
            {"name": "a", "func": "accuracy"},
            {"name": "b", "func": "precision"},
            {"name": "c", "func": "roc_auc"},
            {"name": "d", "func": "categorical_accuracy"},
            {"name": "e", "func": "mcc"},
            {"name": "f", "func": "f1"},
            {"name": "g", "func": "recall"},
        ],
        [{"name": "a", "func": "recall"}, {"name": "b", "func": "f1"}],
        [{"name": "c", "func": "precision"}, {"name": "d", "func": "recall"}],
        [{"name": "e", "func": "accuracy"}],
    ],
)
@pytest.mark.parametrize(
    ("y_true", "y_pred"),
    [
        ([0, 1], [1, 1]),
        ([1, 0, 0], [1, 1, 1]),
        ([1, 0, 0, 0, 1, 1], [0, 1, 1, 1, 0, 0]),
        ([1, 0, 1], [1, 0, 0]),
        ([0, 1, 1, 0, 1, 0, 1], [1, 0, 0, 1, 0, 0, 0]),
    ],
)
def test_get_performance_metric_list(request_, y_true, y_pred) -> None:
    from dioptra_builtins.metrics.performance import get_performance_metric_list

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    result: list = get_performance_metric_list(request_)
    for res in result:
        assert isinstance(res[0], str)
        performance = res[1](y_true, y_pred)
        assert isinstance(performance, float)


@pytest.mark.parametrize(
    "func",
    ["accuracy", "precision", "roc_auc", "categorical_accuracy", "mcc", "f1", "recall"],
)
@pytest.mark.parametrize(
    ("y_true", "y_pred"),
    [
        ([0, 1], [1, 1]),
        ([1, 0, 0], [1, 1, 1]),
        ([1, 0, 0, 0, 1, 1], [0, 1, 1, 1, 0, 0]),
        ([1, 0, 1], [1, 0, 0]),
        ([0, 1, 1, 0, 1, 0, 1], [1, 0, 0, 1, 0, 0, 0]),
    ],
)
def test_get_performance_metric(func, y_true, y_pred) -> None:
    from dioptra_builtins.metrics.performance import get_performance_metric

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    metric = get_performance_metric(func)
    result = metric(y_true, y_pred)
    assert isinstance(result, float)


@pytest.mark.parametrize(
    ("y_true", "y_pred", "weights", "normalize", "expected"),
    [
        ([0, 1], [1, 1], None, True, 0.5),
        ([1, 2, 4], [4, 1, 1], [0.3, 0.6, 0.1], False, 0.0),
        ([1, 2, 3, 6, 5, 6], [6, 6, 6, 6, 6, 6], None, True, 0.33333333),
        (
            [9, 9, 9, 9, 9, 2],
            [9, 9, 9, 9, 9, 9],
            [0.2, 0.1, 0.3, 0.1, 0.1, 0.2],
            False,
            0.8,
        ),
        ([2, 2, 3, 4, 5], [2, 2, 5, 5, 5], [0.2, 0.2, 0.2, 0.2, 0.2], True, 0.6),
    ],
)
def test_accuracy(y_true, y_pred, weights, normalize, expected) -> None:
    from dioptra_builtins.metrics.performance import accuracy

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    expected = np.array(expected)
    kwargs = {"normalize": normalize, "sample_weight": weights}
    result: float = accuracy(y_true, y_pred, **kwargs)
    assert np.isclose(result, expected)


@pytest.mark.parametrize(
    ("y_true", "y_pred", "weights", "average", "multiclass", "expected"),
    [
        (
            [2, 1, 3],
            [[0.3, 0.5, 0.2], [0.4, 0.5, 0.1], [0.3, 0.3, 0.4]],
            None,
            "macro",
            "ovr",
            0.9166666,
        ),
        (
            [2, 1, 3, 1, 1],
            [
                [0.3, 0.5, 0.2],
                [0.4, 0.5, 0.1],
                [0.3, 0.3, 0.4],
                [0.9, 0.05, 0.05],
                [0.1, 0.1, 0.8],
            ],
            None,
            "macro",
            "ovo",
            0.8055555555555557,
        ),
        (
            [2, 1, 3, 1, 1],
            [
                [0.3, 0.5, 0.2],
                [0.4, 0.5, 0.1],
                [0.3, 0.3, 0.4],
                [0.9, 0.05, 0.05],
                [0.1, 0.1, 0.8],
            ],
            [0.2, 0.3, 0.3, 0.1, 0.1],
            "macro",
            "ovr",
            0.8232142857142858,
        ),
        (
            [2, 1, 3, 1, 1],
            [
                [0.3, 0.5, 0.2],
                [0.4, 0.5, 0.1],
                [0.3, 0.3, 0.4],
                [0.9, 0.05, 0.05],
                [0.1, 0.1, 0.8],
            ],
            None,
            "weighted",
            "ovo",
            0.7666666666666668,
        ),
        (
            [2, 1, 3, 1, 1],
            [
                [0.1, 0.5, 0.4],
                [0.4, 0.5, 0.1],
                [0, 0.9, 0.1],
                [0.9, 0.05, 0.05],
                [0.1, 0.1, 0.8],
            ],
            None,
            "weighted",
            "ovr",
            0.75,
        ),
        ([0, 1, 0, 1, 1], [1, 0, 1, 0, 1], None, "micro", "ovo", 0.1666666),
        ([0, 1, 0, 1, 0], [1, 0, 1, 1, 1], None, "macro", "ovr", 0.25),
        ([1, 1, 1, 1, 0], [1, 1, 1, 1, 0], None, "weighted", "ovr", 1.0),
    ],
)
def test_roc_auc(y_true, y_pred, weights, average, multiclass, expected) -> None:
    from dioptra_builtins.metrics.performance import roc_auc

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    kwargs = {"average": average, "multi_class": multiclass, "sample_weight": weights}
    result: float = roc_auc(y_true, y_pred, **kwargs)
    assert np.isclose(result, expected)


@pytest.mark.parametrize(
    ("y_true", "y_pred", "expected"),
    [
        ([0, 1], [1, 1], 0.5),
        ([1, 2, 4], [4, 1, 1], 0.0),
        ([1, 2, 3, 6, 5, 6], [6, 6, 6, 6, 6, 6], 0.33333333),
        ([9, 9, 9, 9, 9, 2], [9, 9, 9, 9, 9, 9], 0.83333333),
        ([2, 2, 3, 4, 5], [2, 2, 5, 5, 5], 0.6),
    ],
)
def test_categorical_accuracy(y_true, y_pred, expected) -> None:
    from dioptra_builtins.metrics.performance import categorical_accuracy

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    result: float = categorical_accuracy(y_true, y_pred)
    assert np.isclose(expected, result)


@pytest.mark.parametrize(
    ("y_true", "y_pred", "weights", "expected"),
    [
        ([0, 1], [1, 1], None, 0.0),
        ([1, 2, 4], [4, 1, 1], [0.3, 0.6, 0.1], -0.5039526306789696),
        ([1, 2, 3, 6, 5, 6], [6, 6, 6, 6, 6, 6], None, 0.0),
        ([9, 9, 9, 9, 9, 2], [9, 9, 9, 9, 9, 9], [0.2, 0.1, 0.3, 0.1, 0.1, 0.2], 0.0),
        (
            [2, 2, 3, 4, 5],
            [2, 2, 5, 5, 5],
            [0.2, 0.2, 0.2, 0.2, 0.2],
            0.5443310539518176,
        ),
    ],
)
def test_mcc(y_true, y_pred, weights, expected) -> None:
    from dioptra_builtins.metrics.performance import mcc

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    kwargs = {"sample_weight": weights}
    result: float = mcc(y_true, y_pred, **kwargs)
    assert np.isclose(expected, result)


@pytest.mark.parametrize(
    ("y_true", "y_pred", "weights", "average", "expected"),
    [
        ([0, 1], [1, 1], None, "micro", 0.5),
        ([1, 2, 4], [4, 1, 1], [0.3, 0.6, 0.1], "macro", 0.0),
        ([1, 2, 3, 6, 5, 6], [6, 6, 6, 6, 6, 6], None, "weighted", 0.16666666),
        (
            [9, 9, 9, 9, 9, 2],
            [9, 9, 9, 9, 9, 9],
            [0.2, 0.1, 0.3, 0.1, 0.1, 0.2],
            "micro",
            0.8,
        ),
        ([2, 2, 3, 4, 5], [2, 2, 5, 5, 5], [0.2, 0.2, 0.2, 0.2, 0.2], "weighted", 0.5),
    ],
)
def test_f1(y_true, y_pred, weights, average, expected) -> None:
    from dioptra_builtins.metrics.performance import f1

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    kwargs = {"average": average, "sample_weight": weights}
    result: float = f1(y_true, y_pred, **kwargs)
    assert np.isclose(result, expected)


@pytest.mark.parametrize(
    ("y_true", "y_pred", "weights", "average", "expected"),
    [
        ([0, 1], [1, 1], None, "micro", 0.5),
        ([1, 2, 4], [4, 1, 1], [0.3, 0.6, 0.1], "macro", 0.0),
        ([1, 2, 3, 6, 5, 6], [6, 6, 6, 6, 6, 6], None, "weighted", 0.1111111),
        (
            [9, 9, 9, 9, 9, 2],
            [9, 9, 9, 9, 9, 9],
            [0.2, 0.1, 0.3, 0.1, 0.1, 0.2],
            "micro",
            0.8,
        ),
        (
            [2, 2, 3, 4, 5],
            [2, 2, 5, 5, 5],
            [0.2, 0.2, 0.2, 0.2, 0.2],
            "weighted",
            0.466666666,
        ),
    ],
)
def test_precision(y_true, y_pred, weights, average, expected) -> None:
    from dioptra_builtins.metrics.performance import precision

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    kwargs = {"average": average, "sample_weight": weights}
    result: float = precision(y_true, y_pred, **kwargs)
    assert np.isclose(result, expected)


@pytest.mark.parametrize(
    ("y_true", "y_pred", "weights", "average", "expected"),
    [
        ([0, 1], [1, 1], None, "micro", 0.5),
        ([1, 2, 4], [4, 1, 1], [0.3, 0.6, 0.1], "macro", 0.0),
        ([1, 2, 3, 6, 5, 6], [6, 6, 6, 6, 6, 6], None, "weighted", 0.3333333),
        (
            [9, 9, 9, 9, 9, 2],
            [9, 9, 9, 9, 9, 9],
            [0.2, 0.1, 0.3, 0.1, 0.1, 0.2],
            "micro",
            0.8,
        ),
        ([2, 2, 3, 4, 5], [2, 2, 5, 5, 5], [0.2, 0.2, 0.2, 0.2, 0.2], "weighted", 0.6),
    ],
)
def test_recall(y_true, y_pred, weights, average, expected) -> None:
    from dioptra_builtins.metrics.performance import recall

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    kwargs = {"average": average, "sample_weight": weights}
    result: float = recall(y_true, y_pred, **kwargs)
    assert np.isclose(result, expected)
