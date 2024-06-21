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
"""The module defining the endpoints for User resources."""
import uuid
from typing import Any, cast
from urllib.parse import unquote

import structlog
from flask import request
from flask_accepts import accepts, responds
from flask_login import login_required
from flask_restx import Namespace, Resource
from injector import inject
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import models
from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.schemas import IdStatusResponseSchema

from .schema import (
    UserCurrentSchema,
    UserDeleteSchema,
    UserGetQueryParameters,
    UserMutableFieldsSchema,
    UserPageSchema,
    UserPasswordSchema,
    UserSchema,
)
from .service import UserCurrentService, UserIdService, UserService

LOGGER: BoundLogger = structlog.stdlib.get_logger()

api: Namespace = Namespace("Users", description="Users endpoint")


@api.route("/")
class UserEndpoint(Resource):
    @inject
    def __init__(self, user_service: UserService, *args, **kwargs) -> None:
        """Initialize the user resource.

        All arguments are provided via dependency injection.

        Args:
            user_service: A UserService object.
        """
        self._user_service = user_service
        super().__init__(*args, **kwargs)

    @login_required
    @accepts(query_params_schema=UserGetQueryParameters, api=api)
    @responds(schema=UserPageSchema, api=api)
    def get(self):
        """Gets a list of all Users."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="User", request_type="GET"
        )
        parsed_query_params = request.parsed_query_params  # noqa: F841

        search_string = unquote(parsed_query_params["search"])
        page_index = parsed_query_params["index"]
        page_length = parsed_query_params["page_length"]

        users, total_num_users = self._user_service.get(
            search_string=search_string,
            page_index=page_index,
            page_length=page_length,
            log=log,
        )
        return utils.build_paging_envelope(
            "users",
            build_fn=utils.build_user,
            data=users,
            query=search_string,
            draft_type=None,
            group_id=None,
            index=page_index,
            length=page_length,
            total_num_elements=total_num_users,
        )

    @accepts(schema=UserSchema, api=api)
    @responds(schema=UserCurrentSchema, api=api)
    def post(self):
        """Creates a User."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="User", request_type="POST"
        )
        parsed_obj = request.parsed_obj  # noqa: F841

        user = self._user_service.create(
            username=str(parsed_obj["username"]),
            email_address=str(parsed_obj["email"]),
            password=str(parsed_obj["password"]),
            confirm_password=str(parsed_obj["confirm_password"]),
            log=log,
        )
        return utils.build_current_user(user)


@api.route("/<int:id>")
@api.param("id", "ID for the User resource.")
class UserIdEndpoint(Resource):
    @inject
    def __init__(self, user_id_service: UserIdService, *args, **kwargs) -> None:
        """Initialize the user id resource.

        All arguments are provided via dependency injection.

        Args:
            user_service: A UserIdService object.
        """
        self._user_id_service = user_id_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=UserSchema, api=api)
    def get(self, id: int) -> dict[str, Any]:
        """Gets the User with the provided ID."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="User", request_type="GET", id=id
        )
        user = cast(
            models.User, self._user_id_service.get(id, error_if_not_found=True, log=log)
        )
        return utils.build_user(user)


@api.route("/<int:id>/password")
@api.param("id", "ID for the User resource.")
class UserIdPasswordEndpoint(Resource):
    @inject
    def __init__(self, user_id_service: UserIdService, *args, **kwargs) -> None:
        """Initialize the user id password resource.

        All arguments are provided via dependency injection.

        Args:
            user_service: A UserIdService object.
        """
        self._user_id_service = user_id_service
        super().__init__(*args, **kwargs)

    @login_required
    @accepts(schema=UserPasswordSchema, api=api)
    @responds(schema=IdStatusResponseSchema, api=api)
    def post(self, id: int):
        """Updates the User's password with a given ID."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="User", request_type="POST", id=id
        )
        parsed_obj = request.parsed_obj  # type: ignore # noqa: F841
        return self._user_id_service.change_password(
            user_id=id,
            current_password=parsed_obj["old_password"],
            new_password=parsed_obj["new_password"],
            confirm_new_password=parsed_obj["confirm_new_password"],
            log=log,
        )


@api.route("/current")
class UserCurrentEndpoint(Resource):
    @inject
    def __init__(
        self, user_current_service: UserCurrentService, *args, **kwargs
    ) -> None:
        """Initialize the user current resource.

        All arguments are provided via dependency injection.

        Args:
            user_service: A UserCurrentService object.
        """
        self._user_current_service = user_current_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=UserCurrentSchema, api=api)
    def get(self):
        """Gets the Current User."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="User", request_type="GET"
        )
        user = self._user_current_service.get(log=log)
        return utils.build_current_user(user)

    @login_required
    @accepts(schema=UserDeleteSchema, api=api)
    @responds(schema=IdStatusResponseSchema, api=api)
    def delete(self) -> dict[str, Any]:
        """Deletes a Current User."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="User",
            request_type="DELETE",
        )
        parsed_obj = request.parsed_obj  # type: ignore
        return self._user_current_service.delete(parsed_obj["password"], log=log)

    @login_required
    @accepts(schema=UserMutableFieldsSchema, api=api)
    @responds(schema=UserCurrentSchema, api=api)
    def put(self) -> dict[str, Any]:
        """Modifies the Current User"""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="User",
            request_type="PUT",
        )
        parsed_obj = request.parsed_obj  # type: ignore
        user = self._user_current_service.modify(
            username=parsed_obj["username"],
            email_address=parsed_obj["email"],
            error_if_not_found=True,
            log=log,
        )
        return utils.build_current_user(user)


@api.route("/current/password")
class UserCurrentPasswordEndpoint(Resource):
    @inject
    def __init__(
        self, user_current_service: UserCurrentService, *args, **kwargs
    ) -> None:
        """Initialize the user current resource.

        All arguments are provided via dependency injection.

        Args:
            user_service: A UserCurrentService object.
        """
        self._user_current_service = user_current_service
        super().__init__(*args, **kwargs)

    @login_required
    @accepts(schema=UserPasswordSchema, api=api)
    @responds(schema=IdStatusResponseSchema, api=api)
    def post(self):
        """Updates the Current User's password."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="User",
            request_type="POST",
        )
        parsed_obj = request.parsed_obj  # noqa: F841
        return self._user_current_service.change_password(
            current_password=parsed_obj["old_password"],
            new_password=parsed_obj["new_password"],
            confirm_new_password=parsed_obj["confirm_new_password"],
            log=log,
        )
