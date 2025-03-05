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
"""The server-side functions that perform resource operations."""
from __future__ import annotations

from typing import Any

import structlog
from injector import inject
from structlog.stdlib import BoundLogger

from dioptra.restapi.errors import DioptraError
from dioptra.restapi.v1.artifacts.service import ArtifactIdService, ArtifactService
from dioptra.restapi.v1.entrypoints.service import (
    EntrypointIdService,
    EntrypointService,
)
from dioptra.restapi.v1.experiments.service import (
    ExperimentIdService,
    ExperimentService,
)
from dioptra.restapi.v1.models.service import ModelIdService, ModelService
from dioptra.restapi.v1.plugin_parameter_types.service import (
    PluginParameterTypeIdService,
    PluginParameterTypeService,
)
from dioptra.restapi.v1.plugins.service import (
    PluginIdFileIdService,
    PluginIdFileService,
    PluginIdService,
    PluginService,
)
from dioptra.restapi.v1.queues.service import QueueIdService, QueueService

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class ResourceService(object):
    """The service methods for creating resources."""

    @inject
    def __init__(
        self,
        artifact_service: ArtifactService,
        entrypoint_service: EntrypointService,
        experiment_service: ExperimentService,
        model_service: ModelService,
        plugin_service: PluginService,
        plugin_id_file_service: PluginIdFileService,
        plugin_parameter_type_service: PluginParameterTypeService,
        queue_service: QueueService,
    ) -> None:
        """Initialize the resource service.

        All arguments are provided via dependency injection.

        Args:
            artifact_service: An ArtifactService object
            entrypoint_service: An EntrypointService object
            experiment_service: An ExperimentService object
            model_service: A ModelService object
            plugin_service: A PluginService object
            plugin_id_file_service: A PluginIdFileService object
            plugin_parameter_type_service: A PluginParameterTypeService object
            queue_service: A QueueService object
        """

        self._services: dict[str, object] = {
            "artifact": artifact_service,
            "entry_point": entrypoint_service,
            "experiment": experiment_service,
            "ml_model": model_service,
            "plugin": plugin_service,
            "plugin_file": plugin_id_file_service,
            "plugin_task_parameter_type": plugin_parameter_type_service,
            "queue": queue_service,
        }

    def create(
        self,
        *resource_ids: int,
        resource_type: str,
        resource_data: dict,
        group_id: int,
        commit: bool = True,
        **kwargs,
    ) -> Any:
        """Create a new resource.

        Args:
            resource_ids: The list of resource
            resource_type: The type of resource to create, e.g. queue
            resource_data: Arguments passed to create services as kwargs
            group_id: The group that will own the resource.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The newly created resource object.

        Raises:
            DioptraError: If resource_type is not valid.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        if resource_type not in self._services:
            raise DioptraError(f"Invalid resource type: {resource_type}")

        return self._services[resource_type].create(  # type: ignore
            *resource_ids, group_id=group_id, **resource_data, commit=commit, log=log
        )


class ResourceIdService(object):
    """The service methods for creating resources."""

    @inject
    def __init__(
        self,
        artifact_id_service: ArtifactIdService,
        entrypoint_id_service: EntrypointIdService,
        experiment_id_service: ExperimentIdService,
        model_id_service: ModelIdService,
        plugin_id_service: PluginIdService,
        plugin_id_file_id_service: PluginIdFileIdService,
        plugin_parameter_type_id_service: PluginParameterTypeIdService,
        queue_id_service: QueueIdService,
    ) -> None:
        """Initialize the resource id service.

        All arguments are provided via dependency injection.

        Args:
            artifact_id_service: An ArtifactIdService object
            entrypoint_id_service: An EntrypointIdService object
            experiment_id_service: An ExperimentIdService object
            model_id_service: A ModelIdService object
            plugin_id_service: A PluginIdService object
            plugin_id_file_id_service: A PluginIdFileIdService object
            plugin_parameter_type_id_service: A PluginParameterTypeIdService object
            queue_id_service: A QueueIdService object
        """

        self._services = {
            "artifact": artifact_id_service,
            "entry_point": entrypoint_id_service,
            "experiment": experiment_id_service,
            "ml_model": model_id_service,
            "plugin": plugin_id_service,
            "plugin_file": plugin_id_file_id_service,
            "plugin_task_parameter_type": plugin_parameter_type_id_service,
            "queue": queue_id_service,
        }

    def modify(
        self,
        *resource_ids: int,
        resource_type: str,
        resource_data: dict,
        group_id: int,
        commit: bool = True,
        **kwargs,
    ) -> Any:
        """Modify an existing resource.

        Args:
            resource_ids: The list of resource
            resource_type: The type of resource to create, e.g. queue
            resource_data: Arguments passed to create services as kwargs
            group_id: The group that will own the resource.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The modified resource object.

        Raises:
            DioptraError: If resource_type is not valid.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        if resource_type not in self._services:
            raise DioptraError(f"Invalid resource type: {resource_type}")

        return self._services[resource_type].modify(  # type: ignore
            *resource_ids, group_id=group_id, **resource_data, commit=commit, log=log
        )
