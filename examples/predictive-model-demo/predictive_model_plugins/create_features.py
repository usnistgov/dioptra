from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from .utility import ensure_list


def stat_column_transform(
    df: pd.DataFrame,
    raw_cols: List[str] | str,
    transform_func: function,
    colname_extension: str,
    drop_original: bool = True,
) -> pd.DataFrame:
    """Helper function to extend - performs feature engineering within one column."""
    
    raw_cols = ensure_list(raw_cols)

    for col in raw_cols:
        df[f"{col}{colname_extension}"] = transform_func(df[col])
        if drop_original and colname_extension != "":
            df = df.drop(col, axis=1)

    return df


def normalize_col(
    df: pd.DataFrame,
    raw_cols: List[str] | str,
    drop_original: bool = True,
    colname_extension: str = "_norm",
) -> pd.DataFrame:
    """Transforms column(s) through normalization."""

    def normalize(col):
        return (col - col.mean()) / col.std()

    return stat_column_transform(
        df, raw_cols, normalize, colname_extension, drop_original
    )


def log_col(
    df: pd.DataFrame,
    raw_cols: List[str] | str,
    drop_original: bool = True,
    colname_extension: str = "_log",
) -> pd.DataFrame:
    """Transforms column(s) through logarithm."""

    def log(col):
        return np.log(col)

    return stat_column_transform(df, raw_cols, log, colname_extension, drop_original)


feature_func_map = {
    "normalize": normalize_col,
    "log": log_col,
    # add transformations here ...
}
