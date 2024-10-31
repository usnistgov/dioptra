from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, override

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.neighbors import KNeighborsRegressor
from sklearn.tree import DecisionTreeRegressor


class PredictiveModel(ABC):
    def __init__(self, hyperparameters: Dict[str, Any] = None):
        self.model = None
        self.labels = None  # for classification
        self.hyperparameters = hyperparameters if hyperparameters else {}

    @abstractmethod
    def fit(self, X: pd.DataFrame | np.ndarray, y: np.ndarray) -> None:
        """Uses hyperparameters and data to fit a Predictive Model"""
        pass

    @abstractmethod
    def predict(self, X):
        """Given a fit model and 1+ observation(s), predicts y value(s)"""
        pass

    @property
    @abstractmethod
    def model_type(self):
        """The type of predictive model - Regression or Classification"""
        pass


class LinearRegressor(PredictiveModel):
    def __init__(self, hyperparameters: Dict[str, Any] = None):
        super().__init__(hyperparameters)
        self.model = LinearRegression()

    @property
    def model_type(self):
        return "regression"

    @override
    def fit(self, X: pd.DataFrame | np.ndarray, y: np.ndarray) -> None:
        self.model.fit(X, y)

    @override
    def predict(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        return self.model.predict(X)


class DTRegressor(PredictiveModel):

    def __init__(self, hyperparameters: Dict[str, Any] = None):
        super().__init__(hyperparameters)
        self.model = DecisionTreeRegressor()
        self.default_hyperparameters =  {
            "criterion": lambda X: "squared_error",
            "max_depth": (lambda X: 
                          int(np.ceil(np.sqrt(X.shape[1])))
                          if X is not None
                          else 5),
            "min_samples_split": lambda X: 10,
            }

    @property
    def model_type(self):
        return "regression"

    def set_hyperparameters(self, X: pd.DataFrame | None = None):
        """Sets hyperparameters for DT model, using defaults if necessary"""

        for hyperparameter, default in self.default_hyperparameters.items():
            if hyperparameter not in self.hyperparameters:
                self.hyperparameters[hyperparameter] = default(X)

        self.model.set_params(**self.hyperparameters)

    @override
    def fit(self, X: pd.DataFrame | np.ndarray, y: np.ndarray) -> None:

        self.set_hyperparameters(X=X)
        self.model.fit(X, y)

    @override
    def predict(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        return self.model.predict(X)


class KNNRegressor(PredictiveModel):

    def __init__(self, hyperparameters: Dict[str, Any] = None):
        super().__init__(hyperparameters)
        self.model = KNeighborsRegressor()
        self.default_hyperparameters =  {
            "n_neighbors": lambda X: (int(np.ceil(np.sqrt(X.shape[0])))
                                    if X is not None
                                    else 5),
            "weights": lambda X: "distance",
        }

    @property
    def model_type(self):
        return "regression"

    def set_hyperparameters(self, X: pd.DataFrame | None = None):
        """Sets hyperparameters for DT model, using defaults if necessary"""

        for hyperparameter, default in self.default_hyperparameters.items():
            if hyperparameter not in self.hyperparameters:
                self.hyperparameters[hyperparameter] = default(X)

        self.model.set_params(**self.hyperparameters)

    @override
    def fit(self, X: pd.DataFrame | np.ndarray, y: np.ndarray) -> None:
        self.set_hyperparameters(X=X)
        self.model.fit(X, y)

    @override
    def predict(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        return self.model.predict(X)


model_map = {
    "LinearRegressor": LinearRegressor,
    "DecisionTreeRegressor": DTRegressor,
    "KNNRegressor": KNNRegressor,
}
