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
"""The module defining the user endpoints."""
from __future__ import annotations

import uuid
from typing import Any, cast

import structlog
from flask import request
from flask_accepts import accepts, responds
from flask_login import current_user, login_required
from flask_restx import Namespace, Resource
from injector import inject
from structlog.stdlib import BoundLogger

from .model import User
from .schema import (
    ChangePasswordCurrentUserSchema,
    ChangePasswordUserSchema,
    DeleteCurrentUserSchema,
    UsernameStatusResponseSchema,
    UserSchema,
)
from .service import CurrentUserService, UserPasswordService, UserService

LOGGER: BoundLogger = structlog.stdlib.get_logger()

api: Namespace = Namespace(
    "User",
    description="User accounts",
)


@api.route("/")
class UserResource(Resource):
    """Methods for the /user endpoint."""

    @inject
    def __init__(self, user_service: UserService, *args, **kwargs) -> None:
        """Initialize the user resource.

        All arguments are provided via dependency injection.

        Args:
            user_service: A UserService object.
        """
        self._user_service = user_service
        super().__init__(*args, **kwargs)

    @accepts(schema=UserSchema, api=api)
    @responds(schema=UserSchema, api=api)
    def post(self) -> User:
        """Register a new user."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="user", request_type="POST"
        )  # noqa: F841
        log.info("Request received")
        parsed_obj = request.parsed_obj  # type: ignore
        username = str(parsed_obj["username"])
        email_address = str(parsed_obj["email_address"])
        password = str(parsed_obj["password"])
        confirm_password = str(parsed_obj["confirm_password"])

        return self._user_service.create(
            username=username,
            email_address=email_address,
            password=password,
            confirm_password=confirm_password,
            log=log,
        )


@api.route("/password")
class UserPasswordResource(Resource):
    """Methods for the /user/password endpoint."""

    @inject
    def __init__(self, user_service: UserService, *args, **kwargs) -> None:
        """Initialize the user password resource.

        All arguments are provided via dependency injection.

        Args:
            user_service: A UserService object.
        """
        self._user_service = user_service
        super().__init__(*args, **kwargs)

    @accepts(schema=ChangePasswordUserSchema, api=api)
    @responds(schema=UsernameStatusResponseSchema, api=api)
    def post(self) -> dict[str, Any]:
        """Change the password of the specified user account."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="userId/password",
            request_type="POST",
        )  # noqa: F841
        log.info("Request received")
        parsed_obj = request.parsed_obj  # type: ignore
        user_id = int(parsed_obj["user_id"])
        current_password = str(parsed_obj["current_password"])
        new_password = str(parsed_obj["new_password"])
        return self._user_service.change_password(
            user_id=user_id,
            current_password=current_password,
            new_password=new_password,
            log=log,
        )


@api.route("/<int:userId>")
class UserIdResource(Resource):
    """Methods for the /user/<userId> endpoint."""

    @inject
    def __init__(self, user_service: UserService, *args, **kwargs) -> None:
        """Initialize the user id resource.

        All arguments are provided via dependency injection.

        Args:
            user_service: A UserService object.
        """
        self._user_service = user_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=UserSchema, api=api)
    def get(self, userId: int) -> User:
        """Get info about a specified user.

        Must be logged in.
        """
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="current", request_type="GET"
        )  # noqa: F841
        return cast(
            User,
            self._user_service.get(user_id=userId, error_if_not_found=True, log=log),
        )


@api.route("/current")
class CurrentUserResource(Resource):
    """Methods for the /user/current endpoint."""

    @inject
    def __init__(
        self, current_user_service: CurrentUserService, *args, **kwargs
    ) -> None:
        """Initialize the current user resource.

        All arguments are provided via dependency injection.

        Args:
            current_user_service: A CurrentUserService object.
        """
        self._current_user_service = current_user_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=UserSchema, api=api)
    def get(self) -> User:
        """Get info about the current user.

        Must be logged in.
        """
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="current", request_type="GET"
        )  # noqa: F841
        return self._current_user_service.get(log=log)

    @login_required
    @accepts(schema=DeleteCurrentUserSchema, api=api)
    @responds(schema=UsernameStatusResponseSchema, api=api)
    def delete(self) -> dict[str, Any]:
        """Delete the current user.

        Must be logged in.
        """
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="current", request_type="DELETE"
        )  # noqa: F841
        log.info("Request received")
        parsed_obj = request.parsed_obj  # type: ignore
        password = str(parsed_obj["password"])
        return self._current_user_service.delete(password=password, log=log)


@api.route("/current/password")
class CurrentUserPasswordResource(Resource):
    """Methods for the /user/current/password endpoint."""

    @inject
    def __init__(
        self, user_password_service: UserPasswordService, *args, **kwargs
    ) -> None:
        """Initialize the current user password resource.

        All arguments are provided via dependency injection.

        Args:
            user_password_service: A UserPasswordService object.
        """
        self._user_password_service = user_password_service
        super().__init__(*args, **kwargs)

    @login_required
    @accepts(schema=ChangePasswordCurrentUserSchema, api=api)
    @responds(schema=UsernameStatusResponseSchema, api=api)
    def post(self) -> dict[str, Any] | tuple[dict[str, Any], int]:
        """Change the current user's password.

        Must be logged in.
        """
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="current/password",
            request_type="POST",
        )  # noqa: F841
        log.info("Request received")
        parsed_obj = request.parsed_obj  # type: ignore
        current_password = str(parsed_obj["current_password"])
        new_password = str(parsed_obj["new_password"])
        return self._user_password_service.change(
            user=current_user,
            current_password=current_password,
            new_password=new_password,
            log=log,
        )
