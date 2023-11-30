"""The application's REST controllers for the API."""
from __future__ import annotations

from typing import Any, Optional, Union, cast
from urllib.parse import quote_plus

from flask import Response, g, redirect, request, session, url_for
from flask_accepts import accepts
from flask_login import current_user, login_required, login_user
from flask_restx import Namespace, Resource

from .schemas import (
    ChangePasswordSchema,
    DeleteUserSchema,
    LoginReactiveSchema,
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


# -- Authentication Resources ---------------------------------------------------------


@auth_api.route("/login", endpoint="login")
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

    @accepts(query_params_schema=LoginReactiveSchema, api=auth_api)
    def get(self):
        """
        Act as a flask-login view function.  This will forward to an OIDC
        Provider for authentication, and ensure that if OIDC authentication is
        successful, flask-login also sees an authenticated user.
        """

        next_ = request.parsed_query_params.get("next")

        if current_user.is_authenticated:
            # User already logged in!
            # Need to validate the redirect URL here?
            resp = redirect(next_ or request.root_url)

        elif g.oidc.user_loggedin:
            # This request is a redirect back from the OIDC authorize
            # endpoint, after successful authentication.  So we logged in
            # via flask-oidc, but don't have an authenticated current_user yet.
            user = SERVICES.user.create_user_from_id_token(session["oidc_auth_token"])

            login_user(user)

            original_next = session.pop(
                "_dioptra_reactive_login_next", request.root_url
            )

            resp = redirect(original_next)

        else:
            # This request is reactive after the user-agent attempted to
            # access a protected endpoint without having authenticated.
            # Forward to the OIDC authentication endpoint.
            if next_:
                # The original "next" URL: set in the session so we don't lose
                # it.
                session["_dioptra_reactive_login_next"] = next_

            redirect_uri = "{login}?next={here}".format(
                login=url_for("oidc_auth.login"),
                here=quote_plus(request.url),
            )
            resp = redirect(redirect_uri)

        return resp


@auth_api.route("/logout")
class LogoutResource(Resource):
    @accepts(query_params_schema=LogoutSchema, api=auth_api)
    def get(self) -> Optional[Union[dict[str, Any], Response]]:
        """Logout the current user.  No-op if not logged in."""
        parsed_query_params = cast(
            dict[str, Any], request.parsed_query_params  # type: ignore[attr-defined]
        )
        everywhere = bool(parsed_query_params["everywhere"])
        resp = SERVICES.auth.logout(everywhere=everywhere)

        # If there is no authenticated user, what is the right thing to return?
        return resp


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
