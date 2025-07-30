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
"""The server-side functions that perform plugin endpoint operations."""

import itertools
from typing import Any, Final, Iterable, cast

import structlog
from flask_login import current_user
from injector import inject
from sqlalchemy import Integer, func, select
from sqlalchemy.orm import aliased
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import db, models
from dioptra.restapi.db.models.constants import resource_lock_types
from dioptra.restapi.errors import (
    BackendDatabaseError,
    EntityDoesNotExistError,
    EntityExistsError,
    QueryParameterNotUniqueError,
    SortParameterValidationError,
)
from dioptra.restapi.utils import find_non_unique
from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.groups.service import GroupIdService
from dioptra.restapi.v1.plugin_parameter_types.service import (
    get_plugin_task_parameter_types_by_id,
)
from dioptra.restapi.v1.shared.search_parser import construct_sql_query_filters

LOGGER: BoundLogger = structlog.stdlib.get_logger()

PLUGIN_RESOURCE_TYPE: Final[str] = "plugin"
PLUGIN_FILE_RESOURCE_TYPE: Final[str] = "plugin_file"
PLUGIN_TASK_RESOURCE_TYPE: Final[str] = "plugin_task"
PLUGIN_SEARCHABLE_FIELDS: Final[dict[str, Any]] = {
    "name": lambda x: models.Plugin.name.like(x, escape="/"),
    "description": lambda x: models.Plugin.description.like(x, escape="/"),
    "tag": lambda x: models.Plugin.tags.any(models.Tag.name.like(x, escape="/")),
}
PLUGIN_FILE_SEARCHABLE_FIELDS: Final[dict[str, Any]] = {
    "filename": lambda x: models.PluginFile.filename.like(x, escape="/"),
    "description": lambda x: models.PluginFile.description.like(x, escape="/"),
    "contents": lambda x: models.PluginFile.contents.like(x, escape="/"),
    "tag": lambda x: models.PluginFile.tags.any(models.Tag.name.like(x, escape="/")),
}
PLUGIN_SORTABLE_FIELDS: Final[dict[str, Any]] = {
    "name": models.Plugin.name,
    "createdOn": models.Plugin.created_on,
    "lastModifiedOn": models.Resource.last_modified_on,
    "description": models.Plugin.description,
}
PLUGIN_FILE_SORTABLE_FIELDS: Final[dict[str, Any]] = {
    "filename": models.PluginFile.filename,
    "createdOn": models.PluginFile.created_on,
    "lastModifiedOn": models.Resource.last_modified_on,
    "description": models.PluginFile.description,
}


class PluginService(object):
    @inject
    def __init__(
        self, plugin_name_service: "PluginNameService", group_id_service: GroupIdService
    ) -> None:
        """Initialize the plugin service.

        All arguments are provided via dependency injection.

        Args:
            plugin_name_service: A PluginNameService object.
            group_id_service: A GroupIdService object.
        """
        self._plugin_name_service = plugin_name_service
        self._group_id_service = group_id_service

    def create(
        self,
        name: str,
        description: str | None,
        group_id: int,
        commit: bool = True,
        **kwargs,
    ) -> utils.PluginWithFilesDict:
        """Create a new plugin.

        Args:
            name: The name of the plugin. The combination of name and group_id must be
                unique.
            description: The description of the plugin.
            group_id: The group that will own the plugin.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The newly created plugin object.

        Raises:
            EntityExistsError: If a plugin with the given name already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        duplicate = self._plugin_name_service.get(name, group_id=group_id, log=log)
        if duplicate is not None:
            raise EntityExistsError(
                PLUGIN_RESOURCE_TYPE,
                duplicate.resource_id,
                name=name,
                group_id=group_id,
            )

        group = self._group_id_service.get(group_id, error_if_not_found=True)

        resource = models.Resource(resource_type="plugin", owner=group)
        new_plugin = models.Plugin(
            name=name, description=description, resource=resource, creator=current_user
        )
        db.session.add(new_plugin)

        if commit:
            db.session.commit()
            log.debug(
                "Plugin registration successful",
                plugin_id=new_plugin.resource_id,
                name=new_plugin.name,
            )

        plugin_dict = utils.PluginWithFilesDict(
            plugin=new_plugin, plugin_files=[], has_draft=False
        )
        return plugin_dict

    def get(
        self,
        group_id: int | None,
        search_string: str,
        page_index: int,
        page_length: int,
        sort_by_string: str,
        descending: bool,
        **kwargs,
    ) -> tuple[list[utils.PluginWithFilesDict], int]:
        """Fetch a list of plugins, optionally filtering by search string and paging
        parameters.

        Args:
            group_id: A group ID used to filter results.
            search_string: A search string used to filter results.
            page_index: The index of the first group to be returned.
            page_length: The maximum number of plugins to be returned.
            sort_by_string: The name of the column to sort.
            descending: Boolean indicating whether to sort by descending or not.

        Returns:
            A tuple containing a list of plugins and the total number of plugins
            matching the query.

        Raises:
            SearchNotImplementedError: If a search string is provided.
            BackendDatabaseError: If the database query returns a None when counting
                the number of plugins.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get full list of plugins")

        filters = list()

        if group_id is not None:
            filters.append(models.Resource.group_id == group_id)

        if search_string:
            filters.append(
                construct_sql_query_filters(search_string, PLUGIN_SEARCHABLE_FIELDS)
            )

        stmt = (
            select(func.count(models.Plugin.resource_id))
            .join(models.Resource)
            .where(
                *filters,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.Plugin.resource_snapshot_id,
            )
        )
        total_num_plugins = db.session.scalar(stmt)

        if total_num_plugins is None:
            log.error(
                "The database query returned a None when counting the number of "
                "groups when it should return a number.",
                sql=str(stmt),
            )
            raise BackendDatabaseError

        if total_num_plugins == 0:
            return [], total_num_plugins

        # get latest plugin snapshots
        latest_plugins_stmt = (
            select(models.Plugin)
            .join(models.Resource)
            .where(
                *filters,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.Plugin.resource_snapshot_id,
            )
            .offset(page_index)
            .limit(page_length)
        )

        if sort_by_string and sort_by_string in PLUGIN_SORTABLE_FIELDS:
            sort_column = PLUGIN_SORTABLE_FIELDS[sort_by_string]
            if descending:
                sort_column = sort_column.desc()
            else:
                sort_column = sort_column.asc()
            latest_plugins_stmt = latest_plugins_stmt.order_by(sort_column)
        elif sort_by_string and sort_by_string not in PLUGIN_SORTABLE_FIELDS:
            raise SortParameterValidationError(PLUGIN_RESOURCE_TYPE, sort_by_string)

        plugins = db.session.scalars(latest_plugins_stmt).all()

        plugins_dict: dict[int, utils.PluginWithFilesDict] = {
            plugin.resource_id: utils.PluginWithFilesDict(
                plugin=plugin, plugin_files=plugin.plugin_files, has_draft=False
            )
            for plugin in plugins
        }

        drafts_stmt = select(
            models.DraftResource.payload["resource_id"].as_string().cast(Integer)
        ).where(
            models.DraftResource.payload["resource_id"]
            .as_string()
            .cast(Integer)
            .in_(
                tuple(plugin["plugin"].resource_id for plugin in plugins_dict.values())
            ),
            models.DraftResource.user_id == current_user.user_id,
        )
        for resource_id in db.session.scalars(drafts_stmt):
            plugins_dict[resource_id]["has_draft"] = True

        return list(plugins_dict.values()), total_num_plugins


