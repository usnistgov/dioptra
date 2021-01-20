"""Exceptions for optional dependencies"""

from .base import BaseOptionalDependencyError


class ARTDependencyError(BaseOptionalDependencyError):
    """Method/function depends on the "art" package."""


class CryptographyDependencyError(BaseOptionalDependencyError):
    """Method/function depends on the "cryptography" package."""


class PrefectDependencyError(BaseOptionalDependencyError):
    """Method/function depends on the "prefect" package."""


class TensorflowDependencyError(BaseOptionalDependencyError):
    """Method/function depends on the "tensorflow" package."""
