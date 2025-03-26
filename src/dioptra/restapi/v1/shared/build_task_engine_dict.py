from pathlib import Path
from typing import Any, cast

import structlog
import yaml
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import models
from dioptra.restapi.v1 import utils
from dioptra.task_engine.type_registry import BUILTIN_TYPES

LOGGER: BoundLogger = structlog.stdlib.get_logger()


def build_task_engine_dict(
    plugins: list[utils.PluginWithFilesDict],
    parameters: dict[str, Any],
    task_graph: str,
) -> dict[str, Any]:
    """Build a dictionary representation of a task engine YAML file.

    Args:
        plugins: The entrypoint's plugin files.
        parameters: The entrypoint parameteres.
        task_graph: The task graph of the entrypoint.

    Returns:
        The task engine dictionary.
    """
    tasks: dict[str, Any] = {}
    parameter_types: dict[str, Any] = {}
    for plugin in plugins:
        for plugin_file in plugin["plugin_files"]:
            for task in plugin_file.tasks:
                input_parameters = task.input_parameters
                output_parameters = task.output_parameters
                tasks[task.plugin_task_name] = {
                    "plugin": _build_plugin_field(plugin["plugin"], plugin_file, task),
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

    task_engine_dict = {
        "types": parameter_types,
        "parameters": parameters,
        "tasks": tasks,
        "graph": cast(dict[str, Any], yaml.safe_load(task_graph)),
    }
    return task_engine_dict


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
