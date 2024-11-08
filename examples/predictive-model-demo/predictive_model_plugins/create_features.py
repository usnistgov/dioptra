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

"""Functions that perform feature engineering using columns in a DF"""

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
    """Wrapper function for single column statistical transformations"""

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
