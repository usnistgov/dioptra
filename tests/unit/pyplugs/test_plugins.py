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
# https://github.com/gahjelle/pyplugs/blob/6921de46a2158462dc07c2f013155b53fbcebebb/tests/test_plugins.py  # noqa: B950
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
"""Tests for Pyplugs

Based on the Pytest test runner
"""
import importlib
import pathlib
import sys

import pytest
from prefect import Flow

from dioptra import pyplugs
from dioptra.sdk.exceptions import (
    UnknownPackageError,
    UnknownPluginError,
    UnknownPluginFunctionError,
)


@pytest.fixture
def tmpfile(tmpdir):
    """A temporary file that can be read"""
    file_path = tmpdir.join("test")
    file_path.write("Temporary test file")

    return file_path


@pytest.fixture
def plugin_package():
    """Name of the test plugin package"""
    plugins_dir = pathlib.Path(__file__).absolute().parent / "plugin_directory"
    relative = plugins_dir.relative_to(pathlib.Path.cwd())

    return ".".join(relative.parts)


@pytest.fixture
def pyplugs_no_prefect(monkeypatch):
    package_modules = [x for x in sys.modules.keys() if "dioptra" in x]
    prefect_modules = [x for x in sys.modules.keys() if "prefect" in x]

    for module in package_modules + prefect_modules:
        monkeypatch.delitem(sys.modules, module)

    monkeypatch.setitem(sys.modules, "prefect", None)

    return (
        importlib.import_module("dioptra.pyplugs"),
        importlib.import_module("dioptra.sdk.exceptions"),
    )


def test_package_not_empty(plugin_package):
    """Test that names() finds some plugins in package"""
    plugins = pyplugs.names(plugin_package)
    assert len(plugins) > 0


def test_package_empty():
    """Test that names() does not find plugins in the dioptra.pyplugs
    package.
    """
    lib_plugins = pyplugs.names("dioptra.pyplugs")
    assert len(lib_plugins) == 0


def test_list_funcs(plugin_package):
    """Test that funcs() finds some plugins in package"""
    plugins = pyplugs.funcs(plugin_package, "plugin_parts")
    assert len(plugins) == 3


def test_package_non_existing():
    """Test that a non-existent package raises an appropriate error"""
    with pytest.raises(UnknownPackageError):
        pyplugs.names("dioptra.pyplugs.non_existent")


def test_plugin_exists(plugin_package):
    """Test that an existing plugin returns its own plugin name"""
    plugin_name = pyplugs.names(plugin_package)[0]
    assert pyplugs.info(plugin_package, plugin_name).plugin_name == plugin_name


@pytest.mark.parametrize("plugin_name", ["no_plugins", "non_existent"])
def test_plugin_not_exists(plugin_package, plugin_name):
    """Test that a non-existing plugin raises UnknownPluginError

    Tests both for an existing module (no_plugins) and a non-existent module
    (non_existent).
    """
    with pytest.raises(UnknownPluginError):
        pyplugs.info(plugin_package, plugin_name)


@pytest.mark.parametrize("task_func_name", ["get_task", "call_task"])
def test_prefect_dependency_not_installed(
    pyplugs_no_prefect, plugin_package, task_func_name
):
    plugin_name = "plugin_plain"
    pyplugs, exceptions = pyplugs_no_prefect
    task_func = getattr(pyplugs, task_func_name)

    with pytest.raises(exceptions.PrefectDependencyError):
        task_func(plugin_package, plugin=plugin_name)


@pytest.mark.parametrize("task_factory_name", ["get_task_factory", "call_task_factory"])
def test_factory_prefect_dependency_not_installed(
    pyplugs_no_prefect, plugin_package, task_factory_name
):
    pyplugs, exceptions = pyplugs_no_prefect
    task_factory_func = getattr(pyplugs, task_factory_name)

    with pytest.raises(exceptions.PrefectDependencyError):
        task_factory_func(plugin_package)


def test_exists(plugin_package):
    """Test that exists() function correctly identifies existing plugins"""
    assert pyplugs.exists(plugin_package, "plugin_parts") is True
    assert pyplugs.exists(plugin_package, "no_plugins") is False
    assert pyplugs.exists(plugin_package, "non_existent") is False


def test_exists_on_non_existing_package():
    """Test that exists() correctly returns False for non-existing packages"""
    assert pyplugs.exists("non_existent_package", "plugin_parts") is False
    assert pyplugs.exists("non_existent_package", "non_existent") is False


def test_call_existing_plugin(plugin_package):
    """Test that calling a test-plugin works, and returns a string"""
    plugin_name = pyplugs.names(plugin_package)[0]
    return_value = pyplugs.call(plugin_package, plugin_name)
    assert isinstance(return_value, str)


def test_call_non_existing_plugin():
    """Test that calling a non-existing plugin raises an error"""
    with pytest.raises(UnknownPluginError):
        pyplugs.call("dioptra.pyplugs", "non_existent")


def test_ordered_plugin(plugin_package):
    """Test that order of plugins can be customized"""
    plugin_names = pyplugs.names(plugin_package)
    assert plugin_names[0] == "plugin_first"
    assert plugin_names[-1] == "plugin_last"


