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

from typing import Any, Final, Iterable

import structlog
from flask_login import current_user
from injector import inject
from sqlalchemy import Integer, func, select
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import db, models
from dioptra.restapi.db.models.constants import resource_lock_types
from dioptra.restapi.errors import (
    ArtifactTaskPluginTaskOverlapError,
    BackendDatabaseError,
    EntityDoesNotExistError,
    EntityExistsError,
    PluginTaskArtifactTaskOverlapError,
    QueryParameterNotUniqueError,
    SortParameterValidationError,
)
from dioptra.restapi.utils import find_non_unique
from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.groups.service import GroupIdService
from dioptra.restapi.v1.plugins.service import (
    PluginIdsService,
    get_plugin_task_parameter_types_by_id,
)
from dioptra.restapi.v1.queues.service import RESOURCE_TYPE as QUEUE_RESOURCE_TYPE
from dioptra.restapi.v1.queues.service import QueueIdsService
from dioptra.restapi.v1.shared.search_parser import construct_sql_query_filters
from dioptra.restapi.v1.shared.task_engine_yaml.service import (
    coerce_entrypoint_default_param_types,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()
PLUGIN_RESOURCE_TYPE: Final[str] = "entry_point_plugin"

RESOURCE_TYPE: Final[str] = "entry_point"
SEARCHABLE_FIELDS: Final[dict[str, Any]] = {
    "name": lambda x: models.EntryPoint.name.like(x, escape="/"),
    "description": lambda x: models.EntryPoint.description.like(x, escape="/"),
    "task_graph": lambda x: models.EntryPoint.task_graph.like(x, escape="/"),
    "artifact_graph": lambda x: models.EntryPoint.artifact_graph.like(x, escape="/"),
    "tag": lambda x: models.EntryPoint.tags.any(models.Tag.name.like(x, escape="/")),
}
SORTABLE_FIELDS: Final[dict[str, Any]] = {
    "name": models.EntryPoint.name,
    "createdOn": models.EntryPoint.created_on,
    "lastModifiedOn": models.Resource.last_modified_on,
    "description": models.EntryPoint.description,
}


class EntrypointService(object):
    """The service methods for creating and managing entrypoints."""

    @inject
    def __init__(
        self,
        entrypoint_name_service: "EntrypointNameService",
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
        description: str | None,
        task_graph: str,
        artifact_graph: str,
        parameters: list[dict[str, Any]],
        artifact_parameters: list[dict[str, Any]],
        plugin_ids: list[int],
        artifact_plugin_ids: list[int],
        queue_ids: list[int],
        group_id: int,
        commit: bool = True,
        **kwargs,
    ) -> utils.EntrypointDict:
        """Create a new entrypoint.

        Args:
            name: The name of the entrypoint. The combination of name and group_id must
                be unique.
            description: The description of the new entrypoint.
            task_graph: The task graph for the new entrypoint as a YAML-formatted
                string.
            artifact_graph: The artifact graph for the new entrypoint as a
                YAML-formatted string. An empty string indicates there are no artifacts
                which need to be stored.
            parameters: The list of parameters for the new entrypoint.
            artifact_parameters: The list of artifact parameters for the new entrypoint.
            plugin_ids: A list of plugin ids to associate with the new entrypoint.
                Optional, defaults to None.
            artifact_plugin_ids: A list of artifact plugin ids to associate with the new
                entrypoint. Optional, defaults to None.
            queue_ids: A list of queue ids to associate with the new entrypoint.
            group_id: The id of the group that will own the entrypoint.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The newly created entrypoint object.

        Raises:
            EntityExistsError: If a entrypoint with the given name already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        # TODO: need to add a check here that graphs are valid yaml

        duplicate = self._entrypoint_name_service.get(name, group_id=group_id, log=log)
        if duplicate is not None:
            raise EntityExistsError(
                RESOURCE_TYPE, duplicate.resource_id, name=name, group_id=group_id
            )

        plugin_ids = list(set(plugin_ids))
        artifact_plugin_ids = list(set(artifact_plugin_ids))
        group = self._group_id_service.get(group_id, error_if_not_found=True)
        queues = self._queue_ids_service.get(queue_ids, error_if_not_found=True)
        plugins = self._plugin_ids_service.get(plugin_ids, error_if_not_found=True)
        artifact_plugins = self._plugin_ids_service.get(
            artifact_plugin_ids, error_if_not_found=True
        )
        # check this early
        _ensure_no_plugin_task_overlap(plugin_ids, artifact_plugin_ids, True)

        resource = models.Resource(resource_type=RESOURCE_TYPE, owner=group)

        new_entrypoint = models.EntryPoint(
            name=name,
            description=description,
            task_graph=task_graph,
            artifact_graph=artifact_graph,
            parameters=_create_parameters(parameters),
            artifact_parameters=_create_artifact_parameters(
                artifact_parameters=artifact_parameters, log=log
            ),
            resource=resource,
            creator=current_user,
        )
        db.session.add(new_entrypoint)

        new_entrypoint.entry_point_plugins = [
            models.EntryPointPlugin(
                entry_point=new_entrypoint,
                plugin=plugin["plugin"],
            )
            for plugin in plugins
        ]

        new_entrypoint.entry_point_artifact_plugins = [
            models.EntryPointArtifactPlugin(
                entry_point=new_entrypoint,
                plugin=artifact_plugin["plugin"],
            )
            for artifact_plugin in artifact_plugins
        ]

        plugin_resources = [plugin["plugin"].resource for plugin in plugins]
        artifact_plugin_resources = [
            artifact_plugin["plugin"].resource for artifact_plugin in artifact_plugins
        ]
        queue_resources = [queue.resource for queue in queues]
        new_entrypoint.children.extend(
            plugin_resources + queue_resources + artifact_plugin_resources
        )

        if commit:
            db.session.commit()
            log.debug(
                "Entrypoint registration successful",
                entrypoint_id=new_entrypoint.resource_id,
                name=new_entrypoint.name,
            )

        return utils.EntrypointDict(
            entry_point=new_entrypoint, queues=queues, has_draft=False
        )

    def get(
        self,
        group_id: int | None,
        search_string: str,
        page_index: int,
        page_length: int,
        sort_by_string: str,
        descending: bool,
        **kwargs,
    ) -> tuple[list[utils.EntrypointDict], int]:
        """Fetch a list of entrypoints, optionally filtering by search string and paging
        parameters.

        Args:
            group_id: A group ID used to filter results.
            search_string: A search string used to filter results.
            page_index: The index of the first group to be returned.
            page_length: The maximum number of entrypoints to be returned.
            sort_by_string: The name of the column to sort.
            descending: Boolean indicating whether to sort by descending or not.

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

        filters = []

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

        if sort_by_string and sort_by_string in SORTABLE_FIELDS:
            sort_column = SORTABLE_FIELDS[sort_by_string]
            if descending:
                sort_column = sort_column.desc()
            else:
                sort_column = sort_column.asc()
            entrypoints_stmt = entrypoints_stmt.order_by(sort_column)
        elif sort_by_string and sort_by_string not in SORTABLE_FIELDS:
            raise SortParameterValidationError(RESOURCE_TYPE, sort_by_string)

        entrypoints = list(db.session.scalars(entrypoints_stmt).unique().all())

        queue_ids = {
            resource.resource_id
            for entrypoint in entrypoints
            for resource in entrypoint.children
            if resource.resource_type == "queue" and not resource.is_deleted
        }
        queues = {
            queue.resource_id: queue
            for queue in self._queue_ids_service.get(
                list(queue_ids), error_if_not_found=True
            )
        }

        entrypoint_dicts = {
            entrypoint.resource_id: utils.EntrypointDict(
                entry_point=entrypoint, queues=[], has_draft=False
            )
            for entrypoint in entrypoints
        }
        for entrypoint in entrypoint_dicts.values():
            for resource in entrypoint["entry_point"].children:
                if resource.resource_type == "queue" and not resource.is_deleted:
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
    """The service methods for creating and managing entrypoints by
    their unique id."""

    @inject
    def __init__(
        self,
        entrypoint_name_service: "EntrypointNameService",
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
        entrypoint_snapshot_id: int | None = None,
        **kwargs,
    ) -> utils.EntrypointDict:
        """Fetch a entrypoint by its unique id.

        Args:
            entrypoint_id: The unique id of the entrypoint.

        Returns:
            The entrypoint object

        Raises:
            EntityDoesNotExistError: If the entrypoint is not found
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get entrypoint by id", entrypoint_id=entrypoint_id)
        # Get a specific snapshot if entrypoint_snapshot_id is specified
        snapshot_id = (
            entrypoint_snapshot_id
            if entrypoint_snapshot_id is not None
            else models.Resource.latest_snapshot_id
        )
        stmt = (
            select(models.EntryPoint)
            .join(models.Resource)
            .where(
                models.EntryPoint.resource_id == entrypoint_id,
                models.EntryPoint.resource_snapshot_id == snapshot_id,
                models.Resource.is_deleted == False,  # noqa: E712
            )
        )
        entrypoint = db.session.scalars(stmt).first()

        if entrypoint is None:
            raise EntityDoesNotExistError(
                RESOURCE_TYPE,
                entrypoint_id=entrypoint_id,
                entrypoint_snapshot_id=entrypoint_snapshot_id,
            )

        queue_ids = {
            resource.resource_id
            for resource in entrypoint.children
            if resource.resource_type == "queue" and not resource.is_deleted
        }
        queues = self._queue_ids_service.get(list(queue_ids), error_if_not_found=True)

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
            entry_point=entrypoint, queues=queues, has_draft=has_draft
        )

    def modify(
        self,
        entrypoint_id: int,
        name: str,
        description: str | None,
        task_graph: str,
        artifact_graph: str,
        parameters: list[dict[str, Any]],
        artifact_parameters: list[dict[str, Any]],
        queue_ids: list[int],
        commit: bool = True,
        **kwargs,
    ) -> utils.EntrypointDict:
        """Modify an entrypoint.

        Args:
            entrypoint_id: The unique id of the entrypoint.
            name: The new name of the entrypoint.
            description: The new description of the entrypoint.
            task_graph: The new task graph of the entrypoint.
            artifact_graph: The new artifact definitions of the entrypoint.
            parameters: the new parameters of the entrypoint.
            artifact_parameters: the new artifact_parameters of the entrypoint. If None
                or empty list, all artifact_parameters will be removed.
            queue_ids: A list of queue ids that will replace the current list of
                entrypoint queues.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The updated entrypoint object.

        Raises:
            EntityDoesNotExistError: If the entrypoint is not found
            EntityExistsError: If the entrypoint name already exists.
            QueryParameterNotUniqueError: If the values for the "name" parameter in the
                parameters list is not unique
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        duplicates = find_non_unique("name", parameters)
        if len(duplicates) > 0:
            raise QueryParameterNotUniqueError(RESOURCE_TYPE, name=duplicates)
        artifact_parameter_duplicates = find_non_unique("name", artifact_parameters)
        if len(artifact_parameter_duplicates) > 0:
            raise QueryParameterNotUniqueError(
                RESOURCE_TYPE, name=artifact_parameter_duplicates
            )

        entrypoint_dict = self.get(entrypoint_id, log=log)

        entrypoint = entrypoint_dict["entry_point"]
        group_id = entrypoint.resource.group_id
        if name != entrypoint.name:
            duplicate = self._entrypoint_name_service.get(
                name, group_id=group_id, log=log
            )
            if duplicate is not None:
                raise EntityExistsError(
                    RESOURCE_TYPE, duplicate.resource_id, name=name, group_id=group_id
                )

        queues = self._queue_ids_service.get(queue_ids, error_if_not_found=True)

        new_entrypoint = models.EntryPoint(
            name=name,
            description=description,
            task_graph=task_graph,
            artifact_graph=artifact_graph,
            parameters=_create_parameters(parameters),
            artifact_parameters=_create_artifact_parameters(
                artifact_parameters=artifact_parameters, log=log
            ),
            resource=entrypoint.resource,
            creator=current_user,
        )
        db.session.add(new_entrypoint)

        plugin_resources = _copy_plugins(
            plugins=entrypoint.entry_point_plugins, target_entrypoint=new_entrypoint
        )
        artifact_plugin_resources = _copy_artifact_plugins(
            artifact_plugins=entrypoint.entry_point_artifact_plugins,
            target_entrypoint=new_entrypoint,
        )
        queue_resources = [queue.resource for queue in queues]
        new_entrypoint.children = (
            plugin_resources + queue_resources + artifact_plugin_resources
        )

        if commit:
            db.session.commit()
            log.debug(
                "Entrypoint modification successful",
                entrypoint_id=entrypoint_id,
                name=name,
                description=description,
            )

        return utils.EntrypointDict(
            entry_point=new_entrypoint, queues=queues, has_draft=False
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
            raise EntityDoesNotExistError(RESOURCE_TYPE, entrypoint_id=entrypoint_id)

        deleted_resource_lock = models.ResourceLock(
            resource_lock_type=resource_lock_types.DELETE,
            resource=entrypoint_resource,
        )
        db.session.add(deleted_resource_lock)
        db.session.commit()
        log.debug("Entrypoint deleted", entrypoint_id=entrypoint_id)

        return {"status": "Success", "id": [entrypoint_id]}


class EntrypointSnapshotIdService(object):
    def get(
        self, entrypoint_id: int, entrypoint_snapshot_id: int, **kwargs
    ) -> models.EntryPoint:
        """Run a query to get the EntryPoint for an entrypoint snapshot id.

        Args:
            entrypoint_id: the ID of the entrypoint
            entrypoint_snapshot_id: The Snapshot ID of the entrypoint to retrieve

        Returns:
            The entrypoint.

        Raises:
            EntityDoesNotExistError: If the entrypoint is not found
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug(
            "get entrypoint snapshot",
            resource_id=entrypoint_id,
            resource_snapshot_id=entrypoint_snapshot_id,
        )
        entry_point_resource_snapshot_stmt = select(models.EntryPoint).where(
            models.EntryPoint.resource_id == entrypoint_id,
            models.EntryPoint.resource_snapshot_id == entrypoint_snapshot_id,
        )
        entry_point = db.session.scalar(entry_point_resource_snapshot_stmt)

        if entry_point is None:
            raise EntityDoesNotExistError(
                RESOURCE_TYPE,
                entrypoint_id=entrypoint_id,
                entrypoint_snapshot_id=entrypoint_snapshot_id,
            )
        return entry_point

    def get_plugin_files(
        self,
        entrypoint_id: int,
        entrypoint_snapshot_id: int,
        **kwargs,
    ) -> list[models.PluginPluginFile]:
        """Run a query to get the plugin files for an entrypoint.

        Args:
            entrypoint_snapshot_id: The Snapshot ID of the entrypoint to get the plugin
            files for.

        Returns:
            The plugin files for the entrypoint.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("get plugin files", resource_snapshot_id=entrypoint_snapshot_id)

        entry_point = self.get(
            entrypoint_id=entrypoint_id,
            entrypoint_snapshot_id=entrypoint_snapshot_id,
            log=log,
        )
        return [
            plugin_plugin_file
            for entry_point_plugin in entry_point.entry_point_plugins
            for plugin_plugin_file in entry_point_plugin.plugin.plugin_plugin_files
        ]

    def get_artifact_plugin_files(
        self,
        entrypoint_id: int,
        entrypoint_snapshot_id: int,
        **kwargs,
    ) -> list[models.PluginPluginFile]:
        """Run a query to get the plugin files for an entrypoint.

        Args:
            entrypoint_snapshot_id: The Snapshot ID of the entrypoint to get the plugin
            files for.

        Returns:
            The plugin files for the entrypoint.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("get plugin files", resource_snapshot_id=entrypoint_snapshot_id)

        entry_point = self.get(
            entrypoint_id=entrypoint_id,
            entrypoint_snapshot_id=entrypoint_snapshot_id,
            log=log,
        )
        return [
            plugin_plugin_file
            for artifact_plugin in entry_point.entry_point_artifact_plugins
            for plugin_plugin_file in artifact_plugin.plugin.plugin_plugin_files
        ]

    def get_group_plugin_parameter_types(
        self, group_id: int, **kwargs
    ) -> list[models.PluginTaskParameterType]:
        """Run a query to get the plugin task parameter types associated with a group.

        Args:
            group_id: The group id for which to get the plugin task parameter types.
            log: A structlog logger object to use for logging. A new logger will be
                created if None.

        Returns:
            The plugin files for the Job's entrypoint.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841

        plugin_parameter_types_stmt = (
            select(models.PluginTaskParameterType)
            .join(models.Resource)
            .where(
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.group_id == group_id,
                models.Resource.latest_snapshot_id
                == models.PluginTaskParameterType.resource_snapshot_id,
            )
        )
        return list(db.session.scalars(plugin_parameter_types_stmt).all())


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
    ) -> list[utils.PluginWithFilesDict]:
        """Fetch the plugin snapshots for an entrypoint by its unique id.

        Args:
            entrypoint_id: The unique id of the entrypoint.

        Returns:
            The plugin snapshots for the entrypoint.

        Raises:
            EntityDoesNotExistError: If the entrypoint is not found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get entrypoint by id", entrypoint_id=entrypoint_id)

        entrypoint = self._entrypoint_id_service.get(entrypoint_id, log=log)

        return _get_entrypoint_plugin_snapshots(entrypoint["entry_point"])

    def append(
        self,
        entrypoint_id: int,
        plugin_ids: list[int],
        commit: bool = True,
        **kwargs,
    ) -> list[utils.PluginWithFilesDict]:
        """Append plugins to an entrypoint.

        Args:
            entrypoint_id: The unique id of the entrypoint.
            plugin_ids: The plugins to be appended. If a plugin is already attached
                to the entrypoint, it is synced to the latest snapshot.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The updated entrypoint object.

        Raises:
            EntityDoesNotExistError: If the entrypoint is not found.
            EntityExistsError: If the entrypoint name already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        entrypoint = self._entrypoint_id_service.get(entrypoint_id, log=log)[
            "entry_point"
        ]
        # make sure the ids are unique

        plugin_id_set = set(plugin_ids)
        plugin_ids = list(plugin_id_set)
        # check this early
        _ensure_no_plugin_task_overlap(
            plugin_ids,
            [
                artifact_plugin.plugin.resource_id
                for artifact_plugin in entrypoint.entry_point_artifact_plugins
            ],
            True,
        )

        new_entrypoint = models.EntryPoint(
            name=entrypoint.name,
            description=entrypoint.description,
            task_graph=entrypoint.task_graph,
            artifact_graph=entrypoint.artifact_graph,
            parameters=_copy_parameters(entrypoint.parameters),
            artifact_parameters=_copy_artifact_parameters(
                entrypoint.artifact_parameters
            ),
            resource=entrypoint.resource,
            creator=current_user,
        )
        db.session.add(new_entrypoint)

        # copy over the existing plugins (except the ones which need to be updated)
        plugin_resources = _copy_plugins(
            plugins=filter(
                lambda p: p.plugin.resource_id not in plugin_id_set,
                entrypoint.entry_point_plugins,
            ),
            target_entrypoint=new_entrypoint,
        )

        # now add to the existing plugins (gets the latest version)
        for plugin in self._plugin_ids_service.get(plugin_ids, error_if_not_found=True):
            new_plugin = models.EntryPointPlugin(
                entry_point=new_entrypoint, plugin=plugin["plugin"]
            )
            new_entrypoint.entry_point_plugins.append(new_plugin)
            plugin_resources.append(new_plugin.plugin.resource)

        # artifact plugins stay the same, task plugins are changing
        artifact_plugin_resources = _copy_artifact_plugins(
            artifact_plugins=entrypoint.entry_point_artifact_plugins,
            target_entrypoint=new_entrypoint,
        )

        queue_resources = [
            resource
            for resource in entrypoint.children
            if resource.resource_type == "queue"
        ]

        new_entrypoint.children = (
            plugin_resources + queue_resources + artifact_plugin_resources
        )

        if commit:
            db.session.commit()
            log.debug(
                "Plugins appended to Entrypoint successfully",
                entrypoint_id=entrypoint_id,
                plugin_ids=plugin_ids,
            )

        return _get_entrypoint_plugin_snapshots(new_entrypoint)


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
        **kwargs,
    ) -> utils.PluginWithFilesDict:
        """Fetch the plugin snapshots for an entrypoint by its unique id.

        Args:
            entrypoint_id: The unique id of the entrypoint.

        Returns:
            The plugin snapshots for the entrypoint.

        Raises:
            EntityDoesNotExistError: If the entrypoint or plugin is not found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get entrypoint by id", entrypoint_id=entrypoint_id)

        entrypoint = self._entrypoint_id_service.get(entrypoint_id, log=log)[
            "entry_point"
        ]

        plugin = [
            entry_point_plugin.plugin
            for entry_point_plugin in entrypoint.entry_point_plugins
            if plugin_id == entry_point_plugin.plugin.resource_id
        ]

        if not plugin:
            raise EntityDoesNotExistError(
                PLUGIN_RESOURCE_TYPE, entrypoint_id=entrypoint_id, plugin_id=plugin_id
            )

        return utils.PluginWithFilesDict(
            plugin=plugin[0], plugin_files=plugin[0].plugin_files, has_draft=None
        )

    def delete(
        self,
        entrypoint_id: int,
        plugin_id: int,
        commit: bool = True,
        **kwargs,
    ) -> dict[str, Any]:
        """Remove a plugin from an entrypoint.

        Args:
            entrypoint_id: The unique id of the entrypoint.
            plugin_id: The plugin to be removed.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            A dictionary reporting the status of the request.

        Raises:
            EntityDoesNotExistError: If the entrypoint or plugin is not found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        entrypoint = self._entrypoint_id_service.get(entrypoint_id, log=log)[
            "entry_point"
        ]

        plugin_ids = {
            plugin.plugin.resource_id for plugin in entrypoint.entry_point_plugins
        }
        if plugin_id not in plugin_ids:
            raise EntityDoesNotExistError(
                PLUGIN_RESOURCE_TYPE, entrypoint_id=entrypoint_id, plugin_id=plugin_id
            )

        # create a new snapshot with the plugin removed
        new_entrypoint = models.EntryPoint(
            name=entrypoint.name,
            description=entrypoint.description,
            task_graph=entrypoint.task_graph,
            artifact_graph=entrypoint.artifact_graph,
            parameters=_copy_parameters(entrypoint.parameters),
            artifact_parameters=_copy_artifact_parameters(
                entrypoint.artifact_parameters
            ),
            resource=entrypoint.resource,
            creator=current_user,
        )
        db.session.add(new_entrypoint)

        artifact_plugin_resources = _copy_artifact_plugins(
            artifact_plugins=entrypoint.entry_point_artifact_plugins,
            target_entrypoint=new_entrypoint,
        )
        # copy all plugins but the one targeted for deletion
        plugin_resources = _copy_plugins(
            plugins=filter(
                lambda p: p.plugin.resource_id != plugin_id,
                entrypoint.entry_point_plugins,
            ),
            target_entrypoint=new_entrypoint,
        )

        queue_resources = [
            resource
            for resource in entrypoint.children
            if resource.resource_type == "queue"
        ]

        new_entrypoint.children = (
            plugin_resources + queue_resources + artifact_plugin_resources
        )

        if commit:
            db.session.commit()
            log.debug(
                "Plugin removed from entrypoint",
                entrypoint_id=entrypoint_id,
                plugin_id=plugin_id,
            )

        return {"status": "Success", "id": [plugin_id]}


