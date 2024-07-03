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

LOGGER: BoundLogger = structlog.stdlib.get_logger()

YAML_FILE_ENCODING: Final[str] = "utf-8"
YAML_EXPORT_SETTINGS: Final[dict[str, Any]] = {
    "indent": 2,
    "sort_keys": False,
    "encoding": YAML_FILE_ENCODING,
}


def export_task_engine_yaml(
    entrypoint: models.EntryPoint,
    entry_point_plugin_files: list[models.EntryPointPluginFile],
    base_dir: Path,
    logger: BoundLogger | None = None,
) -> Path:
    """Export an entrypoint's task engine YAML file to a specified directory.

    Args:
        entrypoint: The entrypoint to export.
        entry_point_plugin_files: The entrypoint's plugin files.
        base_dir: The directory to export the task engine YAML file to.
        logger: A structlog logger object to use for logging. A new logger will be
            created if None.

    Returns:
        The path to the exported task engine YAML file.
    """
    log = logger or LOGGER.new()  # noqa: F841
    task_yaml_path = Path(base_dir, entrypoint.name).with_suffix(".yml")
    task_engine_dict = build_task_engine_dict(
        entrypoint=entrypoint, entry_point_plugin_files=entry_point_plugin_files
    )

    with task_yaml_path.open("wt", encoding=YAML_FILE_ENCODING) as f:
        yaml.safe_dump(task_engine_dict, f, **YAML_EXPORT_SETTINGS)

    return task_yaml_path


def build_task_engine_dict(
    entrypoint: models.EntryPoint,
    entry_point_plugin_files: list[models.EntryPointPluginFile],
    logger: BoundLogger | None = None,
) -> dict[str, Any]:
    """Build a dictionary representation of a task engine YAML file.

    Args:
        entrypoint: The entrypoint to export.
        entry_point_plugin_files: The entrypoint's plugin files.
        logger: A structlog logger object to use for logging. A new logger will be
            created if None.

    Returns:
        A dictionary representation of a task engine YAML file.
    """
    log = logger or LOGGER.new()  # noqa: F841
    tasks, parameter_types = extract_tasks(entry_point_plugin_files)
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
    return {param.name: param.default_value for param in entrypoint.parameters}


def extract_tasks(
    entry_point_plugin_files: list[models.EntryPointPluginFile],
    logger: BoundLogger | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Extract the plugin tasks and parameter types from the entrypoint plugin files.

    Args:
        entry_point_plugin_files: The entrypoint's plugin files.
        logger: A structlog logger object to use for logging. A new logger will be
            created if None.

    Returns:
        A tuple containing the plugin tasks dictionary and the parameter types
        dictionary.
    """
    log = logger or LOGGER.new()  # noqa: F841

    tasks = {}
    parameter_types = {}
    for entry_point_plugin_file in entry_point_plugin_files:
        plugin = entry_point_plugin_file.plugin
        plugin_file = entry_point_plugin_file.plugin_file

        for task in plugin_file.tasks:
            input_parameters = task.input_parameters
            output_parameters = task.output_parameters

            # TODO: Handle case where user puts a plugin task in an __init__.py file.
            tasks[task.plugin_task_name] = {
                "plugin": ".".join(
                    [
                        plugin.name,
                        *[Path(x).stem for x in Path(plugin_file.filename).parts],
                        task.plugin_task_name,
                    ]
                ),
                "inputs": [
                    {
                        "name": input_param.name,
                        "type": input_param.parameter_type.name,
                        "required": input_param.required,
                    }
                    for input_param in input_parameters
                ],
                "outputs": [
                    {output_param.name: output_param.parameter_type.name}
                    for output_param in output_parameters
                ],
            }

            for param in input_parameters + output_parameters:
                name = param.parameter_type.name
                if name not in BUILTIN_TYPES:
                    parameter_types[name] = param.parameter_type.structure

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