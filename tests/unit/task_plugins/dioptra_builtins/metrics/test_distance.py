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
            {"name": "a", "func": "l_inf_norm"},
            {"name": "b", "func": "l_1_norm"},
            {"name": "c", "func": "l_2_norm"},
            {"name": "d", "func": "paired_cosine_similarities"},
            {"name": "e", "func": "paired_euclidean_distances"},
            {"name": "f", "func": "paired_manhattan_distances"},
            {"name": "g", "func": "paired_wasserstein_distances"},
        ],
        [{"name": "a", "func": "l_inf_norm"}, {"name": "b", "func": "l_1_norm"}],
        [{"name": "c", "func": "l_1_norm"}, {"name": "d", "func": "l_inf_norm"}],
        [{"name": "e", "func": "paired_wasserstein_distances"}],
    ],
)
@pytest.mark.parametrize(
    ("y_true", "y_pred"),
    [
        ([[1, 2, 3], [3, 4, 5]], [[-2, 4, 5], [-9, 0, 1]]),
        ([[1, 2], [3, 4], [4, 5]], [[-2, 4], [5, -9], [0, 1]]),
        ([1, 2, 3, 4, 5, 6], [-2, 4, 5, -9, 0, 1]),
        ([10], [1]),
    ],
)
def test_get_distance_metric_list(request_, y_true, y_pred) -> None:
    from dioptra_builtins.metrics.distance import get_distance_metric_list

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    result: list = get_distance_metric_list(request_)
    for res in result:
        assert isinstance(res[0], str)
        dists = res[1](y_true, y_pred)
        assert all([isinstance(dist, float) for dist in dists])


@pytest.mark.parametrize(
    "func",
    [
        "l_inf_norm",
        "l_1_norm",
        "l_2_norm",
        "paired_cosine_similarities",
        "paired_euclidean_distances",
        "paired_manhattan_distances",
        "paired_wasserstein_distances",
    ],
)
@pytest.mark.parametrize(
    ("y_true", "y_pred"),
    [
        ([[1, 2, 3], [3, 4, 5]], [[-2, 4, 5], [-9, 0, 1]]),
        ([[1, 2], [3, 4], [4, 5]], [[-2, 4], [5, -9], [0, 1]]),
        ([1, 2, 3, 4, 5, 6], [-2, 4, 5, -9, 0, 1]),
        ([10], [1]),
    ],
)
def test_get_distance_metric(func, y_true, y_pred) -> None:
    from dioptra_builtins.metrics.distance import get_distance_metric

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    metric = get_distance_metric(func)
    results = metric(y_true, y_pred)
    assert all([isinstance(res, float) for res in results])


@pytest.mark.parametrize(
    ("y_true", "y_pred", "expected"),
    [
        ([[1, 2, 3], [3, 4, 5]], [[-2, 4, 5], [-9, 0, 1]], [3.0, 12.0]),
        ([[1, 2], [3, 4], [4, 5]], [[-2, 4], [5, -9], [0, 1]], [3.0, 13.0, 4.0]),
        ([1, 2, 3, 4, 5, 6], [-2, 4, 5, -9, 0, 1], [3.0, 2.0, 2.0, 13.0, 5.0, 5.0]),
        ([10], [1], [9.0]),
    ],
)
def test_l_inf_norm(y_true, y_pred, expected) -> None:
    from dioptra_builtins.metrics.distance import l_inf_norm

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    expected = np.array(expected)
    result: np.ndarray = l_inf_norm(y_true, y_pred)

    assert all([isinstance(res, float) for res in result])
    assert np.allclose(expected, result)


@pytest.mark.parametrize(
    ("y_true", "y_pred", "expected"),
    [
        ([[1, 2, 3], [3, 4, 5]], [[-2, 4, 5], [-9, 0, 1]], [7.0, 20.0]),
        ([[1, 2], [3, 4], [4, 5]], [[-2, 4], [5, -9], [0, 1]], [5.0, 15.0, 8.0]),
        ([1, 2, 3, 4, 5, 6], [-2, 4, 5, -9, 0, 1], [3.0, 2.0, 2.0, 13.0, 5.0, 5.0]),
        ([10], [1], [9.0]),
    ],
)
def test_l_1_norm(y_true, y_pred, expected) -> None:
    from dioptra_builtins.metrics.distance import l_1_norm

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    expected = np.array(expected)

    result: np.ndarray = l_1_norm(y_true, y_pred)

    assert all([isinstance(res, float) for res in result])
    assert np.allclose(expected, result)


