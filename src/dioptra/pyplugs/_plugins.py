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
#
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

from __future__ import annotations

import functools
import importlib
import sys
import textwrap
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    NamedTuple,
    Optional,
    TypeVar,
    Union,
    cast,
    overload,
)

import structlog
from structlog.stdlib import BoundLogger

from dioptra.sdk.exceptions import (
    PrefectDependencyError,
    UnknownPackageError,
    UnknownPluginError,
    UnknownPluginFunctionError,
)
from dioptra.sdk.utilities.decorators import require_package

LOGGER: BoundLogger = structlog.stdlib.get_logger()


try:
    from importlib import resources

except ImportError:  # pragma: nocover
    import importlib_resources as resources  # type: ignore

try:
    from prefect import task

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="prefect",
    )

try:
    from typing import Protocol

except ImportError:  # pragma: nocover
    from typing_extensions import Protocol  # type: ignore

if TYPE_CHECKING:
    from prefect.tasks.core.function import FunctionTask


# Structural subtyping
class NoutPlugin(Protocol):
    _task_nout: int

    def __call__(self, *args, **kwargs) -> Any: ...  # noqa: E704; pragma: nocover


# Type aliases
T = TypeVar("T")
Plugin = Callable[..., Any]


class PluginInfo(NamedTuple):
    """Information about one plug-in"""

    package_name: str
    plugin_name: str
    func_name: str
    func: Union[Plugin, NoutPlugin]
    description: str
    doc: str
    module_doc: str
    sort_value: float


# Dictionary with information about all registered plug-ins
_PLUGINS: Dict[str, Dict[str, Dict[str, PluginInfo]]] = {}


@overload
def register(*, sort_value: float) -> Callable[[Plugin], Plugin]:
    """Signature for using decorator with parameters"""
    ...  # pragma: nocover


@overload
def register(func: Plugin) -> Plugin:
    """Signature for using decorator without parameters"""
    ...  # pragma: nocover


def register(_func=None, *, sort_value=0):
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


def task_nout(nout: int) -> Callable[[Plugin], NoutPlugin]:
    def decorator(func: Plugin) -> NoutPlugin:
        # We're just assigning an attribute, and we need mypy to let us
        # do that.  So we just force a type change, to a callable type which
        # includes an attribute.
        nout_func = cast(NoutPlugin, func)
        nout_func._task_nout = nout

        return nout_func

    return decorator


def names(package: str) -> List[str]:
    """List all plug-ins in one package"""
    _import_all(package)

    return sorted(_PLUGINS[package].keys(), key=lambda p: info(package, p).sort_value)


def funcs(package: str, plugin: str) -> List[str]:
    """List all functions in one plug-in"""
    _import(package, plugin)
    plugin_info = _PLUGINS[package][plugin]

    return list(plugin_info.keys())


def info(package: str, plugin: str, func: Optional[str] = None) -> PluginInfo:
    """Get information about a plug-in"""
    _import(package, plugin)

    try:
        plugin_info = _PLUGINS[package][plugin]

    except KeyError as exc:
        raise UnknownPluginError(
            f"Could not find any plug-in named {plugin!r} inside {package!r}. "
            "Use pyplugs.register to register functions as plug-ins"
        ) from exc

    func = next(iter(plugin_info.keys())) if func is None else func

    try:
        return plugin_info[func]

    except KeyError as exc:
        raise UnknownPluginFunctionError(
            f"Could not find any function named {func!r} inside '{package}.{plugin}'. "
            "Use pyplugs.register to register plug-in functions"
        ) from exc


def exists(package: str, plugin: str) -> bool:
    """Check if a given plugin exists"""
    if package in _PLUGINS and plugin in _PLUGINS[package]:
        return True

    try:
        _import(package, plugin)

    except (UnknownPluginError, UnknownPackageError):
        return False

    else:
        return package in _PLUGINS and plugin in _PLUGINS[package]