class PluginIdService(object):
    """The service methods for registering and managing plugins by their unique id."""

    @inject
    def __init__(
        self,
        plugin_name_service: "PluginNameService",
    ) -> None:
        """Initialize the plugin service.

        All arguments are provided via dependency injection.

        Args:
            plugin_name_service: A pluginNameService object.
        """
        self._plugin_name_service = plugin_name_service

    def get(
        self,
        plugin_id: int,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> utils.PluginWithFilesDict | None:
        """Fetch a plugin by its unique id.

        Args:
            plugin_id: The unique id of the plugin.
            error_if_not_found: If True, raise an error if the plugin is not found.
                Defaults to False.

        Returns:
            The plugin object if found, otherwise None.

        Raises:
            EntityDoesNotExistError: If the plugin is not found and `error_if_not_found`
                is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get plugin by id", plugin_id=plugin_id)

        stmt = (
            select(models.Plugin)
            .join(models.Resource)
            .where(
                models.Plugin.resource_id == plugin_id,
                models.Plugin.resource_snapshot_id
                == models.Resource.latest_snapshot_id,
                models.Resource.is_deleted == False,  # noqa: E712
            )
        )
        plugin = db.session.scalar(stmt)

        if plugin is None:
            if error_if_not_found:
                raise EntityDoesNotExistError(PLUGIN_RESOURCE_TYPE, plugin_id=plugin_id)

            return None

        drafts_stmt = (
            select(models.DraftResource.draft_resource_id)
            .where(
                models.DraftResource.payload["resource_id"].as_string().cast(Integer)
                == plugin.resource_id,
                models.DraftResource.user_id == current_user.user_id,
            )
            .exists()
            .select()
        )
        has_draft = db.session.scalar(drafts_stmt)

        return utils.PluginWithFilesDict(
            plugin=plugin, plugin_files=plugin.plugin_files, has_draft=has_draft
        )

    def modify(
        self,
        plugin_id: int,
        name: str,
        description: str,
        error_if_not_found: bool = False,
        commit: bool = True,
        **kwargs,
    ) -> utils.PluginWithFilesDict | None:
        """Rename a plugin.

        Args:
            plugin_id: The unique id of the plugin.
            name: The new name of the plugin.
            description: The new description of the plugin.
            error_if_not_found: If True, raise an error if the plugin is not found.
                Defaults to False.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The updated plugin object.

        Raises:
            EntityDoesNotExistError: If the plugin is not found and `error_if_not_found`
                is True.
            EntityExistsError: If the plugin name already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        plugin_dict = self.get(
            plugin_id, error_if_not_found=error_if_not_found, log=log
        )

        if plugin_dict is None:
            return None

        plugin = plugin_dict["plugin"]
        plugin_files = plugin_dict["plugin_files"]
        group_id = plugin.resource.group_id

        if name != plugin.name:
            duplicate = self._plugin_name_service.get(name, group_id=group_id, log=log)
            if duplicate is not None:
                raise EntityExistsError(
                    PLUGIN_RESOURCE_TYPE,
                    duplicate.resource_id,
                    name=name,
                    group_id=group_id,
                )

        new_plugin = models.Plugin(
            name=name,
            description=description,
            resource=plugin.resource,
            creator=current_user,
        )
        db.session.add(new_plugin)

        for plugin_file in plugin_files:
            plugin_plugin_file = models.PluginPluginFile(
                plugin=new_plugin, plugin_file=plugin_file
            )
            db.session.add(plugin_plugin_file)

        if commit:
            db.session.commit()
            log.debug(
                "Plugin modification successful",
                plugin_id=plugin_id,
                name=name,
                description=description,
            )

        return utils.PluginWithFilesDict(
            plugin=new_plugin, plugin_files=plugin_files, has_draft=False
        )

    def delete(self, plugin_id: int, **kwargs) -> dict[str, Any]:
        """Delete a plugin.

        Args:
            plugin_id: The unique id of the plugin.

        Returns:
            A dictionary reporting the status of the request.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        stmt = select(models.Resource).filter_by(
            resource_id=plugin_id, resource_type=PLUGIN_RESOURCE_TYPE, is_deleted=False
        )
        plugin_resource = db.session.scalar(stmt)

        if plugin_resource is None:
            raise EntityDoesNotExistError(PLUGIN_RESOURCE_TYPE, plugin_id=plugin_id)

        deleted_resource_lock = models.ResourceLock(
            resource_lock_type=resource_lock_types.DELETE,
            resource=plugin_resource,
        )
        db.session.add(deleted_resource_lock)

        plugin_file_resources = [
            child
            for child in plugin_resource.children
            if child.resource_type == PLUGIN_FILE_RESOURCE_TYPE
        ]
        plugin_file_ids = [
            plugin_file_resource.resource_id
            for plugin_file_resource in plugin_file_resources
        ]
        for plugin_file_resource in plugin_file_resources:
            deleted_resource_lock = models.ResourceLock(
                resource_lock_type=resource_lock_types.DELETE,
                resource=plugin_file_resource,
            )
            db.session.add(deleted_resource_lock)

        db.session.commit()

        log.debug(
            "Plugin and associated files deleted",
            plugin_id=plugin_id,
            plugin_file_ids=plugin_file_ids,
        )

        return {
            "status": "Success",
            "plugin_id": plugin_id,
            "file_ids": plugin_file_ids,
        }


class PluginIdsService(object):
    """The service methods for registering and managing plugins by their unique id."""

    def get(
        self,
        plugin_ids: list[int],
        error_if_not_found: bool = False,
        **kwargs,
    ) -> list[utils.PluginWithFilesDict]:
        """Fetch a plugin by its unique id.

        Args:
            plugin_ids: The unique ids of the plugins.
            error_if_not_found: If True, raise an error if the plugin is not found.
                Defaults to False.

        Returns:
            A list of  plugin objects.

        Raises:
            EntityDoesNotExistError: If the plugin is not found and `error_if_not_found`
                is True.
        """
        latest_plugins_stmt = (
            select(models.Plugin)
            .join(models.Resource)
            .where(
                models.Plugin.resource_id.in_(tuple(plugin_ids)),
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.Plugin.resource_snapshot_id,
            )
        )
        plugins = db.session.scalars(latest_plugins_stmt).all()

        if len(plugins) != len(plugin_ids) and error_if_not_found:
            plugin_ids_missing = set(plugin_ids) - set(
                plugin.resource_id for plugin in plugins
            )
            raise EntityDoesNotExistError(
                PLUGIN_RESOURCE_TYPE, plugin_ids=list(plugin_ids_missing)
            )

        # extract list of plugin ids
        plugin_ids = [plugin.resource_id for plugin in plugins]

        # Build CTE that retrieves all snapshot ids for the list of plugin files
        # associated with retrieved plugins
        parent_plugin = aliased(models.Plugin)
        plugin_file_snapshot_ids_cte = (
            select(models.PluginFile.resource_snapshot_id)
            .join(
                models.resource_dependencies_table,
                models.PluginFile.resource_id
                == models.resource_dependencies_table.c.child_resource_id,
            )
            .join(
                parent_plugin,
                parent_plugin.resource_id
                == models.resource_dependencies_table.c.parent_resource_id,
            )
            .where(parent_plugin.resource_id.in_(plugin_ids))
            .cte()
        )

        # get the latest plugin file snapshots associated with the retrieved plugins
        latest_plugin_files_stmt = (
            select(models.PluginFile)
            .join(models.Resource)
            .where(
                models.Resource.latest_snapshot_id.in_(
                    select(plugin_file_snapshot_ids_cte)
                ),
                models.Resource.latest_snapshot_id
                == models.PluginFile.resource_snapshot_id,
                models.Resource.is_deleted == False,  # noqa: E712
            )
        )
        plugin_files = db.session.scalars(latest_plugin_files_stmt).unique().all()

        # build a dictionary structure to re-associate plugins and plugin files
        plugins_dict: dict[int, utils.PluginWithFilesDict] = {
            plugin.resource_id: utils.PluginWithFilesDict(
                plugin=plugin, plugin_files=[], has_draft=False
            )
            for plugin in plugins
        }
        for plugin_file in plugin_files:
            plugins_dict[plugin_file.plugin_id]["plugin_files"].append(plugin_file)

        drafts_stmt = select(
            models.DraftResource.payload["resource_id"].as_string().cast(Integer)
        ).where(
            models.DraftResource.payload["resource_id"]
            .as_string()
            .cast(Integer)
            .in_(
                tuple(plugin["plugin"].resource_id for plugin in plugins_dict.values())
            ),
            models.DraftResource.user_id == current_user.user_id,
        )
        for resource_id in db.session.scalars(drafts_stmt):
            plugins_dict[resource_id]["has_draft"] = True

        return list(plugins_dict.values())


class PluginNameService(object):
    """The service methods for managing plugins by their name."""

    def get(
        self,
        name: str,
        group_id: int,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> models.Plugin | None:
        """Fetch a plugin by its name.

        Args:
            name: The name of the plugin.
            group_id: The the group id of the plugin.
            error_if_not_found: If True, raise an error if the plugin is not found.
                Defaults to False.

        Returns:
            The plugin object if found, otherwise None.

        Raises:
            EntityDoesNotExistError: If the plugin is not found and `error_if_not_found`
                is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get plugin by name", plugin_name=name, group_id=group_id)

        stmt = (
            select(models.Plugin)
            .join(models.Resource)
            .where(
                models.Plugin.name == name,
                models.Resource.group_id == group_id,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.Plugin.resource_snapshot_id,
            )
        )
        plugin = db.session.scalar(stmt)

        if plugin is None:
            if error_if_not_found:
                raise EntityDoesNotExistError(
                    PLUGIN_RESOURCE_TYPE, name=name, group_id=group_id
                )

        return plugin


class PluginFileNameService(object):
    """The service methods for managing plugin files by their filename."""

    def get(
        self, filename: str, plugin_id: int, error_if_not_found: bool = False, **kwargs
    ) -> models.PluginFile | None:
        """Fetch a plugin file by its filename.

        Args:
            filename: The filename of the plugin file.
            plugin_id: The plugin id of the plugin to which the plugin file belongs.
            error_if_not_found: If True, raise an error if the plugin file is not found.
                Defaults to False.

        Returns:
            The plugin file object if found, otherwise None.

        Raises:
            EntityDoesNotExistError: If the plugin is not found and
            `error_if_not_found` is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug(
            "Get plugin file by filename",
            plugin_file_filename=filename,
            plugin_id=plugin_id,
        )

        stmt = (
            select(models.PluginFile)
            .join(models.Resource)
            .where(
                models.PluginFile.filename == filename,
                models.PluginFile.plugin_id == plugin_id,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.PluginFile.resource_snapshot_id,
            )
        )
        plugin_file = db.session.scalar(stmt)

        if plugin_file is None:
            if error_if_not_found:
                raise EntityDoesNotExistError(
                    PLUGIN_FILE_RESOURCE_TYPE, plugin_id=plugin_id, filename=filename
                )

            return None

        return plugin_file


class PluginIdFileService(object):
    @inject
    def __init__(
        self,
        plugin_file_name_service: PluginFileNameService,
        plugin_id_service: PluginIdService,
        group_id_service: GroupIdService,
    ) -> None:
        """Initialize the plugin file service.

        All arguments are provided via dependency injection.

        Args:
            plugin_file_name_service: A PluginFileNameService object.
            plugin_id_service: A PluginIdService object.
            group_id_service: A GroupIdService object.
        """
        self._plugin_file_name_service = plugin_file_name_service
        self._plugin_id_service = plugin_id_service
        self._group_id_service = group_id_service

    def create(
        self,
        plugin_id: int,
        filename: str,
        contents: str,
        description: str | None,
        function_tasks: list[dict[str, Any]],
        artifact_tasks: list[dict[str, Any]],
        commit: bool = True,
        **kwargs,
    ) -> utils.PluginFileDict:
        """Creates a new PluginFile object.

        The PluginFile object will belong to the group that owns the plugin associated
        with the PluginFile. The creator will be the current user.

        Args:
            plugin_id: The unique id of the plugin containing the plugin file.
            filename: The name of the plugin file.
            contents: The contents of the plugin file.
            description: The description of the plugin file.
            tasks: The tasks associated with the plugin file.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The newly created plugin file object.

        Raises:
            EntityExistsError: If a plugin file with the given filename
                already exists.
        """

        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Create a new plugin file", plugin_id=plugin_id, filename=filename)

        # Check if plugin_id points to a Plugin that exists, and if so, retrieve it.
        plugin_dict = cast(
            utils.PluginWithFilesDict,
            self._plugin_id_service.get(plugin_id, error_if_not_found=True),
        )
        plugin = plugin_dict["plugin"]

        # Validate that the proposed filename hasn't already been used in the plugin.
        duplicate = self._plugin_file_name_service.get(
            filename, plugin_id=plugin_id, log=log
        )
        if duplicate is not None:
            raise EntityExistsError(
                PLUGIN_FILE_RESOURCE_TYPE,
                duplicate.resource_id,
                filename=filename,
                plugin_id=plugin_id,
            )

        # a new plugin file creates a new plugin snapshot
        new_plugin = models.Plugin(
            name=plugin.name,
            description=plugin.description,
            resource=plugin.resource,
            creator=current_user,
        )
        db.session.add(new_plugin)

        resource = models.Resource(
            resource_type=PLUGIN_FILE_RESOURCE_TYPE, owner=new_plugin.resource.owner
        )
        new_plugin_file = models.PluginFile(
            filename=filename,
            contents=contents,
            description=description,
            resource=resource,
            creator=current_user,
        )
        new_plugin_file.parents.append(new_plugin.resource)
        db.session.add(new_plugin_file)

        new_plugin_files = plugin.plugin_files + [new_plugin_file]
        _associate_plugin_with_plugin_files(new_plugin, new_plugin_files)

        _add_plugin_tasks(
            function_tasks=function_tasks,
            artifact_tasks=artifact_tasks,
            plugin_file=new_plugin_file,
            log=log,
        )

        if commit:
            db.session.commit()
            log.debug(
                "Plugin file registration successful",
                plugin_file_id=new_plugin_file.resource_id,
                filename=new_plugin_file.filename,
            )

        return utils.PluginFileDict(
            plugin_file=new_plugin_file, plugin=plugin, has_draft=False
        )

    def get(
        self,
        plugin_id: int,
        search_string: str,
        page_index: int,
        page_length: int,
        sort_by_string: str,
        descending: bool,
        **kwargs,
    ) -> tuple[list[utils.PluginFileDict], int]:
        """Fetch a list of plugin files associated with a plugin, optionally
        filtering by search string and paging parameters.

        Args:
            plugin_id: A plugin ID used to filter results.
            search_string: A search string used to filter results.
            page_index: The index of the first group to be returned.
            page_length: The maximum number of plugins to be returned.
            sort_by_string: The name of the column to sort.
            descending: Boolean indicating whether to sort by descending or not.

        Returns:
            A tuple containing a list of plugins and the total number of plugins
            matching the query.

        Raises:
            SearchNotImplementedError: If a search string is provided.
            BackendDatabaseError: If the database query returns a None when counting
                the number of plugins.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug(
            "Get list of plugin files",
            plugin_id=plugin_id,
            search_string=search_string,
            page_index=page_index,
            page_length=page_length,
        )

        filters = list()

        if search_string:
            filters.append(
                construct_sql_query_filters(
                    search_string, PLUGIN_FILE_SEARCHABLE_FIELDS
                )
            )

        latest_plugin_stmt = (
            select(models.Plugin)
            .join(models.Resource)
            .where(
                models.Plugin.resource_id == plugin_id,
                models.Plugin.resource_snapshot_id
                == models.Resource.latest_snapshot_id,
                models.Resource.is_deleted == False,  # noqa: E712
            )
        )
        plugin = db.session.scalar(latest_plugin_stmt)

        if plugin is None:
            raise EntityDoesNotExistError(PLUGIN_RESOURCE_TYPE, plugin_id=plugin_id)

        latest_plugin_files_count_stmt = (
            select(func.count(models.PluginFile.resource_id))
            .join(models.Resource)
            .where(
                *filters,
                models.PluginFile.plugin_id == plugin_id,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.PluginFile.resource_snapshot_id,
            )
        )
        total_num_plugin_files = db.session.scalar(latest_plugin_files_count_stmt)

        if total_num_plugin_files is None:
            log.error(
                "The database query returned a None when counting the number of "
                "groups when it should return a number.",
                sql=str(latest_plugin_files_count_stmt),
            )
            raise BackendDatabaseError

        if total_num_plugin_files == 0:
            return [], total_num_plugin_files

        latest_plugin_files_stmt = (
            select(models.PluginFile)
            .join(models.Resource)
            .where(
                *filters,
                models.PluginFile.plugin_id == plugin_id,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.PluginFile.resource_snapshot_id,
            )
            .offset(page_index)
            .limit(page_length)
        )

        if sort_by_string and sort_by_string in PLUGIN_FILE_SORTABLE_FIELDS:
            sort_column = PLUGIN_FILE_SORTABLE_FIELDS[sort_by_string]
            if descending:
                sort_column = sort_column.desc()
            else:
                sort_column = sort_column.asc()
            latest_plugin_files_stmt = latest_plugin_files_stmt.order_by(sort_column)
        elif sort_by_string and sort_by_string not in PLUGIN_FILE_SORTABLE_FIELDS:
            raise SortParameterValidationError(
                PLUGIN_FILE_RESOURCE_TYPE, sort_by_string
            )

        plugin_files_dict: dict[int, utils.PluginFileDict] = {
            plugin_file.resource_id: utils.PluginFileDict(
                plugin=plugin, plugin_file=plugin_file, has_draft=False
            )
            for plugin_file in db.session.scalars(latest_plugin_files_stmt).unique()
        }

        drafts_stmt = select(
            models.DraftResource.payload["resource_id"].as_string().cast(Integer)
        ).where(
            models.DraftResource.payload["resource_id"]
            .as_string()
            .cast(Integer)
            .in_(
                tuple(
                    plugin_file["plugin_file"].resource_id
                    for plugin_file in plugin_files_dict.values()
                )
            ),
            models.DraftResource.user_id == current_user.user_id,
        )
        for resource_id in db.session.scalars(drafts_stmt):
            plugin_files_dict[resource_id]["has_draft"] = True

        return list(plugin_files_dict.values()), total_num_plugin_files

    def delete(self, plugin_id: int, **kwargs) -> dict[str, Any]:
        """Deletes all plugin files associated with a plugin.

        Args:
            plugin_id: The unique id of the plugin.

        Returns:
            A dictionary reporting the status of the request.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        stmt = select(models.Resource).filter_by(
            resource_id=plugin_id, resource_type=PLUGIN_RESOURCE_TYPE, is_deleted=False
        )

        plugin_resource = db.session.scalar(stmt)

        if plugin_resource is None:
            raise EntityDoesNotExistError(PLUGIN_RESOURCE_TYPE, plugin_id=plugin_id)

        latest_plugin_files_stmt = (
            select(models.PluginFile)
            .join(models.Resource)
            .where(
                models.PluginFile.plugin_id == plugin_id,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.PluginFile.resource_snapshot_id,
            )
        )

        plugin_files = db.session.scalars(latest_plugin_files_stmt).unique().all()
        num_plugin_files = len(plugin_files)

        plugin_file_ids = []
        for plugin_file in plugin_files:
            db.session.add(
                models.ResourceLock(
                    resource_lock_type=resource_lock_types.DELETE,
                    resource=plugin_file.resource,
                )
            )
            plugin_file_ids.append(plugin_file.resource_id)

        db.session.commit()

        log.debug(
            "Plugin files deleted",
            plugin_id=plugin_id,
            num_plugin_files=num_plugin_files,
        )

        return {"status": "Success", "id": plugin_file_ids}


class PluginIdSnapshotIdService(object):
    def get(self, plugin_id: int, plugin_snapshot_id: int, **kwargs) -> models.Plugin:
        """Run a query to get the EntryPoint for an entrypoint snapshot id.

        Args:
            entrypoint_snapshot_id: The Snapshot ID of the entrypoint to retrieve

        Returns:
            The entrypoint.

        Raises:
            EntityDoesNotExistError: If the entrypoint is not found
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug(
            "get plugin snapshot",
            resource_id=plugin_id,
            resource_snapshot_id=plugin_snapshot_id,
        )
        plugin_resource_snapshot_stmt = (
            select(models.Plugin)
            .join(models.Resource)
            .where(
                models.Plugin.resource_id == plugin_id,
                models.Plugin.resource_snapshot_id == plugin_snapshot_id,
                models.Resource.is_deleted == False,  # noqa: E712
            )
        )
        plugin = db.session.scalar(plugin_resource_snapshot_stmt)

        if plugin is None:
            raise EntityDoesNotExistError(
                PLUGIN_RESOURCE_TYPE,
                plugin_id=plugin_id,
                plugin_snapshot_id=plugin_snapshot_id,
            )
        return plugin

    def get_plugin_plugin_file(
        self, plugin_snapshot_id: int, plugin_file_snapshot_id: int, **kwargs
    ) -> models.PluginPluginFile | None:
        """Gets the Plugin Plugin File for this combination of plugin and plugin file.

        Args:
            plugin_snapshot_id: The Snapshot ID of the plugin
            plugin_file_snapshot_id: The Snapshot ID of the plugin file

        Returns:
            The PluginPluginFile or None if not found
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug(
            "get PluginPluginFile",
            plugin_snapshot_id=plugin_snapshot_id,
            plugin_file_snapshot_id=plugin_file_snapshot_id,
        )
        plugin_plugin_file_stmt = select(models.PluginPluginFile).where(
            models.PluginPluginFile.plugin_file_resource_snapshot_id
            == plugin_file_snapshot_id,
            models.PluginPluginFile.plugin_resource_snapshot_id == plugin_snapshot_id,
        )
        return db.session.scalar(plugin_plugin_file_stmt)


class PluginTaskIdService(object):
    def get(self, task_id: int, **kwargs) -> models.PluginTask:
        """Run a query to get the Plugin Task for a task id.

        Args:
            task_id: The ID of the task to retrieve

        Returns:
            The PluginTask.

        Raises:
            EntityDoesNotExistError: If the PluginTask is not found
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("get plugin task", task_id=task_id)
        task_snapshot_stmt = select(models.PluginTask).where(
            models.PluginTask.task_id == task_id
        )
        task = db.session.scalar(task_snapshot_stmt)

        if task is None:
            raise EntityDoesNotExistError(
                PLUGIN_TASK_RESOURCE_TYPE,
                task_id=task_id,
            )
        return task


class PluginIdFileIdService(object):
    @inject
    def __init__(self, plugin_file_name_service: PluginFileNameService):
        self._plugin_file_name_service = plugin_file_name_service

    def get(
        self,
        plugin_id: int,
        plugin_file_id: int,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> utils.PluginFileDict | None:
        """Fetch a plugin file by its unique id.

        Args:
            plugin_id: The unique id of the plugin containing the plugin file.
            plugin_file_id: The unique id of the plugin file.
            error_if_not_found: If True, raise an error if the plugin or plugin file is
                not found. Defaults to False.

        Returns:
            The plugin object if found, otherwise None.

        Raises:
            EntityDoesNotExistError: If the plugin or plugin file is not found and
                `error_if_not_found` is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug(
            "Get plugin file by id", plugin_id=plugin_id, plugin_file_id=plugin_file_id
        )

        latest_plugin_stmt = (
            select(models.Plugin)
            .join(models.Resource)
            .where(
                models.Plugin.resource_id == plugin_id,
                models.Plugin.resource_snapshot_id
                == models.Resource.latest_snapshot_id,
                models.Resource.is_deleted == False,  # noqa: E712
            )
        )
        plugin = db.session.scalar(latest_plugin_stmt)

        if plugin is None:
            if error_if_not_found:
                raise EntityDoesNotExistError(PLUGIN_RESOURCE_TYPE, plugin_id=plugin_id)

            return None

        latest_plugin_file_stmt = (
            select(models.PluginFile)
            .join(models.Resource)
            .where(
                models.PluginFile.plugin_id == plugin_id,
                models.PluginFile.resource_id == plugin_file_id,
                models.PluginFile.resource_snapshot_id
                == models.Resource.latest_snapshot_id,
                models.Resource.is_deleted == False,  # noqa: E712
            )
        )
        plugin_file = db.session.scalar(latest_plugin_file_stmt)

        if plugin_file is None:
            if error_if_not_found:
                raise EntityDoesNotExistError(
                    PLUGIN_FILE_RESOURCE_TYPE,
                    plugin_id=plugin_id,
                    plugin_file_id=plugin_file_id,
                )

            return None

        drafts_stmt = (
            select(models.DraftResource.draft_resource_id)
            .where(
                models.DraftResource.payload["resource_id"].as_string().cast(Integer)
                == plugin_file.resource_id,
                models.DraftResource.user_id == current_user.user_id,
            )
            .exists()
            .select()
        )
        has_draft = db.session.scalar(drafts_stmt)

        return utils.PluginFileDict(
            plugin_file=plugin_file, plugin=plugin, has_draft=has_draft
        )

    def modify(
        self,
        plugin_id: int,
        plugin_file_id: int,
        filename: str,
        contents: str,
        description: str,
        function_tasks: list[dict[str, Any]],
        artifact_tasks: list[dict[str, Any]],
        error_if_not_found: bool = False,
        commit: bool = True,
        **kwargs,
    ) -> utils.PluginFileDict | None:
        """Modify a plugin file.

        Args:
            plugin_id: The unique id of the plugin.
            plugin_file_id: The unique id of the plugin file.
            filename: The updated filename of the plugin file.
            contents: The updated contents of the plugin file.
            description: The updated description of the plugin file.
            tasks: The updated tasks associated with the plugin file.
            error_if_not_found: If True, raise an error if the plugin or plugin file is
                not found. Defaults to False.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The updated plugin file object.

        Raises:
            EntityDoesNotExistError: If the plugin or plugin file is not found and
                `error_if_not_found` is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        plugin_file_dict = self.get(
            plugin_id=plugin_id,
            plugin_file_id=plugin_file_id,
            error_if_not_found=error_if_not_found,
            log=log,
        )

        if plugin_file_dict is None:
            return None

        plugin = plugin_file_dict["plugin"]
        plugin_file = plugin_file_dict["plugin_file"]

        if filename != plugin_file.filename:
            duplicate = self._plugin_file_name_service.get(
                filename, plugin_id=plugin_id, log=log
            )
            if duplicate is not None:
                raise EntityExistsError(
                    PLUGIN_FILE_RESOURCE_TYPE,
                    duplicate.resource_id,
                    filename=filename,
                    plugin_id=plugin_id,
                )

        # a modification to a plugin file creates a new plugin snapshot
        new_plugin = models.Plugin(
            name=plugin.name,
            description=plugin.description,
            resource=plugin.resource,
            creator=current_user,
        )
        db.session.add(new_plugin)

        updated_plugin_file = models.PluginFile(
            filename=filename,
            contents=contents,
            description=description,
            resource=plugin_file.resource,
            creator=current_user,
        )
        db.session.add(updated_plugin_file)

        new_plugin_files = {
            plugin_file.resource_id: plugin_file for plugin_file in plugin.plugin_files
        }
        new_plugin_files[updated_plugin_file.resource_id] = updated_plugin_file
        _associate_plugin_with_plugin_files(new_plugin, list(new_plugin_files.values()))

        _add_plugin_tasks(
            function_tasks=function_tasks,
            artifact_tasks=artifact_tasks,
            plugin_file=updated_plugin_file,
            log=log,
        )

        if commit:
            db.session.commit()
            log.debug(
                "Plugin file modification successful",
                plugin_file_id=updated_plugin_file.resource_id,
                filename=updated_plugin_file.filename,
            )

        return utils.PluginFileDict(
            plugin_file=updated_plugin_file, plugin=plugin, has_draft=False
        )

    def delete(self, plugin_id: int, plugin_file_id: int, **kwargs) -> dict[str, Any]:
        """Deletes a plugin file.

        Args:
            plugin_id: The unique id of the plugin.
            plugin_file_id: The unique id of the plugin file.

        Returns:
            A dictionary reporting the status of the request.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        plugin_stmt = (
            select(models.Plugin)
            .join(models.Resource)
            .where(
                models.Plugin.resource_id == plugin_id,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.Plugin.resource_snapshot_id,
            )
        )
        plugin = db.session.scalar(plugin_stmt)

        if plugin is None:
            raise EntityDoesNotExistError(PLUGIN_RESOURCE_TYPE, plugin_id=plugin_id)

        plugin_file_stmt = (
            select(models.PluginFile)
            .join(models.Resource)
            .where(
                models.PluginFile.plugin_id == plugin_id,
                models.PluginFile.resource_id == plugin_file_id,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.PluginFile.resource_snapshot_id,
            )
        )
        plugin_file = db.session.scalar(plugin_file_stmt)

        if plugin_file is None:
            raise EntityDoesNotExistError(
                PLUGIN_FILE_RESOURCE_TYPE,
                plugin_id=plugin_id,
                plugin_file_id=plugin_file_id,
            )

        # a deletion of a plugin file creates a new plugin snapshot
        new_plugin = models.Plugin(
            name=plugin.name,
            description=plugin.description,
            resource=plugin.resource,
            creator=current_user,
        )
        db.session.add(new_plugin)

        new_plugin_files = [
            plugin_file
            for plugin_file in plugin.plugin_files
            if plugin_file.resource_id != plugin_file_id
        ]
        _associate_plugin_with_plugin_files(new_plugin, new_plugin_files)

        plugin_file_id_to_return = plugin_file.resource_id  # to return to user
        db.session.add(
            models.ResourceLock(
                resource_lock_type=resource_lock_types.DELETE,
                resource=plugin_file.resource,
            )
        )
        db.session.commit()

        log.debug("Plugin file deleted", plugin_id=plugin_id)
        return {"status": "Success", "id": [plugin_file_id_to_return]}


def _construct_input_params(
    task_name: str,
    parameters: list[dict[str, Any]],
    map: dict[int, models.PluginTaskParameterType],
) -> Iterable[models.PluginTaskInputParameter]:
    duplicates = find_non_unique("name", parameters)
    if len(duplicates) > 0:
        raise QueryParameterNotUniqueError(
            "artifact task input parameter",
            plugin_task_name=task_name,
            input_param_names=duplicates,
        )
    return [
        models.PluginTaskInputParameter(
            name=input_param["name"],
            parameter_number=parameter_number,
            parameter_type=map[input_param["parameter_type_id"]],
            required=input_param["required"],
        )
        for parameter_number, input_param in enumerate(parameters)
    ]


def _construct_output_params(
    task_name: str,
    parameters: list[dict[str, Any]],
    map: dict[int, models.PluginTaskParameterType],
) -> Iterable[models.PluginTaskOutputParameter]:
    duplicates = find_non_unique("name", parameters)
    if len(duplicates) > 0:
        raise QueryParameterNotUniqueError(
            "artifact task output parameter",
            plugin_task_name=task_name,
            output_param_names=duplicates,
        )
    return [
        models.PluginTaskOutputParameter(
            name=output_param["name"],
            parameter_number=parameter_number,
            parameter_type=map[output_param["parameter_type_id"]],
        )
        for parameter_number, output_param in enumerate(parameters)
    ]


def _construct_function_task(
    plugin_file: models.PluginFile,
    task: dict[str, Any],
    parameter_type_ids_to_orm: dict[int, models.PluginTaskParameterType],
) -> models.FunctionTask:
    return models.FunctionTask(
        file=plugin_file,
        plugin_task_name=task["name"],
        input_parameters=_construct_input_params(
            task["name"], task["input_params"], parameter_type_ids_to_orm
        ),
        output_parameters=_construct_output_params(
            task["name"], task["output_params"], parameter_type_ids_to_orm
        ),
    )


def _construct_artifact_task(
    plugin_file: models.PluginFile,
    task: dict[str, Any],
    parameter_type_ids_to_orm: dict[int, models.PluginTaskParameterType],
) -> models.ArtifactTask:
    return models.ArtifactTask(
        file=plugin_file,
        plugin_task_name=task["name"],
        output_parameters=_construct_output_params(
            task["name"], task["output_params"], parameter_type_ids_to_orm
        ),
    )


def get_referenced_parameter_types(
    function_tasks: list[dict[str, Any]],
    artifact_tasks: list[dict[str, Any]],
    log: BoundLogger,
) -> dict[int, models.PluginTaskParameterType]:
    parameter_type_ids = list(
        itertools.chain(
            [
                param["parameter_type_id"]
                for task in function_tasks
                for param in itertools.chain(
                    task["input_params"], task["output_params"]
                )
            ],
            [
                param["parameter_type_id"]
                for task in artifact_tasks
                for param in task["output_params"]
            ],
        )
    )

    if not len(parameter_type_ids) > 0:
        return {}

    return get_plugin_task_parameter_types_by_id(ids=parameter_type_ids, log=log)


def _add_plugin_tasks(
    function_tasks: list[dict[str, Any]],
    artifact_tasks: list[dict[str, Any]],
    plugin_file: models.PluginFile,
    log: BoundLogger,
) -> None:
    duplicates = find_non_unique(
        "name", itertools.chain(function_tasks, artifact_tasks)
    )
    if len(duplicates) > 0:
        raise QueryParameterNotUniqueError("plugin task", task_names=duplicates)

    parameter_type_ids_to_orm = get_referenced_parameter_types(
        function_tasks=function_tasks, artifact_tasks=artifact_tasks, log=log
    )

    for task in function_tasks:
        plugin_task = _construct_function_task(
            plugin_file,
            task=task,
            parameter_type_ids_to_orm=parameter_type_ids_to_orm,
        )
        db.session.add(plugin_task)
    for task in artifact_tasks:
        plugin_task = _construct_artifact_task(
            plugin_file,
            task=task,
            parameter_type_ids_to_orm=parameter_type_ids_to_orm,
        )
        db.session.add(plugin_task)


def _associate_plugin_with_plugin_files(
    plugin: models.Plugin, plugin_files: list[models.PluginFile]
) -> None:
    for plugin_file in plugin_files:
        plugin_plugin_file = models.PluginPluginFile(
            plugin=plugin, plugin_file=plugin_file
        )
        db.session.add(plugin_plugin_file)