@pytest.mark.parametrize(
    ("y_true", "y_pred", "expected"),
    [
        ([[1, 2, 3], [3, 4, 5]], [[-2, 4, 5], [-9, 0, 1]], [4.123105625, 13.2664991]),
        (
            [[1, 2], [3, 4], [4, 5]],
            [[-2, 4], [5, -9], [0, 1]],
            [3.605551275, 13.152946437, 5.656854249],
        ),
        ([1, 2, 3, 4, 5, 6], [-2, 4, 5, -9, 0, 1], [3.0, 2.0, 2.0, 13.0, 5.0, 5.0]),
        ([10], [1], [9.0]),
    ],
)
def test_l_2_norm(y_true, y_pred, expected) -> None:
    from dioptra_builtins.metrics.distance import l_2_norm

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    expected = np.array(expected)

    result: np.ndarray = l_2_norm(y_true, y_pred)

    assert all([isinstance(res, float) for res in result])
    assert np.allclose(expected, result)


@pytest.mark.parametrize(
    ("y_true", "y_pred", "expected"),
    [
        (
            [[1, 2, 3], [3, 4, 5]],
            [[-2, 4, 5], [-9, 0, 1]],
            [0.8366600265340757, -0.3435822761549333],
        ),
        (
            [[1, 2], [3, 4], [4, 5]],
            [[-2, 4], [5, -9], [0, 1]],
            [0.6, -0.40794006219005097, 0.7808688094430304],
        ),
        ([1, 2, 3, 4, 5, 6], [-2, 4, 5, -9, 0, 1], [-1.0, 1.0, 1.0, -1.0, np.nan, 1.0]),
        ([10], [1], [1.0]),
    ],
)
def test_paired_cosine_similarities(y_true, y_pred, expected) -> None:
    from dioptra_builtins.metrics.distance import (
        _flatten_batch,
        _normalize_batch,
        paired_cosine_similarities,
    )

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    expected = np.array(expected)

    result: np.ndarray = paired_cosine_similarities(y_true, y_pred)

    assert all([isinstance(res, float) for res in result])
    assert np.allclose(expected, result, equal_nan=True)


@pytest.mark.parametrize(
    ("y_true", "y_pred", "expected"),
    [
        (
            [[1, 2, 3], [3, 4, 5]],
            [[-2, 4, 5], [-9, 0, 1]],
            [4.123105625617661, 13.2664991614216],
        ),
        (
            [[1, 2], [3, 4], [4, 5]],
            [[-2, 4], [5, -9], [0, 1]],
            [3.605551275463989, 13.152946437965905, 5.656854249492381],
        ),
        ([1, 2, 3, 4, 5, 6], [-2, 4, 5, -9, 0, 1], [3.0, 2.0, 2.0, 13.0, 5.0, 5.0]),
        ([10], [1], [9.0]),
    ],
)
def test_paired_euclidean_distances(y_true, y_pred, expected) -> None:
    from dioptra_builtins.metrics.distance import (
        _flatten_batch,
        paired_euclidean_distances,
    )

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    expected = np.array(expected)
    result: np.ndarray = paired_euclidean_distances(y_true, y_pred)

    assert all([isinstance(res, float) for res in result])
    assert np.allclose(expected, result)


@pytest.mark.parametrize(
    ("y_true", "y_pred", "expected"),
    [
        ([[1, 2, 3], [3, 4, 5]], [[-2, 4, 5], [-9, 0, 1]], [7.0, 20.0]),
        ([[1, 2], [3, 4], [4, 5]], [[-2, 4], [5, -9], [0, 1]], [5.0, 15.0, 8.0]),
        ([1, 2, 3, 4, 5, 6], [-2, 4, 5, -9, 0, 1], [3.0, 2.0, 2.0, 13.0, 5.0, 5.0]),
        ([10], [1], [9.0]),
    ],
)
def test_paired_manhattan_distances(y_true, y_pred, expected) -> None:
    from dioptra_builtins.metrics.distance import (
        _flatten_batch,
        paired_manhattan_distances,
    )

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    expected = np.array(expected)
    result: np.ndarray = paired_manhattan_distances(y_true, y_pred)

    assert all([isinstance(res, float) for res in result])
    assert np.allclose(expected, result)


