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
"""
The plugins repository: data operations related to plugins and plugin files
"""

from collections.abc import Callable, Iterable, Sequence
from typing import Any, Final, overload

import sqlalchemy as sa

import dioptra.restapi.db.repository.utils as utils
from dioptra.restapi.db import models as m
from dioptra.restapi.db.models import Group, Plugin, PluginFile, Resource, Tag
from dioptra.restapi.db.models.plugins import PluginTaskParameterType
from dioptra.restapi.v1.entity_types import EntityType


class PluginRepository:
    SEARCHABLE_FIELDS: Final[dict[str, Any]] = {
        "name": lambda x: Plugin.name.like(x, escape="/"),
        "description": lambda x: Plugin.description.like(x, escape="/"),
        "tag": lambda x: Plugin.tags.any(Tag.name.like(x, escape="/")),
    }

    SORTABLE_FIELDS: Final[dict[str, Any]] = {
        "name": Plugin.name,
        "createdOn": Plugin.created_on,
        "lastModifiedOn": Resource.last_modified_on,
        "description": Plugin.description,
    }

    FILE_SEARCHABLE_FIELDS: Final[dict[str, Any]] = {
        "filename": lambda x: PluginFile.filename.like(x, escape="/"),
        "description": lambda x: PluginFile.description.like(x, escape="/"),
        "contents": lambda x: PluginFile.contents.like(x, escape="/"),
        "tag": lambda x: PluginFile.tags.any(Tag.name.like(x, escape="/")),
    }

    FILE_SORTABLE_FIELDS: Final[dict[str, Any]] = {
        "filename": PluginFile.filename,
        "createdOn": PluginFile.created_on,
        "lastModifiedOn": Resource.last_modified_on,
        "description": PluginFile.description,
    }

    def __init__(self, session: utils.CompatibleSession[utils.S]):
        self.session = session

    def create(self, plugin: Plugin):
        """
        Create a new plugin resource. This creates both the resource and
        the initial snapshot.

        Args:
            plugin: The plugin to create

        Raises:
            EntityExistsError: if the plugin resource or snapshot already
                exists, or the plugin name collides with another plugin
                in the same group
            EntityDoesNotExistError: if any child plugin file doesn't exist, or
                the group owner or user creator do not exist
            EntityDeletedError: if the plugin, its creator, or its group
                owner is deleted, or if all plugin files exist but some
                are deleted
            UserNotInGroupError: if the plugin creator is not a member of
                the group who will own the resource
            MismatchedResourceTypeError: if the snapshot or resource's type is
                not "plugin"
        """
        utils.assert_can_create_resource(self.session, plugin, EntityType.PLUGIN)
        utils.assert_resource_name_available(self.session, plugin)

        self.session.add(plugin)

    def create_snapshot(self, plugin: Plugin):
        """
        Create a new plugin snapshot.

        Args:
            plugin: A Plugin object with the desired snapshot settings

        Raises:
            EntityDoesNotExistError: if the plugin resource, snapshot
                creator user, or any child plugin file does not exist
            EntityExistsError: if the snapshot already exists, or this new
                snapshot's plugin name collides with another plugin in
                the same group
            EntityDeletedError: if the plugin resource is deleted, snapshot
                creator user is deleted, or if all child resources exist but
                some are deleted
            UserNotInGroupError: if the snapshot creator user is not a member
                of the group who owns the plugin
            MismatchedResourceTypeError: if the snapshot or resource's type is
                not "plugin"
        """
        utils.assert_can_create_snapshot(self.session, plugin, EntityType.PLUGIN)
        utils.assert_snapshot_name_available(self.session, plugin)

        self.session.add(plugin)

    @overload
    def get(
        self,
        resource_ids: int,
        deletion_policy: utils.DeletionPolicy,
    ) -> Plugin | None: ...

    @overload
    def get(
        self,
        resource_ids: Iterable[int],
        deletion_policy: utils.DeletionPolicy,
    ) -> Sequence[Plugin]: ...

    def get(
        self,
        resource_ids: int | Iterable[int],
        deletion_policy: utils.DeletionPolicy = utils.DeletionPolicy.NOT_DELETED,
    ) -> Plugin | Sequence[Plugin] | None:
        """
        Get the latest snapshot of the given plugin resource(s).

        Args:
            resource_ids: A single or iterable of plugin resource IDs
            deletion_policy: Whether to look at deleted plugins,
                non-deleted plugins, or all plugins

        Returns:
            A Plugin/list of Plugin objects, or None/empty list if
            none were found with the given ID(s)
        """
        return utils.get_latest_snapshots(
            self.session, Plugin, resource_ids, deletion_policy
        )

    def get_exact(
        self,
        resource_ids: Sequence[int],
        deletion_policy: utils.DeletionPolicy = utils.DeletionPolicy.NOT_DELETED,
    ) -> Sequence[Plugin]:
        """
        Get the latest snapshots of the given plugin resource IDs.

        Args:
            resource_ids: An or iterable of plugin resource IDs
            deletion_policy: Whether to look at deleted plugins,
                non-deleted plugins, or all plugins

        Returns:
            A list of EntryPoint objects matching the given IDs

        Raises:
            EntityDoesNotExistError: if any of the plugins do not exist in the
                database (according to deletion policy)
        """

        return utils.get_exact_latest_snapshots(
            self.session, Plugin, resource_ids, deletion_policy
        )

    def get_one(
        self,
        resource_id: int,
        deletion_policy: utils.DeletionPolicy,
    ) -> Plugin:
        """
        Get the latest snapshot of the given plugin resource; require that
        exactly one is found, or raise an exception.

        Args:
            resource_id: A resource ID
            deletion_policy: Whether to look at deleted plugins, non-deleted
                plugins, or all plugins

        Returns:
            A Plugin object

        Raises:
            EntityDoesNotExistError: if the plugin does not exist in the
                database (deleted or not)
            EntityExistsError: if the plugin exists and is not deleted, but
                policy was to find a deleted plugin
            EntityDeletedError: if the plugin is deleted, but policy was to
                find a non-deleted plugin
        """
        return utils.get_one_latest_snapshot(
            self.session, Plugin, resource_id, deletion_policy
        )

    def get_one_snapshot(
        self,
        resource_id: int,
        snapshot_id: int,
        deletion_policy: utils.DeletionPolicy,
    ) -> Plugin:
        """
        Get the a specific plugin snapshot given the resource snapshot ID; require
        that exactly one is found, or raise an exception.

        Args:
            snapshot_id: A resource ID
            snapshot_id: A resource snapshot ID
            deletion_policy: Whether to look at deleted plugins, non-deleted
                plugins, or all plugins

        Returns:
            An Plugin object

        Raises:
            EntityDoesNotExistError: if the plugin does not exist in the
                database (deleted or not)
            EntityExistsError: if the plugin exists and is not deleted, but
                policy was to find a deleted plugin
            EntityDeletedError: if the plugin is deleted, but policy was to
                find a non-deleted plugin
        """
        return utils.get_one_snapshot(
            self.session, Plugin, resource_id, snapshot_id, deletion_policy
        )

    def get_by_name(
        self,
        name: str,
        group: Group | int,
        deletion_policy: utils.DeletionPolicy = utils.DeletionPolicy.NOT_DELETED,
    ) -> Plugin | None:
        """
        Get the latest snapshot of a plugin by its name and group.

        Args:
            name: The name of the plugin
            group: The group that owns the plugin
            deletion_policy: Whether to look at deleted plugins,
                non-deleted plugins, or all plugins

        Returns:
            A plugin, or None if one was not found

        Raises:
            EntityDoesNotExistError: if the given group does not exist
            EntityDeletedError: if the given group is deleted
        """
        return utils.get_snapshot_by_name(
            self.session, Plugin, name, group, deletion_policy
        )

    def get_by_filters_paged(
        self,
        group: Group | int | None,
        filters: list[dict],
        page_start: int,
        page_length: int,
        sort_by: str | None,
        descending: bool,
        deletion_policy: utils.DeletionPolicy = utils.DeletionPolicy.NOT_DELETED,
    ) -> tuple[Sequence[Plugin], int]:
        """
        Get a page of plugins matching the given filters.

        Args:
            group: The group to filter by, or None to look across groups
            filters: A list of search strings to filter by
            page_start: The index of the first plugin to be returned
            page_length: The maximum number of plugins to be returned
            sort_by: The name of the attribute to sort by
            descending: If True, sort in descending order
            search_string: A general search string
            deletion_policy: Whether to look at deleted plugins,
                non-deleted plugins, or all plugins

        Returns:
            A 2-tuple including the page of plugins and total count of matching
            plugins which exist

        Raises:
            SearchParseError: if filters includes a non-searchable field
            SortParameterValidationError: if sort_by is a non-sortable field
            EntityDoesNotExistError: if the given group does not exist
            EntityDeletedError: if the given group is deleted
        """
        additional_query_terms: list[Callable[[sa.Select], sa.Select]] = []

        return utils.get_by_filters_paged(
            self.session,
            Plugin,
            self.SORTABLE_FIELDS,
            self.SEARCHABLE_FIELDS,
            group,
            filters,
            page_start,
            page_length,
            sort_by,
            descending,
            deletion_policy,
            additional_query_terms=additional_query_terms,
        )

    def delete(self, plugin: Plugin | int):
        """
        Delete a plugin.

        Args:
            plugin: A Plugin object or resource_id integer

        Raises:
            EntityDoesNotExistError: if the plugin does not exist
        """
        utils.delete_resource(self.session, plugin)

    def associate_plugin_files(
        self,
        plugin: Plugin,
        plugin_files: Iterable[PluginFile | Resource | int],
    ) -> Sequence[PluginFile]:
        """
        Associate plugin files as children of the given plugin by creating
        PluginPluginFile associations.

        Args:
            plugin: A Plugin object (snapshot)
            plugin_files: The plugin files to associate (can be PluginFile objects,
                          Resource objects, or resource IDs)

        Returns:
            The list of associated plugin files as latest snapshots.

        Raises:
            EntityDoesNotExistError: if parent or any new child does not exist
            EntityDeletedError: if parent or any new child is deleted
        """
        plugin_file_snaps = utils.get_exact_latest_snapshots(
            self.session,
            PluginFile,
            plugin_files,
            utils.DeletionPolicy.ANY,
        )

        for plugin_file in plugin_file_snaps:
            plugin_plugin_file = m.PluginPluginFile(
                plugin=plugin,
                plugin_file=plugin_file,
            )
            self.session.add(plugin_plugin_file)

        return plugin_file_snaps

    def _assert_plugin_file_name_available(
        self,
        plugin_file: PluginFile,
        exclude_resource_id: int | None = None,
        plugin_id: int | None = None,
    ) -> None:
        """Check that the plugin file's filename is unique within its parent plugin.

        Args:
            plugin_file: The plugin file to check
            exclude_resource_id: Optional resource ID to exclude from the check
                (used when updating an existing file to allow keeping the same name)
            plugin_id: The plugin resource ID (optional, can be derived from parents)
        """
        from dioptra.restapi.errors import EntityExistsError

        if plugin_id is None:
            for parent in plugin_file.parents:
                if parent.resource_type == "plugin":
                    plugin_id = parent.resource_id
                    break

        if plugin_id is None:
            return

        plugin_subq = (
            sa.select(m.Resource.resource_id)
            .join(
                m.PluginPluginFile,
                m.PluginPluginFile.plugin_resource_snapshot_id
                == m.ResourceSnapshot.resource_snapshot_id,
            )
            .join(
                m.ResourceSnapshot,
                m.ResourceSnapshot.resource_id == m.Resource.resource_id,
            )
            .where(
                m.PluginPluginFile.plugin_file_resource_snapshot_id
                == PluginFile.resource_snapshot_id
            )
            .correlate(PluginFile)
            .limit(1)
            .scalar_subquery()
        )

        stmt = (
            sa.select(PluginFile.resource_id)
            .join(m.Resource)
            .where(
                PluginFile.filename == plugin_file.filename,
                plugin_subq == plugin_id,
                m.Resource.is_deleted == False,  # noqa: E712
            )
        )
        existing_id = self.session.scalar(stmt)
        if existing_id:
            raise EntityExistsError(
                EntityType.PLUGIN_FILE,
                existing_id,
                filename=plugin_file.filename,
                plugin_id=plugin_id,
            )

    def create_file(self, plugin_file: PluginFile, plugin_id: int | None = None):
        """
        Create a new plugin file resource. This creates both the resource and
        the initial snapshot.

        Args:
            plugin_file: The plugin file to create
            plugin_id: The parent plugin's resource ID (optional, can be derived from parents)

        Raises:
            EntityExistsError: if the plugin file resource or snapshot already
                exists, or the plugin file name collides with another plugin file
                in the same plugin
            EntityDoesNotExistError: if any child doesn't exist, or
                the group owner or user creator do not exist
            EntityDeletedError: if the plugin file, its creator, or its group
                owner is deleted
            UserNotInGroupError: if the plugin file creator is not a member of
                the group who will own the resource
            MismatchedResourceTypeError: if the snapshot or resource's type is
                not "plugin_file"
        """
        utils.assert_can_create_resource(
            self.session, plugin_file, EntityType.PLUGIN_FILE
        )
        self._assert_plugin_file_name_available(plugin_file, plugin_id=plugin_id)

        self.session.add(plugin_file)

    def create_file_snapshot(
        self, plugin_file: PluginFile, plugin_id: int | None = None
    ):
        """
        Create a new plugin file snapshot.

        Args:
            plugin_file: A PluginFile object with the desired snapshot settings
            plugin_id: The parent plugin's resource ID (optional, can be derived from parents)

        Raises:
            EntityDoesNotExistError: if the plugin file resource, snapshot
                creator user does not exist
            EntityExistsError: if the snapshot already exists, or this new
                snapshot's plugin file name collides with another plugin file in
                the same plugin
            EntityDeletedError: if the plugin file resource is deleted, or snapshot
                creator user is deleted
            UserNotInGroupError: if the snapshot creator user is not a member
                of the group who owns the plugin file
            MismatchedResourceTypeError: if the snapshot or resource's type is
                not "plugin_file"
        """
        utils.assert_can_create_snapshot(
            self.session, plugin_file, EntityType.PLUGIN_FILE
        )
        self._assert_plugin_file_name_available(
            plugin_file,
            exclude_resource_id=plugin_file.resource_id,
            plugin_id=plugin_id,
        )

        self.session.add(plugin_file)

    def get_one_file(
        self,
        plugin_id: int,
        plugin_file_id: int,
        deletion_policy: utils.DeletionPolicy,
    ) -> PluginFile:
        """
        Get the latest snapshot of the given plugin file resource; require that
        exactly one is found, or raise an exception.  The plugin the file belongs
        to must also exist.

        Args:
            resource_id: A resource ID
            deletion_policy: Whether to look at deleted files, non-deleted files,
                or all files

        Returns:
            A PluginFile object

        Raises:
            EntityDoesNotExistError: if the plugin file does not exist in the
                database (deleted or not), or the plugin does not exist in the
                database.
            EntityExistsError: if the plugin file exists and is not deleted, but
                policy was to find a deleted plugin file
            EntityDeletedError: if the plugin file is deleted, but policy was to
                find a non-deleted plugin file
        """
        utils.assert_resource_exists(
            self.session, plugin_id, utils.DeletionPolicy.NOT_DELETED
        )
        return utils.get_one_latest_snapshot(
            self.session, PluginFile, plugin_file_id, deletion_policy
        )

    def get_by_filters_paged_files(
        self,
        plugin: Plugin | int,
        filters: list[dict[Any, Any]],
        page_start: int,
        page_length: int,
        sort_by: str | None,
        descending: bool,
        deletion_policy: utils.DeletionPolicy = utils.DeletionPolicy.NOT_DELETED,
    ) -> tuple[Sequence[PluginFile], int]:
        """
        Get a page of plugin files matching the given filters.

        Args:
            plugin: The parent plugin (Plugin object or resource_id)
            filters: A list of search strings to filter by
            page_start: The index of the first plugin file to be returned
            page_length: The maximum number of plugin files to be returned
            sort_by: The name of the attribute to sort by
            descending: If True, sort in descending order
            search_string: A general search string
            deletion_policy: Whether to look at deleted files, non-deleted files,
                or all files

        Returns:
            A 2-tuple including the page of plugin files and total count of
            matching plugin files which exist

        Raises:
            SearchParseError: if filters includes a non-searchable field
            SortParameterValidationError: if sort_by is a non-sortable field
            EntityDoesNotExistError: if the parent plugin does not exist
            EntityDeletedError: if the parent plugin is deleted
        """

        plugin_resource_id = (
            plugin.resource_id if isinstance(plugin, Plugin) else plugin
        )

        utils.assert_resource_exists(
            self.session, plugin_resource_id, utils.DeletionPolicy.ANY
        )

        sql_filter: dict[Any, Any] | sa.ColumnElement[bool] | None = None
        if filters and len(filters) > 0:
            first_filter = filters[0]
            if isinstance(first_filter, sa.ColumnElement):
                sql_filter = first_filter
            elif first_filter is not True:
                sql_filter = first_filter

        if sort_by and sort_by not in self.FILE_SORTABLE_FIELDS:
            from dioptra.restapi.errors import SortParameterValidationError

            raise SortParameterValidationError("plugin_file", sort_by)

        plugin_subq = (
            sa.select(m.Resource.resource_id)
            .join(
                m.PluginPluginFile,
                m.PluginPluginFile.plugin_resource_snapshot_id
                == m.ResourceSnapshot.resource_snapshot_id,
            )
            .join(
                m.ResourceSnapshot,
                m.ResourceSnapshot.resource_id == m.Resource.resource_id,
            )
            .where(
                m.PluginPluginFile.plugin_file_resource_snapshot_id
                == PluginFile.resource_snapshot_id
            )
            .correlate(PluginFile)
            .limit(1)
            .scalar_subquery()
        )

        count_stmt = (
            sa.select(sa.func.count())
            .select_from(PluginFile)
            .join(m.Resource)
            .where(
                plugin_subq == plugin_resource_id,
                PluginFile.resource_snapshot_id == m.Resource.latest_snapshot_id,
            )
        )

        if sql_filter is not None:
            count_stmt = count_stmt.where(sql_filter)  # type: ignore[arg-type]

        count_stmt = utils.apply_resource_deletion_policy(count_stmt, deletion_policy)

        total_count = self.session.scalar(count_stmt)
        assert total_count is not None

        if total_count == 0:
            return [], 0

        page_stmt = (
            sa.select(PluginFile)
            .join(m.Resource)
            .where(
                plugin_subq == plugin_resource_id,
                PluginFile.resource_snapshot_id == m.Resource.latest_snapshot_id,
            )
        )

        if sql_filter is not None:
            page_stmt = page_stmt.where(sql_filter)  # type: ignore[arg-type]

        page_stmt = utils.apply_resource_deletion_policy(page_stmt, deletion_policy)

        if sort_by:
            sort_attr = self.FILE_SORTABLE_FIELDS.get(sort_by)
            if sort_attr is not None:
                page_stmt = page_stmt.order_by(
                    sort_attr.desc() if descending else sort_attr
                )

        page_stmt = page_stmt.offset(page_start).limit(page_length)

        return self.session.scalars(page_stmt).unique().all(), total_count

    def delete_file(self, plugin_file: PluginFile | int):
        """
        Delete a plugin file.

        Args:
            plugin_file: A PluginFile object or resource_id integer

        Raises:
            EntityDoesNotExistError: if the plugin file does not exist
        """
        utils.delete_resource(self.session, plugin_file)

    def add_plugin_tasks(
        self,
        function_tasks: list[dict[str, Any]],
        artifact_tasks: list[dict[str, Any]],
        plugin_file: m.PluginFile,
        types: list[PluginTaskParameterType],
    ) -> None:
        """
        TODO: docstrings
        """

        id_type_map = {type_.resource_id: type_ for type_ in types}

        for task in function_tasks:
            function_task = m.FunctionTask(
                file=plugin_file,
                plugin_task_name=task["name"],
                input_parameters=_construct_input_params(
                    task["input_params"], id_type_map
                ),
                output_parameters=_construct_output_params(
                    task["output_params"], id_type_map
                ),
            )
            self.session.add(function_task)

        for task in artifact_tasks:
            artifact_task = m.ArtifactTask(
                file=plugin_file,
                plugin_task_name=task["name"],
                output_parameters=_construct_output_params(
                    task["output_params"], parameter_type_ids_to_orm
                ),
            )
            self.session.add(artifact_task)


def _construct_input_params(
    parameters: list[dict[str, Any]],
    param_type_map: dict[int, m.PluginTaskParameterType],
) -> Iterable[m.PluginTaskInputParameter]:
    return [
        m.PluginTaskInputParameter(
            name=input_param["name"],
            parameter_number=parameter_number,
            parameter_type=param_type_map[input_param["parameter_type_id"]],
            required=input_param["required"],
        )
        for parameter_number, input_param in enumerate(parameters)
    ]


def _construct_output_params(
    parameters: list[dict[str, Any]],
    map: dict[int, m.PluginTaskParameterType],
) -> Iterable[m.PluginTaskOutputParameter]:
    return [
        m.PluginTaskOutputParameter(
            name=output_param["name"],
            parameter_number=parameter_number,
            parameter_type=param_type_map[output_param["parameter_type_id"]],
        )
        for parameter_number, output_param in enumerate(parameters)
    ]
