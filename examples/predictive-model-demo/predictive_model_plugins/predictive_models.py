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

"""Classes of predictive models to be fit and then predict on observations"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, override

import numpy as np
import pandas as pd
from scipy import stats as st
from sklearn.ensemble import AdaBoostClassifier, AdaBoostRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor


class PredictiveModel(ABC):
    """Parent class wrapping primarily SKLearn regression/classification models."""

    def __init__(self, hyperparameters: Dict[str, Any] = None):
        self.model = None
        self.labels = None  # for classification
        self.hyperparameters = hyperparameters if hyperparameters else {}
        self.default_hyperparameters = {}
        self._model_type = None

    @property
    def model_type(self):
        """The type of predictive model - Regression or Classification"""
        return self._model_type

    @model_type.setter
    def model_type(self, value):
        if value.lower() not in ["classification", "regression"]:
            raise ValueError("model_type must be 'classification' or 'regression'")
        self._model_type = value

    @abstractmethod
    def fit(self, X: pd.DataFrame | np.ndarray, y: np.ndarray) -> None:
        """Uses data and optionally hyperparameters to fit a Predictive Model"""
        pass

    def predict(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        """Given a fit model and 1+ observation(s), predicts y value(s)"""
        if self.model_type == "regression":
            return self.predict_regression(X)

        elif self.model_type == "classification":
            return self.predict_score(X)

    def predict_score(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        """Predicts a score between 0 and 1 for classification models"""
        raise NotImplementedError()

    def predict_regression(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        """Predicts a real valued number for regression models"""
        raise NotImplementedError()

    def set_hyperparameters(self, X: pd.DataFrame | None = None):
        """Sets hyperparameters for model, using defaults if necessary"""

        for hyperparameter, default in self.default_hyperparameters.items():
            if hyperparameter not in self.hyperparameters:
                self.hyperparameters[hyperparameter] = (
                    default(X=X) if callable(default) else default
                )

        self.model.set_params(**self.hyperparameters)


class LinearRegressor(PredictiveModel):
    """A predictive model using basic linear regression model for continuous prediction"""

    def __init__(
        self, model_type: str = "regression", hyperparameters: Dict[str, Any] = None
    ):
        super().__init__(hyperparameters)
        if model_type is None:
            model_type = "regression"
        self.model_type = model_type
        self.model = LinearRegression()
        self.default_hyperparameters = {"fit_intercept": True}

    @override
    def fit(self, X: pd.DataFrame | np.ndarray, y: np.ndarray) -> None:
        self.model.fit(X, y)

    @override
    def predict_regression(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        return self.model.predict(X)


class LogisticClassifier(PredictiveModel):
    """A predictive model using logistic classification"""

    def __init__(
        self, model_type: str = "classification", hyperparameters: Dict[str, Any] = None
    ):
        super().__init__(hyperparameters)
        self.model = LogisticRegression()
        if model_type is None:
            model_type = "classification"
        self.model_type = model_type

        self.default_hyperparameters = {"penalty": None, "fit_intercept": True}

    @override
    def fit(self, X: pd.DataFrame | np.ndarray, y: np.ndarray) -> None:
        self.set_hyperparameters()
        self.model.fit(X, y)

    @override
    def predict_score(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        scores = self.model.predict_proba(X)
        class_1_index = np.where(self.model.classes_ == 1)[0][0]
        return scores[:, class_1_index]


class DecisionTreeModel(PredictiveModel):
    """A predictive model utilizing decision trees for regression or classification"""

    def __init__(
        self,
        model_type: "regression" | "classification" = None,
        hyperparameters: Dict[str, Any] = None,
    ):
        """Initialize DT regressor/classifier, pass hyperparameters to parent constructor."""
        super().__init__(hyperparameters)

        self.model_type = model_type
        dt_model_dict = {
            "regression": DecisionTreeRegressor,
            "classification": DecisionTreeClassifier,
        }
        self.model = dt_model_dict.get(self.model_type, None)()

        self.default_hyperparameters = {
            "criterion": (
                "squared_error"
                if self.model_type == "regression"
                else ("gini" if self.model_type == "classification" else None)
            ),
            "max_depth": (
                lambda X: int(np.ceil(np.sqrt(X.shape[1]))) if X is not None else 5
            ),
            "min_samples_split": 10,
        }

    @override
    def fit(self, X: pd.DataFrame | np.ndarray, y: np.ndarray) -> None:
        self.set_hyperparameters(X=X)
        self.model.fit(X, y)

    @override
    def predict_regression(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        return self.model.predict(X)

    @override
    def predict_score(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        scores = self.model.predict_proba(X)
        class_1_index = np.where(self.model.classes_ == 1)[0][0]
        return scores[:, class_1_index]


class KNNModel(PredictiveModel):
    """A predictive model using K Nearest Neighbors for regression/classification"""

    def __init__(
        self,
        model_type: "regression" | "classification" = None,
        hyperparameters: Dict[str, Any] = None,
    ):
        """Initialize KNNRegressor, pass hyperparameters to parent constructor."""
        super().__init__(hyperparameters)

        self.model_type = model_type
        dt_model_dict = {
            "regression": KNeighborsRegressor,
            "classification": KNeighborsClassifier,
        }
        self.model = dt_model_dict.get(self.model_type, None)()

        self.default_hyperparameters = {
            "n_neighbors": lambda **kwargs: (
                int(np.ceil(np.sqrt(kwargs.get("X").shape[0])))
                if kwargs.get("X", None) is not None
                else 5
            ),
            "weights": "distance",
        }

    @override
    def fit(self, X: pd.DataFrame | np.ndarray, y: np.ndarray) -> None:
        self.set_hyperparameters(X=X)
        self.model.fit(X, y)

    @override
    def predict_regression(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        return self.model.predict(X)

    @override
    def predict_score(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        scores = self.model.predict_proba(X)
        class_1_index = np.where(self.model.classes_ == 1)[0][0]
        return scores[:, class_1_index]


class AdaBoostModel(PredictiveModel):
    """A predictive model using AdaBoost for regression/classification"""

    def __init__(
        self,
        model_type: "regression" | "classification" = None,
        hyperparameters: Dict[str, Any] = None,
    ):
        """Initialize AdaBoost, pass hyperparameters to parent constructor."""
        super().__init__(hyperparameters)

        self.model_type = model_type
        dt_model_dict = {
            "regression": AdaBoostRegressor,
            "classification": AdaBoostClassifier,
        }
        self.model = dt_model_dict.get(self.model_type, None)()

        self.default_hyperparameters = {}

    @override
    def fit(self, X: pd.DataFrame | np.ndarray, y: np.ndarray) -> None:
        self.set_hyperparameters()
        self.model.fit(X, y)

    @override
    def predict_regression(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        return self.model.predict(X)

    @override
    def predict_score(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        scores = self.model.predict_proba(X)
        class_1_index = np.where(self.model.classes_ == 1)[0][0]
        return scores[:, class_1_index]


class NaiveModel(PredictiveModel):
    """A predictive model that naively returns the mean/modal y value"""

    def __init__(
        self,
        model_type: "regression" | "classification" = None,
        hyperparameters: Dict[str, Any] = None,
    ):
        """Initialize Niave Regressor/Classifier"""

        super().__init__(hyperparameters)
        self.model = {"naive_prediction": None}
        self.model_type = model_type

    @override
    def fit(self, X: pd.DataFrame | np.ndarray | None, y: np.ndarray) -> None:
        if self.model_type == "regression":
            self.model["naive_prediction"] = np.mean(y)
        elif self.model_type == "classification":
            self.model["naive_prediction"] = st.mode(y)[0]

    @override
    def predict(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        n_samples = len(X) if hasattr(X, "__len__") else 1
        # return np.full(shape=(n_samples,), fill_value =  self.model['naive_prediction'])
        return np.random.rand(n_samples)


def get_predictions(
    model: PredictiveModel,
    df: pd.DataFrame,
    target_var: str,
    indep_vars: List[str] | None = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Given a model, DF and x/y varnames, subset df and make predictions"""

    indep_vars = (
        [col for col in df.columns if col != "target_var"]
        if indep_vars is None
        else indep_vars
    )
    X = df[indep_vars]
    y_true = df[target_var]
    y_pred = model.predict(X)

    return (y_pred, y_true, X)


def scores_to_labels(y_scores, threshhold) -> np.ndarray:

    return (y_scores >= threshhold).astype(int)


# Access models via string names
model_map = {
    "LinearRegressor": LinearRegressor,
    "DecisionTreeModel": DecisionTreeModel,
    "KNNModel": KNNModel,
    "NaiveRegressor": NaiveModel,
    "LogisticClassifier": LogisticClassifier,
    "AdaBoostModel": AdaBoostModel,
}
