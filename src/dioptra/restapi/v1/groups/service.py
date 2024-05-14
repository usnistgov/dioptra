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
from dioptra.restapi.v1.utils import build_group

from .errors import GroupNameNotAvailableError, GroupDoesNotExistError

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class GroupService(object):
    """The service methods used to register and manage groups."""

    @inject
    def __init__(
        self,
    ) -> None:
        """Initialize the group service.

        All arguments are provided via dependency injection.
        """

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

        group: models.Group = self._get_group_by_name(name)
        if group is not None:
            if error_if_exists:
                log.info("Group name already exists", name=name)
                raise GroupNameNotAvailableError
            else:
                return build_group(group)

        new_group: models.Group = models.Group(name=name, creator=current_user)
        db.session.add(new_group)
        db.session.commit()

        log.info("Group creation successful", group_id=new_group.group_id)

        return build_group(new_group)

    def _get_group_by_name(
        self, name: str, error_if_not_found: bool = False, **kwargs
    ) -> models.Group | None:
        """Fetch a group by its name.

        Args:
            name: The name of the group.
            error_if_not_found: If True, raise an error if the user is not found.
                Defaults to False.

        Returns:
            The group object if found, otherwise None.

        Raises:
            GroupDoesNotExistError: If the group is not found and `error_if_not_found`
                is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.info("Lookup group by name", name=name)

        stmt = select(models.Group).filter_by(group_name=name)
        group: models.Group | None = db.session.scalars(stmt).first()

        if group is None:
            if error_if_not_found:
                log.error("Group not found", name=name)
                raise GroupDoesNotExistError

            return None


