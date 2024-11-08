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

"""Functions to calculate evaluation metrics given a fitted model"""


from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from aif360.datasets import BinaryLabelDataset
from aif360.explainers import MetricJSONExplainer, MetricTextExplainer
from aif360.metrics import ClassificationMetric
from sklearn.metrics import accuracy_score

from .predictive_models import PredictiveModel, get_predictions, scores_to_labels
from .utility import ensure_list, get_dict_value


def calc_MSE(model, df, target_var, indep_vars, **kwargs) -> Dict:
    """Calculates Mean Squared Error between predictions and true labels"""

    y_pred, y_true, _ = get_predictions(model, df, target_var, indep_vars)
    return {
        "metric_name": "Mean Squared Error",
        "metric_value": float(np.mean((y_true - y_pred) ** 2)),
    }


def calc_accuracy(model, df, target_var, indep_vars, **kwargs) -> float:
    """Calculates Accuracy of scores to Label Given a threshold"""

    y_scores, y_true, _ = get_predictions(model, df, target_var, indep_vars)
    threshhold = kwargs.get("threshhold", 0.5)
    predicted_labels = scores_to_labels(y_scores, threshhold)

    accuracy = accuracy_score(y_true, predicted_labels)

    return {"metric_name": "Accuracy", "metric_value": accuracy}


def create_bias_dfs(
    model: PredictiveModel,
    df: pd.DataFrame,
    target_var: str,
    indep_vars: List[str],
    protected_attribute_names: str | List[str],
    score_threshhold: float = 0.5,
) -> Tuple[BinaryLabelDataset, BinaryLabelDataset]:
    """Helper function to turn pd dataframe into aif360 dataframes class for bias calculations"""

    df_labels = df.copy()
    df_preds = df.copy()
    target_var = ensure_list(target_var)

    df_labels = BinaryLabelDataset(
        df=df_labels,
        label_names=target_var,
        protected_attribute_names=protected_attribute_names,
    )

    if model.model_type == "classification":
        y_scores, _, _ = get_predictions(model, df, target_var, indep_vars)
        y_pred = scores_to_labels(y_scores, score_threshhold)
    elif model.model_type == "regression":
        y_pred = get_predictions(model, df, target_var, indep_vars)

    df_preds[target_var[0]] = y_pred
    df_preds = BinaryLabelDataset(
        df=df_preds,
        label_names=target_var,
        protected_attribute_names=protected_attribute_names,
    )

    return df_labels, df_preds


def calc_bias_classification(
    model: PredictiveModel,
    df: pd.DataFrame,
    target_var: str,
    indep_vars: List[str],
    **kwargs,
) -> Dict:
    """Takes a fitted model, bias metric and kwargs and calculates bias on dataset"""

    protected_attribute_names = ensure_list(
        get_dict_value(
            kwargs,
            "protected_attribute_names",
            error_type="ValueError",
            error_message="Missing required kwarg 'protected_attribute_names' for classification bias calculation",
        )
    )
    bias_metric = get_dict_value(
        kwargs,
        "bias_metric",
        error_type="ValueError",
        error_message="Missing required kwarg 'bias_metric' for classification bias calculation",
    )

    priv_group = get_dict_value(
        kwargs,
        "privileged_groups",
        error_type="ValueError",
        error_message="Missing required kwarg 'privileged_groups' for classification bias calculation",
    )

    unpriv_group = get_dict_value(
        kwargs,
        "unprivileged_groups",
        error_type="ValueError",
        error_message="Missing required kwarg 'unprivileged_groups' for classification bias calculation",
    )

    # Get datasets, group names, etc in aif360 expected format
    df_labels, df_preds = create_bias_dfs(
        model, df, target_var, indep_vars, protected_attribute_names
    )
    class_metric_instance = ClassificationMetric(
        df_labels,
        df_preds,
        unprivileged_groups=unpriv_group,
        privileged_groups=priv_group,
    )
    explainer_instance = MetricJSONExplainer(class_metric_instance)

    metric_method = getattr(class_metric_instance, bias_metric, None)
    explainer_method = getattr(explainer_instance, bias_metric, None)
    if callable(metric_method):
        metric_value = metric_method()
        metric_explanation = json.loads(explainer_method())
    else:
        raise ValueError(f"{metric_method} is not a valid classification metric")

    return {
        "metric_name": bias_metric,
        "metric_description": metric_explanation,
        "metric_value": metric_value,
    }


# Access metrics via strings
metric_map = {
    "MSE": calc_MSE,
    "accuracy": calc_accuracy,
    "classification_bias": calc_bias_classification,
}
