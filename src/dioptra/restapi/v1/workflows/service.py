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
"""The server-side functions that perform workflows endpoint operations."""
from typing import IO, Final, Any, cast

import structlog
from structlog.stdlib import BoundLogger
from injector import inject
import yaml

from .lib import views
from .lib.package_job_files import package_job_files
from .schema import FileTypes

LOGGER: BoundLogger = structlog.stdlib.get_logger()

RESOURCE_TYPE: Final[str] = "workflow"

from dioptra.restapi.db import db
from dioptra.restapi.errors import EntrpointWorkflowYamlValidationError
from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.plugins.service import PluginIdFileService, PluginIdsService
from dioptra.task_engine.type_registry import BUILTIN_TYPES
from dioptra.restapi.v1.workflows.lib.export_task_engine_yaml import extract_tasks
from dioptra.task_engine.validation import (
    validate, 
    is_valid,
)
from dioptra.restapi.v1.workflows.lib.export_task_engine_yaml import (
    _build_plugin_field,
    _build_task_inputs,
    _build_task_outputs,
)


class JobFilesDownloadService(object):
    """The service methods for packaging job files for download."""

    def get(self, job_id: int, file_type: FileTypes, **kwargs) -> IO[bytes]:
        """Get the files needed to run a job and package them for download.

        Args:
            job_id: The identifier of the job.
            file_type: The type of file to package the job files into. Must be one of
                the values in the FileTypes enum.

        Returns:
            The packaged job files returned as a named temporary file.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get job files download", job_id=job_id, file_type=file_type)

        experiment = views.get_experiment(job_id=job_id, logger=log)
        entry_point = views.get_entry_point(job_id=job_id, logger=log)
        entry_point_plugin_files = views.get_entry_point_plugin_files(
            job_id=job_id, logger=log
        )
        job_parameter_values = views.get_job_parameter_values(job_id=job_id, logger=log)
        plugin_parameter_types = views.get_plugin_parameter_types(
            job_id=job_id, logger=log
        )
        return package_job_files(
            job_id=job_id,
            experiment=experiment,
            entry_point=entry_point,
            entry_point_plugin_files=entry_point_plugin_files,
            job_parameter_values=job_parameter_values,
            plugin_parameter_types=plugin_parameter_types,
            file_type=file_type,
            logger=log,
        )


class EntrypointValidateService(object):
    """"""

    @inject
    def __init__(
        self,
        plugin_id_service: PluginIdsService,
        plugin_id_file_service: PluginIdFileService,
    ) -> None:
        """Initialize the entrypoint service.

        All arguments are provided via dependency injection.

        Args:
            plugin_ids_service: A PluginIdsService object.
        """
        self._plugin_id_service = plugin_id_service
        self._plugin_id_file_service = plugin_id_file_service

    def validate(
        self, 
        task_graph: str, 
        plugin_ids: list[int], 
        entrypoint_parameters: list[dict[str, Any]],
        **kwargs,
    ) -> dict[str, Any]:
        """Validate a entrypoint workflow before the entrypoint is created.

        Args:
            task_graph:
            plugin_ids: 
            parameters: 

        Returns:
            

        Raises:
            
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Validate a entrypoint workflow", task_graph=task_graph, plugin_ids=plugin_ids, entrypoint_parameters=entrypoint_parameters)

        parameters = {param['name']: param['default_value'] for param in entrypoint_parameters}

        tasks: dict[str, Any] = {}
        parameter_types: dict[str, Any] = {}
        plugins = self._plugin_id_service.get(plugin_ids)
        for plugin in plugins:
            for plugin_file in plugin['plugin_files']:
                for task in plugin_file.tasks:
                    input_parameters = task.input_parameters
                    output_parameters = task.output_parameters
                    tasks[task.plugin_task_name] = {
                        "plugin": _build_plugin_field(plugin['plugin'], plugin_file, task),
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
        valid = is_valid(task_engine_dict)

        if valid:
            return {"status": "Success", "valid": valid}
        else:
            issues = validate(task_engine_dict)
            log.debug("Entrypoint workflow validation failed", issues=issues)
            raise EntrpointWorkflowYamlValidationError(issues)
