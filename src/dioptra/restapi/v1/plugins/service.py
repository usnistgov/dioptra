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

from itertools import chain
from typing import Any

import structlog
from flask_login import current_user
from sqlalchemy import select
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import db, models
from dioptra.restapi.db.repository.plugins import PluginRepository
from dioptra.restapi.db.repository.utils.common import DeletionPolicy
from dioptra.restapi.db.unit_of_work import UnitOfWorkService
from dioptra.restapi.errors import (
    PluginTaskDoesNotExistError,
)
from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.entity_types import EntityType
from dioptra.restapi.v1.shared.search_parser import (
    construct_sql_query_filters,
    parse_search_text,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class PluginService(UnitOfWorkService):
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

        group = self._uow.group_repo.get_one(group_id, DeletionPolicy.NOT_DELETED)

        resource = models.Resource(resource_type="plugin", owner=group)
        new_plugin = models.Plugin(
            name=name, description=description, resource=resource, creator=current_user
        )

        with self._uow(commit):
            self._uow.plugin_repo.create(new_plugin)

        log.debug(
            "Plugin registration successful",
            plugin_id=new_plugin.resource_id,
            name=new_plugin.name,
        )

        return utils.PluginWithFilesDict(
            plugin=new_plugin, plugin_files=[], has_draft=False
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

        search_struct = parse_search_text(search_string) if search_string else []

        plugins, total_num_plugins = self._uow.plugin_repo.get_by_filters_paged(
            group=group_id,
            filters=search_struct,
            page_start=page_index,
            page_length=page_length,
            sort_by=sort_by_string,
            descending=descending,
            deletion_policy=DeletionPolicy.NOT_DELETED,
        )

        if total_num_plugins == 0:
            return [], total_num_plugins

        resource_ids_with_drafts = self._uow.drafts_repo.has_draft_modifications(
            plugins, current_user
        )

        plugin_dicts = [
            utils.PluginWithFilesDict(
                plugin=plugin,
                plugin_files=plugin.plugin_files,
                has_draft=plugin.resource_id in resource_ids_with_drafts,
            )
            for plugin in plugins
        ]

        return plugin_dicts, total_num_plugins


class PluginIdService(UnitOfWorkService):
    """The service methods for registering and managing plugins by their unique id."""

    def get(self, plugin_id: int, **kwargs) -> utils.PluginWithFilesDict | None:
        """Fetch a plugin by its unique id.

        Args:
            plugin_id: The unique id of the plugin.

        Returns:
            The plugin object if found, otherwise None.

        Raises:
            EntityDoesNotExistError: If the plugin is not found
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get plugin by id", plugin_id=plugin_id)

        plugin = self._uow.plugin_repo.get_one(plugin_id, DeletionPolicy.NOT_DELETED)

        has_draft = self._uow.drafts_repo.has_draft_modification(plugin, current_user)

        return utils.PluginWithFilesDict(
            plugin=plugin, plugin_files=plugin.plugin_files, has_draft=has_draft
        )

    def modify(
        self,
        plugin_id: int,
        name: str,
        description: str | None,
        commit: bool = True,
        **kwargs,
    ) -> utils.PluginWithFilesDict | None:
        """Rename a plugin.

        Args:
            plugin_id: The unique id of the plugin.
            name: The new name of the plugin.
            description: The new description of the plugin.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The updated plugin object.

        Raises:
            EntityDoesNotExistError: If the plugin is not found
                is True.
            EntityExistsError: If the plugin name already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        plugin = self._uow.plugin_repo.get_one(plugin_id, DeletionPolicy.NOT_DELETED)
        plugin_files = plugin.plugin_files

        new_plugin = models.Plugin(
            name=name,
            description=description,
            resource=plugin.resource,
            creator=current_user,
        )

        with self._uow(commit):
            self._uow.plugin_repo.create_snapshot(new_plugin)
            self._uow.plugin_repo.associate_plugin_files(new_plugin, plugin_files)

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

        plugin = self._uow.plugin_repo.get_one(plugin_id, DeletionPolicy.NOT_DELETED)

        with self._uow():
            self._uow.plugin_repo.delete(plugin)

            for plugin_file in plugin.plugin_files:
                self._uow.plugin_repo.delete_file(plugin_file)

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


class PluginIdsService(UnitOfWorkService):
    """The service methods for registering and managing plugins by their unique id."""

    def get(
        self,
        plugin_ids: list[int],
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

        plugins = self._uow.plugin_repo.get_exact(
            plugin_ids, DeletionPolicy.NOT_DELETED
        )

        resource_ids_with_drafts = self._uow.drafts_repo.has_draft_modifications(
            plugins, current_user
        )

        plugin_dicts = [
            utils.PluginWithFilesDict(
                plugin=plugin,
                plugin_files=plugin.plugin_files,
                has_draft=plugin.resource_id in resource_ids_with_drafts,
            )
            for plugin in plugins
        ]

        return plugin_dicts


class PluginNameService(UnitOfWorkService):
    """The service methods for managing plugins by their name."""

    def get(self, name: str, group_id: int, **kwargs) -> models.Plugin | None:
        """Fetch a plugin by its name.

        Args:
            name: The name of the plugin.
            group_id: The the group id of the plugin.

        Returns:
            The plugin object if found, otherwise None.

        Raises:
            EntityDoesNotExistError: If the plugin is not found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get plugin by name", plugin_name=name, group_id=group_id)

        group = self._uow.group_repo.get_one(group_id, DeletionPolicy.NOT_DELETED)
        plugin = self._uow.plugin_repo.get_by_name(
            name, group, DeletionPolicy.NOT_DELETED
        )

        return plugin


class PluginIdFileService(UnitOfWorkService):
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

        plugin = self._uow.plugin_repo.get_one(plugin_id, DeletionPolicy.NOT_DELETED)

        # a new plugin file creates a new plugin snapshot
        new_plugin = models.Plugin(
            name=plugin.name,
            description=plugin.description,
            resource=plugin.resource,
            creator=current_user,
        )
        self._uow.plugin_repo.create_snapshot(new_plugin)

        resource = models.Resource(
            resource_type=EntityType.PLUGIN_FILE.db_table_name,
            owner=new_plugin.resource.owner,
        )
        new_plugin_file = models.PluginFile(
            filename=filename,
            contents=contents,
            description=description,
            resource=resource,
            creator=current_user,
        )

        with self._uow(commit):
            self._uow.plugin_repo.create_file(new_plugin_file, plugin_id=plugin_id)

            new_plugin_files = list(plugin.plugin_files) + [new_plugin_file]
            self._uow.plugin_repo.associate_plugin_files(new_plugin, new_plugin_files)

            type_ids = _get_referenced_parameter_types(function_tasks, artifact_tasks)
            types = self._uow.type_repo.get_exact(type_ids, DeletionPolicy.NOT_DELETED)
            self._uow.plugin_repo.add_plugin_tasks(
                function_tasks,
                artifact_tasks,
                new_plugin_file,
                types,
            )

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


        plugin = self._uow.plugin_repo.get_one(plugin_id, DeletionPolicy.NOT_DELETED)

        sql_filters: list[Any] = []
        if search_string is not None:
            filter_obj = construct_sql_query_filters(
                search_string, PluginRepository.FILE_SEARCHABLE_FIELDS
            )
            if filter_obj is not None and filter_obj is not True:
                sql_filters.append(filter_obj)

        log.debug(
            "Get list of plugin files calling repo",
            plugin_id=plugin_id,
            search_string=search_string,
            sql_filters_count=len(sql_filters),
        )

        plugin_files, total_num_plugin_files = (
            self._uow.plugin_repo.get_by_filters_paged_files(
                plugin=plugin_id,
                filters=sql_filters,
                page_start=page_index,
                page_length=page_length,
                sort_by=sort_by_string,
                descending=descending,
                deletion_policy=DeletionPolicy.NOT_DELETED,
            )
        )

        if total_num_plugin_files == 0:
            return [], total_num_plugin_files

        plugin_files_dict: dict[int, utils.PluginFileDict] = {
            plugin_file.resource_id: utils.PluginFileDict(
                plugin=plugin, plugin_file=plugin_file, has_draft=False
            )
            for plugin_file in plugin_files
        }

        resource_ids_with_drafts = self._uow.drafts_repo.has_draft_modifications(
            [pf["plugin_file"] for pf in plugin_files_dict.values()], current_user
        )
        for resource_id in resource_ids_with_drafts:
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

        plugin = self._uow.plugin_repo.get_one(plugin_id, DeletionPolicy.NOT_DELETED)
        plugin_file_ids = [file.resource_id for file in plugin.plugin_files]

        with self._uow():
            for plugin_file in plugin.plugin_files:
                self._uow.plugin_repo.delete_file(plugin_file)

        log.debug(
            "Plugin files deleted",
            plugin_id=plugin_id,
            num_plugin_files=len(plugin.plugin_files),
        )

        return {"status": "Success", "id": plugin_file_ids}


class PluginIdSnapshotIdService(UnitOfWorkService):
    def get(self, plugin_id: int, plugin_snapshot_id: int, **kwargs) -> models.Plugin:
        """Run a query to get the Plugin for an Plugin snapshot id.

        Args:
            plugin_id: The plugin id of the plugin to retrieve
            plugin_snapshot_id: The Snapshot ID of the plugin to retrieve

        Returns:
            The Plugin.

        Raises:
            EntityDoesNotExistError: If the plugin is not found
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug(
            "get plugin snapshot",
            resource_id=plugin_id,
            resource_snapshot_id=plugin_snapshot_id,
        )

        return self._uow.plugin_repo.get_one_snapshot(
            plugin_id, plugin_snapshot_id, DeletionPolicy.NOT_DELETED
        )

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

        # TODO add repo method
        plugin_plugin_file_stmt = select(models.PluginPluginFile).where(
            models.PluginPluginFile.plugin_file_resource_snapshot_id
            == plugin_file_snapshot_id,
            models.PluginPluginFile.plugin_resource_snapshot_id == plugin_snapshot_id,
        )
        return db.session.scalar(plugin_plugin_file_stmt)


class PluginTaskIdService(UnitOfWorkService):
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

        # TODO add repo method
        task_snapshot_stmt = select(models.PluginTask).where(
            models.PluginTask.task_id == task_id
        )
        task = db.session.scalar(task_snapshot_stmt)

        if task is None:
            raise PluginTaskDoesNotExistError(task_id=task_id)

        return task


class PluginIdFileIdService(UnitOfWorkService):
    def get(
        self,
        plugin_id: int,
        plugin_file_id: int,
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

        plugin_file = self._uow.plugin_repo.get_one_file(
            plugin_id, plugin_file_id, DeletionPolicy.NOT_DELETED
        )

        has_draft = self._uow.drafts_repo.has_draft_modification(
            plugin_file, current_user
        )

        return utils.PluginFileDict(
            plugin_file=plugin_file, plugin=plugin_file.plugin, has_draft=has_draft
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
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The updated plugin file object.

        Raises:
            EntityDoesNotExistError: If the plugin or plugin file is not found and
                `error_if_not_found` is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        plugin_file = self._uow.plugin_repo.get_one_file(
            plugin_id, plugin_file_id, DeletionPolicy.NOT_DELETED
        )
        plugin = plugin_file.plugin

        # a modification to a plugin file creates a new plugin snapshot
        new_plugin = models.Plugin(
            name=plugin.name,
            description=plugin.description,
            resource=plugin.resource,
            creator=current_user,
        )

        updated_plugin_file = models.PluginFile(
            filename=filename,
            contents=contents,
            description=description,
            resource=plugin_file.resource,
            creator=current_user,
        )

        with self._uow(commit):
            self._uow.plugin_repo.create_snapshot(new_plugin)
            self._uow.plugin_repo.create_file_snapshot(
                updated_plugin_file, plugin_id=plugin_id
            )

            new_plugin_files = {
                plugin_file.resource_id: plugin_file
                for plugin_file in plugin.plugin_files
            }
            new_plugin_files[updated_plugin_file.resource_id] = updated_plugin_file
            self._uow.plugin_repo.associate_plugin_files(
                new_plugin, list(new_plugin_files.values())
            )

            type_ids = _get_referenced_parameter_types(function_tasks, artifact_tasks)
            types = self._uow.type_repo.get_exact(type_ids, DeletionPolicy.NOT_DELETED)
            self._uow.plugin_repo.add_plugin_tasks(
                function_tasks,
                artifact_tasks,
                updated_plugin_file,
                types,
            )

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

        with self._uow():
            self._uow.plugin_repo.delete_file(plugin_file_id)

        log.debug("Plugin file deleted", plugin_id=plugin_id)
        return {"status": "Success", "id": [plugin_id]}


def _get_referenced_parameter_types(
    function_tasks: list[dict[str, Any]],
    artifact_tasks: list[dict[str, Any]],
) -> list[int]:
    return list(
        chain(
            [
                param["parameter_type_id"]
                for task in function_tasks
                for param in chain(task["input_params"], task["output_params"])
            ],
            [
                param["parameter_type_id"]
                for task in artifact_tasks
                for param in task["output_params"]
            ],
        )
    )
