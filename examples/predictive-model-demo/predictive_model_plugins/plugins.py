from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple, Union, Any
from sklearn.base import BaseEstimator
import pandas as pd
import random


from .create_features import normalize_col, log_col
from .predictive_models import PredictiveModel, DTRegressor, LinearRegressor, KNNRegressor
from .metrics import calc_MSE

def load_dataset(
        dataset_path: str,
        dataset_type: str = 'csv',
        vars_to_keep: List[str] | None = None,
        dtypes: Dict[str, Any] = {},
) -> pd.DataFrame:
    
        if dataset_type == 'csv':
                df = pd.read_csv(dataset_path, dtype=dtypes)
        elif dataset_type == 'json':
               raise NotImplementedError
        
        if vars_to_keep:
               df = df[vars_to_keep]

        return df

def create_features(
        df: pd.DataFrame,
        transformations: List[tuple]
) -> pd.DataFrame:
        
        # transformation tuple is (func_name, args, kwargs)

        func_map = {'normalize': normalize_col,
                           'log' : log_col
                           # add transformations here ...
                           }
        
        for func_name, args, kwargs in transformations:
               df = func_map[func_name](*([df]+args), **kwargs) #df always first positional arg

        return df


def make_data_splits(
        df: pd.DataFrame,
        split_dicts: Dict[str, Dict] = {'train': {'frac':.8},
                                        'test': {'frac':.2} },
        shuffle: bool = True
)-> Dict[str, pd.DataFrame]:

        if sum([split_dict['frac'] for split_dict in split_dicts.values()]) >1:
               raise ValueError("Splits cannot sum to more than 1")
        
        indices = list(df.index)
        n_obs = len(indices)
        if shuffle:
               random.shuffle(indices)

        l,r = (0,0)
        for split_dict in split_dicts.values():
               n_obs_split = int(split_dict['frac']*n_obs)
               r = min(l+n_obs_split, n_obs)
               split_dict['indices'] = indices[l:r]
               split_dict['df'] = df.iloc[split_dict['indices']]
               l=r+1
               
        return split_dicts


def train_predictive_model(
        model_type: str,
        df : pd.DataFrame,
        target_var: str, 
        indep_vars: List[str] | None = None,
        hyperparameters: Dict = {}
):
        
        indep_vars = [col for col in df.columns if col != 'target_var'] if indep_vars is None else indep_vars
        X = df[indep_vars]
        y = df[target_var]

        model_map = {'LinearRegressor':LinearRegressor,
                 'DecisionTreeRegressor':DTRegressor,
                 'KNNRegressor':KNNRegressor}
    
        model = model_map[model_type](hyperparameters)

        model.fit(X,y)

        return model


def evaluate_model(
        model: PredictiveModel,
        df : pd.DataFrame,
        metrics : List[str],
        target_var: str, 
        indep_vars: List[str] | None = None,

) -> Dict[Any]:
        
        metrics = [metrics] if isinstance( metrics, str) else metrics
        metric_map = { 'MSE' : calc_MSE }

        indep_vars = [col for col in df.columns if col != 'target_var'] if indep_vars is None else indep_vars
        X = df[indep_vars]
        y_true = df[target_var]       
        y_pred = model.predict(X)


        out = {}
        for metric in metrics:
                out[metric] = metric_map[metric](y_true, y_pred)

        return out