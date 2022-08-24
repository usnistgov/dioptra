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

import structlog
from flask import jsonify
from flask.wrappers import Response
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource
from injector import inject
from structlog.stdlib import BoundLogger

from dioptra.restapi.utils import as_api_parser

from .errors import UserDoesNotExistError, UserRegistrationError
from .model import User, UserRegistrationForm, UserRegistrationFormData
from .schema import UserRegistrationSchema, UserSchema
from .service import UserService

LOGGER: BoundLogger = structlog.stdlib.get_logger()

api: Namespace = Namespace(
    "User",
    description="User accounts",
)


@api.route("/")
class UserResource(Resource):
    """Shows a list of all users, and lets you POST to register new ones."""

    @inject
    def __init__(self, *args, user_service: UserService, **kwargs) -> None:
        self._user_service = user_service
        super().__init__(*args, **kwargs)

    @responds(schema=UserSchema(many=True), api=api)
    def get(self) -> list[User]:
        """Gets a list of all registered users."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="user", request_type="GET"
        )  # noqa: F841
        log.info("Request received")
        return self._user_service.get_all(log=log)

    @api.expect(as_api_parser(api, UserRegistrationSchema))
    @accepts(UserRegistrationSchema, api=api)
    @responds(schema=UserSchema, api=api)
    def post(self) -> User:
        """Creates a new user via an user registration form."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="user", request_type="POST"
        )  # noqa: F841
        user_registration_form: UserRegistrationForm = UserRegistrationForm()

        log.info("Request received")

        if not user_registration_form.validate_on_submit():
            log.info("Form validation failed")
            raise UserRegistrationError

        log.info("Form validation successful")
        user_registration_form_data: UserRegistrationFormData = (
            self._user_service.extract_data_from_form(
                user_registration_form=user_registration_form, log=log
            )
        )
        return self._user_service.create(
            user_registration_form_data=user_registration_form_data, log=log
        )


@api.route("/<int:userId>")
@api.param("userId", "An integer identifying a registered user account.")
class UserIdResource(Resource):
    """Shows a single user (id reference) and lets you delete it."""

    @inject
    def __init__(self, *args, user_service: UserService, **kwargs) -> None:
        self._user_service = user_service
        super().__init__(*args, **kwargs)

    @responds(schema=UserSchema, api=api)
    def get(self, userId: int) -> User:
        """Gets user account by its unique identifier."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="userId", request_type="GET"
        )  # noqa: F841
        log.info("Request received", user_id=userId)
        user: User | None = self._user_service.get_by_id(user_id=userId, log=log)

        if user is None:
            log.info("User not found", user_id=userId)
            raise UserDoesNotExistError

        return user

    def delete(self, userId: int) -> Response:
        """Deletes user account by its unique identifier."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="userId", request_type="DELETE"
        )  # noqa: F841
        log.info("Request received", user_id=userId)
        id: list[int] = self._user_service.delete(user_id=userId)

        return jsonify(dict(status="Success", id=id))  # type: ignore
