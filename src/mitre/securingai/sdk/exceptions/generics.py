"""Exceptions for SecuringAI SDK generics."""

from .base import BaseGenericsRegistryError


class EstimatorPredictGenericPredTypeError(BaseGenericsRegistryError):
    """Unknown pred_type argument passed to estimator_predict."""