def get(package: str, plugin: str, func: Optional[str] = None) -> Plugin:
    """Get a given plugin"""
    return info(package, plugin, func).func


def call(
    package: str, plugin: str, func: Optional[str] = None, *args: Any, **kwargs: Any
) -> Any:
    """Call the given plugin"""
    plugin_func = get(package, plugin, func)

    return plugin_func(*args, **kwargs)


@require_package("prefect", exc_type=PrefectDependencyError)
def get_task(package: str, plugin: str, func: Optional[str] = None) -> FunctionTask:
    """Get a given plugin wrapped as a prefect task"""
    plugin_func: Union[Plugin, NoutPlugin] = info(package, plugin, func).func
    nout: Optional[int] = getattr(plugin_func, "_task_nout", None)

    return task(nout=nout)(plugin_func)


@require_package("prefect", exc_type=PrefectDependencyError)
def call_task(
    package: str, plugin: str, func: Optional[str] = None, *args: Any, **kwargs: Any
) -> Any:
    """Call the given plugin as a prefect task"""
    plugin_task = get_task(package, plugin, func)

    return plugin_task(*args, **kwargs)


def _import(package: str, plugin: str) -> None:
    """Import the given plugin file from a package"""
    if package in _PLUGINS and plugin in _PLUGINS[package]:
        return None

    # If the plugin does not have a package, it is registered with package ""
    # (empty string).  Don't prepend the package in that case.
    if package:
        plugin_module = f"{package}.{plugin}"
    else:
        plugin_module = plugin

    try:
        importlib.import_module(plugin_module)

    except ImportError as err:
        if repr(plugin_module) in err.msg:
            #   Plugin not found in ''
            # is a confusing error message... don't mention a package in the
            # error message if there wasn't one.
            message = f"Plugin {plugin!r} not found"
            if package:
                message += f" in {package!r}"
            raise UnknownPluginError(message) from None

        elif repr(package) in err.msg:
            raise UnknownPackageError(f"Package {package!r} does not exist") from None

        raise


def _import_all(package: str) -> None:
    """Import all plugins in a package"""
    try:
        all_resources = resources.contents(package)

    except ImportError as err:
        raise UnknownPackageError(err) from None

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


def names_factory(package: str) -> Callable[[], List[str]]:
    """Create a names() function for one package"""
    return functools.partial(names, package)


def funcs_factory(package: str) -> Callable[[str], List[str]]:
    """Create a funcs() function for one package"""
    return functools.partial(funcs, package)


def info_factory(package: str) -> Callable[[str, Optional[str]], PluginInfo]:
    """Create a info() function for one package"""
    return functools.partial(info, package)


def exists_factory(package: str) -> Callable[[str], bool]:
    """Create an exists() function for one package"""
    return functools.partial(exists, package)


def get_factory(package: str) -> Callable[[str, Optional[str]], Plugin]:
    """Create a get() function for one package"""
    return functools.partial(get, package)


def call_factory(package: str) -> Callable[..., Any]:
    """Create a call() function for one package"""
    return functools.partial(call, package)


@require_package("prefect", exc_type=PrefectDependencyError)
def get_task_factory(package: str) -> Callable[[str, Optional[str]], FunctionTask]:
    """Create a get_task() function for one package"""
    return functools.partial(get_task, package)


@require_package("prefect", exc_type=PrefectDependencyError)
def call_task_factory(package: str) -> Callable[..., Any]:
    """Create a call_task() function for one package"""
    return functools.partial(call_task, package)


__all__ = [
    "register",
    "task_nout",
    "names",
    "funcs",
    "info",
    "exists",
    "get",
    "call",
    "get_task",
    "call_task",
    "names_factory",
    "funcs_factory",
    "info_factory",
    "exists_factory",
    "get_factory",
    "call_factory",
    "get_task_factory",
    "call_task_factory",
]
