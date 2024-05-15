"""The application's REST controllers for the API."""

from __future__ import annotations

from typing import Any, cast

from flask import current_app, request
from flask_accepts import accepts
from flask_login import login_required
from flask_restx import Namespace, Resource

from .schemas import (
    ChangePasswordSchema,
    DeleteUserSchema,
    LoginSchema,
    LogoutSchema,
    RegisterUserSchema,
)
from .services import SERVICES

# -- Endpoint Namespaces --------------------------------------------------------------

auth_api: Namespace = Namespace(
    "Authentication",
    description="Authentication endpoint",
)
user_api: Namespace = Namespace(
    "User",
    description="User endpoint",
)
hello_api: Namespace = Namespace(
    "Hello",
    description="Hello endpoint",
)
test_api: Namespace = Namespace(
    "Test",
    description="Test endpoint",
)
world_api: Namespace = Namespace(
    "World",
    description="World endpoint",
)
foo_api: Namespace = Namespace(
    "Foo",
    description="Foo endpoint",
)
logging_api: Namespace = Namespace(
    "Logging", description="Destination for logging information"
)

# -- Authentication Resources ---------------------------------------------------------


@auth_api.route("/login")
class LoginResource(Resource):
    @accepts(schema=LoginSchema, api=auth_api)
    def post(self) -> dict[str, Any] | tuple[dict[str, Any], int]:
        """Login to a registered user account."""
        parsed_obj = cast(
            dict[str, Any], request.parsed_obj  # type: ignore[attr-defined]
        )
        username = str(parsed_obj["username"])
        password = str(parsed_obj["password"])
        return SERVICES.auth.login(username=username, password=password)


@auth_api.route("/logout")
class LogoutResource(Resource):
    @login_required
    @accepts(query_params_schema=LogoutSchema, api=auth_api)
    def post(self) -> dict[str, Any]:
        """Logout the current user.

        Must be logged in.
        """
        parsed_query_params = cast(
            dict[str, Any], request.parsed_query_params  # type: ignore[attr-defined]
        )
        everywhere = bool(parsed_query_params["everywhere"])
        return SERVICES.auth.logout(everywhere=everywhere)


# -- User Resource -------------------------------------------------------------------


@user_api.route("/")
class UserResource(Resource):
    @accepts(schema=RegisterUserSchema, api=user_api)
    def post(self) -> dict[str, Any] | tuple[dict[str, Any], int]:
        """Register a new user in the application."""
        parsed_obj = cast(
            dict[str, Any], request.parsed_obj  # type: ignore[attr-defined]
        )
        name = str(parsed_obj["name"])
        password = str(parsed_obj["password"])
        confirm_password = str(parsed_obj["confirm_password"])
        return SERVICES.user.register_new_user(
            name=name, password=password, confirm_password=confirm_password
        )

    @login_required
    @accepts(schema=DeleteUserSchema, api=user_api)
    def delete(self) -> dict[str, Any] | tuple[dict[str, Any], int]:
        """Permanently delete the current user.

        Must be logged in.
        """
        parsed_obj = cast(
            dict[str, Any], request.parsed_obj  # type: ignore[attr-defined]
        )
        password = str(parsed_obj["password"])
        return SERVICES.user.delete_current_user(password=password)


@user_api.route("/password")
class UserPasswordResource(Resource):
    @login_required
    @accepts(schema=ChangePasswordSchema, api=user_api)
    def post(self) -> dict[str, Any] | tuple[dict[str, Any], int]:
        """Change the current user's password.

        Must be logged in.
        """
        parsed_obj = cast(
            dict[str, Any], request.parsed_obj  # type: ignore[attr-defined]
        )
        current_password = str(parsed_obj["current_password"])
        new_password = str(parsed_obj["new_password"])
        return SERVICES.user.change_password(
            current_password=current_password, new_password=new_password
        )


# -- Hello Resource -------------------------------------------------------------------


@hello_api.route("/")
class HelloResource(Resource):
    def get(self) -> str:
        """Responds "Hello, World!"."""
        return SERVICES.hello.say_hello_world()

    def post(self) -> str:
        """Responds "Hello, World!"."""
        return SERVICES.hello.say_hello_world()

    def put(self) -> str:
        """Responds "Hello, World!"."""
        return SERVICES.hello.say_hello_world()


# -- Test Resource --------------------------------------------------------------------


@test_api.route("/")
class TestResource(Resource):
    @login_required
    def get(self) -> str:
        """Responds with the server's secret key.

        Must be logged in.
        """
        return SERVICES.test.reveal_secret_key()

    @login_required
    def post(self) -> str:
        """Responds with the server's secret key.

        Must be logged in.
        """
        return SERVICES.test.reveal_secret_key()

    @login_required
    def put(self) -> str:
        """Responds with the server's secret key.

        Must be logged in.
        """
        return SERVICES.test.reveal_secret_key()


# -- World Resource -------------------------------------------------------------------


@world_api.route("/")
class WorldResource(Resource):
    @login_required
    def get(self) -> dict[str, Any]:
        """Responds with the user's information.

        Must be logged in.
        """
        return SERVICES.world.show_user_info()

    @login_required
    def post(self) -> dict[str, Any]:
        """Responds with the user's information.

        Must be logged in.
        """
        return SERVICES.world.show_user_info()

    @login_required
    def put(self) -> dict[str, Any]:
        """Responds with the user's information.

        Must be logged in.
        """
        return SERVICES.world.show_user_info()


# -- Foo Resource ---------------------------------------------------------------------


@foo_api.route("/")
class FooResource(Resource):
    @login_required
    def get(self) -> str:
        """Responds with "bar".

        Must be logged in.
        """
        return SERVICES.foo.say_bar()

    @login_required
    def post(self):
        """Echoes the JSON payload in the request.

        Must be logged in.
        """
        return SERVICES.foo.echo_request(request)

    @login_required
    def put(self) -> str:
        """Responds with "bar".

        Must be logged in.
        """
        return SERVICES.foo.say_bar()


@logging_api.route("/")
class LoggingResource(Resource):
    @login_required
    def post(self):
        current_app.logger.info(str(request.form))
