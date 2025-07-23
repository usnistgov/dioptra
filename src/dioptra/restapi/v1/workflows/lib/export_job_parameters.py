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
from typing import Any

import structlog
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import models
from dioptra.restapi.v1.type_coercions import GlobalParameterType, coerce_to_type

LOGGER: BoundLogger = structlog.stdlib.get_logger()


def build_job_parameters_dict(
    job_param_values: list[models.EntryPointParameterValue],
    logger: BoundLogger | None = None,
) -> dict[str, GlobalParameterType]:
    """Builds a dict of a job's parameters coerce types as appropriate.

    Args:
        job_param_values: the list of EntryPointParameterValues.
        logger: A structlog logger object to use for logging. A new logger will be
            created if None.

    Returns:
        The a dict of the names of the parameters mapped to their type.
    """
    log = logger or LOGGER.new()  # noqa: F841

    job_parameters: dict[str, GlobalParameterType] = {}
    for param_value in job_param_values:
        value = coerce_to_type(
            x=param_value.value,
            type_name=param_value.parameter.parameter_type,
        )
        job_parameters[param_value.parameter.name] = value
    return job_parameters


def build_job_artifacts_dict(
    job_artifact_values: list[models.EntryPointArtifactParameterValue],
    logger: BoundLogger | None = None,
) -> dict[str, dict[str, Any]]:
    """Builds a dict of a job's parameters coerce types as appropriate.

    Args:
        values: a list of EntryPointArtifactValue instances.
        logger: A structlog logger object to use for logging. A new logger will be
            created if None.

    Returns:
        The a dict of the names of the parameters mapped to their type.
    """
    log = logger or LOGGER.new()  # noqa: F841

    artifacts: dict[str, dict[str, Any]] = {}
    for value in job_artifact_values:
        artifacts[value.artifact_parameter.name] = {
            "artifact_id": value.artifact.resource_id,
            "artifact_snapshot_id": value.artifact.resource_snapshot_id,
            "is_dir": value.artifact.is_dir,
            "artifact_task": {
                "plugin_id": value.artifact.plugin_plugin_file.plugin.resource_id,
                "plugin_name": value.artifact.plugin_plugin_file.plugin.name,
                "plugin_snapshot_id": value.artifact.plugin_snapshot_id,
                "file_name": value.artifact.plugin_plugin_file.plugin_file.filename,
                "task_name": value.artifact.task_name,
                "outputs": [
                    {"name": param.name, "type": param.parameter_type.name}
                    for param in value.artifact.task.output_parameters
                ],
            },
        }

    return artifacts
