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
"""The server-side functions that perform group membership endpoint operations."""
from __future__ import annotations

from typing import Any, cast

import structlog
from sqlalchemy.exc import IntegrityError
from structlog.stdlib import BoundLogger

from dioptra.restapi.app import db

from .errors import GroupMembershipDoesNotExistError
from .model import GroupMembership

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class GroupMembershipService(object):
    def get_all(self, **kwargs) -> list[GroupMembership]:
        """Retrieve a list of all group memberships.

        Returns:
            List of group memberships.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841

        return GroupMembership.query.all()  # type: ignore

    def get(
        self, group_id: int, user_id: int, error_if_not_found: bool = False, **kwargs
    ) -> GroupMembership | None:
        """Retrieve a group membership.

        Args:
            group_id: The unique ID of the group.
            user_id: The unique ID of the user.
            error_if_not_found: Flag to raise an error if the membership is
                not found.

        Returns:
            The group membership if found, else None.

        Raises:
            GroupMembershipNotFoundError: If the membership is not found and
                error_if_not_found is True.
        """

        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841

        membership = GroupMembership.query.filter(
            GroupMembership.user_id == user_id, GroupMembership.group_id == group_id
        ).first()

        if error_if_not_found:
            if membership is None:
                log.error("Group Membership not found", group_id=group_id)
                raise GroupMembershipDoesNotExistError

        return cast(GroupMembership, membership)

    def create(
        self,
        group_id: int,
        user_id: int,
        read: bool,
        write: bool,
        share_read: bool,
        share_write: bool,
        **kwargs,
    ) -> GroupMembership:
        """Create a new group membership.

        Args:
            group_id: The unique ID of the group.
            user_id: The unique ID of the user.
            read: Permission flag for read access.
            write: Permission flag for write access.
            share_read: Permission flag for sharing with read access.
            share_write: Permission flag for sharing with write access.

        Returns:
            GroupMembership: The newly created group membership.

        Raises:
            GroupMembershipAlreadyExistsError: If the membership already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        if self.get(group_id=group_id, user_id=user_id) is not None:
            log.error("Group Membership already exists", group_id=group_id)
            raise GroupMembershipDoesNotExistError

        new_group_membership = GroupMembership(
            group_id=group_id,
            user_id=user_id,
            read=read,
            write=write,
            share_read=share_read,
            share_write=share_write,
        )

        db.session.add(new_group_membership)
        db.session.commit()

        log.info(
            "Group Membership submission successful",
            group_id=new_group_membership.group_id,
            user_id=new_group_membership.user_id,
        )

        return new_group_membership

    def delete(self, group_id, user_id, **kwargs) -> dict[str, Any]:
        """Delete a group membership.

        Args:
            group_id: The unique ID of the group.
            user_id: The unique ID of the user.

        Returns:
            A dictionary with the status and IDs of the deleted membership.
        Raises:
            IntegrityError: If there is an issue with the database integrity during
                deletion.
        """

        log: BoundLogger = kwargs.get("log", LOGGER.new())

        if (membership := self.get(group_id=group_id, user_id=user_id)) is None:
            return {"status": "Success", "id": []}
        try:
            db.session.delete(membership)
            db.session.commit()

            log.info("Group Membership deleted", group_id=group_id, user_id=user_id)
            return {"status": "Success", "id": [group_id, user_id]}
        except IntegrityError:
            db.session.rollback()
            return {"status": "Failure", "id": [group_id, user_id]}
