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
"""The server-side functions that perform plugin parameter type endpoint operations."""
from typing import Any, Final

import structlog
from flask_login import current_user
from injector import inject
from sqlalchemy import Integer, func, select
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import db, models
from dioptra.restapi.db.models.constants import resource_lock_types
from dioptra.restapi.errors import BackendDatabaseError
from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.groups.service import GroupIdService
from dioptra.restapi.v1.shared.search_parser import construct_sql_query_filters
from dioptra.task_engine.type_registry import BUILTIN_TYPES

from .errors import (
    PluginParameterTypeAlreadyExistsError,
    PluginParameterTypeDoesNotExistError,
    PluginParameterTypeMatchesBuiltinTypeError,
    PluginParameterTypeReadOnlyLockError,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()

RESOURCE_TYPE: Final[str] = "plugin_task_parameter_type"
SEARCHABLE_FIELDS: Final[dict[str, Any]] = {
    "name": lambda x: models.PluginTaskParameterType.name.like(x, escape="/"),
    "description": lambda x: models.PluginTaskParameterType.description.like(
        x, escape="/"
    ),
    "tag": lambda x: models.PluginTaskParameterType.tags.any(
        models.Tag.name.like(x, escape="/")
    ),
}


class PluginParameterTypeService(object):
    """The service methods for registering and managing plugin parameter types
    by their unique id."""

    @inject
    def __init__(
        self,
        plugin_parameter_type_name_service: "PluginParameterTypeNameService",
        group_id_service: GroupIdService,
    ) -> None:
        """Initialize the plugin parameter type service.

        All arguments are provided via dependency injection.

        Args:
            plugin_parameter_type_name_service: A PluginParameterTypeNameService object.
            group_id_service: A GroupIdService object.
        """
        self._plugin_parameter_type_name_service = plugin_parameter_type_name_service
        self._group_id_service = group_id_service

    def create(
        self,
        name: str,
        structure: dict[str, Any],
        description: str,
        group_id: int,
        commit: bool = True,
        **kwargs,
    ) -> utils.PluginParameterTypeDict:
        """Create a new plugin parameter type.

        Args:
            name: The name of the plugin parameter type. The combination of
                name and group_id must be unique. The name also cannot match
                any built-in types.
            structure: Optional JSON-type field for further constraining a
                type's structure.
            description: The description of the plugin parameter type.
            group_id: The group that will own the plugin parameter type.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The newly created plugin parameter type object.

        Raises:
            PluginParameterTypeMatchesBuiltinTypeError: If the plugin parameter
                type name matches a built-in type.
            PluginParameterTypeAlreadyExistsError: If a plugin parameter type
                with the given name already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        if name.strip().lower() in BUILTIN_TYPES:
            log.debug(
                "Plugin Parameter Type name matches a built-in type",
                name=name,
                normalized_name=name.strip().lower(),
            )
            raise PluginParameterTypeMatchesBuiltinTypeError

        if (
            self._plugin_parameter_type_name_service.get(
                name, group_id=group_id, log=log
            )
            is not None
        ):
            log.debug(
                "Plugin Parameter Type name already exists",
                name=name,
                group_id=group_id,
            )
            raise PluginParameterTypeAlreadyExistsError

        group = self._group_id_service.get(group_id, error_if_not_found=True)

        resource = models.Resource(resource_type=RESOURCE_TYPE, owner=group)
        new_plugin_parameter_type = models.PluginTaskParameterType(
            name=name,
            structure=structure,
            description=description,
            resource=resource,
            creator=current_user,
        )
        db.session.add(new_plugin_parameter_type)

        if commit:
            db.session.commit()
            log.debug(
                "Plugin Parameter Type registration successful",
                plugin_parameter_type_id=new_plugin_parameter_type.resource_id,
                name=new_plugin_parameter_type.name,
            )

        return utils.PluginParameterTypeDict(
            plugin_task_parameter_type=new_plugin_parameter_type, has_draft=False
        )

    def get(
        self,
        group_id: int | None,
        search_string: str,
        page_index: int,
        page_length: int,
        **kwargs,
    ) -> tuple[list[utils.PluginParameterTypeDict], int]:
        """Fetch a list of plugin parameter types, optionally filtering by
        search string and paging parameters.

        Args:
            group_id: A group ID used to filter results.
            search_string: A search string used to filter results.
            page_index: The index of the first group to be returned.
            page_length: The maximum number of plugin parameter types to be
                returned.

        Returns:
            A tuple containing a list of plugin parameter types and the total
            number of plugin parameter types matching the query.

        Raises:
            SearchNotImplementedError: If a search string is provided.
            BackendDatabaseError: If the database query returns a None when
                counting the number of plugin parameter types.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get full list of plugin parameter types")

        filters = list()

        if group_id is not None:
            filters.append(models.Resource.group_id == group_id)

        if search_string:
            filters.append(
                construct_sql_query_filters(search_string, SEARCHABLE_FIELDS)
            )

        stmt = (
            select(func.count(models.PluginTaskParameterType.resource_id))
            .join(models.Resource)
            .where(
                *filters,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.PluginTaskParameterType.resource_snapshot_id,
            )
        )
        total_num_plugin_parameter_types = db.session.scalars(stmt).first()

        if total_num_plugin_parameter_types is None:
            log.error(
                "The database query returned a None when counting the number of "
                "groups when it should return a number.",
                sql=str(stmt),
            )
            raise BackendDatabaseError

        if total_num_plugin_parameter_types == 0:
            return [], total_num_plugin_parameter_types

        plugin_parameter_types_stmt = (
            select(models.PluginTaskParameterType)
            .join(models.Resource)
            .where(
                *filters,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.PluginTaskParameterType.resource_snapshot_id,
            )
            .offset(page_index)
            .limit(page_length)
        )
        plugin_parameter_types = list(
            db.session.scalars(plugin_parameter_types_stmt).all()
        )

        drafts_stmt = select(
            models.DraftResource.payload["resource_id"].as_string().cast(Integer)
        ).where(
            models.DraftResource.payload["resource_id"]
            .as_string()
            .cast(Integer)
            .in_(
                tuple(
                    plugin_parameter_type.resource_id
                    for plugin_parameter_type in plugin_parameter_types
                )
            ),
            models.DraftResource.user_id == current_user.user_id,
        )
        plugin_parameter_types_dict: dict[int, utils.PluginParameterTypeDict] = {
            plugin_parameter_type.resource_id: utils.PluginParameterTypeDict(
                plugin_task_parameter_type=plugin_parameter_type, has_draft=False
            )
            for plugin_parameter_type in plugin_parameter_types
        }
        for resource_id in db.session.scalars(drafts_stmt):
            plugin_parameter_types_dict[resource_id]["has_draft"] = True

        return (
            list(plugin_parameter_types_dict.values()),
            total_num_plugin_parameter_types,
        )


class PluginParameterTypeIdService(object):
    """The service methods for registering and managing plugin parameter type
    by their unique id."""

    @inject
    def __init__(
        self,
        plugin_parameter_type_name_service: "PluginParameterTypeNameService",
    ) -> None:
        """Initialize the plugin parameter type service.

        All arguments are provided via dependency injection.

        Args:
            plugin_parameter_type_name_service: A PluginParameterTypeNameService object.
        """
        self._plugin_parameter_type_name_service = plugin_parameter_type_name_service

    def get(
        self,
        plugin_parameter_type_id: int,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> utils.PluginParameterTypeDict | None:
        """Fetch a plugin parameter type by its unique id.

        Args:
            plugin_parameter_type_id: The unique id of the plugin parameter
                type.
            error_if_not_found: If True, raise an error if the plugin parameter
                type is not found. Defaults to False.

        Returns:
            The plugin parameter type object if found, otherwise None.

        Raises:
            PluginParameterTypeDoesNotExistError: If the plugin parameter type
                is not found and `error_if_not_found` is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug(
            "Get plugin parameter type by id",
            plugin_parameter_type_id=plugin_parameter_type_id,
        )

        stmt = (
            select(models.PluginTaskParameterType)
            .join(models.Resource)
            .where(
                models.PluginTaskParameterType.resource_id == plugin_parameter_type_id,
                models.PluginTaskParameterType.resource_snapshot_id
                == models.Resource.latest_snapshot_id,
                models.Resource.is_deleted == False,  # noqa: E712
            )
        )
        plugin_parameter_type = db.session.scalars(stmt).first()

        if plugin_parameter_type is None:
            if error_if_not_found:
                log.debug(
                    "Plugin Parameter Type not found",
                    plugin_parameter_type_id=plugin_parameter_type_id,
                )
                raise PluginParameterTypeDoesNotExistError

            return None

        drafts_stmt = (
            select(models.DraftResource.draft_resource_id)
            .where(
                models.DraftResource.payload["resource_id"].as_string().cast(Integer)
                == plugin_parameter_type.resource_id,
                models.DraftResource.user_id == current_user.user_id,
            )
            .exists()
            .select()
        )
        has_draft = db.session.scalar(drafts_stmt)

        return utils.PluginParameterTypeDict(
            plugin_task_parameter_type=plugin_parameter_type, has_draft=has_draft
        )

    def modify(
        self,
        plugin_parameter_type_id: int,
        name: str,
        structure: str,
        description: str,
        error_if_not_found: bool = False,
        commit: bool = True,
        **kwargs,
    ) -> utils.PluginParameterTypeDict | None:
        """Modify a plugin parameter type.

        Args:
            plugin_parameter_type_id: The unique id of the plugin parameter
                type.
            name: The new name of the plugin parameter type.
            structure: Optional JSON-type field for further constraining a
                type's structure.
            description: The new description of the plugin parameter type.
            error_if_not_found: If True, raise an error if the group is not
                found. Defaults to False.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The updated plugin parameter type object.

        Raises:
            PluginParameterTypeDoesNotExistError: If the plugin parameter type
                is not found and `error_if_not_found` is True.
            PluginParameterTypeAlreadyExistsError: If the plugin parameter type
                name already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        plugin_parameter_type_dict = self.get(
            plugin_parameter_type_id, error_if_not_found=error_if_not_found, log=log
        )

        if plugin_parameter_type_dict is None:
            return None

        plugin_parameter_type = plugin_parameter_type_dict["plugin_task_parameter_type"]
        group_id = plugin_parameter_type.resource.group_id

        if plugin_parameter_type.resource.is_readonly:
            log.debug(
                "The Plugin Parameter Type is read-only and cannot be modified",
                plugin_parameter_type_id=plugin_parameter_type_id,
                name=plugin_parameter_type.name,
            )
            raise PluginParameterTypeReadOnlyLockError

        if name.strip().lower() in BUILTIN_TYPES:
            log.debug(
                "Plugin Parameter Type name matches a built-in type",
                name=name,
                normalized_name=name.strip().lower(),
            )
            raise PluginParameterTypeMatchesBuiltinTypeError

        if (
            name != plugin_parameter_type.name
            and self._plugin_parameter_type_name_service.get(
                name, group_id=group_id, log=log
            )
            is not None
        ):
            log.debug(
                "Plugin Parameter Type name already exists",
                name=name,
                group_id=group_id,
            )
            raise PluginParameterTypeAlreadyExistsError

        new_plugin_parameter_type = models.PluginTaskParameterType(
            name=name,
            structure=structure,
            description=description,
            resource=plugin_parameter_type.resource,
            creator=current_user,
        )
        db.session.add(new_plugin_parameter_type)

        if commit:
            db.session.commit()
            log.debug(
                "Plugin Parameter Type modification successful",
                plugin_parameter_type_id=plugin_parameter_type_id,
                name=name,
                structure=structure,
                description=description,
            )

        return utils.PluginParameterTypeDict(
            plugin_task_parameter_type=new_plugin_parameter_type, has_draft=False
        )

    def delete(self, plugin_parameter_type_id: int, **kwargs) -> dict[str, Any]:
        """Delete a plugin parameter type.

        Args:
            plugin_parameter_type_id: The unique id of the plugin parameter type.

        Returns:
            A dictionary reporting the status of the request.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        stmt = select(models.Resource).filter_by(
            resource_id=plugin_parameter_type_id,
            resource_type=RESOURCE_TYPE,
            is_deleted=False,
        )
        plugin_parameter_type_resource = db.session.scalars(stmt).first()

        if plugin_parameter_type_resource is None:
            raise PluginParameterTypeDoesNotExistError

        if plugin_parameter_type_resource.is_readonly:
            log.debug(
                "The Plugin Parameter Type is read-only and cannot be deleted",
                plugin_parameter_type_id=plugin_parameter_type_id,
            )
            raise PluginParameterTypeReadOnlyLockError

        deleted_resource_lock = models.ResourceLock(
            resource_lock_type=resource_lock_types.DELETE,
            resource=plugin_parameter_type_resource,
        )
        db.session.add(deleted_resource_lock)
        db.session.commit()
        log.debug(
            "Plugin Parameter Type deleted",
            plugin_parameter_type_id=plugin_parameter_type_id,
        )

        return {
            "status": "Success",
            "id": [plugin_parameter_type_id],
        }


class PluginParameterTypeNameService(object):
    """The service methods for managing plugin parameter types by their name."""

    def get(
        self,
        name: str,
        group_id: int,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> models.PluginTaskParameterType | None:
        """Fetch a plugin parameter type by its name.

        Args:
            name: The name of the plugin parameter type.
            group_id: The the group id of the plugin parameter type.
            error_if_not_found: If True, raise an error if the plugin parameter
                type is not found. Defaults to False.

        Returns:
            The plugin parameter type object if found, otherwise None.

        Raises:
            PluginParameterTypeDoesNotExistError: If the plugin parameter type
                is not found and `error_if_not_found` is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug(
            "Get plugin parameter type by name",
            plugin_parameter_type_name=name,
            group_id=group_id,
        )

        stmt = (
            select(models.PluginTaskParameterType)
            .join(models.Resource)
            .where(
                models.PluginTaskParameterType.name == name,
                models.Resource.group_id == group_id,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.PluginTaskParameterType.resource_snapshot_id,
            )
        )
        plugin_parameter_type = db.session.scalars(stmt).first()

        if plugin_parameter_type is None:
            if error_if_not_found:
                log.debug("Plugin Parameter Type not found", name=name)
                raise PluginParameterTypeDoesNotExistError

            return None

        return plugin_parameter_type


class BuiltinPluginParameterTypeService(object):
    """The service methods for registering the built-in plugin parameter types"""

    @inject
    def __init__(
        self,
        group_id_service: GroupIdService,
    ) -> None:
        """Initialize the builtin plugin parameter type service.

        All arguments are provided via dependency injection.

        Args:
            group_id_service: A GroupIdService object.
        """
        self._group_id_service = group_id_service

    def create_all(
        self,
        user: models.User,
        group: models.Group,
        commit: bool = True,
        **kwargs,
    ) -> list[utils.PluginParameterTypeDict]:
        """Create all built-in plugin parameter types in a given group.

        Args:
            user: The user that is creating the built-in plugin parameter types.
            group: The group that will own the registered built-in plugin parameter
                types.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            A list of the newly registered built-in plugin parameter types.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        builtin_types = list(BUILTIN_TYPES.keys())
        new_builtin_parameter_types: list[models.PluginTaskParameterType] = []
        for builtin_type in builtin_types:
            resource = models.Resource(resource_type=RESOURCE_TYPE, owner=group)
            new_plugin_parameter_type = models.PluginTaskParameterType(
                name=builtin_type,
                structure=None,
                description=None,
                resource=resource,
                creator=user,
            )
            db.session.add(new_plugin_parameter_type)
            db.session.add(
                models.ResourceLock(
                    resource_lock_type=resource_lock_types.READONLY,
                    resource=resource,
                )
            )
            new_builtin_parameter_types.append(new_plugin_parameter_type)

        if commit:
            db.session.commit()
            log.debug(
                "Built-in Plugin Parameter Types registration successful",
                builtin_parameter_type_ids=[
                    x.resource_id for x in new_builtin_parameter_types
                ],
            )

        return [
            utils.PluginParameterTypeDict(
                plugin_task_parameter_type=new_builtin_parameter_type, has_draft=False
            )
            for new_builtin_parameter_type in new_builtin_parameter_types
        ]