class EntrypointIdArtifactPluginsService(object):
    """
    The service methods for creating and managing artifact plugins for an entrypoint.
    """

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
    ) -> list[utils.PluginWithFilesDict]:
        """Fetch the artifact plugin snapshots for an entrypoint by its unique id.

        Args:
            entrypoint_id: The unique id of the entrypoint.

        Returns:
            The artifact plugin snapshots for the entrypoint.

        Raises:
            EntityDoesNotExistError: If the entrypoint is not found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get entrypoint by id", entrypoint_id=entrypoint_id)

        entrypoint = self._entrypoint_id_service.get(entrypoint_id, log=log)

        return _get_entrypoint_artifact_plugin_snapshots(entrypoint["entry_point"])

    def append(
        self,
        entrypoint_id: int,
        artifact_plugin_ids: list[int],
        commit: bool = True,
        **kwargs,
    ) -> list[utils.PluginWithFilesDict]:
        """Append artifact plugins to an entrypoint.

        Args:
            entrypoint_id: The unique id of the entrypoint.
            artifact_plugin_ids: The plugins to be appended. If an artifact
                plugin is already attached to the entrypoint, it is synced to
                the latest snapshot.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The updated entrypoint object.

        Raises:
            EntityDoesNotExistError: If the entrypoint is not found.
            EntityExistsError: If the entrypoint name already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        entrypoint = self._entrypoint_id_service.get(entrypoint_id, log=log)[
            "entry_point"
        ]

        artifact_plugin_id_set = set(artifact_plugin_ids)
        artifact_plugin_ids = list(artifact_plugin_id_set)
        _ensure_no_plugin_task_overlap(
            [plugin.plugin.resource_id for plugin in entrypoint.entry_point_plugins],
            artifact_plugin_ids,
            False,
        )

        new_entrypoint = models.EntryPoint(
            name=entrypoint.name,
            description=entrypoint.description,
            task_graph=entrypoint.task_graph,
            artifact_graph=entrypoint.artifact_graph,
            parameters=_copy_parameters(entrypoint.parameters),
            artifact_parameters=_copy_artifact_parameters(
                entrypoint.artifact_parameters
            ),
            resource=entrypoint.resource,
            creator=current_user,
        )
        db.session.add(new_entrypoint)

        # plugins stay the same, artifact plugins are changing
        plugin_resources = _copy_plugins(
            plugins=entrypoint.entry_point_plugins, target_entrypoint=new_entrypoint
        )

        # copy over existing artifact plugins (except the ones which need to be updated)
        artifact_plugin_resources = _copy_artifact_plugins(
            artifact_plugins=filter(
                lambda a: a.plugin.resource_id not in artifact_plugin_id_set,
                entrypoint.entry_point_artifact_plugins,
            ),
            target_entrypoint=new_entrypoint,
        )

        # now add to the existing artfiact plugins (gets the latest version)
        for plugin in self._plugin_ids_service.get(
            artifact_plugin_ids, error_if_not_found=True
        ):
            new_plugin = models.EntryPointArtifactPlugin(
                entry_point=new_entrypoint, plugin=plugin["plugin"]
            )
            new_entrypoint.entry_point_artifact_plugins.append(new_plugin)
            artifact_plugin_resources.append(new_plugin.plugin.resource)

        queue_resources = [
            resource
            for resource in entrypoint.children
            if resource.resource_type == "queue"
        ]

        new_entrypoint.children = (
            plugin_resources + queue_resources + artifact_plugin_resources
        )

        if commit:
            db.session.commit()
            log.debug(
                "Artifact Plugins appended to Entrypoint successfully",
                entrypoint_id=entrypoint_id,
                plugin_ids=artifact_plugin_ids,
            )

        return _get_entrypoint_artifact_plugin_snapshots(new_entrypoint)


