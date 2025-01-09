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
"""The module defining the auth endpoints."""
from __future__ import annotations

import uuid
from typing import Any

import structlog
from flask import request
from flask_accepts import accepts, responds
from flask_login import login_required
from flask_restx import Namespace, Resource
from injector import inject
from structlog.stdlib import BoundLogger

from .schema import LoginSchema, LogoutQueryParametersSchema, LogoutSchema
from .service import AuthService

LOGGER: BoundLogger = structlog.stdlib.get_logger()

api: Namespace = Namespace("Authentication", description="Authentication endpoint")


@api.route("/login")
class LoginResource(Resource):
    """Methods for the /auth/login endpoint."""

    @inject
    def __init__(self, auth_service: AuthService, *args, **kwargs) -> None:
        """Initialize the login resource.

        All arguments are provided via dependency injection.

        Args:
            auth_service: An AuthService object.
        """
        self._auth_service = auth_service
        super().__init__(*args, **kwargs)

    @accepts(schema=LoginSchema, api=api)
    @responds(schema=LoginSchema, api=api)
    def post(self) -> dict[str, Any]:
        """Login to a registered user account."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="auth/login", request_type="POST"
        )
        parsed_obj = request.parsed_obj  # type: ignore
        return self._auth_service.login(
            username=parsed_obj["username"], password=parsed_obj["password"], log=log
        )


@api.route("/logout")
class LogoutResource(Resource):
    """Methods for the /auth/logout endpoint."""

    @inject
    def __init__(self, auth_service: AuthService, *args, **kwargs) -> None:
        """Initialize the login resource.

        All arguments are provided via dependency injection.

        Args:
            auth_service: An AuthService object.
        """
        self._auth_service = auth_service
        super().__init__(*args, **kwargs)

    @login_required
    @accepts(query_params_schema=LogoutQueryParametersSchema, api=api)
    @responds(schema=LogoutSchema, api=api)
    def post(self) -> dict[str, Any]:
        """Logout the current user.

        Must be logged in.
        """
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="auth/logout", request_type="POST"
        )
        parsed_query_params = request.parsed_query_params  # type: ignore
        return self._auth_service.logout(
            everywhere=parsed_query_params["everywhere"], log=log
        )
