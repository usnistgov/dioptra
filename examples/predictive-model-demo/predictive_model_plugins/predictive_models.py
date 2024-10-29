from __future__ import annotations


from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional, Tuple, Union, Any
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.neighbors import KNeighborsRegressor



class PredictiveModel(ABC):
    def __init__(self,  hyperparameters: Dict[str, Any] = None):
        self.model = None
        self.labels = None # for classification
        self.hyperparameters = hyperparameters if hyperparameters else {}

    @abstractmethod
    def fit(self, X, y, hyperparameters):
        pass

    @abstractmethod
    def predict(self, X):
        pass

    @property
    @abstractmethod
    def model_type(self):
        pass # to distinguish between regression/classification later on


class LinearRegressor(PredictiveModel):
    def __init__(self, hyperparameters: Dict[str, Any] = None):
        super().__init__(hyperparameters)
        self.model = LinearRegression()

    @property
    def model_type(self):
        return 'regression'
    
    def fit(self, X:pd.DataFrame|np.ndarray, y:np.ndarray) -> None:
        self.model.fit(X,y)

    def predict(self, X:pd.DataFrame|np.ndarray) -> np.ndarray:
        return self.model.predict(X)
    

class DTRegressor(PredictiveModel):

    def __init__(self, hyperparameters: Dict[str, Any] = None):
        super().__init__(hyperparameters)
        self.model = DecisionTreeRegressor()

    @property
    def model_type(self):
        return 'regression'
    
    def set_hyperparameters(self, X: pd.DataFrame|None = None):

        default_hyperparameters = {'criterion':'squared_error',
                                   'max_depth' : int(np.ceil(np.sqrt(X.shape[1]))) if X is not None else 5,
                                   'min_samples_split': 10
                                    }
        
        for hyperparameter, default in default_hyperparameters.items():
            if hyperparameter not in self.hyperparameters:
                self.hyperparameters[hyperparameter] = default 

        self.model.set_params(**self.hyperparameters)

    def fit(self, X:pd.DataFrame|np.ndarray, y:np.ndarray) -> None:
        
        self.set_hyperparameters(X=X)
        self.model.fit(X,y)

    def predict(self, X:pd.DataFrame|np.ndarray) -> np.ndarray:
        return self.model.predict(X)
    

class KNNRegressor(PredictiveModel):

    def __init__(self, hyperparameters: Dict[str, Any] = None):
        super().__init__(hyperparameters)
        self.model = KNeighborsRegressor()

    
    @property
    def model_type(self):
        return 'regression'
    
    def set_hyperparameters(self, X: pd.DataFrame|None = None):
                
        default_hyperparameters = {'n_neighbors': int(np.ceil(np.sqrt(X.shape[0]))) if X is not None else 5,
                                   'weights' : 'distance'}
        
        for hyperparameter, default in default_hyperparameters.items():
            if hyperparameter not in self.hyperparameters:
                self.hyperparameters[hyperparameter] = default 

        self.model.set_params(**self.hyperparameters)
    
    def fit(self, X:pd.DataFrame|np.ndarray, y:np.ndarray) -> None:
        self.set_hyperparameters(X=X)
        self.model.fit(X,y)

    def predict(self, X:pd.DataFrame|np.ndarray) -> np.ndarray:
        return self.model.predict(X)