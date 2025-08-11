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

from typing import Any, Final, Iterable

import structlog
from flask_login import current_user
from injector import inject
from sqlalchemy import select
from structlog.stdlib import BoundLogger

import dioptra.restapi.db.repository.utils as repoutils
from dioptra.restapi.db import db, models
from dioptra.restapi.db.unit_of_work import UnitOfWork
from dioptra.restapi.errors import (
    BackendDatabaseError,
    EntityDoesNotExistError,
    InconsistentBuiltinPluginParameterTypesError,
    PluginParameterTypeMatchesBuiltinTypeError,
)
from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.entity_types import EntityTypes
from dioptra.restapi.v1.shared.search_parser import parse_search_text
from dioptra.task_engine.type_registry import BUILTIN_TYPES

LOGGER: BoundLogger = structlog.stdlib.get_logger()

RESOURCE_TYPE: Final[EntityTypes] = EntityTypes.PLUGIN_TASK_PARAMETER_TYPE


class PluginParameterTypeService(object):
    """The service methods for registering and managing plugin parameter types
    by their unique id."""

    @inject
    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the plugin parameter type service.

        All arguments are provided via dependency injection.

        Args:
            uow: A UnitOfWork instance
        """
        self._uow = uow

    def create(
        self,
        name: str,
        structure: dict[str, Any] | None,
        description: str | None,
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
            EntityExistsError: If a plugin parameter type with the given name already
                exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        if name.strip().lower() in BUILTIN_TYPES:
            log.debug(
                "Plugin Parameter Type name matches a built-in type",
                name=name,
                normalized_name=name.strip().lower(),
            )
            raise PluginParameterTypeMatchesBuiltinTypeError

        group = self._uow.group_repo.get_one(
            group_id, repoutils.DeletionPolicy.NOT_DELETED
        )

        resource = models.Resource(
            resource_type=RESOURCE_TYPE.get_db_schema_name(), owner=group
        )
        new_plugin_parameter_type = models.PluginTaskParameterType(
            name=name,
            structure=structure,
            description=description,
            resource=resource,
            creator=current_user,
        )

        try:
            self._uow.type_repo.create(new_plugin_parameter_type)
        except Exception:
            self._uow.rollback()
            raise

        if commit:
            self._uow.commit()
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
        sort_by_string: str,
        descending: bool,
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
            sort_by_string: The name of the column to sort.
            descending: Boolean indicating whether to sort by descending or not.

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

        search_struct = parse_search_text(search_string)

        types, total_num_types = self._uow.type_repo.get_by_filters_paged(
            group_id,
            search_struct,
            page_index,
            page_length,
            sort_by_string,
            descending,
            repoutils.DeletionPolicy.NOT_DELETED,
        )

        plugin_parameter_types_dict: dict[int, utils.PluginParameterTypeDict] = {
            plugin_parameter_type.resource_id: utils.PluginParameterTypeDict(
                plugin_task_parameter_type=plugin_parameter_type, has_draft=False
            )
            for plugin_parameter_type in types
        }

        resource_ids_with_drafts = self._uow.drafts_repo.has_draft_modifications(
            types,
            current_user,
        )

        for resource_id in resource_ids_with_drafts:
            plugin_parameter_types_dict[resource_id]["has_draft"] = True

        return (
            list(plugin_parameter_types_dict.values()),
            total_num_types,
        )


class PluginParameterTypeIdService(object):
    """The service methods for registering and managing plugin parameter type
    by their unique id."""

    @inject
    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the plugin parameter type service.

        All arguments are provided via dependency injection.

        Args:
            uow: A UnitOfWork instance
        """
        self._uow = uow

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
            EntityDoesNotExistError: If the plugin parameter type
                is not found and `error_if_not_found` is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug(
            "Get plugin parameter type by id",
            plugin_parameter_type_id=plugin_parameter_type_id,
        )

        plugin_parameter_type = self._uow.type_repo.get(
            plugin_parameter_type_id, repoutils.DeletionPolicy.NOT_DELETED
        )

        if plugin_parameter_type is None:
            if error_if_not_found:
                raise EntityDoesNotExistError(
                    RESOURCE_TYPE, plugin_parameter_type_id=plugin_parameter_type_id
                )

            return None

        has_draft = self._uow.drafts_repo.has_draft_modification(
            plugin_parameter_type, current_user
        )

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
            EntityDoesNotExistError: If the plugin parameter type
                is not found and `error_if_not_found` is True.
            EntityExistsError: If the plugin parameter type
                name already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        plugin_parameter_type_dict = self.get(
            plugin_parameter_type_id, error_if_not_found=error_if_not_found, log=log
        )

        if plugin_parameter_type_dict is None:
            return None

        plugin_parameter_type = plugin_parameter_type_dict["plugin_task_parameter_type"]

        if name.strip().lower() in BUILTIN_TYPES:
            log.debug(
                "Plugin Parameter Type name matches a built-in type",
                name=name,
                normalized_name=name.strip().lower(),
            )
            raise PluginParameterTypeMatchesBuiltinTypeError

        new_plugin_parameter_type = models.PluginTaskParameterType(
            name=name,
            structure=structure,
            description=description,
            resource=plugin_parameter_type.resource,
            creator=current_user,
        )

        try:
            self._uow.type_repo.create_snapshot(new_plugin_parameter_type)
        except Exception:
            self._uow.rollback()
            raise

        if commit:
            self._uow.commit()
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
        with self._uow:
            self._uow.type_repo.delete(plugin_parameter_type_id)

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

    @inject
    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the builtin plugin parameter type service.

        All arguments are provided via dependency injection.

        Args:
            uow: A UnitOfWork instance
        """
        self._uow = uow

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
            EntityDoesNotExistError: If the given group does not exist or if the
                plugin parameter type is not found and `error_if_not_found` is True.
            EntityDeletedError: If the given group is deleted.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug(
            "Get plugin parameter type by name",
            plugin_parameter_type_name=name,
            group_id=group_id,
        )

        plugin_parameter_type = self._uow.type_repo.get_by_name(
            name, group_id, repoutils.DeletionPolicy.NOT_DELETED
        )

        if plugin_parameter_type is None:
            if error_if_not_found:
                raise EntityDoesNotExistError(
                    RESOURCE_TYPE, name=name, group_id=group_id
                )

            return None

        return plugin_parameter_type


class BuiltinPluginParameterTypeService(object):
    """The service methods for registering the built-in plugin parameter types"""

    @inject
    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the builtin plugin parameter type service.

        All arguments are provided via dependency injection.

        Args:
            uow: A UnitOfWork instance
        """
        self._uow = uow

    def get(
        self,
        group_id: int,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> list[models.PluginTaskParameterType]:
        """Fetch a list of builtin plugin parameter types.

        Args:
            group_id: The group id of the plugin parameter type.
            error_if_not_found: Deprecated, does not control anything. Kept for
                backwards compatibility purposes.

        Returns:
            The plugin parameter type object if found, otherwise None.

        Raises:
            PluginParameterTypeDoesNotExistError: If the plugin parameter type
                is not found and `error_if_not_found` is True.
            EntityDoesNotExistError: If the given group does not exist.
            EntityDeletedError: If the given group is deleted.
            InconsistentBuiltinPluginParameterTypesError: If the number of
                builtin types in the database does not match the number of
                builtin types declared in the code.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug(
            "Get builtin plugin parameter types",
            group_id=group_id,
        )

        builtin_types = self._uow.type_repo.get_by_name(
            BUILTIN_TYPES,
            group_id,
            repoutils.DeletionPolicy.NOT_DELETED,
        )

        if len(BUILTIN_TYPES) != len(builtin_types):
            retrieved_names = {param_type.name for param_type in builtin_types}
            missing_names = BUILTIN_TYPES.keys() - retrieved_names
            extra_names = retrieved_names - BUILTIN_TYPES.keys()
            raise InconsistentBuiltinPluginParameterTypesError(
                missing_names=missing_names,
                extra_names=extra_names,
            )

        return list(builtin_types)

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

        new_builtin_parameter_types = []
        for builtin_type_name in BUILTIN_TYPES:
            type_ = models.PluginTaskParameterType(
                None,
                models.Resource("plugin_task_parameter_type", group),
                user,
                builtin_type_name,
                None,
            )

            try:
                self._uow.type_repo.create(type_, {repoutils.ResourceLockType.READONLY})
            except Exception:
                self._uow.rollback()
                raise

            new_builtin_parameter_types.append(type_)

        if commit:
            self._uow.commit()
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


def get_plugin_task_parameter_types_by_id(
    ids: Iterable[int], log: BoundLogger
) -> dict[int, models.PluginTaskParameterType]:
    """Gets all of the PluginTaskParameterType instances based on the given ids
    iterable

    Args:
        ids: an iterable containing all of the ids
        log: where log messages should go

    Returns:
        The a dictionary of ids to PluginTaskParameterType instances

    Raises:
        ValueError: if ids does not contain at least one value
        EntityDoesNotExistError: if one or more of the ids does not exist in the
            PluginTaskParameterType table
    """
    id_list = set(ids)
    num_ids = len(id_list)
    if num_ids < 1:
        return {}
    parameter_types_stmt = (
        select(models.PluginTaskParameterType)
        .join(models.Resource)
        .where(
            models.PluginTaskParameterType.resource_id.in_(tuple(id_list)),
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
            num_expected=num_ids,
        )
        raise BackendDatabaseError

    if not len(parameter_types) == num_ids:
        returned_parameter_type_ids = {x.resource_id for x in parameter_types}
        ids_not_found = id_list - returned_parameter_type_ids
        raise EntityDoesNotExistError(
            RESOURCE_TYPE,
            num_expected=num_ids,
            num_found=len(parameter_types),
            ids_not_found=sorted(ids_not_found),
        )

    return {x.resource_id: x for x in parameter_types}
