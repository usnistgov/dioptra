# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
"""A subpackage of generic functions for common data science operations."""

from __future__ import annotations

from ._estimator_predict import estimator_predict
from ._fit_estimator import fit_estimator
from ._registry import register_entrypoints

__all__ = ["estimator_predict", "fit_estimator"]


register_entrypoints()
