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
"""The server-side functions that perform entrypoint endpoint operations."""
from __future__ import annotations

from typing import Any, Final, cast

import structlog
from flask_login import current_user
from injector import inject
from sqlalchemy import Integer, func, select
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import db, models
from dioptra.restapi.errors import BackendDatabaseError
from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.groups.service import GroupIdService
from dioptra.restapi.v1.plugins.service import PluginIdsService
from dioptra.restapi.v1.queues.service import QueueIdsService
from dioptra.restapi.v1.shared.search_parser import construct_sql_query_filters

from .errors import (
    EntrypointAlreadyExistsError,
    EntrypointDoesNotExistError,
    EntrypointParameterNamesNotUniqueError,
    EntrypointPluginDoesNotExistError,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()

RESOURCE_TYPE: Final[str] = "entry_point"
SEARCHABLE_FIELDS: Final[dict[str, Any]] = {
    "name": lambda x: models.EntryPoint.name.like(x, escape="/"),
    "description": lambda x: models.EntryPoint.description.like(x, escape="/"),
    "task_graph": lambda x: models.EntryPoint.task_graph.like(x, escape="/"),
}


class EntrypointService(object):
    """The service methods for creating and managing entrypoints."""

    @inject
    def __init__(
        self,
        entrypoint_name_service: EntrypointNameService,
        plugin_ids_service: PluginIdsService,
        queue_ids_service: QueueIdsService,
        group_id_service: GroupIdService,
    ) -> None:
        """Initialize the entrypoint service.

        All arguments are provided via dependency injection.

        Args:
            entrypoint_name_service: A EntrypointNameService object.
            plugin_ids_service: A PluginIdsService object.
            queue_ids_service: A QueueIdsService object.
            group_id_service: A GroupIdService object.
        """
        self._entrypoint_name_service = entrypoint_name_service
        self._plugin_ids_service = plugin_ids_service
        self._queue_ids_service = queue_ids_service
        self._group_id_service = group_id_service

    def create(
        self,
        name: str,
        description: str,
        task_graph: str,
        parameters: list[dict[str, Any]],
        plugin_ids: list[int],
        queue_ids: list[int],
        group_id: int,
        commit: bool = True,
        **kwargs,
    ) -> utils.EntrypointDict:
        """Create a new entrypoint.

        Args:
            name: The name of the entrypoint. The combination of name and group_id must
                be unique.
            description: The description of the entrypoint.
            group_id: The group that will own the entrypoint.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The newly created entrypoint object.

        Raises:
            EntrypointAlreadyExistsError: If a entrypoint with the given name already
                exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        if (
            self._entrypoint_name_service.get(name, group_id=group_id, log=log)
            is not None
        ):
            log.debug("Entrypoint name already exists", name=name, group_id=group_id)
            raise EntrypointAlreadyExistsError

        group = self._group_id_service.get(group_id, error_if_not_found=True)
        queues = self._queue_ids_service.get(queue_ids, error_if_not_found=True)
        plugins = self._plugin_ids_service.get(plugin_ids, error_if_not_found=True)

        resource = models.Resource(resource_type=RESOURCE_TYPE, owner=group)

        entrypoint_parameters = [
            models.EntryPointParameter(
                name=param["name"],
                default_value=param["default_value"],
                parameter_type=param["parameter_type"],
                parameter_number=i,
            )
            for i, param in enumerate(parameters)
        ]

        new_entrypoint = models.EntryPoint(
            name=name,
            description=description,
            task_graph=task_graph,
            parameters=entrypoint_parameters,
            resource=resource,
            creator=current_user,
        )

        entry_point_plugin_files = [
            models.EntryPointPluginFile(
                entry_point=new_entrypoint,
                plugin=plugin["plugin"],
                plugin_file=plugin_file,
            )
            for plugin in plugins
            for plugin_file in plugin["plugin_files"]
        ]
        new_entrypoint.entry_point_plugin_files = entry_point_plugin_files

        plugin_resources = [plugin["plugin"].resource for plugin in plugins]
        queue_resources = [queue.resource for queue in queues]
        new_entrypoint.children.extend(plugin_resources + queue_resources)

        db.session.add(new_entrypoint)

        if commit:
            db.session.commit()
            log.debug(
                "Entrypoint registration successful",
                entrypoint_id=new_entrypoint.resource_id,
                name=new_entrypoint.name,
            )

        return utils.EntrypointDict(
            entry_point=new_entrypoint, queues=queues, plugins=plugins, has_draft=False
        )

    def get(
        self,
        group_id: int | None,
        search_string: str,
        page_index: int,
        page_length: int,
        **kwargs,
    ) -> tuple[list[utils.EntrypointDict], int]:
        """Fetch a list of entrypoints, optionally filtering by search string and paging
        parameters.

        Args:
            group_id: A group ID used to filter results.
            search_string: A search string used to filter results.
            page_index: The index of the first group to be returned.
            page_length: The maximum number of entrypoints to be returned.

        Returns:
            A tuple containing a list of entrypoints and the total number of entrypoints
            matching the query.

        Raises:
            SearchNotImplementedError: If a search string is provided.
            BackendDatabaseError: If the database query returns a None when counting
                the number of entrypoints.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get full list of entrypoints")

        filters = list()

        if group_id is not None:
            filters.append(models.Resource.group_id == group_id)

        if search_string:
            filters.append(
                construct_sql_query_filters(search_string, SEARCHABLE_FIELDS)
            )

        stmt = (
            select(func.count(models.EntryPoint.resource_id))
            .join(models.Resource)
            .where(
                *filters,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.EntryPoint.resource_snapshot_id,
            )
        )
        total_num_entrypoints = db.session.scalars(stmt).first()

        if total_num_entrypoints is None:
            log.error(
                "The database query returned a None when counting the number of "
                "groups when it should return a number.",
                sql=str(stmt),
            )
            raise BackendDatabaseError

        if total_num_entrypoints == 0:
            return [], total_num_entrypoints

        entrypoints_stmt = (
            select(models.EntryPoint)
            .join(models.Resource)
            .where(
                *filters,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.EntryPoint.resource_snapshot_id,
            )
            .offset(page_index)
            .limit(page_length)
        )
        entrypoints = list(db.session.scalars(entrypoints_stmt).all())

        queue_ids = set(
            resource.resource_id
            for entrypoint in entrypoints
            for resource in entrypoint.children
            if resource.resource_type == "queue"
        )
        queues = {
            queue.resource_id: queue
            for queue in self._queue_ids_service.get(
                list(queue_ids), error_if_not_found=True
            )
        }

        entrypoint_dicts = {
            entrypoint.resource_id: utils.EntrypointDict(
                entry_point=entrypoint, queues=[], plugins=[], has_draft=False
            )
            for entrypoint in entrypoints
        }
        for entrypoint in entrypoint_dicts.values():
            entrypoint["plugins"] = _get_entrypoint_plugin_snapshots(
                entrypoint["entry_point"]
            )
            for resource in entrypoint["entry_point"].children:
                if resource.resource_type == "queue":
                    entrypoint["queues"].append(queues[resource.resource_id])

        drafts_stmt = select(
            models.DraftResource.payload["resource_id"].as_string().cast(Integer)
        ).where(
            models.DraftResource.payload["resource_id"]
            .as_string()
            .cast(Integer)
            .in_(tuple(entrypoint_dicts.keys())),
            models.DraftResource.user_id == current_user.user_id,
        )
        for resource_id in db.session.scalars(drafts_stmt):
            entrypoint_dicts[resource_id]["has_draft"] = True

        return list(entrypoint_dicts.values()), total_num_entrypoints


class EntrypointIdService(object):
    """The service methods for creating and managing entrypoints by their unique id."""

    @inject
    def __init__(
        self,
        entrypoint_name_service: EntrypointNameService,
        queue_ids_service: QueueIdsService,
    ) -> None:
        """Initialize the entrypoint service.

        All arguments are provided via dependency injection.

        Args:
            entrypoint_name_service: A EntrypointNameService object.
            queue_ids_service: A QueueIdsService object.
        """
        self._entrypoint_name_service = entrypoint_name_service
        self._queue_ids_service = queue_ids_service

    def get(
        self,
        entrypoint_id: int,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> utils.EntrypointDict | None:
        """Fetch a entrypoint by its unique id.

        Args:
            entrypoint_id: The unique id of the entrypoint.
            error_if_not_found: If True, raise an error if the entrypoint is not found.
                Defaults to False.

        Returns:
            The entrypoint object if found, otherwise None.

        Raises:
            EntrypointDoesNotExistError: If the entrypoint is not found and
            `error_if_not_found` is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get entrypoint by id", entrypoint_id=entrypoint_id)

        stmt = (
            select(models.EntryPoint)
            .join(models.Resource)
            .where(
                models.EntryPoint.resource_id == entrypoint_id,
                models.EntryPoint.resource_snapshot_id
                == models.Resource.latest_snapshot_id,
                models.Resource.is_deleted == False,  # noqa: E712
            )
        )
        entrypoint = db.session.scalars(stmt).first()

        if entrypoint is None:
            if error_if_not_found:
                log.debug("Entrypoint not found", entrypoint_id=entrypoint_id)
                raise EntrypointDoesNotExistError

            return None

        queue_ids = set(
            resource.resource_id
            for resource in entrypoint.children
            if resource.resource_type == "queue"
        )
        queues = self._queue_ids_service.get(list(queue_ids), error_if_not_found=True)
        plugins = _get_entrypoint_plugin_snapshots(entrypoint)

        drafts_stmt = (
            select(models.DraftResource.draft_resource_id)
            .where(
                models.DraftResource.payload["resource_id"].as_string().cast(Integer)
                == entrypoint.resource_id,
                models.DraftResource.user_id == current_user.user_id,
            )
            .exists()
            .select()
        )
        has_draft = db.session.scalar(drafts_stmt)

        return utils.EntrypointDict(
            entry_point=entrypoint, queues=queues, plugins=plugins, has_draft=has_draft
        )

    def modify(
        self,
        entrypoint_id: int,
        name: str,
        description: str,
        task_graph: str,
        parameters: list[dict[str, Any]],
        queue_ids: list[int],
        error_if_not_found: bool = False,
        commit: bool = True,
        **kwargs,
    ) -> utils.EntrypointDict | None:
        """Modify an entrypoint.

        Args:
            entrypoint_id: The unique id of the entrypoint.
            name: The new name of the entrypoint.
            description: The new description of the entrypoint.
            task_graph: The new task graph of the entrypoint.
            parameters: the new parameters of the entrypoint.
            error_if_not_found: If True, raise an error if the group is not found.
                Defaults to False.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The updated entrypoint object.

        Raises:
            EntrypointDoesNotExistError: If the entrypoint is not found and
                `error_if_not_found` is True.
            EntrypointAlreadyExistsError: If the entrypoint name already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        parameter_names = [parameter["name"] for parameter in parameters]
        if len(parameter_names) > len(set(parameter_names)):
            raise EntrypointParameterNamesNotUniqueError

        entrypoint_dict = self.get(
            entrypoint_id, error_if_not_found=error_if_not_found, log=log
        )

        if entrypoint_dict is None:
            return None

        entrypoint = entrypoint_dict["entry_point"]
        group_id = entrypoint.resource.group_id
        if (
            name != entrypoint.name
            and self._entrypoint_name_service.get(name, group_id=group_id, log=log)
            is not None
        ):
            log.debug("Entrypoint name already exists", name=name, group_id=group_id)
            raise EntrypointAlreadyExistsError

        queues = self._queue_ids_service.get(queue_ids, error_if_not_found=True)

        entrypoint_parameters = [
            models.EntryPointParameter(
                name=param["name"],
                default_value=param["default_value"],
                parameter_type=param["parameter_type"],
                parameter_number=i,
            )
            for i, param in enumerate(parameters)
        ]

        new_entrypoint = models.EntryPoint(
            name=name,
            description=description,
            task_graph=task_graph,
            parameters=entrypoint_parameters,
            resource=entrypoint.resource,
            creator=current_user,
        )
        new_entrypoint.entry_point_plugin_files = entrypoint.entry_point_plugin_files

        plugins = _get_entrypoint_plugin_snapshots(new_entrypoint)

        plugin_resources = [plugin["plugin"].resource for plugin in plugins]
        queue_resources = [queue.resource for queue in queues]
        new_entrypoint.children = plugin_resources + queue_resources

        db.session.add(new_entrypoint)

        if commit:
            db.session.commit()
            log.debug(
                "Entrypoint modification successful",
                entrypoint_id=entrypoint_id,
                name=name,
                description=description,
            )

        return utils.EntrypointDict(
            entry_point=new_entrypoint, queues=queues, plugins=plugins, has_draft=False
        )

    def delete(self, entrypoint_id: int, **kwargs) -> dict[str, Any]:
        """Delete a entrypoint.

        Args:
            entrypoint_id: The unique id of the entrypoint.

        Returns:
            A dictionary reporting the status of the request.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        stmt = select(models.Resource).filter_by(
            resource_id=entrypoint_id, resource_type=RESOURCE_TYPE, is_deleted=False
        )
        entrypoint_resource = db.session.scalars(stmt).first()

        if entrypoint_resource is None:
            raise EntrypointDoesNotExistError

        deleted_resource_lock = models.ResourceLock(
            resource_lock_type="delete",
            resource=entrypoint_resource,
        )
        db.session.add(deleted_resource_lock)
        db.session.commit()
        log.debug("Entrypoint deleted", entrypoint_id=entrypoint_id)

        return {"status": "Success", "entrypoint_id": entrypoint_id}


class EntrypointIdPluginsService(object):
    """The service methods for creating and managing entrypoints by their unique id."""

    @inject
    def __init__(
        self,
        entrypoint_id_service: EntrypointIdService,
        plugin_ids_service: PluginIdsService,
        queue_ids_service: QueueIdsService,
    ) -> None:
        """Initialize the entrypoint service.

        All arguments are provided via dependency injection.

        Args:
            entrypoint_id_service: A EntrypointIdService object.
            plugin_ids_service: A PluginIdsService object.
            queue_ids_service: A QueueIdsService object.
        """
        self._entrypoint_id_service = entrypoint_id_service
        self._plugin_ids_service = plugin_ids_service
        self._queue_ids_service = queue_ids_service

    def get(
        self,
        entrypoint_id: int,
        **kwargs,
    ) -> utils.EntrypointDict:
        """Fetch the plugin snapshots for an entrypoint by its unique id.

        Args:
            entrypoint_id: The unique id of the entrypoint.

        Returns:
            The plugin snapshots for the entrypoint.

        Raises:
            EntrypointDoesNotExistError: If the entrypoint is not found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get entrypoint by id", entrypoint_id=entrypoint_id)

        return cast(
            utils.EntrypointDict,
            self._entrypoint_id_service.get(
                entrypoint_id, error_if_not_found=True, log=log
            ),
        )

    def append(
        self,
        entrypoint_id: int,
        plugin_ids: list[int],
        commit: bool = True,
        **kwargs,
    ) -> utils.EntrypointDict:
        """Append plugins to an entrypoint.

        Args:
            entrypoint_id: The unique id of the entrypoint.
            plugin_ids: The plugins to be appended. If a plugin is already attached
                to the entrypoint, it is synced to the latest snapshot.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The updated entrypoint object.

        Raises:
            EntrypointDoesNotExistError: If the entrypoint is not found.
            EntrypointAlreadyExistsError: If the entrypoint name already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        entrypoint = cast(
            utils.EntrypointDict,
            self._entrypoint_id_service.get(
                entrypoint_id, error_if_not_found=True, log=log
            ),
        )["entry_point"]

        new_entrypoint_parameters = [
            models.EntryPointParameter(
                name=param.name,
                default_value=param.default_value,
                parameter_type=param.parameter_type,
                parameter_number=param.parameter_number
            )
            for param in entrypoint.parameters
        ]
        new_entrypoint = models.EntryPoint(
            name=entrypoint.name,
            description=entrypoint.description,
            task_graph=entrypoint.task_graph,
            parameters=new_entrypoint_parameters,
            resource=entrypoint.resource,
            creator=current_user,
        )

        new_entry_point_plugin_files = [
            models.EntryPointPluginFile(
                entry_point=new_entrypoint,
                plugin=plugin["plugin"],
                plugin_file=plugin_file,
            )
            for plugin in self._plugin_ids_service.get(
                plugin_ids, error_if_not_found=True
            )
            for plugin_file in plugin["plugin_files"]
        ]
        existing_entry_point_plugin_files = [
            entry_point_plugin_file
            for entry_point_plugin_file in entrypoint.entry_point_plugin_files
            if entry_point_plugin_file.plugin.resource_id not in set(plugin_ids)
        ]
        new_entrypoint.entry_point_plugin_files = (
            existing_entry_point_plugin_files + new_entry_point_plugin_files
        )

        plugins = _get_entrypoint_plugin_snapshots(new_entrypoint)

        queue_ids = set(
            resource.resource_id
            for resource in entrypoint.children
            if resource.resource_type == "queue"
        )
        queues = self._queue_ids_service.get(list(queue_ids), error_if_not_found=True)

        plugin_resources = [plugin["plugin"].resource for plugin in plugins]
        queue_resources = [queue.resource for queue in queues]
        new_entrypoint.children = plugin_resources + queue_resources

        db.session.add(new_entrypoint)

        if commit:
            db.session.commit()
            log.debug(
                "Entrypoint modification successful",
                entrypoint_id=entrypoint_id,
                name=entrypoint.name,
                description=entrypoint.description,
            )

        return utils.EntrypointDict(
            entry_point=new_entrypoint, queues=queues, plugins=plugins, has_draft=False
        )


class EntrypointIdPluginsIdService(object):
    """The service methods for creating and managing entrypoints by their unique id."""

    @inject
    def __init__(
        self,
        entrypoint_id_service: EntrypointIdService,
        queue_ids_service: QueueIdsService,
    ) -> None:
        """Initialize the entrypoint service.

        All arguments are provided via dependency injection.

        Args:
            entrypoint_id_service: A EntrypointIdService object.
            queue_ids_service: A QueueIdsService object.
        """
        self._entrypoint_id_service = entrypoint_id_service
        self._queue_ids_service = queue_ids_service

    def get(
        self,
        entrypoint_id: int,
        plugin_id: int,
        error_if_not_found: bool = True,
        **kwargs,
    ) -> utils.PluginWithFilesDict | None:
        """Fetch the plugin snapshots for an entrypoint by its unique id.

        Args:
            entrypoint_id: The unique id of the entrypoint.

        Returns:
            The plugin snapshots for the entrypoint.

        Raises:
            EntrypointDoesNotExistError: If the entrypoint is not found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get entrypoint by id", entrypoint_id=entrypoint_id)

        plugins_dict = cast(
            utils.EntrypointDict,
            self._entrypoint_id_service.get(
                entrypoint_id, error_if_not_found=True, log=log
            ),
        )["plugins"]
        plugins = {plugin["plugin"].resource_id: plugin for plugin in plugins_dict}

        if error_if_not_found and plugin_id not in plugins:
            raise EntrypointPluginDoesNotExistError

        return plugins.get(plugin_id, None)

    def delete(
        self,
        entrypoint_id: int,
        plugin_id: int,
        commit: bool = True,
        **kwargs,
    ) -> utils.EntrypointDict:
        """Remove a plugin from an entrypoint.

        Args:
            entrypoint_id: The unique id of the entrypoint.
            plugin_id: The plugin to be removed.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The updated entrypoint object.

        Raises:
            EntrypointDoesNotExistError: If the entrypoint is not found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        entrypoint = cast(
            utils.EntrypointDict,
            self._entrypoint_id_service.get(
                entrypoint_id, error_if_not_found=True, log=log
            ),
        )["entry_point"]

        new_entrypoint = models.EntryPoint(
            name=entrypoint.name,
            description=entrypoint.description,
            task_graph=entrypoint.task_graph,
            parameters=entrypoint.parameters,
            resource=entrypoint.resource,
            creator=current_user,
        )
        new_entrypoint.entry_point_plugin_files = [
            entry_point_plugin_file
            for entry_point_plugin_file in entrypoint.entry_point_plugin_files
            if entry_point_plugin_file.plugin.resource_id != plugin_id
        ]

        plugins = _get_entrypoint_plugin_snapshots(new_entrypoint)

        queue_ids = set(
            resource.resource_id
            for resource in entrypoint.children
            if resource.resource_type == "queue"
        )
        queues = self._queue_ids_service.get(list(queue_ids), error_if_not_found=True)

        plugin_resources = [plugin["plugin"].resource for plugin in plugins]
        queue_resources = [queue.resource for queue in queues]
        new_entrypoint.children = plugin_resources + queue_resources

        db.session.add(new_entrypoint)

        if commit:
            db.session.commit()
            log.debug(
                "Entrypoint modification successful",
                entrypoint_id=entrypoint_id,
                name=entrypoint.name,
                description=entrypoint.description,
            )

        return utils.EntrypointDict(
            entry_point=new_entrypoint, queues=queues, plugins=plugins, has_draft=False
        )


class EntrypointIdsService(object):
    """The service methods for retrieving entrypoints from a list of ids."""

    def get(
        self,
        entrypoint_ids: list[int],
        error_if_not_found: bool = False,
        **kwargs,
    ) -> list[models.EntryPoint]:
        """Fetch a list of entrypoints by their unique ids.

        Args:
            entrypoint_ids: The unique ids of the entrypoints.
            error_if_not_found: If True, raise an error if the entrypoint is not found.
                Defaults to False.

        Returns:
            The entrypoint object if found, otherwise None.

        Raises:
            EntrypointDoesNotExistError: If the entrypoint is not found and
                `error_if_not_found` is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get entrypoint by id", entrypoint_ids=entrypoint_ids)

        stmt = (
            select(models.EntryPoint)
            .join(models.Resource)
            .where(
                models.EntryPoint.resource_id.in_(tuple(entrypoint_ids)),
                models.EntryPoint.resource_snapshot_id
                == models.Resource.latest_snapshot_id,
                models.Resource.is_deleted == False,  # noqa: E712
            )
        )
        entrypoints = list(db.session.scalars(stmt).all())

        if len(entrypoints) != len(entrypoint_ids) and error_if_not_found:
            entrypoint_ids_missing = set(entrypoint_ids) - set(
                entrypoint.resource_id for entrypoint in entrypoints
            )
            log.debug(
                "Entrypoint not found", entrypoint_ids=list(entrypoint_ids_missing)
            )
            raise EntrypointDoesNotExistError

        return entrypoints


class EntrypointNameService(object):
    """The service methods for managing entrypoints by their name."""

    def get(
        self,
        name: str,
        group_id: int,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> models.EntryPoint | None:
        """Fetch a entrypoint by its name.

        Args:
            name: The name of the entrypoint.
            group_id: The the group id of the entrypoint.
            error_if_not_found: If True, raise an error if the entrypoint is not found.
                Defaults to False.

        Returns:
            The entrypoint object if found, otherwise None.

        Raises:
            EntrypointDoesNotExistError: If the entrypoint is not found and
                `error_if_not_found` is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get entrypoint by name", entrypoint_name=name, group_id=group_id)

        stmt = (
            select(models.EntryPoint)
            .join(models.Resource)
            .where(
                models.EntryPoint.name == name,
                models.Resource.group_id == group_id,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.EntryPoint.resource_snapshot_id,
            )
        )
        entrypoint = db.session.scalars(stmt).first()

        if entrypoint is None:
            if error_if_not_found:
                log.debug("Entrypoint not found", name=name)
                raise EntrypointDoesNotExistError

            return None

        return entrypoint


def _get_entrypoint_plugin_snapshots(
    entrypoint: models.EntryPoint,
) -> list[utils.PluginWithFilesDict]:
    plugins_dict = {
        entry_point_plugin_file.plugin.resource_id: utils.PluginWithFilesDict(
            plugin=entry_point_plugin_file.plugin, plugin_files=[], has_draft=False
        )
        for entry_point_plugin_file in entrypoint.entry_point_plugin_files
    }
    for entry_point_plugin_file in entrypoint.entry_point_plugin_files:
        resource_id = entry_point_plugin_file.plugin.resource_id
        plugin_file = entry_point_plugin_file.plugin_file
        plugins_dict[resource_id]["plugin_files"].append(plugin_file)
    return list(plugins_dict.values())
