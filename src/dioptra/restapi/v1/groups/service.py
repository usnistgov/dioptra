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

from typing import Any, Final, cast

import structlog
from flask_login import current_user
from injector import inject
from sqlalchemy import select
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import db, models
from dioptra.restapi.v1.utils import build_group_ref, build_user_ref

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class GroupService(object):
    """The service methods used to register and manage user accounts."""

    @inject
    def __init__(
        self,
    ) -> None:
        """Initialize the user service.

        All arguments are provided via dependency injection.

        Args:
            user_password_service: A UserPasswordService object.
            user_name_service: A UserNameService object.
        """

    def create(
        self,
        name: str,
        **kwargs,
    ) -> models.User:
        """Create a new group.

        Args:
            name: The name requested by the user.
            password: The password for the new user.
            confirm_password: The password confirmation for the new user.

        Returns:
            The new user object.

        Raises:
            UserRegistrationError: If the password and confirmation password do not
                match.
            UsernameNotAvailableError: If the username already exists.
            UserEmailNotAvailableError: If the email already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        new_group: models.Group = models.Group(name=name, creator=current_user)
        db.session.add(new_group)
        db.session.commit()

        log.info("Group creation successful", group_id=new_group.group_id)

        return build_group(new_group)


def build_group(group: models.Group) -> dict[str:Any]:
    members = [
        {
            "user": build_user_ref(member.user),
            "group": build_group_ref(group),
            "permissions": {
                "read": member.read,
                "write": member.write,
                "shareRead": member.share_read,
                "shareWrite": member.share_write,
                "admin": False,
                "owner": False,
            },
        }
        for member in group.members
    ]
    return {
        "id": group.group_ud,
        "name": group.name,
        "user": build_user_ref(group.creator),
        "members": members,
        "createdOn": group.created_on,
        "lastModified_on": group.last_modified_on,
    }
