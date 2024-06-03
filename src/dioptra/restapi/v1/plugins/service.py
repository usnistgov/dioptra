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

from typing import Any, Final

import structlog
from flask_login import current_user
from injector import inject
from sqlalchemy import func, select
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import db, models
from dioptra.restapi.errors import BackendDatabaseError, SearchNotImplementedError
from dioptra.restapi.v1.groups.service import GroupIdService

from .errors import PluginAlreadyExistsError, PluginDoesNotExistError

LOGGER: BoundLogger = structlog.stdlib.get_logger()

RESOURCE_TYPE: Final[str] = "plugin"


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
    ) -> models.Plugin:
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

        return new_plugin

    def get(
        self,
        group_id: int | None,
        search_string: str,
        page_index: int,
        page_length: int,
        **kwargs,
    ) -> Any:
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
            log.debug("Searching is not implemented", search_string=search_string)
            raise SearchNotImplementedError

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
        total_num_plugins = db.session.scalars(stmt).first()

        if total_num_plugins is None:
            log.error(
                "The database query returned a None when counting the number of "
                "groups when it should return a number.",
                sql=str(stmt),
            )
            raise BackendDatabaseError

        if total_num_plugins == 0:
            return [], total_num_plugins

        stmt = (
            select(models.Plugin)  # type: ignore
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
        plugins = db.session.scalars(stmt).all()

        return plugins, total_num_plugins


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
    ) -> models.Plugin | None:
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
        plugin = db.session.scalars(stmt).first()

        if plugin is None:
            if error_if_not_found:
                log.debug("Plugin not found", plugin_id=plugin_id)
                raise PluginDoesNotExistError

            return None

        return plugin

    def modify(
        self,
        plugin_id: int,
        name: str,
        description: str,
        error_if_not_found: bool = False,
        commit: bool = True,
        **kwargs,
    ) -> models.Plugin | None:
        """Rename a plugin.

        Args:
            plugin_id: The unique id of the plugin.
            name: The new name of the plugin.
            description: The new description of the plugin.
            error_if_not_found: If True, raise an error if the group is not found.
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

        plugin = self.get(plugin_id, error_if_not_found=error_if_not_found, log=log)

        if plugin is None:
            return None

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

        return new_plugin

    def delete(self, plugin_id: int, **kwargs) -> dict[str, Any]:
        """Delete a plugin.

        Args:
            plugin_id: The unique id of the plugin.

        Returns:
            A dictionary reporting the status of the request.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        stmt = select(models.Resource).filter_by(
            resource_id=plugin_id, resource_type=RESOURCE_TYPE, is_deleted=False
        )
        plugin_resource = db.session.scalars(stmt).first()

        if plugin_resource is None:
            raise PluginDoesNotExistError

        deleted_resource_lock = models.ResourceLock(
            resource_lock_type="delete",
            resource=plugin_resource,
        )
        db.session.add(deleted_resource_lock)
        db.session.commit()
        log.debug("Plugin deleted", plugin_id=plugin_id)

        return {"status": "Success", "plugin_id": plugin_id}


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
        plugin = db.session.scalars(stmt).first()

        if plugin is None:
            if error_if_not_found:
                log.debug("Plugin not found", name=name)
                raise PluginDoesNotExistError

            return None

        return plugin
