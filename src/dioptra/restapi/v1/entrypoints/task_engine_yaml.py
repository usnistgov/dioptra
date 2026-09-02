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
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Final, cast

import yaml
from yaml.parser import ParserError
from yaml.scanner import ScannerError

from dioptra.restapi.db.models.artifacts import ArtifactTask
from dioptra.restapi.errors import (
    EntrypointParameterTypeMismatchError,
    InvalidYamlError,
)
from dioptra.restapi.v1.entrypoints.protocols import (
    EntryPointArtifactParameterProtocol,
    EntryPointParameterProtocol,
    EntryPointProtocol,
    PluginFileProtocol,
    PluginPluginFileProtocol,
    PluginProtocol,
    PluginTaskInputParameterProtocol,
    PluginTaskOutputParameterProtocol,
    PluginTaskParameterTypeProtocol,
    PluginTaskProtocol,
)
from dioptra.restapi.v1.type_coercions import (
    BOOLEAN_PARAM_TYPE,
    FLOAT_PARAM_TYPE,
    INTEGER_PARAM_TYPE,
    STRING_PARAM_TYPE,
    coerce_to_type,
)
from dioptra.task_engine.type_registry import BUILTIN_TYPES


def coerce_entrypoint_default_param_types(
    parameters: Sequence[EntryPointParameterProtocol],
) -> dict[str, Any]:
    """Coerce entrypoint parameter defaults to their declared types."""
    param_values = []
    param_names = []
    correct_types = []
    params: dict[str, Any] = {}

    for param in parameters:
        default_value = param.default_value
        try:
            if default_value is None:
                params[param.name] = {}
            else:
                params[param.name] = {
                    "default": coerce_to_type(
                        x=default_value,
                        type_name=param.parameter_type,
                    )
                }
        except ValueError:
            param_values.append(default_value)
            param_names.append(param.name)
            correct_types.append(param.parameter_type)

    if param_names:
        raise EntrypointParameterTypeMismatchError(
            values=param_values,
            parameter_names=param_names,
            correct_types=correct_types,
        )

    return params


_EXPLICIT_GLOBAL_TYPES: Final[set[str]] = {
    STRING_PARAM_TYPE,
    BOOLEAN_PARAM_TYPE,
    INTEGER_PARAM_TYPE,
    FLOAT_PARAM_TYPE,
}


def build_task_engine_dict(
    entry_point: EntryPointProtocol,
    plugin_plugin_files: Sequence[PluginPluginFileProtocol],
    plugin_parameter_types: Sequence[PluginTaskParameterTypeProtocol],
    sections: list[str] | None = None,
) -> dict[str, Any]:
    """Build a task-engine configuration from entrypoint and plugin metadata."""
    output = {}
    sections = sections or [
        "types",
        "parameters",
        "tasks",
        "graph",
        "artifact_outputs",
        "artifact_inputs",
    ]

    if {"tasks", "types", "artifact_inputs"} & set(sections):
        tasks, parameter_types = _extract_tasks(
            plugin_plugin_files,
            plugin_parameter_types=plugin_parameter_types,
        )
        _add_artifact_parameter_types(
            entry_point.artifact_parameters,
            parameter_types,
        )

        if "tasks" in sections:
            output["tasks"] = tasks
        if "types" in sections:
            output["types"] = parameter_types
        if "artifact_inputs" in sections:
            output["artifact_inputs"] = _extract_artifact_inputs(
                entry_point.artifact_parameters
            )

    if "parameters" in sections:
        output["parameters"] = _extract_parameters(entry_point)

    if "graph" in sections:
        output["graph"] = _extract_graph(entry_point)

    if "artifact_outputs" in sections:
        output["artifact_outputs"] = _extract_artifact_outputs(entry_point)

    return output


def _add_artifact_parameter_types(
    artifact_parameters: Sequence[EntryPointArtifactParameterProtocol],
    types: dict[str, Any],
) -> None:
    for param in artifact_parameters:
        for output in param.output_parameters:
            name = output.parameter_type.name
            if name not in BUILTIN_TYPES and name not in types:
                types[name] = output.parameter_type.structure


