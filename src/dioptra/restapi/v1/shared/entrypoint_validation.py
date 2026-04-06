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
"""Service for building entrypoint data adapters for validation."""

from dataclasses import dataclass
from structlog.stdlib import BoundLogger
from typing import Any

from dioptra.restapi.db import models
from dioptra.restapi.v1.plugin_parameter_types.service import get_plugin_task_parameter_types_by_id

@dataclass
class EntryPointParameterDataAdapter(object):
    """Data adapter for entrypoint parameters."""
    parameter_type: str
    name: str
    default_value: str | None

@dataclass
class TaskOutputParameterDataAdapter(object):
    """Data adapter for task output parameters."""
    parameter_number: int
    name: str
    parameter_type: models.PluginTaskParameterType

@dataclass
class EntryPointArtifactDataAdapter(object):
    """Data adapter for entrypoint artifacts."""
    name: str
    output_parameters: list[TaskOutputParameterDataAdapter]

@dataclass
class EntryPointDataAdapter(object):
    """Data adapter for entrypoint data."""
    task_graph: str
    artifact_graph: str
    parameters: list[EntryPointParameterDataAdapter]
    artifact_parameters: list[EntryPointArtifactDataAdapter]

def build_entrypoint_data_adapter(
    task_graph: str,
    artifact_graph: str,
    entrypoint_parameters: list[dict[str, Any]],
    entrypoint_artifacts: list[dict[str, Any]],
    log: BoundLogger,
) -> EntryPointDataAdapter:
    """Build an EntryPointDataAdapter from an entrypoint model.

    Args:
        entrypoint: The entrypoint model to adapt
        task_graph: The task graph YAML string to use

    Returns:
        An EntryPointDataAdapter instance
    """

    type_ids = [
        parameter["parameter_type_id"]
        for artifact in entrypoint_artifacts
        for parameter in artifact["output_params"]
    ]
    
    id_type_map = get_plugin_task_parameter_types_by_id(ids=type_ids, log=log)

    return EntryPointDataAdapter(
        task_graph=task_graph,
        artifact_graph=artifact_graph,
        parameters=[
            EntryPointParameterDataAdapter(
                parameter_type=param["parameter_type"],
                name=param["name"],
                default_value=param["default_value"],
            )
            for param in entrypoint_parameters
        ],
        artifact_parameters=[
            EntryPointArtifactDataAdapter(
                name=artifact["name"],
                output_parameters=[
                    TaskOutputParameterDataAdapter(
                        name=param["name"],
                        parameter_number=p,
                        parameter_type=id_type_map[param["parameter_type_id"]],
                    )
                    for p, param in enumerate(artifact["output_params"])
                ],
            )
            for artifact in entrypoint_artifacts
        ],
    )
