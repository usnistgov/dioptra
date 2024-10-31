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

"""A task plugin module demonstrating basic ML regression training/testing."""


from __future__ import annotations

import random
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import pandas as pd

from .create_features import feature_func_map
from .metrics import metric_map
from .predictive_models import PredictiveModel, model_map
from .utility import ensure_list


def load_dataset(
    dataset_path: str,
    dataset_type: str = "csv",
    vars_to_keep: List[str] | None = None,
    dtypes: Dict[str, Any] = {},
) -> pd.DataFrame:
    """Loads a tabular dataset from a filepath and returns a pandas dataframe."""

    if dataset_type == "csv":
        df = pd.read_csv(dataset_path, dtype=dtypes)
    elif dataset_type == "json":
        raise NotImplementedError

    if vars_to_keep:
        df = df[vars_to_keep]

    return df


def create_features(df: pd.DataFrame, transformations: List[tuple]) -> pd.DataFrame:
    """Peforms feature engineering on a tabular dataset by transforming columns.

    Args:
        df: a Pandas Dataframe to perform feature engineering on
        transformations: A list of tuples, where each tuple contains a desired
            trasnformation as well as the positional and keyword arguments.
            Each transformation is a tuple in the form of:
            (func_name, args, kwargs).
            Each transformation is loaded from the create_features.py
            module and is mapped in a Dict[str, func].

    Returns:
        a pandas.DataFrame with the engineered features
    """

    for func_name, args, kwargs in transformations:
        df = feature_func_map[func_name](
            *([df] + args), **kwargs
        )  # df always first positional arg

    return df


def make_data_splits(
    df: pd.DataFrame,
    split_dicts: Dict[str, Dict] = {"train": {"frac": 0.8}, "test": {"frac": 0.2}},
    shuffle: bool = True,
) -> Dict[str, pd.DataFrame]:
    """Splits a dataframe into subsets, defaulting to train/test splits of 80/20.

    Args:
        df: The tabular dataset which will be split into subsets
        split_dicts: A dictionary of dictionaries where the key is the name of
            the split. The value is another dictionary with the 'frac' key
            which indicates the fraction of the dataset in the split
        shuffle: if True, shuffles the dataset to randomize the order of
            observations in each split.

    Returns:
        splict_dicts: the updated dictionary containing indices and subsets of
            the original dataframe to be used for downstream training/testing
            tasks.
    """

    if sum([split_dict["frac"] for split_dict in split_dicts.values()]) > 1:
        raise ValueError("Splits cannot sum to more than 1")

    indices = list(df.index)
    n_obs = len(indices)
    if shuffle:
        random.shuffle(indices)

    # Subset the dataframe by slicing the row indices.
    # We have a left and right counter to track the indices of the dataframe.
    # We determine the size of the subset by multiplying the fraction by the
    # number of observations available, making sure not to throw an error
    # indexing out of range on our list of indices

    l, r = (0, 0)
    for split_dict in split_dicts.values():
        n_obs_split = int(split_dict["frac"] * n_obs)
        r = min(l + n_obs_split, n_obs)
        split_dict["indices"] = indices[l:r]
        split_dict["df"] = df.iloc[split_dict["indices"]]
        l = r + 1

    return split_dicts


def train_predictive_model(
    model_type: str,
    df: pd.DataFrame,
    target_var: str,
    indep_vars: List[str] | None = None,
    hyperparameters: Dict = {},
) -> PredictiveModel:
    """Given hyperparameters and train data, fits a predictive model.

    Args:
        model_type: the string key value which maps to a PredictiveModel in
            the model_map dictionary
        df: the training dataframe
        target_var: the column name for the target/lable variable in df
        indep_vars: list of column names to fit the model on, defaulting
            to all variables (besides the label)
        hyperparameters: a dictionary of hyperparameters with key names
            matching those of the underlying sklearn model

    Returns:
        An instance of the PredictiveModel class to be used for downstream
        predictions and evaluations
    """

    indep_vars = (
        [col for col in df.columns if col != "target_var"]
        if indep_vars is None
        else indep_vars
    )
    X = df[indep_vars]
    y = df[target_var]

    model = model_map[model_type](hyperparameters)

    model.fit(X, y)

    return model


def evaluate_model(
    model: PredictiveModel,
    df: pd.DataFrame,
    metrics: List[str],
    target_var: str,
    indep_vars: List[str] | None = None,
) -> Dict[Any]:
    """Given a model and a dataset, compute ML evaluation metrics.

    Args:
        model: an already fitted PredictiveModel
        df: a pandas dataframe to evaluate the model on
        metrics: keys to access functions in metric_map dictionary
        target_var: name of target/label column in df
        indep_vars: name of predictor variables. Must match the variables
            used to fit the model originally

    Returns:
        A dictionary of the computed metrics
    """

    metrics = ensure_list(metrics)

    indep_vars = (
        [col for col in df.columns if col != "target_var"]
        if indep_vars is None
        else indep_vars
    )
    X = df[indep_vars]
    y_true = df[target_var]
    y_pred = model.predict(X)

    out = {}
    for metric in metrics:
        out[metric] = metric_map[metric](y_true, y_pred)

    return out