def test_default_part(plugin_package):
    """Test that first registered function in a plugin is called by default"""
    plugin_name = "plugin_parts"
    default = pyplugs.call(plugin_package, plugin_name)
    explicit = pyplugs.call(plugin_package, plugin_name, func="plugin_default")
    assert default == explicit


def test_call_non_existing_func(plugin_package):
    """Test that calling a non-existing plug-in function raises an error"""
    plugin_name = "plugin_parts"
    func_name = "non_existent"
    with pytest.raises(UnknownPluginFunctionError):
        pyplugs.call(plugin_package, plugin_name, func=func_name)


def test_short_doc(plugin_package):
    """Test that we can retrieve the short docstring from a plugin"""
    plugin_name = "plugin_plain"
    doc = pyplugs.info(plugin_package, plugin_name).description
    assert doc == "A plain plugin"


def test_long_doc(plugin_package):
    """Test that we can retrieve the long docstring from a plugin"""
    plugin_name = "plugin_plain"
    doc = pyplugs.info(plugin_package, plugin_name).doc
    assert doc == "This is the plain docstring."


def test_names_factory(plugin_package):
    """Test that the names factory can retrieve names in package"""
    names = pyplugs.names_factory(plugin_package)
    factory_names = names()
    pyplugs_names = pyplugs.names(plugin_package)
    assert factory_names == pyplugs_names


def test_funcs_factory(plugin_package):
    """Test that the funcs factory can retrieve funcs within plugin"""
    plugin_name = "plugin_parts"
    funcs = pyplugs.funcs_factory(plugin_package)
    factory_funcs = funcs(plugin_name)
    pyplugs_funcs = pyplugs.funcs(plugin_package, plugin_name)
    assert factory_funcs == pyplugs_funcs


def test_info_factory(plugin_package):
    """Test that the info factory can retrieve info in package"""
    plugin_name = "plugin_parts"
    info = pyplugs.info_factory(plugin_package)
    factory_info = info(plugin_name)
    pyplugs_info = pyplugs.info(plugin_package, plugin=plugin_name)
    assert factory_info == pyplugs_info


def test_exists_factory(plugin_package):
    """Test that the exists factory can check for plugins in a package"""
    exists = pyplugs.exists_factory(plugin_package)
    assert exists("plugin_parts") is True
    assert exists("no_plugins") is False
    assert exists("non_existent") is False


def test_get_factory(plugin_package):
    """Test that the get factory can retrieve get in package"""
    plugin_name = "plugin_parts"
    get = pyplugs.get_factory(plugin_package)
    factory_get = get(plugin_name)
    pyplugs_get = pyplugs.get(plugin_package, plugin=plugin_name)
    assert factory_get == pyplugs_get


def test_call_factory(plugin_package):
    """Test that the call factory can retrieve call in package"""
    plugin_name = "plugin_parts"
    call = pyplugs.call_factory(plugin_package)
    factory_call = call(plugin_name)
    pyplugs_call = pyplugs.call(plugin_package, plugin=plugin_name)
    assert factory_call == pyplugs_call


def test_get_task_factory(plugin_package):
    """Test that the get task factory can retrieve a task get in package"""
    plugin_name = "plugin_parts"
    get_task = pyplugs.get_task_factory(plugin_package)

    with Flow("Test Get Task Factory") as flow:  # noqa: F841
        factory_get_task = get_task(plugin_name)
        pyplugs_get_task = pyplugs.get_task(plugin_package, plugin=plugin_name)
        assert factory_get_task.is_equal(pyplugs_get_task)


def test_call_task_factory(plugin_package):
    """Test that the call task factory can retrieve a task call in package"""
    plugin_name = "plugin_parts"
    call_task = pyplugs.call_task_factory(plugin_package)

    with Flow("Test Call Task Factory") as flow:
        factory_call_task = call_task(plugin_name)
        pyplugs_call_task = pyplugs.call_task(plugin_package, plugin=plugin_name)

    state = flow.run()
    assert (
        state.result[factory_call_task].result == state.result[pyplugs_call_task].result
    )


def test_call_tasks_with_nout(plugin_package):
    """Test that the task_nout decorator handles multiple argument returns in prefect
    tasks.
    """
    plugin_name = "plugin_task_nout"
    call_task = pyplugs.call_task_factory(plugin_package)

    with Flow("Test Call Task with nout") as flow:
        factory_result_1, factory_result_2 = call_task(
            plugin_name, func="plugin_with_nout"
        )
        pyplugs_result_1, pyplugs_result_2 = pyplugs.call_task(
            plugin_package, plugin=plugin_name, func="plugin_with_nout"
        )

    state = flow.run()
    assert (
        state.result[factory_result_1].result == state.result[pyplugs_result_1].result
    )
    assert (
        state.result[factory_result_2].result == state.result[pyplugs_result_2].result
    )


def test_call_tasks_without_nout(plugin_package):
    """Test that omitting the task_nout decorator is not compatible with multiple
    argument returns in prefect tasks.
    """
    plugin_name = "plugin_task_nout"

    with pytest.raises(TypeError):
        with Flow("Test Call Task without nout") as flow:
            result_1, result_2 = pyplugs.call_task(
                plugin_package, plugin=plugin_name, func="plugin_without_nout"
            )

            _ = flow.run()