def _extract_parameters(entry_point: EntryPointProtocol) -> dict[str, Any]:
    parameters = coerce_entrypoint_default_param_types(entry_point.parameters)

    for param in entry_point.parameters:
        if param.parameter_type in _EXPLICIT_GLOBAL_TYPES:
            parameters[param.name]["type"] = (
                _convert_parameter_type_to_task_engine_type(param.parameter_type)
            )

    return parameters


def _extract_artifact_inputs(
    artifact_parameters: Sequence[EntryPointArtifactParameterProtocol],
) -> dict[str, Any]:
    return {
        param.name: _build_outputs(param.output_parameters)
        for param in artifact_parameters
    }


def _extract_tasks(
    plugin_plugin_files: Sequence[PluginPluginFileProtocol],
    plugin_parameter_types: Sequence[PluginTaskParameterTypeProtocol],
) -> tuple[dict[str, Any], dict[str, Any]]:
    tasks: dict[str, Any] = {}
    parameter_types: dict[str, Any] = {}
    has_plugin_tasks = False

    for plugin_plugin_file in plugin_plugin_files:
        plugin = plugin_plugin_file.plugin
        plugin_file = plugin_plugin_file.plugin_file

        for task in plugin_file.tasks:
            if isinstance(task, ArtifactTask):
                continue

            has_plugin_tasks = True
            input_parameters = sorted(
                task.input_parameters,
                key=lambda x: x.parameter_number,
            )
            output_parameters = sorted(
                task.output_parameters,
                key=lambda x: x.parameter_number,
            )

            tasks[task.plugin_task_name] = {
                "plugin": _build_plugin_field(plugin, plugin_file, task),
            }
            if input_parameters:
                tasks[task.plugin_task_name]["inputs"] = _build_task_inputs(
                    input_parameters
                )

            if output_parameters:
                tasks[task.plugin_task_name]["outputs"] = _build_outputs(
                    output_parameters
                )

            for param in input_parameters + output_parameters:
                name = param.parameter_type.name
                if name not in BUILTIN_TYPES:
                    parameter_types[name] = param.parameter_type.structure

    if has_plugin_tasks:
        for parameter_type in plugin_parameter_types:
            name = parameter_type.name
            if name not in BUILTIN_TYPES and name not in parameter_types:
                parameter_types[name] = parameter_type.structure

    return tasks, parameter_types


def _extract_graph(entry_point: EntryPointProtocol) -> dict[str, Any]:
    try:
        return cast(dict[str, Any], yaml.safe_load(entry_point.task_graph))
    except (ParserError, ScannerError) as e:
        raise InvalidYamlError(str(e)) from e


def _extract_artifact_outputs(entrypoint: EntryPointProtocol) -> dict[str, Any]:
    full_yaml = yaml.safe_load(entrypoint.artifact_graph)
    if full_yaml is None:
        full_yaml = {}
    return cast(dict[str, Any], full_yaml)


def _build_plugin_field(
    plugin: PluginProtocol,
    plugin_file: PluginFileProtocol,
    task: PluginTaskProtocol,
) -> str:
    if plugin_file.filename == "__init__.py":
        module_parts = [Path(x).stem for x in Path(plugin_file.filename).parts[:-1]]
    else:
        module_parts = [Path(x).stem for x in Path(plugin_file.filename).parts]

    return ".".join([plugin.name, *module_parts, task.plugin_task_name])


def _build_task_inputs(
    input_parameters: Sequence[PluginTaskInputParameterProtocol],
) -> list[dict[str, Any]]:
    return [
        {
            "name": input_param.name,
            "type": input_param.parameter_type.name,
            "required": input_param.required,
        }
        for input_param in input_parameters
    ]


def _build_outputs(
    output_parameters: Sequence[PluginTaskOutputParameterProtocol],
) -> list[dict[str, Any]] | dict[str, Any]:
    if len(output_parameters) == 1:
        return {output_parameters[0].name: output_parameters[0].parameter_type.name}

    return [
        {output_param.name: output_param.parameter_type.name}
        for output_param in output_parameters
    ]


def _convert_parameter_type_to_task_engine_type(parameter_type: str) -> Any:
    conversion_map = {
        "boolean": "boolean",
        "string": "string",
        "float": "number",
        "integer": "integer",
        "list": {"list": "any"},
        "mapping": {"mapping": ["string", "any"]},
    }
    return conversion_map[parameter_type]
