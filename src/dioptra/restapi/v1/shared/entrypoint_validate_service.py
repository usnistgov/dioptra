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
"""The shared server-side functions that perform entrypoint validatation operations."""
from typing import Any, Final

import structlog
from injector import inject
from structlog.stdlib import BoundLogger

from dioptra.restapi.errors import EntrypointWorkflowYamlValidationError
from dioptra.restapi.v1.plugins.service import PluginIdsService
from dioptra.restapi.v1.shared.build_task_engine_dict import build_task_engine_dict
from dioptra.task_engine.validation import validate

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class EntrypointValidateService(object):
    """The service for handling requests with entrypoint workflow yamls."""

    @inject
    def __init__(
        self,
        plugin_id_service: PluginIdsService,
    ) -> None:
        """Initialize the entrypoint service.

        All arguments are provided via dependency injection.

        Args:
            plugin_ids_service: A PluginIdsService object.
        """
        self._plugin_id_service = plugin_id_service

    def validate(
        self, 
        task_graph: str, 
        plugin_ids: list[int], 
        entrypoint_parameters: list[dict[str, Any]],
        **kwargs,
    ) -> dict[str, Any]:
        """Validate a entrypoint workflow before the entrypoint is created.

        Args:
            task_graph: The proposed task graph of a new entrypoint resource.
            plugin_ids: A list of plugin files for the new entrypoint.
            parameters: A list of parameters for the new entrypoint.

        Returns:
            A success response and a indicator that states the entrypoint worklflow yaml is valid.

        Raises:
            EntrypointWorkflowYamlValidationError: If the entrypoint worklflow yaml is not valid.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Validate a entrypoint workflow", task_graph=task_graph, plugin_ids=plugin_ids, entrypoint_parameters=entrypoint_parameters)

        parameters = {param['name']: param['default_value'] for param in entrypoint_parameters}
        plugins = self._plugin_id_service.get(plugin_ids)
        task_engine_dict = build_task_engine_dict(
            plugins=plugins, 
            parameters=parameters, 
            task_graph=task_graph
        )

        issues = validate(task_engine_dict)

        if not issues:
            return {"status": "Success", "valid": True}
        else:
            raise EntrypointWorkflowYamlValidationError(issues)