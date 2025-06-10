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
"""The server-side functions that perform auth endpoint operations."""

from __future__ import annotations

import datetime
import uuid
from typing import Any

import structlog
from flask_login import current_user, login_user, logout_user
from injector import inject
from structlog.stdlib import BoundLogger

from dioptra.restapi.db.repository.utils import DeletionPolicy
from dioptra.restapi.db.unit_of_work import UnitOfWork
from dioptra.restapi.errors import UserDoesNotExistError
from dioptra.restapi.v1.users.service import UserPasswordService

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class AuthService(object):
    """The service methods for user logins and logouts."""

    @inject
    def __init__(
        self, user_password_service: UserPasswordService, uow: UnitOfWork
    ) -> None:
        """Initialize the authentication service.

        All arguments are provided via dependency injection.

        Args:
            user_password_service: A UserPasswordService object.
        """
        self._user_password_service = user_password_service
        self._uow = uow

    def login(
        self,
        username: str,
        password: str,
        **kwargs,
    ) -> dict[str, Any]:
        """Login the user with the given username and password.

        Args:
            username: The username for logging into the user account.
            password: The password for authenticating the user account.

        Returns:
            A dictionary containing the login success message.

        Raises:
            UserDoesNotExistError: If the user is not found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        user = self._uow.user_repo.get_by_name(username, DeletionPolicy.NOT_DELETED)
        if not user:
            raise UserDoesNotExistError(username=username)

        self._user_password_service.authenticate(
            password=password,
            user_password=str(user.password),
            expiration_date=user.password_expire_on,
            error_if_failed=True,
            log=log,
        )
        login_user(user, remember=True)
        with self._uow:
            user.last_login_on = datetime.datetime.now(tz=datetime.timezone.utc)
        log.debug("Login successful", user_id=user.user_id)
        return {"status": "Login successful", "username": username}

    def logout(self, everywhere: bool, **kwargs) -> dict[str, Any]:
        """Log the current user out.

        Args:
            everywhere: If True, log out from all devices by regenerating the current
                user's alternative id.

        Returns:
            A dictionary containing the logout success message.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        user_id = current_user.user_id
        username = current_user.username

        if everywhere:
            with self._uow:
                current_user.alternative_id = uuid.uuid4()

        logout_user()
        log.debug("Logout successful", user_id=user_id, everywhere=everywhere)
        return {
            "status": "Logout successful",
            "username": username,
            "everywhere": everywhere,
        }
