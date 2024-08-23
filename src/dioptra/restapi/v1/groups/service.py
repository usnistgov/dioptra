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
"""The server-side functions that perform group endpoint operations."""
from __future__ import annotations

import datetime
from typing import Any, Final, cast

import structlog
from injector import inject
from sqlalchemy import func, select
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import db, models
from dioptra.restapi.db.models.constants import group_lock_types
from dioptra.restapi.errors import BackendDatabaseError
from dioptra.restapi.v1.shared.search_parser import construct_sql_query_filters

from .errors import GroupDoesNotExistError, GroupNameNotAvailableError

LOGGER: BoundLogger = structlog.stdlib.get_logger()

DEFAULT_GROUP_MEMBER_PERMISSIONS: Final[dict[str, bool]] = {
    "read": False,
    "write": False,
    "share_read": False,
    "share_write": False,
}
DEFAULT_GROUP_MANAGER_PERMISSIONS: Final[dict[str, bool]] = {
    "owner": False,
    "admin": True,
}
GROUP_CREATOR_MEMBER_PERMISSIONS: Final[dict[str, bool]] = {
    "read": True,
    "write": True,
    "share_read": True,
    "share_write": True,
}
GROUP_CREATOR_MANAGER_PERMISSIONS: Final[dict[str, bool]] = {
    "owner": True,
    "admin": True,
}
SEARCHABLE_FIELDS: Final[dict[str, Any]] = {
    "name": lambda x: models.Group.name.like(x, escape="/"),
}


class GroupService(object):
    """The service methods used for creating and managing groups."""

    @inject
    def __init__(
        self,
        group_name_service: GroupNameService,
        group_member_service: GroupMemberService,
        group_manager_service: GroupManagerService,
    ) -> None:
        """Initialize the group service.

        All arguments are provided via dependency injection.

        Args:
            group_name_service: A GroupNameService object.
            group_member_service: A GroupMemberService object.
            group_manager_service: A GroupManagerService object.
        """
        self._group_name_service = group_name_service
        self._group_member_service = group_member_service
        self._group_manager_service = group_manager_service

    def create(
        self,
        name: str,
        creator: models.User,
        commit: bool = True,
        **kwargs,
    ) -> models.Group:
        """Create a new group.

        Args:
            name: The name requested by the user.
            creator: The user who created the group.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The new group object.

        Raises:
            GroupNameNotAvailable: If the group name already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        if self._group_name_service.get(name) is not None:
            log.debug("Group name already exists", name=name)
            raise GroupNameNotAvailableError

        new_group = models.Group(name=name, creator=creator)
        self._group_member_service.create(
            group=new_group,
            user=creator,
            permissions=GROUP_CREATOR_MEMBER_PERMISSIONS,
            commit=False,
            log=log,
        )
        self._group_manager_service.create(
            group=new_group,
            user=creator,
            permissions=GROUP_CREATOR_MANAGER_PERMISSIONS,
            commit=False,
            log=log,
        )

        db.session.add(new_group)

        if commit:
            db.session.commit()
            log.debug("Group creation successful", group_id=new_group.group_id)

        return new_group

    def get(
        self,
        search_string: str,
        page_index: int,
        page_length: int,
        **kwargs,
    ) -> tuple[list[models.Group], int]:
        """Fetch a list of groups, optionally filtering by search string and paging
        parameters.

        Args:
            search_string: A search string used to filter results.
            page_index: The index of the first group to be returned.
            page_length: The maximum number of groups to be returned.

        Returns:
            A tuple containing a list of groups and the total number of groups matching
            the query.

        Raises:
            BackendDatabaseError: If the database query returns a None when counting
                the number of groups.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get list of groups")

        search_filters = construct_sql_query_filters(search_string, SEARCHABLE_FIELDS)

        stmt = (
            select(func.count(models.Group.group_id))
            .filter_by(is_deleted=False)
            .filter(search_filters)
        )
        total_num_groups = db.session.scalars(stmt).first()

        if total_num_groups is None:
            log.error(
                "The database query returned a None when counting the number of "
                "groups when it should return a number.",
                sql=str(stmt),
            )
            raise BackendDatabaseError

        if total_num_groups == 0:
            return cast(list[models.Group], []), total_num_groups

        stmt = (
            select(models.Group)  # type: ignore
            .filter_by(is_deleted=False)
            .filter(search_filters)
            .offset(page_index)
            .limit(page_length)
        )
        groups = cast(list[models.Group], db.session.scalars(stmt).all())

        return groups, total_num_groups


