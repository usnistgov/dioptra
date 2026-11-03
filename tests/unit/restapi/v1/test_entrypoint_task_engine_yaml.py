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
"""Tests for task-engine YAML generation of entrypoint global parameters."""

from dataclasses import dataclass

from dioptra.restapi.v1.entrypoints.task_engine_yaml import build_task_engine_dict
from dioptra.task_engine.validation import is_valid


@dataclass
class _FakeEntryPointParameter:
    parameter_type: str
    name: str
    default_value: str | None


@dataclass
class _FakeEntryPoint:
    parameters: list[_FakeEntryPointParameter]
    artifact_parameters: tuple = ()
    task_graph: str = ""
    artifact_graph: str = ""


def _build_parameters(parameters):
    config = build_task_engine_dict(
        entry_point=_FakeEntryPoint(parameters=parameters),
        plugin_plugin_files=[],
        plugin_parameter_types=[],
        sections=["parameters"],
    )
    return config["parameters"]


def test_list_parameter_without_default_gets_explicit_type():
    parameters = _build_parameters(
        [
            _FakeEntryPointParameter(
                parameter_type="list", name="options", default_value=None
            )
        ]
    )

    assert parameters == {"options": {"type": "list"}}


def test_mapping_parameter_without_default_gets_explicit_type():
    parameters = _build_parameters(
        [
            _FakeEntryPointParameter(
                parameter_type="mapping", name="options", default_value=None
            )
        ]
    )

    assert parameters == {"options": {"type": "mapping"}}


def test_list_parameter_with_default_keeps_default_and_type():
    parameters = _build_parameters(
        [
            _FakeEntryPointParameter(
                parameter_type="list",
                name="selections",
                default_value='["a", "b"]',
            )
        ]
    )

    assert parameters == {"selections": {"default": ["a", "b"], "type": "list"}}


def test_mapping_parameter_with_default_keeps_default_and_type():
    parameters = _build_parameters(
        [
            _FakeEntryPointParameter(
                parameter_type="mapping",
                name="options",
                default_value='{"a": 1}',
            )
        ]
    )

    assert parameters == {"options": {"default": {"a": 1}, "type": "mapping"}}


def test_scalar_parameter_behavior_unchanged():
    parameters = _build_parameters(
        [
            _FakeEntryPointParameter(
                parameter_type="string", name="greeting", default_value="hello"
            ),
            _FakeEntryPointParameter(
                parameter_type="integer", name="count", default_value=None
            ),
        ]
    )

    assert parameters == {
        "greeting": {"default": "hello", "type": "string"},
        "count": {"type": "integer"},
    }


def test_required_list_and_mapping_parameters_produce_valid_task_engine_yaml():
    parameters = _build_parameters(
        [
            _FakeEntryPointParameter(
                parameter_type="list", name="selections", default_value=None
            ),
            _FakeEntryPointParameter(
                parameter_type="mapping", name="options", default_value=None
            ),
        ]
    )

    experiment_desc = {
        "parameters": parameters,
        "tasks": {
            "foo": {
                "plugin": "org.example.foo",
                "inputs": [{"n1": "any"}, {"n2": "any"}],
            }
        },
        "graph": {"step1": {"foo": ["$selections", "$options"]}},
    }

    assert is_valid(experiment_desc)
