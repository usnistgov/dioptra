from __future__ import annotations


from typing import Callable, Dict, List, Optional, Tuple, Union, Any
import pandas as pd


def normalize_col(
        df: pd.DataFrame,
        raw_cols: List[str], 
        drop_original: bool = True,
        colname_extension: str = '_norm'
) -> pd.DataFrame:
    
        if isinstance(raw_cols, str):
                raw_cols = list(raw_cols)

        for col in raw_cols:
                df[f'{col}{colname_extension}'] = (df[col] -df[col].mean() )/df[col].std() 
                if drop_original and colname_extension != '':
                        df = df.drop(col, axis=1)
            
        return df

def log_col(
        df: pd.DataFrame,
        raw_cols: List[str], 
        drop_original: bool = True,
        colname_extension: str = '_log'
) -> pd.DataFrame:
    
        pass