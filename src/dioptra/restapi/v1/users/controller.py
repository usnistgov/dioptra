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

import structlog
from flask import request
from flask_accepts import accepts, responds
from flask_login import current_user, login_required
from flask_restx import Namespace, Resource
from injector import inject
from structlog.stdlib import BoundLogger

from dioptra.restapi.v1.schemas import IdStatusResponseSchema
from dioptra.restapi.v1.utils import build_user, build_current_user

from .schema import (
    UserCurrentSchema,
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
        """Initialize the user password resource.

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
        parsed_query_params = request.parsed_args  # noqa: F841

        return self._user_service.get(
            search_string=parsed_query_params["query"],
            page_index=parsed_query_params["index"],
            page_length=parsed_query_params["pageLength"],
            log=log,
        )

    @accepts(schema=UserSchema, api=api)
    @responds(schema=UserCurrentSchema, api=api)
    def post(self):
        """Creates a User."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="User", request_type="POST"
        )
        parsed_obj = request.parsed_obj  # noqa: F841

        return self._user_service.create(
            username=parsed_obj["username"],
            email_address=parsed_obj["email"],
            password=parsed_obj["password"],
            confirm_password=parsed_obj["confirm_password"],
            log=log,
        )


@api.route("/<int:id>")
@api.param("id", "ID for the User resource.")
class UserIdEndpoint(Resource):
    @inject
    def __init__(self, user_id_service: UserIdService, *args, **kwargs) -> None:
        """Initialize the user password resource.

        All arguments are provided via dependency injection.

        Args:
            user_service: A UserIdService object.
        """
        self._user_id_service = user_id_service
        super().__init__(*args, **kwargs)

    # @login_required
    @responds(schema=UserSchema, api=api)
    def get(self, id: int):
        """Gets the User with the provided ID."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="User", request_type="GET", id=id
        )
        return self._user_service.get_by_id(id, log=log)


@api.route("/<int:id>/password")
@api.param("id", "ID for the User resource.")
class UserIdPasswordEndpoint(Resource):
    @inject
    def __init__(self, user_id_service: UserIdService, *args, **kwargs) -> None:
        """Initialize the user password resource.

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
        return self._user_id_service.change_password(log=log)


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
        return self._user_current_service.get(log=log)

    @login_required
    @responds(schema=IdStatusResponseSchema, api=api)
    def delete(self):
        """Deletes a Current User."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="User",
            request_type="DELETE",
        )
        return self._current_user_service.delete(current_user.id, log=log)

    @login_required
    @accepts(schema=UserMutableFieldsSchema, api=api)
    @responds(schema=UserCurrentSchema, api=api)
    def put(self):
        """Modifies the Current User"""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="User",
            request_type="PUT",
        )
        parsed_obj = request.parsed_obj  # noqa: F841
        self._user_current_service.modify(
            username=parsed_obj["username"],
            email=parsed_obj["email"],
            log=log,
        )


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
        self._user_current_service.modify()
        return self._user_current_service.change_password(
            current_password=parsed_obj["current_password"],
            new_password=parsed_obj["new_password"],
            confirm_new_password=parsed_obj["new_password"],
            log=log,
        )
