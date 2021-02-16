"""Base classes for exceptions in the Securing AI package"""


class BaseSecuringAIError(Exception):
    """Base class for all Securing AI exceptions."""


class BaseGenericsRegistryError(BaseSecuringAIError):
    """Base class for all generics registration exceptions."""


class BaseOptionalDependencyError(BaseSecuringAIError):
    """Base class for all optional dependency exceptions."""


class BasePyPlugsException(BaseSecuringAIError):
    """Base class for all PyPlugs exceptions."""


class BaseTaskPluginError(BaseSecuringAIError):
    """Base class for all task plugin exceptions."""