@pytest.mark.parametrize(
    ("y_true", "y_pred", "expected"),
    [
        ([[1, 2, 3], [3, 4, 5]], [[-2, 4, 5], [-9, 0, 1]], [2.33333333, 6.6666666]),
        ([[1, 2], [3, 4], [4, 5]], [[-2, 4], [5, -9], [0, 1]], [2.5, 6.5, 4.0]),
        ([1, 2, 3, 4, 5, 6], [-2, 4, 5, -9, 0, 1], [3.0, 2.0, 2.0, 13.0, 5.0, 5.0]),
        ([10], [1], [9.0]),
    ],
)
def test_paired_wasserstein_distances(y_true, y_pred, expected) -> None:
    from dioptra_builtins.metrics.distance import (
        _flatten_batch,
        paired_wasserstein_distances,
    )

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    expected = np.array(expected)
    result: np.ndarray = paired_wasserstein_distances(y_true, y_pred)

    assert all([isinstance(res, float) for res in result])
    assert np.allclose(expected, result)


@pytest.mark.parametrize(
    "X",
    [
        [[[1, 2, 3], [3, 4, 5]], [[-2, 4, 5], [-9, 0, 1]]],
        [[[1, 2], [3, 4], [4, 5]], [[-2, 4], [5, -9], [0, 1]]],
        [[1, 2, 3, 4, 5, 6], [-2, 4, 5, -9, 0, 1]],
        [[10], [1]],
    ],
)
def test__flatten_batch(X) -> None:
    from dioptra_builtins.metrics.distance import _flatten_batch

    X = np.array(X)

    result: np.ndarray = _flatten_batch(X)
    expected: np.ndarray = X.reshape(X.shape[0], int(np.prod(X.shape[1:])))

    assert result.shape == expected.shape
    assert np.allclose(expected, result)


@pytest.mark.parametrize(
    ("y_true", "y_pred", "order", "expected"),
    [
        ([[1, 2, 3], [3, 4, 5]], [[-2, 4, 5], [-9, 0, 1]], 1, [7.0, 20.0]),
        (
            [[1, 2], [3, 4], [4, 5]],
            [[-2, 4], [5, -9], [0, 1]],
            2,
            [3.605551275463989, 13.152946437965905, 5.656854249492381],
        ),
        (
            [[1, 2], [3, 4], [4, 5]],
            [[-2, 4], [5, -9], [0, 1]],
            np.inf,
            [3.0, 13.0, 4.0],
        ),
        ([1, 2, 3, 4, 5, 6], [-2, 4, 5, -9, 0, 1], 5, [3.0, 2.0, 2.0, 13.0, 5.0, 5.0]),
        ([1, 2, 3, 4, 5, 6], [-2, 4, 5, -9, 0, 1], 1, [3.0, 2.0, 2.0, 13.0, 5.0, 5.0]),
        (
            [1, 2, 3, 4, 5, 6],
            [-2, 4, 5, -9, 0, 1],
            np.inf,
            [3.0, 2.0, 2.0, 13.0, 5.0, 5.0],
        ),
        ([10], [1], 20, [9.0]),
    ],
)
def test__matrix_difference_l_norm(y_true, y_pred, order, expected) -> None:
    from dioptra_builtins.metrics.distance import (
        _flatten_batch,
        _matrix_difference_l_norm,
    )

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    expected = np.array(expected)
    result: np.ndarray = _matrix_difference_l_norm(y_true, y_pred, order)

    assert np.allclose(expected, result)


@pytest.mark.parametrize(
    "X",
    [
        [[[1, 2, 3], [3, 4, 5]], [[-2, 4, 5], [-9, 0, 1]]],
        [[[1, 2], [3, 4], [4, 5]], [[-2, 4], [5, -9], [0, 1]]],
        [[1, 2, 3, 4, 5, 6], [-2, 4, 5, -9, 0, 1]],
        [[10], [1]],
    ],
)
@pytest.mark.parametrize(
    "order",
    [1, 2, 3, 4, 5, 6, 8, 20, np.inf],
)
def test__normalize_batch(X, order) -> None:
    from dioptra_builtins.metrics.distance import _flatten_batch, _normalize_batch

    X = _flatten_batch(np.array(X)).astype(float)
    result: np.ndarray = _normalize_batch(X, order)

    norm = np.linalg.norm(X, axis=1, ord=order)
    norm = norm.reshape((norm.shape[0], 1))
    unnormed = result * norm
    assert np.allclose(unnormed, X)
