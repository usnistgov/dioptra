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
from pathlib import Path
from typing import Any, Final, cast

import structlog
import yaml
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import models
from dioptra.task_engine.type_registry import BUILTIN_TYPES

from .type_coercions import (
    BOOLEAN_PARAM_TYPE,
    FLOAT_PARAM_TYPE,
    INTEGER_PARAM_TYPE,
    STRING_PARAM_TYPE,
    coerce_to_type,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()

EXPLICIT_GLOBAL_TYPES: Final[set[str]] = {
    STRING_PARAM_TYPE,
    BOOLEAN_PARAM_TYPE,
    INTEGER_PARAM_TYPE,
    FLOAT_PARAM_TYPE,
}
YAML_FILE_ENCODING: Final[str] = "utf-8"
YAML_EXPORT_SETTINGS: Final[dict[str, Any]] = {
    "indent": 2,
    "sort_keys": False,
    "encoding": YAML_FILE_ENCODING,
}


def export_task_engine_yaml(
    entrypoint: models.EntryPoint,
    entry_point_plugin_files: list[models.EntryPointPluginFile],
    plugin_parameter_types: list[models.PluginTaskParameterType],
    base_dir: Path,
    logger: BoundLogger | None = None,
) -> Path:
    """Export an entrypoint's task engine YAML file to a specified directory.

    Args:
        entrypoint: The entrypoint to export.
        entry_point_plugin_files: The entrypoint's plugin files.
        plugin_parameter_types: The latest snapshots of the plugin parameter types
            accessible to the entrypoint.
        base_dir: The directory to export the task engine YAML file to.
        logger: A structlog logger object to use for logging. A new logger will be
            created if None.

    Returns:
        The path to the exported task engine YAML file.
    """
    log = logger or LOGGER.new()  # noqa: F841
    task_yaml_path = Path(base_dir, entrypoint.name).with_suffix(".yml")
    task_engine_dict = build_task_engine_dict(
        entrypoint=entrypoint,
        entry_point_plugin_files=entry_point_plugin_files,
        plugin_parameter_types=plugin_parameter_types,
    )

    with task_yaml_path.open("wt", encoding=YAML_FILE_ENCODING) as f:
        yaml.safe_dump(task_engine_dict, f, **YAML_EXPORT_SETTINGS)

    return task_yaml_path


def build_task_engine_dict(
    entrypoint: models.EntryPoint,
    entry_point_plugin_files: list[models.EntryPointPluginFile],
    plugin_parameter_types: list[models.PluginTaskParameterType],
    logger: BoundLogger | None = None,
) -> dict[str, Any]:
    """Build a dictionary representation of a task engine YAML file.

    Args:
        entrypoint: The entrypoint to export.
        entry_point_plugin_files: The entrypoint's plugin files.
        plugin_parameter_types: The latest snapshots of the plugin parameter types
            accessible to the entrypoint.
        logger: A structlog logger object to use for logging. A new logger will be
            created if None.

    Returns:
        A dictionary representation of a task engine YAML file.
    """
    log = logger or LOGGER.new()  # noqa: F841
    tasks, parameter_types = extract_tasks(
        entry_point_plugin_files, plugin_parameter_types=plugin_parameter_types
    )
    parameters = extract_parameters(entrypoint)
    graph = extract_graph(entrypoint)
    return {
        "types": parameter_types,
        "parameters": parameters,
        "tasks": tasks,
        "graph": graph,
    }


def extract_parameters(
    entrypoint: models.EntryPoint,
    logger: BoundLogger | None = None,
) -> dict[str, Any]:
    """Extract the parameters from an entrypoint.

    Args:
        entrypoint: The entrypoint to extract parameters from.
        logger: A structlog logger object to use for logging. A new logger will be
            created if None.

    Returns:
        A dictionary of the entrypoint's parameters.
    """
    log = logger or LOGGER.new()  # noqa: F841
    parameters: dict[str, Any] = {}
    for param in entrypoint.parameters:
        default_value = param.default_value
        parameters[param.name] = {
            "default": coerce_to_type(x=default_value, type_name=param.parameter_type)
        }

        if param.parameter_type in EXPLICIT_GLOBAL_TYPES:
            parameters[param.name]["type"] = (
                _convert_parameter_type_to_task_engine_type(param.parameter_type)
            )

    return parameters


def extract_tasks(
    entry_point_plugin_files: list[models.EntryPointPluginFile],
    plugin_parameter_types: list[models.PluginTaskParameterType],
    logger: BoundLogger | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Extract the plugin tasks and parameter types from the entrypoint plugin files.

    Args:
        entry_point_plugin_files: The entrypoint's plugin files.
        plugin_parameter_types: The latest snapshots of the plugin parameter types
            accessible to the entrypoint.
        logger: A structlog logger object to use for logging. A new logger will be
            created if None.

    Returns:
        A tuple containing the plugin tasks dictionary and the parameter types
        dictionary.
    """
    log = logger or LOGGER.new()  # noqa: F841

    tasks: dict[str, Any] = {}
    parameter_types: dict[str, Any] = {}
    for entry_point_plugin_file in entry_point_plugin_files:
        plugin = entry_point_plugin_file.plugin
        plugin_file = entry_point_plugin_file.plugin_file

        for task in plugin_file.tasks:
            input_parameters = sorted(
                task.input_parameters, key=lambda x: x.parameter_number
            )
            output_parameters = sorted(
                task.output_parameters, key=lambda x: x.parameter_number
            )

            tasks[task.plugin_task_name] = {
                "plugin": _build_plugin_field(plugin, plugin_file, task),
            }
            if input_parameters:
                tasks[task.plugin_task_name]["inputs"] = _build_task_inputs(
                    input_parameters
                )

            if output_parameters:
                tasks[task.plugin_task_name]["outputs"] = _build_task_outputs(
                    output_parameters
                )

            for param in input_parameters + output_parameters:
                name = param.parameter_type.name
                if name not in BUILTIN_TYPES:
                    parameter_types[name] = param.parameter_type.structure

            # HACK: THIS IS A WORKAROUND THAT VIOLATES IDEMPOTENCE/REPRODUCIBILITY!
            #
            # This workaround allows users to create and use parameter types that are
            # only used indirectly, such as when defining a structured parameter type.
            # This is a "hack" because the objects in `plugin_parameter_types` are the
            # latest available snapshots, not the snapshots that were associated with
            # the plugins when the entrypoint was saved/updated. This is in contrast
            # with the parameter types accumulated in the previous for loop block, which
            # are linked to the entrypoint and job by their snapshot id instead of the
            # resource id. This difference means that the task engine YAML files are not
            # 100% reproducible, as any changes to an "indirect" plugin parameter type
            # will be immediately reflected in subsequent download requests made to the
            # job files workflow.
            for parameter_type in plugin_parameter_types:
                name = parameter_type.name
                if name not in BUILTIN_TYPES and name not in parameter_types:
                    parameter_types[name] = parameter_type.structure

    return tasks, parameter_types


def extract_graph(
    entrypoint: models.EntryPoint,
    logger: BoundLogger | None = None,
) -> dict[str, Any]:
    """Extract the task graph from an entrypoint.

    Args:
        entrypoint: The entrypoint containing the task graph.
        logger: A structlog logger object to use for logging. A new logger will be
            created if None.

    Returns:
        A dictionary representation of the entrypoint's task graph.
    """
    log = logger or LOGGER.new()  # noqa: F841
    return cast(dict[str, Any], yaml.safe_load(entrypoint.task_graph))


def _build_plugin_field(
    plugin: models.Plugin, plugin_file: models.PluginFile, task: models.PluginTask
) -> str:
    if plugin_file.filename == "__init__.py":
        # Omit filename from plugin import path if it is an __init__.py file.
        module_parts = [Path(x).stem for x in Path(plugin_file.filename).parts[:-1]]

    else:
        module_parts = [Path(x).stem for x in Path(plugin_file.filename).parts]

    return ".".join([plugin.name, *module_parts, task.plugin_task_name])


def _build_task_inputs(
    input_parameters: list[models.PluginTaskInputParameter],
) -> list[dict[str, Any]]:
    return [
        {
            "name": input_param.name,
            "type": input_param.parameter_type.name,
            "required": input_param.required,
        }
        for input_param in input_parameters
    ]


def _build_task_outputs(
    output_parameters: list[models.PluginTaskOutputParameter],
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
