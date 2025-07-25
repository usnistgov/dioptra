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

import datetime
from typing import Any, Final

import structlog
from injector import inject
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import models
from dioptra.restapi.db.repository.utils import DeletionPolicy
from dioptra.restapi.db.unit_of_work import UnitOfWork
from dioptra.restapi.errors import EntityDoesNotExistError, EntityExistsError
from dioptra.restapi.v1.shared.search_parser import parse_search_text

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

GROUP_TYPE: Final[str] = "group"


class GroupService(object):
    """The service methods used for creating and managing groups."""

    @inject
    def __init__(
        self,
        group_member_service: "GroupMemberService",
        group_manager_service: "GroupManagerService",
        uow: UnitOfWork,
    ) -> None:
        """Initialize the group service.

        All arguments are provided via dependency injection.

        Args:
            group_member_service: A GroupMemberService object.
            group_manager_service: A GroupManagerService object.
            uow: A UnitOfWork instance
        """
        self._group_member_service = group_member_service
        self._group_manager_service = group_manager_service
        self._uow = uow

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

        new_group = models.Group(name=name, creator=creator)
        self._uow.group_repo.create(new_group)

        if commit:
            self._uow.commit()
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

        search_struct = parse_search_text(search_string)
        groups, total_num_groups = self._uow.group_repo.get_by_filters_paged(
            search_struct, page_index, page_length
        )

        return list(groups), total_num_groups


class GroupIdService(object):
    """The service methods used to manage a group by ID."""

    @inject
    def __init__(
        self,
        uow: UnitOfWork,
    ) -> None:
        """Initialize the group ID service.

        All arguments are provided via dependency injection.

        Args:
            uow: A UnitOfWork instance
        """
        self._uow = uow

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
            EntityDoesNotExistError: If the group is not found and `error_if_not_found`
                is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Lookup group by unique id", group_id=group_id)

        group = self._uow.group_repo.get(group_id, DeletionPolicy.NOT_DELETED)

        if group is None:
            if error_if_not_found:
                raise EntityDoesNotExistError(GROUP_TYPE, group_id=group_id)

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
            EntityDoesNotExistError: If the group is not found and `error_if_not_found`
                is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Modify group", group_id=group_id)

        group = self._uow.group_repo.get(group_id, DeletionPolicy.NOT_DELETED)

        if group is None:
            if error_if_not_found:
                raise EntityDoesNotExistError(GROUP_TYPE, group_id=group_id)

            return None

        duplicate = self._uow.group_repo.get_by_name(name, DeletionPolicy.ANY)
        if duplicate is not None:
            raise EntityExistsError(GROUP_TYPE, duplicate.group_id, name=name)

        current_timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        group.last_modified_on = current_timestamp
        group.name = name

        if commit:
            self._uow.commit()

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

        group = self._uow.group_repo.get_one(group_id, DeletionPolicy.NOT_DELETED)

        with self._uow:
            self._uow.group_repo.delete(group)

        log.debug("Group deleted", group_id=group.group_id)

        return {"status": "Success", "group": group.name}


class GroupMemberService(object):
    """The service methods used to manage a group's members."""

    @inject
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

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

        group_member = self._uow.group_repo.add_member(group, user, **permissions)

        if commit:
            self._uow.commit()

        return group_member


class GroupManagerService(object):
    """The service methods used to manage a group's managers."""

    @inject
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

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

        group_manager = self._uow.group_repo.add_manager(group, user, **permissions)

        if commit:
            self._uow.commit()

        return group_manager
