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

from typing import Any, Final

import structlog
from flask_login import current_user
from sqlalchemy import select
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import db, models

from .errors import GroupDoesNotExistError, GroupNameNotAvailableError

LOGGER: BoundLogger = structlog.stdlib.get_logger()

NEW_GROUP_MEMBER_PERMISSIONS: Final[dict[str, bool]] = {
    "read": True,
    "write": True,
    "share_read": True,
    "share_write": True,
}

NEW_GROUP_MANAGER_PERMISSIONS: Final[dict[str, bool]] = {
    "owner": True,
    "admin": True,
}


class GroupService(object):
    """The service methods used to register and manage groups."""

    def create(
        self,
        name: str,
        error_if_exists: bool = False,
        **kwargs,
    ) -> models.User:
        """Create a new group.

        Args:
            name: The name requested by the user.

        Returns:
            The new group object.

        Raises:
            GroupNameNotAvailable: If the group name already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        new_group = GroupService.create_group(
            name,
            current_user,
            NEW_GROUP_MEMBER_PERMISSIONS,
            NEW_GROUP_MANAGER_PERMISSIONS,
            error_if_exists=error_if_exists,
            log=log,
        )
        db.session.add(new_group)
        db.session.commit()

        log.info("Group creation successful", group_id=new_group.group_id)

        return new_group

    @staticmethod
    def create_group(
        name: str,
        user: models.User,
        member_permissions: dict[str, Any] | None = None,
        manager_permissions: dict[str, Any] | None = None,
        error_if_exists: bool = False,
        **kwargs,
    ):
        """
        Constructs a new Group object and attaches GroupManager and GroupMember objects.
        If a group with the specified name already exists, retrieve it and attach
        permissions.

        Args:
            name: The name of the group.
            user: The creator of the group.
            member_permissions: A dictionary specifying the member permissions.
            manager_permissions: A dictionary specifying the member permissions.
            error_if_exist: If True, raise an error if the group already exists.
                Defaults to False.

        Raises:
            GroupNameNotAvailable: If the group name already exists.

        Returns:
            The group object if found, otherwise None.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        group: models.Group | None = GroupService.get_group_by_name(name)
        if group is None:
            group: models.Group = models.Group(name=name, creator=user)
        else:
            if error_if_exists:
                log.info("Group name already exists", name=name)
                raise GroupNameNotAvailableError

        if manager_permissions is not None:
            group.managers.append(
                models.GroupManager(
                    user=user,
                    owner=manager_permissions.get("owner", False),
                    admin=manager_permissions.get("admin", False),
                )
            )

        if member_permissions is not None:
            group.members.append(
                models.GroupMember(
                    user=user,
                    read=member_permissions.get("read", False),
                    write=member_permissions.get("read", False),
                    share_read=member_permissions.get("share_read", False),
                    share_write=member_permissions.get("share_write", False),
                )
            )

        return group

    @staticmethod
    def get_group_by_name(
        name: str, error_if_not_found: bool = False, **kwargs
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
        log.info("Lookup group by name", name=name)

        stmt = select(models.Group).filter_by(name=name)
        group: models.Group | None = db.session.scalars(stmt).first()

        if group is None:
            if error_if_not_found:
                log.error("Group not found", name=name)
                raise GroupDoesNotExistError

            return None

        return group


class GroupIdService(object):
    """The service methods used to manage a group by ID."""

    def get(
        self, group_id: int, error_if_not_found: bool = False, **kwargs
    ) -> models.User | None:
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
        log.info("Lookup group by unique id", group_id=group_id)

        stmt = select(models.Group).filter_by(group_id=group_id, is_deleted=False)
        group: models.Group | None = db.session.scalars(stmt).first()

        if group is None:
            if error_if_not_found:
                log.error("Group not found", group_id=group_id)
                raise GroupDoesNotExistError

            return None

        return group

    def modify(
        self, group_id: str, name: str, error_if_not_found: bool, **kwargs
    ) -> models.Group | None:
        """Modifies the specified group.

        Args:
            name: The group's name.

        Returns:
            The group object.

        Raises:
            GroupDoesNotExistError: If the group is not found.
            error_if_not_found: If True, raise an error if the group is not found.
                Defaults to False.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.info("Modify user account", user_id=current_user.user_id)

        stmt = select(models.Group).filter_by(group_id=group_id, is_deleted=False)
        group: models.Group | None = db.session.scalars(stmt).first()

        if group is None:
            if error_if_not_found:
                log.error("Group not found", group_id=group_id)
                raise GroupDoesNotExistError

            return None

        group.name = name
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
        log.info("Delete group", group_id=group_id)

        stmt = select(models.Group).filter_by(group_id=group_id, is_deleted=False)
        group: models.Group | None = db.session.scalars(stmt).first()

        if group is None:
            raise GroupDoesNotExistError

        name = group.name

        deleted_group_lock = models.GroupLock(
            group_lock_type="delete",
            group=group,
        )
        db.session.add(deleted_group_lock)
        db.session.commit()
        log.info("Group deleted", group_id=group.group_id)

        return {"status": "Success", "group": [name]}
