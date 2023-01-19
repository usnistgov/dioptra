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
from dioptra import pyplugs 
from sklearn.metrics import accuracy_score 
from sklearn.metrics import f1_score 
from sklearn.metrics import matthews_corrcoef 
from sklearn.metrics import precision_score 
from sklearn.metrics import recall_score 
from sklearn.metrics import roc_auc_score 
from structlog.stdlib import BoundLogger 
from typing import Any 
from typing import Callable 
from typing import Dict 
from typing import List 
from typing import Optional 
from typing import Tuple 
import numpy as np
import pytest
import structlog 

@pytest.mark.parametrize(
    "request_",
    [
        [],
        [{"name":"a", "func":"accuracy"},{"name":"b", "func":"precision"},
        {"name":"c", "func":"roc_auc"},{"name":"d", "func":"categorical_accuracy"},
        {"name":"e", "func":"mcc"},{"name":"f", "func":"f1"},
        {"name":"g", "func":"recall"}],
        [{"name":"a", "func":"recall"},{"name":"b", "func":"f1"}],
        [{"name":"c", "func":"precision"},{"name":"d", "func":"recall"}],
        [{"name":"e", "func":"accuracy"}],
    ],
)
@pytest.mark.parametrize(
    ("y_true", "y_pred"),
    [
        ([0,1],[1,1]),
        ([1,0,0],[1,1,1]),
        ([1,0,0,0,1,1],[0,1,1,1,0,0]),
        ([1,0,1],[1,0,0]),
        ([0,1,1,0,1,0,1],[1,0,0,1,0,0,0])
    ]
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
    [
        "accuracy", 
        "precision", 
        "roc_auc", 
        "categorical_accuracy", 
        "mcc", 
        "f1", 
        "recall"
    ],
)
@pytest.mark.parametrize(
    ("y_true", "y_pred"),
    [
        ([0,1],[1,1]),
        ([1,0,0],[1,1,1]),
        ([1,0,0,0,1,1],[0,1,1,1,0,0]),
        ([1,0,1],[1,0,0]),
        ([0,1,1,0,1,0,1],[1,0,0,1,0,0,0])
    ]
)
def test_get_performance_metric(func, y_true, y_pred) -> None:
    from dioptra_builtins.metrics.performance import get_performance_metric
    
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    metric = get_performance_metric(func)
    result = metric(y_true,y_pred)
    assert isinstance(result, float)

@pytest.mark.parametrize(
    ("y_true", "y_pred", "weights"),
    [
        ([0,1],[1,1],None),
        ([1,2,4],[4,1,1],[0.3,0.7,0]),
        ([1,2,3,4,5,6],[6,4,4,3,2,2],None),
        ([9,9,9,9,9,2],[9,9,9,9,9,9],[0.2,0.1,0.3,0.1,0.1,0.2]),
        ([2,2,3,4,5],[5,5,5,5,4],[0.2,0.2,0.2,0.2,0.2])
    ]
)
@pytest.mark.parametrize(
    "normalize",
    [
        True, False
    ]
)

def test_accuracy(y_true, y_pred, weights, normalize) -> None:
    from dioptra_builtins.metrics.performance import accuracy
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    kwargs = {"normalize":normalize, "sample_weight": weights}
    result: float = accuracy(y_true, y_pred, **kwargs)
    assert result == accuracy_score(y_true, y_pred, **kwargs)

@pytest.mark.parametrize(
    ("y_true", "y_pred", "weights"),
    [
        ([2,1,3],[[0.3,0.5,0.2],[0.4,0.5,0.1],[0.3,0.3,0.4]],None),
        ([2,1,3,1,1],[[0.3,0.5,0.2],[0.4,0.5,0.1],[0.3,0.3,0.4],[0.9,0.05,0.05],[0.1,0.1,0.8]],None),
    ]
)
@pytest.mark.parametrize(
    ("average", "multiclass"),
    [
        ("micro","ovr"),
        ("macro", "ovo"),
        ("macro","ovr"),
        ("weighted","ovo"),
        ("weighted","ovr"),
    ]
)
def test_roc_auc(y_true, y_pred, weights, average, multiclass) -> None:
    from dioptra_builtins.metrics.performance import roc_auc
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    kwargs = {"average":average, "multi_class":multiclass, "sample_weight": weights}
    result: float = roc_auc(y_true, y_pred, **kwargs)
    assert result == roc_auc_score(y_true, y_pred, **kwargs)