class EntrypointIdArtifactPluginsIdService(object):
    """The service methods for creating and managing the artifact plugins for a specific
    entrypoint by their unique id."""

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
        artifact_plugin_id: int,
        **kwargs,
    ) -> utils.PluginWithFilesDict:
        """Fetch the artifact plugin snapshots for an entrypoint by its unique id.

        Args:
            entrypoint_id: The unique id of the entrypoint.
            artifact_plugin_id: the artifact plugin id

        Returns:
            The artifact plugin snapshots for the entrypoint.

        Raises:
            EntityDoesNotExistError: If the entrypoint or artifact plugin is not found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get entrypoint by id", entrypoint_id=entrypoint_id)

        entrypoint = self._entrypoint_id_service.get(entrypoint_id, log=log)[
            "entry_point"
        ]

        artifact_plugin = [
            entry_point_artifact_plugin.plugin
            for entry_point_artifact_plugin in entrypoint.entry_point_artifact_plugins
            if artifact_plugin_id == entry_point_artifact_plugin.plugin.resource_id
        ]

        if not artifact_plugin:
            raise EntityDoesNotExistError(
                PLUGIN_RESOURCE_TYPE,
                entrypoint_id=entrypoint_id,
                plugin_id=artifact_plugin_id,
            )

        return utils.PluginWithFilesDict(
            plugin=artifact_plugin[0],
            plugin_files=artifact_plugin[0].plugin_files,
            has_draft=None,
        )

    def delete(
        self,
        entrypoint_id: int,
        artifact_plugin_id: int,
        commit: bool = True,
        **kwargs,
    ) -> dict[str, Any]:
        """Remove an artifact plugin from an entrypoint.

        Args:
            entrypoint_id: The unique id of the entrypoint.
            artifact_plugin_id: The artifact plugin to be removed.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            A dictionary reporting the status of the request.

        Raises:
            EntityDoesNotExistError: If the entrypoint or artifact plugin is not found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        entrypoint = self._entrypoint_id_service.get(entrypoint_id, log=log)[
            "entry_point"
        ]

        artifact_plugin_ids = {
            artifact_plugin.plugin.resource_id
            for artifact_plugin in entrypoint.entry_point_artifact_plugins
        }
        if artifact_plugin_id not in artifact_plugin_ids:
            raise EntityDoesNotExistError(
                PLUGIN_RESOURCE_TYPE,
                entrypoint_id=entrypoint_id,
                artifact_plugin_id=artifact_plugin_id,
            )

        # create a new snapshot with the artifact plugin removed
        new_entrypoint = models.EntryPoint(
            name=entrypoint.name,
            description=entrypoint.description,
            task_graph=entrypoint.task_graph,
            artifact_graph=entrypoint.artifact_graph,
            parameters=_copy_parameters(entrypoint.parameters),
            artifact_parameters=_copy_artifact_parameters(
                entrypoint.artifact_parameters
            ),
            resource=entrypoint.resource,
            creator=current_user,
        )
        db.session.add(new_entrypoint)

        # plugins stay the same, artifact plugins are changing
        plugin_resources = _copy_plugins(
            plugins=entrypoint.entry_point_plugins, target_entrypoint=new_entrypoint
        )

        # copy over artifact plugins but the one targeted for deletion
        artifact_plugin_resources = _copy_artifact_plugins(
            artifact_plugins=filter(
                lambda a: a.plugin.resource_id != artifact_plugin_id,
                entrypoint.entry_point_artifact_plugins,
            ),
            target_entrypoint=new_entrypoint,
        )

        queue_resources = [
            resource
            for resource in entrypoint.children
            if resource.resource_type == "queue"
        ]

        new_entrypoint.children = (
            plugin_resources + queue_resources + artifact_plugin_resources
        )

        if commit:
            db.session.commit()
            log.debug(
                "Artifact Plugin removed from entrypoint",
                entrypoint_id=entrypoint_id,
                artifact_plugin_id=artifact_plugin_id,
            )

        return {"status": "Success", "id": [artifact_plugin_id]}


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
            EntityDoesNotExistError: If the entrypoint is not found and
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
            entrypoint_ids_missing = set(entrypoint_ids) - {
                entrypoint.resource_id for entrypoint in entrypoints
            }
            raise EntityDoesNotExistError(
                RESOURCE_TYPE, entrypoint_ids=list(entrypoint_ids_missing)
            )

        return entrypoints


