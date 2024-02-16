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
import contextlib
import functools
from typing import Any, Callable, Iterator, Mapping

import pytest

import dioptra.pyplugs
import dioptra.pyplugs._plugins
import dioptra.task_engine.task_engine
from dioptra.sdk.exceptions.task_engine import (
    IllegalOutputReferenceError,
    IllegalPluginNameError,
    MissingGlobalParametersError,
    MissingTaskPluginNameError,
    NonIterableTaskOutputError,
    OutputNotFoundError,
    StepNotFoundError,
    StepReferenceCycleError,
    UnresolvableReferenceError,
)

_output = None


def capture_return(f: Callable[..., Any]) -> Callable[..., Any]:
    """
    Hacky way to capture a function's return value so unit tests can test it.
    Task graphs have no outputs, so we have no easy way to see what the task
    plugins are returning.

    This function is a decorator which captures the output of the wrapped
    function into the global _output variable.  Of course if more than one
    plugin is invoked, at the end, _output will contain the return value for
    whichever plugin was invoked last.
    """

    @functools.wraps(f)
    def wrapper(*args: Any, **kwargs: Mapping[str, Any]) -> Any:
        global _output
        _output = f(*args, **kwargs)
        return _output

    return wrapper


@capture_return
def add(a: Any, b: Any) -> Any:
    """Simple function to register with pyplugs, for testing"""
    return a + b


@capture_return
def square(n: Any) -> Any:
    """Simple function to register with pyplugs, for testing"""
    return n * n


@capture_return
def addsub(a: Any, b: Any) -> Any:
    """
    Simple function returning multiple values, to register with pyplugs, for
    testing
    """
    return a + b, a - b


@capture_return
def hello() -> str:
    """
    Simple function which takes no args, to register with pyplugs, for testing
    """
    return "hello"


@contextlib.contextmanager
def pyplugs_register(*funcs: Callable[..., Any]) -> Iterator[None]:
    """
    A contextmanager which registers the given function(s) with pyplugs, and
    then un-registers them again to clean up after itself.

    Args:
        *funcs: An iterable of functions (which must support iteration over
            the values multiple times).
    """
    try:
        for func in funcs:
            dioptra.pyplugs.register(func)

        yield

    finally:
        # I don't know of any other way to unregister a plugin, so this uses
        # non-public API.
        plugin_registry = dioptra.pyplugs._plugins._PLUGINS

        # Just search all the plugins; skip splitting up func.__module__ as
        # pyplugs does.  I think there will be relatively few functions
        # registered, so an exhaustive search like this will be plenty fast
        # enough and perhaps simpler to write?  If any of the sub-dicts empties
        # out, the entry in the parent dict which refers to it, is also
        # removed.  It makes for a cleaner clean!
        packages_to_del = []
        for package_name, package in plugin_registry.items():
            plugins_to_del = []
            for plugin_name, plugin in package.items():
                funcs_to_del = []
                for func_name, plugin_info in plugin.items():
                    if plugin_info.func in funcs:
                        funcs_to_del.append(func_name)

                for func_name in funcs_to_del:
                    del plugin[func_name]

                if not plugin:
                    plugins_to_del.append(plugin_name)

            for plugin_name in plugins_to_del:
                del package[plugin_name]

            if not package:
                packages_to_del.append(package_name)

        for package_name in packages_to_del:
            del plugin_registry[package_name]