class GroupIdService(object):
    """The service methods used to manage a group by ID."""

    @inject
    def __init__(
        self, group_service: GroupService, group_name_service: GroupNameService
    ) -> None:
        """Initialize the group ID service.

        All arguments are provided via dependency injection.

        Args:
            group_service: A GroupService object.
            group_name_service: A GroupNameService object.
        """
        self._group_service = group_service
        self._group_name_service = group_name_service

    def get(
        self, group_id: int, error_if_not_found: bool = False, **kwargs
    ) -> models.Group | None:
        """Fetch a group by its unique id.

        Args:
            group_id: The unique id of the group.
            error_if_not_found: If True, raise an error if the group is not found.
                Defaults to False.

        Returns:
            The group object if found, otherwise None.

        Raises:
            UserDoesNotExistError: If the group is not found and `error_if_not_found`
                is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Lookup group by unique id", group_id=group_id)

        stmt = select(models.Group).filter_by(group_id=group_id, is_deleted=False)
        group: models.Group | None = db.session.scalars(stmt).first()

        if group is None:
            if error_if_not_found:
                log.debug("Group not found", group_id=group_id)
                raise GroupDoesNotExistError

            return None

        return group

    def modify(
        self,
        group_id: int,
        name: str,
        error_if_not_found: bool = False,
        commit: bool = True,
        **kwargs,
    ) -> models.Group | None:
        """Modifies the specified group.

        Args:
            group_id: The ID of the group to be modified.
            name: The new name for the group.
            error_if_not_found: If True, raise an error if the group is not found.
                Defaults to False.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The group object.

        Raises:
            GroupDoesNotExistError: If the group is not found and `error_if_not_found`
                is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Modify group", group_id=group_id)

        stmt = select(models.Group).filter_by(group_id=group_id, is_deleted=False)
        group = db.session.scalars(stmt).first()

        if group is None:
            if error_if_not_found:
                log.debug("Group not found", group_id=group_id)
                raise GroupDoesNotExistError

            return None

        if self._group_name_service.get(name, log=log) is not None:
            log.debug("Group name already exists", name=name)
            raise GroupNameNotAvailableError

        current_timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        group.last_modified_on = current_timestamp
        group.name = name

        if commit:
            db.session.commit()

        return group

    def delete(self, group_id: int, **kwargs) -> dict[str, Any]:
        """Permanently deletes the group by ID.

        Args:
            group_id: The ID of the group to be deleted.

        Returns:
            A dictionary containing the delete group success message if the group is
            deleted successfully.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Delete group", group_id=group_id)

        stmt = select(models.Group).filter_by(group_id=group_id, is_deleted=False)
        group = db.session.scalars(stmt).first()

        if group is None:
            raise GroupDoesNotExistError

        name = group.name

        deleted_group_lock = models.GroupLock(
            group_lock_type=group_lock_types.DELETE,
            group=group,
        )
        db.session.add(deleted_group_lock)
        db.session.commit()
        log.debug("Group deleted", group_id=group.group_id)

        return {"status": "Success", "group": name}


class GroupNameService(object):
    """The service methods used to manage a group by name."""

    def get(
        self, name: str, error_if_not_found: bool = False, **kwargs
    ) -> models.Group | None:
        """Fetch a group by its name.

        Args:
            name: The name of the group.
            error_if_not_found: If True, raise an error if the group is not found.
                Defaults to False.

        Returns:
            The group object if found, otherwise None.

        Raises:
            GroupDoesNotExistError: If the group is not found and `error_if_not_found`
                is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Lookup group by name", name=name)

        stmt = select(models.Group).filter_by(name=name)
        group = db.session.scalars(stmt).first()

        if group is None:
            if error_if_not_found:
                log.debug("Group not found", name=name)
                raise GroupDoesNotExistError

            return None

        return group


class GroupMemberService(object):
    """The service methods used to manage a group's members."""

    def create(
        self,
        group: models.Group,
        user: models.User,
        permissions: dict[str, bool] | None = None,
        commit: bool = True,
        **kwargs,
    ) -> models.GroupMember:
        """Add a user to a group.

        If not specified, the default permissions will be::

            {
                "read": False,
                "write": False,
                "share_read": False,
                "share_write": False,
            }

        Args:
            group: The group to which the user is being added.
            user: The user being added to the group.
            permissions: The permissions for the user in the group. Defaults to None.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The new group member object.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        permissions = permissions or DEFAULT_GROUP_MEMBER_PERMISSIONS
        log.debug("Add group member", group_id=group.group_id, user_id=user.user_id)
        group_member = models.GroupMember(
            user=user,
            read=permissions["read"],
            write=permissions["write"],
            share_read=permissions["share_read"],
            share_write=permissions["share_write"],
        )
        group.members.append(group_member)

        if commit:
            db.session.commit()

        return group_member


class GroupManagerService(object):
    """The service methods used to manage a group's managers."""

    def create(
        self,
        group: models.Group,
        user: models.User,
        permissions: dict[str, bool] | None = None,
        commit: bool = True,
        **kwargs,
    ) -> models.GroupManager:
        """Assign an existing group member to be a manager of a group.

        If not specified, the default permissions will be::

            {
                "owner": False,
                "admin": True,
            }

        Args:
            group: The group receiving a new manager.
            user: The user being assigned as a manager of the group. The user must
                already be a member of the group.
            permissions: The permissions for the user in the group. Defaults to None.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The new group manager object.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        permissions = permissions or DEFAULT_GROUP_MANAGER_PERMISSIONS
        log.debug("Add group manager", group_id=group.group_id, user_id=user.user_id)
        group_manager = models.GroupManager(
            user=user,
            owner=permissions["owner"],
            admin=permissions["admin"],
        )
        group.managers.append(group_manager)

        if commit:
            db.session.commit()

        return group_manager
