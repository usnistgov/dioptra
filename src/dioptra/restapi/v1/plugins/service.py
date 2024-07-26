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
from __future__ import annotations

import itertools
from typing import Any, Final, cast

import structlog
from flask_login import current_user
from injector import inject
from sqlalchemy import Integer, func, select
from sqlalchemy.orm import aliased
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import db, models
from dioptra.restapi.db.models.constants import resource_lock_types
from dioptra.restapi.errors import BackendDatabaseError
from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.groups.service import GroupIdService
from dioptra.restapi.v1.shared.search_parser import construct_sql_query_filters

from .errors import (
    PluginAlreadyExistsError,
    PluginDoesNotExistError,
    PluginFileAlreadyExistsError,
    PluginFileDoesNotExistError,
    PluginTaskInputParameterNameAlreadyExistsError,
    PluginTaskNameAlreadyExistsError,
    PluginTaskOutputParameterNameAlreadyExistsError,
    PluginTaskParameterTypeNotFoundError,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()

PLUGIN_RESOURCE_TYPE: Final[str] = "plugin"
PLUGIN_FILE_RESOURCE_TYPE: Final[str] = "plugin_file"
PLUGIN_SEARCHABLE_FIELDS: Final[dict[str, Any]] = {
    "name": lambda x: models.Plugin.name.like(x, escape="/"),
    "description": lambda x: models.Plugin.description.like(x, escape="/"),
}
PLUGIN_FILE_SEARCHABLE_FIELDS: Final[dict[str, Any]] = {
    "filename": lambda x: models.PluginFile.filename.like(x, escape="/"),
    "description": lambda x: models.PluginFile.description.like(x, escape="/"),
    "contents": lambda x: models.PluginFile.contents.like(x, escape="/"),
}


class PluginService(object):
    @inject
    def __init__(
        self, plugin_name_service: PluginNameService, group_id_service: GroupIdService
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
        self, name: str, description: str, group_id: int, commit: bool = True, **kwargs
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
            PluginAlreadyExistsError: If a plugin with the given name already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        if self._plugin_name_service.get(name, group_id=group_id, log=log) is not None:
            log.debug("Plugin name already exists", name=name, group_id=group_id)
            raise PluginAlreadyExistsError

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
        **kwargs,
    ) -> tuple[list[utils.PluginWithFilesDict], int]:
        """Fetch a list of plugins, optionally filtering by search string and paging
        parameters.

        Args:
            group_id: A group ID used to filter results.
            search_string: A search string used to filter results.
            page_index: The index of the first group to be returned.
            page_length: The maximum number of plugins to be returned.

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
        plugins = db.session.scalars(latest_plugins_stmt).all()

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
                models.PluginFile.resource_snapshot_id.in_(
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

        return list(plugins_dict.values()), total_num_plugins


class PluginIdService(object):
    """The service methods for registering and managing plugins by their unique id."""

    @inject
    def __init__(
        self,
        plugin_name_service: PluginNameService,
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
            PluginDoesNotExistError: If the plugin is not found and `error_if_not_found`
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
                log.debug("Plugin not found", plugin_id=plugin_id)
                raise PluginDoesNotExistError

            return None

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
        plugin_files = list(db.session.scalars(latest_plugin_files_stmt).unique().all())

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
            plugin=plugin, plugin_files=plugin_files, has_draft=has_draft
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
            PluginDoesNotExistError: If the plugin is not found and `error_if_not_found`
                is True.
            PluginAlreadyExistsError: If the plugin name already exists.
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

        if (
            name != plugin.name
            and self._plugin_name_service.get(name, group_id=group_id, log=log)
            is not None
        ):
            log.debug("Plugin name already exists", name=name, group_id=group_id)
            raise PluginAlreadyExistsError

        new_plugin = models.Plugin(
            name=name,
            description=description,
            resource=plugin.resource,
            creator=current_user,
        )
        db.session.add(new_plugin)

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
            raise PluginDoesNotExistError

        deleted_resource_lock = models.ResourceLock(
            resource_lock_type=resource_lock_types.DELETE,
            resource=plugin_resource,
        )
        db.session.add(deleted_resource_lock)
        db.session.commit()
        log.debug("Plugin deleted", plugin_id=plugin_id)

        return {"status": "Success", "id": [plugin_id]}


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
            PluginDoesNotExistError: If the plugin is not found and `error_if_not_found`
                is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

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
            log.debug("Plugin not found", plugin_ids=list(plugin_ids_missing))
            raise PluginDoesNotExistError

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
            PluginDoesNotExistError: If the plugin is not found and `error_if_not_found`
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
                log.debug("Plugin not found", name=name)
                raise PluginDoesNotExistError

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
            PluginFileDoesNotExistError: If the plugin is not found and
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
                log.debug("Plugin file not found", filename=filename)
                raise PluginFileDoesNotExistError

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
        filename: str,
        contents: str,
        description: str,
        tasks: list[dict[str, Any]],
        plugin_id: int,
        commit: bool = True,
        **kwargs,
    ) -> utils.PluginFileDict:
        """Creates a new PluginFile object.

        The PluginFile object will belong to the group that owns the plugin associated
        with the PluginFile. The creator will be the current user.

        Args:
            filename: The name of the plugin file.
            contents: The contents of the plugin file.
            description: The description of the plugin file.
            tasks: The tasks associated with the plugin file.
            plugin_id: The unique id of the plugin containing the plugin file.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The newly created plugin file object.

        Raises:
            PluginFileAlreadyExistsError: If a plugin file with the given filename
                already exists.
        """

        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Create a new plugin file", plugin_id=plugin_id, filename=filename)

        # Check if plugin_id points to a Plugin that exists, and if so, retrieve it.
        plugin_dict = cast(
            utils.PluginWithFilesDict,
            self._plugin_id_service.get(plugin_id, error_if_not_found=True),
        )

        # Validate that the proposed filename hasn't already been used in the plugin.
        if (
            self._plugin_file_name_service.get(filename, plugin_id=plugin_id, log=log)
            is not None
        ):
            log.debug(
                "Plugin filename already exists", filename=filename, plugin_id=plugin_id
            )
            raise PluginFileAlreadyExistsError

        # The owner of the PluginFile resource must match the owner of the Plugin
        # resource.
        plugin = plugin_dict["plugin"]
        resource = models.Resource(
            resource_type=PLUGIN_FILE_RESOURCE_TYPE, owner=plugin.resource.owner
        )
        new_plugin_file = models.PluginFile(
            filename=filename,
            contents=contents,
            description=description,
            resource=resource,
            creator=current_user,
        )

        new_plugin_file.parents.append(plugin.resource)
        db.session.add(new_plugin_file)

        _add_plugin_tasks(tasks, plugin_file=new_plugin_file, log=log)

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
        **kwargs,
    ) -> tuple[list[utils.PluginFileDict], int]:
        """Fetch a list of plugin files associated with a plugin, optionally
        filtering by search string and paging parameters.

        Args:
            plugin_id: A plugin ID used to filter results.
            search_string: A search string used to filter results.
            page_index: The index of the first group to be returned.
            page_length: The maximum number of plugins to be returned.

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
            log.debug("Plugin not found", plugin_id=plugin_id)
            raise PluginDoesNotExistError

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
            raise PluginDoesNotExistError

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
            PluginDoesNotExistError: If the plugin or plugin file is not found and
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
                log.debug("Plugin not found", plugin_id=plugin_id)
                raise PluginDoesNotExistError

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
                log.debug("Plugin file not found", plugin_file_id=plugin_file_id)
                raise PluginFileDoesNotExistError

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
        tasks: list,
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
            PluginDoesNotExistError: If the plugin or plugin file is not found and
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

        if (
            filename != plugin_file.filename
            and self._plugin_file_name_service.get(
                filename, plugin_id=plugin_id, log=log
            )
            is not None
        ):
            log.debug(
                "Plugin filename already exists", filename=filename, plugin_id=plugin_id
            )
            raise PluginFileAlreadyExistsError

        updated_plugin_file = models.PluginFile(
            filename=filename,
            contents=contents,
            description=description,
            resource=plugin_file.resource,
            creator=current_user,
        )
        db.session.add(updated_plugin_file)

        _add_plugin_tasks(tasks, plugin_file=updated_plugin_file, log=log)

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

        stmt = select(models.Resource).filter_by(
            resource_id=plugin_id, resource_type=PLUGIN_RESOURCE_TYPE, is_deleted=False
        )

        plugin_resource = db.session.scalar(stmt)
        if plugin_resource is None:
            raise PluginDoesNotExistError

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
            raise PluginFileDoesNotExistError

        plugin_file_id_to_return = plugin_file.resource_id  # to return to user
        db.session.add(
            models.ResourceLock(
                resource_lock_type=resource_lock_types.DELETE,
                resource=plugin_file.resource,
            )
        )
        db.session.commit()

        log.debug(
            "Plugin file deleted",
            plugin_id=plugin_id,
        )

        return {"status": "Success", "id": [plugin_file_id_to_return]}


def _construct_plugin_task(
    plugin_file: models.PluginFile,
    task: dict[str, Any],
    parameter_types_id_to_orm: dict[int, models.PluginTaskParameterType],
    log: BoundLogger,
) -> models.PluginTask:
    input_param_names = [x["name"] for x in task["input_params"]]
    unique_input_param_names = set(input_param_names)

    if len(unique_input_param_names) != len(input_param_names):
        log.error(
            "One or more input parameters have the same name",
            plugin_task_name=task["name"],
            input_param_names=input_param_names,
        )
        raise PluginTaskInputParameterNameAlreadyExistsError

    output_param_names = [x["name"] for x in task["output_params"]]
    unique_output_param_names = set(output_param_names)

    if len(unique_output_param_names) != len(output_param_names):
        log.error(
            "One or more output parameters have the same name",
            plugin_task_name=task["name"],
            output_param_names=output_param_names,
        )
        raise PluginTaskOutputParameterNameAlreadyExistsError

    input_parameters_list = []
    for parameter_number, input_param in enumerate(task["input_params"]):
        parameter_type = parameter_types_id_to_orm[input_param["parameter_type_id"]]
        input_parameters_list.append(
            models.PluginTaskInputParameter(
                name=input_param["name"],
                parameter_number=parameter_number,
                parameter_type=parameter_type,
                required=input_param["required"],
            )
        )

    output_parameters_list = []
    for parameter_number, output_param in enumerate(task["output_params"]):
        parameter_type = parameter_types_id_to_orm[output_param["parameter_type_id"]]
        output_parameters_list.append(
            models.PluginTaskOutputParameter(
                name=output_param["name"],
                parameter_number=parameter_number,
                parameter_type=parameter_type,
            )
        )

    plugin_task_orm = models.PluginTask(
        file=plugin_file,
        plugin_task_name=task["name"],
        input_parameters=input_parameters_list,
        output_parameters=output_parameters_list,
    )
    return plugin_task_orm


def _get_referenced_parameter_types(
    tasks: list[dict[str, Any]], log: BoundLogger
) -> dict[int, models.PluginTaskParameterType] | None:
    parameter_type_ids = set(
        [
            param["parameter_type_id"]
            for task in tasks
            for param in itertools.chain(task["input_params"], task["output_params"])
        ]
    )

    if not len(parameter_type_ids) > 0:
        return None

    parameter_types_stmt = (
        select(models.PluginTaskParameterType)
        .join(models.Resource)
        .where(
            models.PluginTaskParameterType.resource_id.in_(tuple(parameter_type_ids)),
            models.Resource.is_deleted == False,  # noqa: E712
            models.Resource.latest_snapshot_id
            == models.PluginTaskParameterType.resource_snapshot_id,
        )
    )
    parameter_types = db.session.scalars(parameter_types_stmt).all()

    if parameter_types is None:
        log.error(
            "The database query returned a None when it should return plugin "
            "parameter types.",
            sql=str(parameter_types_stmt),
            num_expected=len(parameter_type_ids),
        )
        raise BackendDatabaseError

    if not len(parameter_types) == len(parameter_type_ids):
        returned_parameter_type_ids = set([x.resource_id for x in parameter_types])
        ids_not_found = parameter_type_ids - returned_parameter_type_ids
        log.error(
            "One or more referenced plugin task parameter types were not found",
            num_expected=len(parameter_type_ids),
            num_found=len(parameter_types),
            ids_not_found=sorted(list(ids_not_found)),
        )
        raise PluginTaskParameterTypeNotFoundError

    return {x.resource_id: x for x in parameter_types}


def _add_plugin_tasks(
    tasks: list[dict[str, Any]], plugin_file: models.PluginFile, log: BoundLogger
) -> None:
    if not tasks:
        return None

    task_names = [x["name"] for x in tasks]
    unique_task_names = set(task_names)

    if len(unique_task_names) != len(tasks):
        log.error("One or more tasks have the same name", task_names=task_names)
        raise PluginTaskNameAlreadyExistsError

    parameter_types_id_to_orm = _get_referenced_parameter_types(tasks, log=log) or {}
    for task in tasks:
        plugin_task = _construct_plugin_task(
            plugin_file,
            task=task,
            parameter_types_id_to_orm=parameter_types_id_to_orm,
            log=log,
        )
        db.session.add(plugin_task)