def require_plugins(
    *funcs: Callable[..., Any]
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator which causes the given plugins to be registered before the
    function runs, and unregistered after it returns.

    Args:
        *funcs: The plugin functions to register

    Returns:
        A wrap function
    """

    def wrap(f):
        def wrapper(*args, **kwargs):
            with pyplugs_register(*funcs):
                return f(*args, **kwargs)

        return wrapper

    return wrap


@require_plugins(add)
def test_single_call_positional() -> None:
    desc = {
        "tasks": {"add": {"plugin": "tests.unit.task_engine.test_task_engine.add"}},
        "graph": {"add": {"add": [1, 1]}},
    }

    dioptra.task_engine.task_engine.run_experiment(desc, {})

    assert _output == 2


@require_plugins(square)
def test_single_call_positional_nolist() -> None:
    desc = {
        "tasks": {
            "square": {"plugin": "tests.unit.task_engine.test_task_engine.square"}
        },
        "graph": {"step1": {"square": 2}},
    }

    dioptra.task_engine.task_engine.run_experiment(desc, {})

    assert _output == 4


@require_plugins(add)
def test_single_call_keyword() -> None:
    desc = {
        "tasks": {"add": {"plugin": "tests.unit.task_engine.test_task_engine.add"}},
        "graph": {"step1": {"add": {"a": 1, "b": 1}}},
    }

    dioptra.task_engine.task_engine.run_experiment(desc, {})

    assert _output == 2


@require_plugins(add)
def test_single_call_mixed_positional_keyword() -> None:
    desc = {
        "tasks": {"add": {"plugin": "tests.unit.task_engine.test_task_engine.add"}},
        "graph": {"step1": {"task": "add", "args": 1, "kwargs": {"b": 1}}},
    }

    dioptra.task_engine.task_engine.run_experiment(desc, {})

    assert _output == 2


@require_plugins(hello)
def test_single_call_no_args_positional() -> None:
    desc = {
        "tasks": {"hello": {"plugin": "tests.unit.task_engine.test_task_engine.hello"}},
        "graph": {"step1": {"hello": []}},
    }

    dioptra.task_engine.task_engine.run_experiment(desc, {})

    assert _output == "hello"


@require_plugins(hello)
def test_single_call_no_args_keyword() -> None:
    desc = {
        "tasks": {"hello": {"plugin": "tests.unit.task_engine.test_task_engine.hello"}},
        "graph": {"step1": {"hello": {}}},
    }

    dioptra.task_engine.task_engine.run_experiment(desc, {})

    assert _output == "hello"


@require_plugins(hello)
def test_single_call_no_args_mixed() -> None:
    desc = {
        "tasks": {"hello": {"plugin": "tests.unit.task_engine.test_task_engine.hello"}},
        "graph": {"step1": {"task": "hello"}},
    }

    dioptra.task_engine.task_engine.run_experiment(desc, {})

    assert _output == "hello"


@require_plugins(add)
def test_globals_dict_nodefault() -> None:
    desc = {
        "parameters": {"global_in": {"type": "integer"}},
        "tasks": {"add": {"plugin": "tests.unit.task_engine.test_task_engine.add"}},
        "graph": {"step1": {"add": [1, "$global_in"]}},
    }

    dioptra.task_engine.task_engine.run_experiment(desc, {"global_in": 2})

    assert _output == 3

    with pytest.raises(MissingGlobalParametersError) as e:
        dioptra.task_engine.task_engine.run_experiment(desc, {})

    assert "global_in" in e.value.parameter_names


@require_plugins(add)
def test_globals_dict_default() -> None:
    desc = {
        "parameters": {"global_in": 1},
        "tasks": {"add": {"plugin": "tests.unit.task_engine.test_task_engine.add"}},
        "graph": {"step1": {"add": [1, "$global_in"]}},
    }

    dioptra.task_engine.task_engine.run_experiment(desc, {"global_in": 2})

    assert _output == 3

    dioptra.task_engine.task_engine.run_experiment(desc, {})

    assert _output == 2


@require_plugins(addsub)
def test_task_nonlist_output() -> None:
    desc = {
        "tasks": {
            "addsub": {
                "plugin": "tests.unit.task_engine.test_task_engine.addsub",
                "outputs": {"value": "sometype"},
            }
        },
        "graph": {"step1": {"addsub": [1, 2]}},
    }

    dioptra.task_engine.task_engine.run_experiment(desc, {})

    assert _output == (3, -1)


@require_plugins(add, addsub)
def test_task_list_output() -> None:
    desc = {
        "tasks": {
            "addsub": {
                "plugin": "tests.unit.task_engine.test_task_engine.addsub",
                "outputs": [{"sum": "sometype"}, {"diff": "sometype"}],
            },
            "add": {
                "plugin": "tests.unit.task_engine.test_task_engine.add",
                "outputs": {"value": "sometype"},
            },
        },
        "graph": {
            "step1": {"addsub": [1, 2]},
            # Hard to check how the multi-outputs from "addsub" are actually
            # stored without peeking at the task engine's internal bookkeeping,
            # but I can use those outputs in another step... maybe that will
            # work just as well?
            "step2": {"add": ["$step1.sum", "$step1.diff"]},
        },
    }

    dioptra.task_engine.task_engine.run_experiment(desc, {})

    # (a+b) + (a-b) = 2a
    assert _output == 2


@require_plugins(add, addsub, square)
def test_task_dependencies_ambig() -> None:
    desc = {
        "tasks": {
            "add": {
                "plugin": "tests.unit.task_engine.test_task_engine.add",
                "outputs": {"value": "sometype"},
            },
            "square": {
                "plugin": "tests.unit.task_engine.test_task_engine.square",
                "outputs": {"value": "sometype"},
            },
            # Bad name for a plugin.
            "dependencies": {
                "plugin": "tests.unit.task_engine.test_task_engine.addsub"
            },
        },
        "graph": {
            "step1": {
                # Ensure "dependencies" below isn't mistaken for the same-named
                # plugin defined above!
                "dependencies": ["step2"],
                "add": [3, 4],
            },
            "step2": {"square": 6},
        },
    }

    dioptra.task_engine.task_engine.run_experiment(desc, {})

    assert _output == 7


@require_plugins(add, addsub, square)
def test_task_task_ambig() -> None:
    desc = {
        "tasks": {
            "add": {
                "plugin": "tests.unit.task_engine.test_task_engine.add",
                "outputs": {"value": "sometype"},
            },
            "square": {
                "plugin": "tests.unit.task_engine.test_task_engine.square",
                "outputs": {"value": "sometype"},
            },
            # Bad name for a plugin.
            "task": {"plugin": "tests.unit.task_engine.test_task_engine.addsub"},
        },
        "graph": {
            "step1": {
                "dependencies": ["step2"],
                # Ensure "task" below isn't mistaken for the same-named
                # plugin defined above!
                "task": "add",
                "args": [3, 4],
            },
            "step2": {"square": 6},
        },
    }

    dioptra.task_engine.task_engine.run_experiment(desc, {})

    assert _output == 7


@require_plugins(add, square)
def test_step_missing_plugin_name() -> None:
    desc = {
        "tasks": {
            "add": {"plugin": "tests.unit.task_engine.test_task_engine.add"},
            "square": {"plugin": "tests.unit.task_engine.test_task_engine.square"},
        },
        "graph": {
            "step1": {
                # Missing the plugin name here
                "dependencies": ["step2"]
            },
            "step2": {"square": 6},
        },
    }

    with pytest.raises(MissingTaskPluginNameError):
        dioptra.task_engine.task_engine.run_experiment(desc, {})


@require_plugins(add, square)
def test_step_cycle() -> None:
    desc = {
        "tasks": {
            "add": {"plugin": "tests.unit.task_engine.test_task_engine.add"},
            "square": {"plugin": "tests.unit.task_engine.test_task_engine.square"},
        },
        "graph": {
            "step1": {"add": [1, 2, "$step2.value"]},
            "step2": {"square": "$step1.value"},
        },
    }

    with pytest.raises(StepReferenceCycleError) as e:
        dioptra.task_engine.task_engine.run_experiment(desc, {})

    assert "step1" in e.value.cycle
    assert "step2" in e.value.cycle


def test_step_not_found_reference() -> None:
    desc = {
        "tasks": {"add": {"plugin": "tests.unit.task_engine.test_task_engine.add"}},
        "graph": {"step1": {"add": [1, "$foo"]}},
    }

    with pytest.raises(UnresolvableReferenceError) as e:
        dioptra.task_engine.task_engine.run_experiment(desc, {})

    assert e.value.reference_name == "foo"


@require_plugins(add)
def test_step_not_found_dependency() -> None:
    desc = {
        "tasks": {"add": {"plugin": "tests.unit.task_engine.test_task_engine.add"}},
        "graph": {"step1": {"add": [1, 2], "dependencies": ["foo"]}},
    }

    with pytest.raises(StepNotFoundError) as e:
        dioptra.task_engine.task_engine.run_experiment(desc, {})

    assert e.value.step_name == "foo"


@require_plugins(add, square)
def test_output_not_found_explicit() -> None:
    desc = {
        "tasks": {
            "add": {
                "plugin": "tests.unit.task_engine.test_task_engine.add",
                "outputs": {"value": "sometype"},
            },
            "square": {"plugin": "tests.unit.task_engine.test_task_engine.square"},
        },
        "graph": {"step1": {"add": [1, 2]}, "step2": {"square": "$step1.foo"}},
    }

    with pytest.raises(OutputNotFoundError) as e:
        dioptra.task_engine.task_engine.run_experiment(desc, {})

    assert e.value.step_name == "step1"
    assert e.value.output_name == "foo"


@require_plugins(add, square)
def test_output_not_found_implicit() -> None:
    desc = {
        "tasks": {
            "add": {"plugin": "tests.unit.task_engine.test_task_engine.add"},
            "square": {"plugin": "tests.unit.task_engine.test_task_engine.square"},
        },
        "graph": {
            "step1": {"add": [1, 2]},
            "step2": {
                # error because plugin "add" did not define any outputs
                "square": "$step1"
            },
        },
    }

    with pytest.raises(UnresolvableReferenceError) as e:
        dioptra.task_engine.task_engine.run_experiment(desc, {})

    assert e.value.reference_name == "step1"


@require_plugins(addsub, square)
def test_output_reference_ambig() -> None:
    desc = {
        "tasks": {
            "addsub": {
                "plugin": "tests.unit.task_engine.test_task_engine.addsub",
                "outputs": ["sum", "diff"],
            },
            "square": {"plugin": "tests.unit.task_engine.test_task_engine.square"},
        },
        "graph": {
            "step1": {"addsub": [1, 2]},
            "step2": {
                # error because plugin "addsub" defines two outputs, so this
                # reference is ambiguous.  It needs to pick one of them.
                "square": "$step1"
            },
        },
    }

    with pytest.raises(IllegalOutputReferenceError) as e:
        dioptra.task_engine.task_engine.run_experiment(desc, {})

    assert e.value.context_step_name == "step2"
    assert e.value.step_name == "step1"


@require_plugins(add)
def test_output_not_iterable() -> None:
    desc = {
        "tasks": {
            "add": {
                "plugin": "tests.unit.task_engine.test_task_engine.add",
                # error: integer addition produces an integer, which is not
                # iterable.
                "outputs": ["value"],
            }
        },
        "graph": {"step1": {"add": [1, 2]}},
    }

    with pytest.raises(NonIterableTaskOutputError) as e:
        dioptra.task_engine.task_engine.run_experiment(desc, {})

    assert e.value.value == 3


def test_illegal_plugin_name() -> None:
    desc = {"tasks": {"add": {"plugin": "foo"}}, "graph": {"step1": {"add": [1, 2]}}}

    with pytest.raises(IllegalPluginNameError) as e:
        dioptra.task_engine.task_engine.run_experiment(desc, {})

    assert e.value.plugin_name == "foo"
