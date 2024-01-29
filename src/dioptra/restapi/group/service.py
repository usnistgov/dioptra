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
"""The server-side functions that perform job endpoint operations."""
from __future__ import annotations

import datetime
from typing import Any, cast

import structlog
from sqlalchemy.exc import IntegrityError
from structlog.stdlib import BoundLogger

from dioptra.restapi.app import db
from dioptra.restapi.utils import slugify

from .errors import GroupDoesNotExistError
from .model import Group

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class GroupService(object):
    """The service methods for registering and managing groups by their unique id."""

    def get_all(self, **kwargs) -> list[Group]:
        """Fetch the list of all groups.

        Returns:
            A list of groups.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841

        log.info("Get full list of groups.")

        return Group.query.all()  # type: ignore

    def get(
        self, group_id: int, error_if_not_found: bool = False, **kwargs
    ) -> Group | None:
        """Fetch a group by its unique id.

        Args:
            group_id: The unique id of the group.
            error_if_not_found: Raise an error if the group cannot be found.
        Returns:
            The group object if found, otherwise None.

        Raises:
            GroupDoesNotExistError: If the group with group_id cannot be found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841

        log.info("Get group by id", group_id=group_id)
        group = Group.query.filter_by(group_id=group_id, deleted=False).first()

        if group is None:
            if error_if_not_found:
                log.error("Group not found", group_id=group_id)
                raise GroupDoesNotExistError
            return None

        return cast(Group, group)

    def create(self, name: str, user_id=None, **kwargs) -> Group:
        """Create a new group.

        Args:
            name: The name of the group.
            user_id: The id of the user creating the group.

        Returns:
            The newly created group object.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        timestamp = datetime.datetime.now()

        # #to be used when user is fully implemented
        # if user_id is None:
        #     user_id= current_user.id

        new_group = Group(
            group_id=Group.next_id(),
            name=slugify(name),
            creator_id=user_id,
            owner_id=user_id,
            created_on=timestamp,
            deleted=False,
        )

        db.session.add(new_group)
        db.session.commit()

        log.info("Group submission successful", group_id=new_group.group_id)

        return new_group

    def delete(self, id: int, **kwargs) -> dict[str, Any]:
        """Delete a group.

        Args:
            group_id: The unique id of the group.

        Returns:
            A dictionary reporting the status of the request.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        if (group := self.get(id, log=log)) is None:
            return {"status": "Success", "id": []}
        group.update(changes={"deleted": True})
        try:
            db.session.commit()

            log.info("Group deleted", group_id=id)
            return {"status": "Success", "id": [id]}
        except IntegrityError:
            db.session.rollback()
            return {"status": "Failure", "id": [id]}
