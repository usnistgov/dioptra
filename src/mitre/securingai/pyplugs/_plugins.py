# This is a fork of the work
# https://github.com/gahjelle/pyplugs/blob/90e635777672f75080291c737f08453a26ea380d/pyplugs/_plugins.py  # noqa: B950
# See copyright below.
#
# Copyright (c) 2019 Geir Arne Hjelle
# Distributed under the terms of the MIT License.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Decorators for registering plugins"""

import functools
import importlib
import sys
import textwrap
from typing import Any, Callable, Dict, List, NamedTuple, Optional, TypeVar, overload

import structlog
from structlog.stdlib import BoundLogger

from . import _exceptions

try:
    from importlib import resources

except ImportError:  # pragma: nocover
    import importlib_resources as resources  # type: ignore


LOGGER: BoundLogger = structlog.stdlib.get_logger()


# Type aliases
T = TypeVar("T")
Plugin = Callable[..., Any]


# Only expose decorated functions to the outside
__all__ = []


def expose(func: Callable[..., T]) -> Callable[..., T]:
    """Add function to __all__ so it will be exposed at the top level"""
    __all__.append(func.__name__)

    return func


class PluginInfo(NamedTuple):
    """Information about one plug-in"""

    package_name: str
    plugin_name: str
    func_name: str
    func: Plugin
    description: str
    doc: str
    module_doc: str
    sort_value: float


# Dictionary with information about all registered plug-ins
_PLUGINS: Dict[str, Dict[str, Dict[str, PluginInfo]]] = {}


@overload
def register(func: None, *, sort_value: float) -> Callable[[Plugin], Plugin]:
    """Signature for using decorator with parameters"""
    ...  # pragma: nocover


@overload
def register(func: Plugin) -> Plugin:
    """Signature for using decorator without parameters"""
    ...  # pragma: nocover


@expose
def register(
    _func: Optional[Plugin] = None, *, sort_value: float = 0
) -> Callable[..., Any]:
    """Decorator for registering a new plug-in"""

    def decorator_register(func: Callable[..., T]) -> Callable[..., T]:
        """Store information about the given function"""
        package_name, _, plugin_name = func.__module__.rpartition(".")
        description, _, doc = (func.__doc__ or "").partition("\n\n")
        func_name = func.__name__
        module_doc = sys.modules[func.__module__].__doc__ or ""

        pkg_info = _PLUGINS.setdefault(package_name, {})
        plugin_info = pkg_info.setdefault(plugin_name, {})
        plugin_info[func_name] = PluginInfo(
            package_name=package_name,
            plugin_name=plugin_name,
            func_name=func_name,
            func=func,
            description=description,
            doc=textwrap.dedent(doc).strip(),
            module_doc=module_doc,
            sort_value=sort_value,
        )

        return func

    if _func is None:
        return decorator_register

    else:
        return decorator_register(_func)


@expose
def names(package: str) -> List[str]:
    """List all plug-ins in one package"""
    _import_all(package)

    return sorted(_PLUGINS[package].keys(), key=lambda p: info(package, p).sort_value)


@expose
def funcs(package: str, plugin: str) -> List[str]:
    """List all functions in one plug-in"""
    _import(package, plugin)
    plugin_info = _PLUGINS[package][plugin]

    return list(plugin_info.keys())


@expose
def info(package: str, plugin: str, func: Optional[str] = None) -> PluginInfo:
    """Get information about a plug-in"""
    _import(package, plugin)

    try:
        plugin_info = _PLUGINS[package][plugin]

    except KeyError:
        raise _exceptions.UnknownPluginError(
            f"Could not find any plug-in named {plugin!r} inside {package!r}. "
            "Use pyplugs.register to register functions as plug-ins"
        )

    func = next(iter(plugin_info.keys())) if func is None else func

    try:
        return plugin_info[func]

    except KeyError:
        raise _exceptions.UnknownPluginFunctionError(
            f"Could not find any function named {func!r} inside '{package}.{plugin}'. "
            "Use pyplugs.register to register plug-in functions"
        )


@expose
def exists(package: str, plugin: str) -> bool:
    """Check if a given plugin exists"""
    if package in _PLUGINS and plugin in _PLUGINS[package]:
        return True

    try:
        _import(package, plugin)

    except (_exceptions.UnknownPluginError, _exceptions.UnknownPackageError):
        return False

    else:
        return package in _PLUGINS and plugin in _PLUGINS[package]


@expose
def get(package: str, plugin: str, func: Optional[str] = None) -> Plugin:
    """Get a given plugin"""
    return info(package, plugin, func).func


@expose
def call(
    package: str, plugin: str, func: Optional[str] = None, *args: Any, **kwargs: Any
) -> Any:
    """Call the given plugin"""
    plugin_func = get(package, plugin, func)

    return plugin_func(*args, **kwargs)


def _import(package: str, plugin: str) -> None:
    """Import the given plugin file from a package"""
    if package in _PLUGINS and plugin in _PLUGINS[package]:
        return None

    plugin_module = f"{package}.{plugin}"

    try:
        importlib.import_module(plugin_module)

    except ImportError as err:
        if repr(plugin_module) in err.msg:  # type: ignore
            raise _exceptions.UnknownPluginError(
                f"Plugin {plugin!r} not found in {package!r}"
            ) from None

        elif repr(package) in err.msg:  # type: ignore
            raise _exceptions.UnknownPackageError(
                f"Package {package!r} does not exist"
            ) from None

        raise


def _import_all(package: str) -> None:
    """Import all plugins in a package"""
    try:
        all_resources = resources.contents(package)

    except ImportError as err:
        raise _exceptions.UnknownPackageError(err) from None

    # Note that we have tried to import the package by adding it to _PLUGINS
    _PLUGINS.setdefault(package, {})

    # Loop through all Python files in the directories of the package
    plugins = [
        r[:-3] for r in all_resources if r.endswith(".py") and not r.startswith("_")
    ]

    for plugin in plugins:
        try:
            _import(package, plugin)

        except ImportError:
            pass  # Don't let errors in one plugin, affect the others


@expose
def names_factory(package: str) -> Callable[[], List[str]]:
    """Create a names() function for one package"""
    return functools.partial(names, package)


@expose
def funcs_factory(package: str) -> Callable[[str], List[str]]:
    """Create a funcs() function for one package"""
    return functools.partial(funcs, package)


@expose
def info_factory(package: str) -> Callable[[str, Optional[str]], PluginInfo]:
    """Create a info() function for one package"""
    return functools.partial(info, package)


@expose
def exists_factory(package: str) -> Callable[[str], bool]:
    """Create an exists() function for one package"""
    return functools.partial(exists, package)


@expose
def get_factory(package: str) -> Callable[[str, Optional[str]], Plugin]:
    """Create a get() function for one package"""
    return functools.partial(get, package)


@expose
def call_factory(package: str) -> Callable[..., Any]:
    """Create a call() function for one package"""
    return functools.partial(call, package)