@pytest.mark.parametrize(
    ("y_true", "y_pred"),
    [
        ([2,1,3],[[0.3,0.5,0.2],[0.4,0.5,0.1],[0.3,0.3,0.4]]),
        ([2,1,3,1,1],[[0.3,0.5,0.2],[0.4,0.5,0.1],[0.3,0.3,0.4],[0.9,0.05,0.05],[0.1,0.1,0.8]]),
    ]
)
def test_categorical_accuracy(y_true, y_pred) -> None:
    from dioptra_builtins.metrics.performance import categorical_accuracy
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    if len(y_true.shape) > 1 and len(y_pred.shape) > 1:
        label_comparison: np.ndarray = np.argmax(y_true, axis=-1) == np.argmax(
            y_pred, axis=-1
        )
    else:
        label_comparison = y_true == y_pred
    metric: float = float(np.mean(label_comparison))    
    assert metric == categorical_accuracy(y_true, y_pred)

@pytest.mark.parametrize(
    ("y_true", "y_pred", "weights"),
    [
        ([0,1],[1,1],None),
        ([1,2,4],[4,1,1],[0.3,0.7,0]),
        ([1,2,3,4,5,6],[6,4,4,3,2,2],None),
        ([9,9,9,9,9,2],[9,9,9,9,9,9],[0.2,0.1,0.3,0.1,0.1,0.2]),
        ([2,2,3,4,5],[5,5,5,5,4],[0.2,0.2,0.2,0.2,0.2])
    ]
)

def test_mcc(y_true, y_pred, weights) -> None:
    from dioptra_builtins.metrics.performance import mcc
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    kwargs = {"sample_weight": weights}
    result: float = mcc(y_true, y_pred, **kwargs)
    assert result == matthews_corrcoef(y_true, y_pred, **kwargs)

@pytest.mark.parametrize(
    ("y_true", "y_pred", "weights"),
    [
        ([0,1],[1,1],None),
        ([1,2,4],[4,1,1],[0.3,0.7,0]),
        ([1,2,3,4,5,6],[6,4,4,3,2,2],None),
        ([9,9,9,9,9,2],[9,9,9,9,9,9],[0.2,0.1,0.3,0.1,0.1,0.2]),
        ([2,2,3,4,5],[5,5,5,5,4],[0.2,0.2,0.2,0.2,0.2])
    ]
)
@pytest.mark.parametrize(
    "average",
    [
        "micro",
        "macro",
        "weighted"
    ]
)
def test_f1(y_true, y_pred, weights, average) -> None:
    from dioptra_builtins.metrics.performance import f1
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    kwargs = {"average":average, "sample_weight": weights}
    result: float = f1(y_true, y_pred, **kwargs)
    assert result == f1_score(y_true, y_pred, **kwargs)


@pytest.mark.parametrize(
    ("y_true", "y_pred", "weights"),
    [
        ([0,1],[1,1],None),
        ([1,2,4],[4,1,1],[0.3,0.7,0]),
        ([1,2,3,4,5,6],[6,4,4,3,2,2],None),
        ([9,9,9,9,9,2],[9,9,9,9,9,9],[0.2,0.1,0.3,0.1,0.1,0.2]),
        ([2,2,3,4,5],[5,5,5,5,4],[0.2,0.2,0.2,0.2,0.2])
    ]
)
@pytest.mark.parametrize(
    "average",
    [
        "micro",
        "macro",
        "weighted"
    ]
)
def test_precision(y_true, y_pred, weights, average) -> None:
    from dioptra_builtins.metrics.performance import precision
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    kwargs = {"average":average, "sample_weight": weights}
    result: float = precision(y_true, y_pred, **kwargs)
    assert result == precision_score(y_true, y_pred, **kwargs)



@pytest.mark.parametrize(
    ("y_true", "y_pred", "weights"),
    [
        ([0,1],[1,1],None),
        ([1,2,4],[4,1,1],[0.3,0.7,0]),
        ([1,2,3,4,5,6],[6,4,4,3,2,2],None),
        ([9,9,9,9,9,2],[9,9,9,9,9,9],[0.2,0.1,0.3,0.1,0.1,0.2]),
        ([2,2,3,4,5],[5,5,5,5,4],[0.2,0.2,0.2,0.2,0.2])
    ]
)
@pytest.mark.parametrize(
    "average",
    [
        "micro",
        "macro",
        "weighted"
    ]
)
def test_recall(y_true, y_pred, weights, average) -> None:
    from dioptra_builtins.metrics.performance import recall
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    kwargs = {"average":average, "sample_weight": weights}
    result: float = recall(y_true, y_pred, **kwargs)
    assert result == recall_score(y_true, y_pred, **kwargs)