class EntrypointIdQueuesService(object):
    """The service methods for managing queues attached to an entrypoint."""

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
        **kwargs,
    ) -> list[models.Queue]:
        """Fetch the list of queues for an entrypoint.

        Args:
            entrypoint_id: The unique id of the entrypoint.
            error_if_not_found: If True, raise an error if the entrypoint is not found.
                Defaults to False.

        Returns:
            The list of plugins.

        Raises:
            EntityDoesNotExistError: If the entrypoint is not found and
                `error_if_not_found` is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug(
            "Get queues for an entrypoint by resource id", resource_id=entrypoint_id
        )

        entrypoint_dict = self._entrypoint_id_service.get(entrypoint_id, log=log)
        return entrypoint_dict["queues"]

    def append(
        self,
        entrypoint_id: int,
        queue_ids: list[int],
        commit: bool = True,
        **kwargs,
    ) -> list[models.Queue] | None:
        """Append one or more Queues to an entrypoint

        Args:
            entrypoint_id: The unique id of the entrypoint.
            queue_ids: The list of queue ids to append.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The updated list of queues resource objects.

        Raises:
            EntityDoesNotExistError: If the resource is not found
            EntityDoesNotExistError: If one or more queues are not found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug(
            "Append queues to an entrypoint by resource id", resource_id=entrypoint_id
        )

        entrypoint_dict = self._entrypoint_id_service.get(entrypoint_id, log=log)
        entrypoint = entrypoint_dict["entry_point"]
        queues = entrypoint_dict["queues"]

        existing_queue_ids = {
            resource.resource_id
            for resource in entrypoint.children
            if resource.resource_type == "queue"
        }
        new_queue_ids = set(queue_ids) - existing_queue_ids
        new_queues = self._queue_ids_service.get(
            list(new_queue_ids), error_if_not_found=True, log=log
        )

        entrypoint.children.extend([queue.resource for queue in new_queues])

        if commit:
            db.session.commit()
            log.debug("Queues appended successfully", queue_ids=queue_ids)

        return queues + new_queues

    def modify(
        self,
        entrypoint_id: int,
        queue_ids: list[int],
        commit: bool = True,
        **kwargs,
    ) -> list[models.Queue]:
        """Modify the list of queues for an entrypoint.

        Args:
            entrypoint_id: The unique id of the entrypoint.
            queue_ids: The list of queue ids to append.
            error_if_not_found: If True, raise an error if the resource is not found.
                Defaults to False.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The updated queue resource object.

        Raises:
            EntityDoesNotExistError: If the resource is not found and
                `error_if_not_found` is True.
            EntityDoesNotExistError: If one or more queues are not found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        entrypoint_dict = self._entrypoint_id_service.get(entrypoint_id, log=log)
        entrypoint = entrypoint_dict["entry_point"]

        queues = self._queue_ids_service.get(
            queue_ids, error_if_not_found=True, log=log
        )

        plugin_resources = [
            resource
            for resource in entrypoint.children
            if resource.resource_type == "plugin"
        ]
        queue_resources = [queue.resource for queue in queues]
        entrypoint.children = plugin_resources + queue_resources

        if commit:
            db.session.commit()
            log.debug("Entrypoint queues updated successfully", queue_ids=queue_ids)

        return queues

    def delete(self, entrypoint_id: int, **kwargs) -> dict[str, Any]:
        """Remove queues from an entrypoint.

        Args:
            entrypoint_id: The unique id of the entrypoint.

        Returns:
            A dictionary reporting the status of the request.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        entrypoint_dict = self._entrypoint_id_service.get(entrypoint_id, log=log)
        entrypoint = entrypoint_dict["entry_point"]
        entrypoint.children = [
            resource
            for resource in entrypoint.children
            if resource.resource_type == "plugin"
        ]

        queue_ids = [queue.resource_id for queue in entrypoint_dict["queues"]]

        db.session.commit()
        log.debug(
            "Queues removed from entrypoint",
            entrypoint_id=entrypoint_id,
            queue_ids=queue_ids,
        )

        return {"status": "Success", "id": queue_ids}


