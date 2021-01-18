"""Exceptions for optional dependencies"""

from mitre.securingai.sdk.exceptions import BaseOptionalDependencyError


class ARTDependencyError(BaseOptionalDependencyError):
    """Method/function depends on the "art" package."""


class CryptographyDependencyError(BaseOptionalDependencyError):
    """Method/function depends on the "cryptography" package."""


class TensorflowDependencyError(BaseOptionalDependencyError):
    """Method/function depends on the "tensorflow" package."""
