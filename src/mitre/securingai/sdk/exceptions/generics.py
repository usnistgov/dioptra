# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
"""Exceptions for SecuringAI SDK generics."""

from .base import BaseGenericsRegistryError


class EstimatorPredictGenericPredTypeError(BaseGenericsRegistryError):
    """Unknown pred_type argument passed to estimator_predict."""