class EntrypointIdQueuesIdService(object):
    """The service methods for removing a queue attached to an entrypoint."""

    @inject
    def __init__(
        self,
        entrypoint_id_service: EntrypointIdService,
    ) -> None:
        """Initialize the entrypoint service.

        All arguments are provided via dependency injection.

        Args:
            entrypoint_id_service: A EntrypointIdService object.
        """
        self._entrypoint_id_service = entrypoint_id_service

    def delete(self, entrypoint_id: int, queue_id, **kwargs) -> dict[str, Any]:
        """Remove a queue from an entrypoint.

        Args:
            entrypoint_id: The unique id of the entrypoint.
            queue_id: The unique id of the queue.

        Returns:
            A dictionary reporting the status of the request.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        entrypoint_dict = self._entrypoint_id_service.get(entrypoint_id, log=log)
        entrypoint = entrypoint_dict["entry_point"]

        queue_resources = {
            resource.resource_id: resource
            for resource in entrypoint.children
            if resource.resource_type == "queue"
        }

        removed_queue = queue_resources.pop(queue_id, None)

        if removed_queue is None:
            raise EntityDoesNotExistError(QUEUE_RESOURCE_TYPE, queue_id=queue_id)

        plugin_resources = [
            resource
            for resource in entrypoint.children
            if resource.resource_type == "plugin"
        ]
        entrypoint.children = plugin_resources + list(queue_resources.values())

        db.session.commit()
        log.debug("Queue removed", entrypoint_id=entrypoint_id, queue_id=queue_id)

        return {"status": "Success", "id": [queue_id]}


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
            EntityDoesNotExistError: If the entrypoint is not found and
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
                raise EntityDoesNotExistError(
                    RESOURCE_TYPE, name=name, group_id=group_id
                )

            return None

        return entrypoint


def _get_entrypoint_plugin_snapshots(
    entrypoint: models.EntryPoint,
) -> list[utils.PluginWithFilesDict]:
    return [
        utils.PluginWithFilesDict(
            plugin=entry_point_plugin.plugin,
            plugin_files=entry_point_plugin.plugin.plugin_files,
            has_draft=False,
        )
        for entry_point_plugin in entrypoint.entry_point_plugins
    ]


def _get_entrypoint_artifact_plugin_snapshots(
    entrypoint: models.EntryPoint,
) -> list[utils.PluginWithFilesDict]:
    return [
        utils.PluginWithFilesDict(
            plugin=entry_point_artifact_plugin.plugin,
            plugin_files=entry_point_artifact_plugin.plugin.plugin_files,
            has_draft=False,
        )
        for entry_point_artifact_plugin in entrypoint.entry_point_artifact_plugins
    ]


def _ensure_no_plugin_task_overlap(
    plugins: list[int],
    artifact_plugins: list[int],
    addingPlugins: bool = True,
):
    intersection = set(plugins).intersection(artifact_plugins)
    if len(intersection) > 0:
        if addingPlugins:
            raise PluginTaskArtifactTaskOverlapError(str(intersection))
        else:
            raise ArtifactTaskPluginTaskOverlapError(str(intersection))


def _copy_plugins(
    plugins: Iterable[models.EntryPointPlugin], target_entrypoint: models.EntryPoint
) -> list[models.Resource]:
    target_entrypoint.entry_point_plugins = [
        models.EntryPointPlugin(
            entry_point=target_entrypoint,
            plugin=plugin.plugin,
        )
        for plugin in plugins
    ]
    # return a unique list of plugin resources
    return list(
        {
            plugin.plugin.resource_id: plugin.plugin.resource
            for plugin in target_entrypoint.entry_point_plugins
        }.values()
    )


def _copy_artifact_plugins(
    artifact_plugins: Iterable[models.EntryPointArtifactPlugin],
    target_entrypoint: models.EntryPoint,
) -> list[models.Resource]:
    target_entrypoint.entry_point_artifact_plugins = [
        models.EntryPointArtifactPlugin(
            entry_point=target_entrypoint,  # pyright: ignore
            plugin=artifact_plugin.plugin,  # pyright: ignore
        )
        for artifact_plugin in artifact_plugins
    ]
    # return a unique list of artifact plugin resources
    return list(
        {
            artifact_plugin.plugin.resource_id: artifact_plugin.plugin.resource
            for artifact_plugin in target_entrypoint.entry_point_artifact_plugins
        }.values()
    )


def _create_parameters(
    parameters: list[dict[str, Any]],
) -> Iterable[models.EntryPointParameter]:
    params = [
        models.EntryPointParameter(
            name=param["name"],
            default_value=param["default_value"],
            parameter_type=param["parameter_type"],
            parameter_number=i,
        )
        for i, param in enumerate(parameters)
    ]

    coerce_entrypoint_default_param_types(params)

    return params


def _copy_parameters(
    parameters: list[models.EntryPointParameter],
) -> Iterable[models.EntryPointParameter]:
    return [
        models.EntryPointParameter(
            name=param.name,
            default_value=param.default_value,
            parameter_type=param.parameter_type,
            parameter_number=param.parameter_number,
        )
        for param in parameters
    ]


def _create_artifact_parameters(
    artifact_parameters: list[dict[str, Any]], log: BoundLogger
) -> Iterable[models.EntryPointArtifactParameter]:
    if artifact_parameters is None or len(artifact_parameters) == 0:
        return []
    for artifact in artifact_parameters:
        duplicates = find_non_unique("name", artifact["output_params"])
        if len(duplicates) > 0:
            raise QueryParameterNotUniqueError(
                "artifact output parameter",
                artifact_parameter_name=artifact["name"],
                parameter_names=duplicates,
            )

    type_ids = [
        parameter["parameter_type_id"]
        for artifact in artifact_parameters
        for parameter in artifact["output_params"]
    ]
    id_type_map = get_plugin_task_parameter_types_by_id(ids=type_ids, log=log)

    return [
        models.EntryPointArtifactParameter(
            name=artifact["name"],
            artifact_number=a,
            output_parameters=[
                models.EntryPointArtifactOutputParameter(
                    name=param["name"],
                    parameter_number=p,
                    parameter_type=id_type_map[param["parameter_type_id"]],
                )
                for p, param in enumerate(artifact["output_params"])
            ],
        )
        for a, artifact in enumerate(artifact_parameters)
    ]


def _copy_artifact_parameters(
    artifact_parameters: list[models.EntryPointArtifactParameter],
) -> Iterable[models.EntryPointArtifactParameter]:
    return [
        models.EntryPointArtifactParameter(
            name=artifact.name,
            artifact_number=index,
            output_parameters=[
                models.EntryPointArtifactOutputParameter(
                    name=param.name,
                    parameter_number=p,
                    parameter_type=param.parameter_type,
                )
                for p, param in enumerate(artifact.output_parameters)
            ],
        )
        for index, artifact in enumerate(artifact_parameters)
    ]
