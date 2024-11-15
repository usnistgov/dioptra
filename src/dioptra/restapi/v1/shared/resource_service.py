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

import structlog
from injector import inject
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import db

from dioptra.restapi.v1.artifacts.service import ArtifactService, ArtifactIdService
from dioptra.restapi.v1.entrypoints.service import (
    EntrypointService,
    EntrypointIdService,
)
from dioptra.restapi.v1.experiments.service import (
    ExperimentService,
    ExperimentIdService,
)
from dioptra.restapi.v1.models.service import ModelService, ModelIdService
from dioptra.restapi.v1.plugin_parameter_types.service import (
    PluginParameterTypeService,
    PluginParameterTypeIdService,
)
from dioptra.restapi.v1.plugins.service import (
    PluginService,
    PluginIdFileService,
    PluginIdService,
    PluginIdFileIdService,
)
from dioptra.restapi.v1.queues.service import QueueService, QueueIdService


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
        """Initialize the queue service.

        All arguments are provided via dependency injection.

        Args:
            queue_name_service: A QueueNameService object.
        """

        self._services = {
            "artifact": artifact_service,
            "entrypoint": entrypoint_service,
            "experiment": experiment_service,
            "model": model_service,
            "plugin": plugin_service,
            "plugin_file": plugin_id_file_service,
            "plugin_parameter_type": plugin_parameter_type_service,
            "queue": queue_service,
        }

    def create(
        self,
        resource_type: str,
        resource_data: dict,
        group_id: int,
        commit: bool = True,
        **kwargs,
    ):
        """Create a new queue.

        Args:
            resource_type: The type of resource to create, e.g. queue
            resource_data: Arguments passed to create services as kwargs
            group_id: The group that will own the queue.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The newly created queue object.

        Raises:
            EntityExistsError: If a queue with the given name already exists.
            EntityDoesNotExistError: If the group with the provided ID does not exist.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        self._services[resource_type].create(
            group_id=group_id, **resource_data, commit=commit, log=log
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
    ) -> db.Model:
        """Initialize the resource id service.

        All arguments are provided via dependency injection.

        Args:
            queue_name_service: A QueueNameService object.
        """

        self._services = {
            "artifact": artifact_id_service,
            "entrypoint": entrypoint_id_service,
            "experiment": experiment_id_service,
            "model": model_id_service,
            "plugin": plugin_id_service,
            "plugin_file": plugin_id_file_id_service,
            "plugin_parameter_type": plugin_parameter_type_id_service,
            "queue": queue_id_service,
        }

    def create(
        self,
        resource_id: int,
        resource_type: str,
        resource_data: dict,
        group_id: int,
        commit: bool = True,
        **kwargs,
    ):
        """Create a new queue.

        Args:
            resource_type: The type of resource to create, e.g. queue
            resource_data: Arguments passed to create services as kwargs
            group_id: The group that will own the queue.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The newly created queue object.

        Raises:
            EntityExistsError: If a queue with the given name already exists.
            EntityDoesNotExistError: If the group with the provided ID does not exist.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        resource_dict = self._services[resource_type].modify(
            resource_id, group_id=group_id, **resource_data, commit=commit, log=log
        )
        return resource_dict[resource_type]
