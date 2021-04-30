"""The task plugin endpoint subpackage."""

from .dependencies import bind_dependencies, register_providers
from .errors import register_error_handlers
from .routes import register_routes

__all__ = [
    "bind_dependencies",
    "register_error_handlers",
    "register_providers",
    "register_routes",
]
