"""The prototype Flask application.

This module contains the application factory function and the application's
configuration parameters.
"""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field

from flask import Flask, g, session
from flask_login import LoginManager, current_user, login_required
from flask_oidc import OpenIDConnect
from flask_restx import Api

from .models import User, db
from .services import SERVICES


def _validate_session_protection(value: str) -> None:
    """Validate the session protection level.

    Args:
        value: The session protection level to be validated. Must be one of "none",
            "basic", or "strong".

    Raises:
        ValueError: If the session protection level is not one of "none", "basic", or
            "strong".
    """
    allowed = {"none", "basic", "strong"}

    if value not in allowed:
        raise ValueError(
            f"Invalid SESSION_PROTECTION value: {value}. "
            f"Allowed values are {allowed}."
        )


@dataclass
class Config(object):
    """The application's configuration parameters.

    Attributes:
        SECRET_KEY: The secret key used to sign session cookies.
        SWAGGER_PATH: The path to the Swagger UI.
        BASE_URL: The base URL of the application.
    """

    SECRET_KEY: str = field(default_factory=lambda: os.getenv("SECRET_KEY", "dev"))
    SWAGGER_PATH: str = field(default_factory=lambda: os.getenv("SWAGGER_PATH", "/api"))
    BASE_URL: str | None = field(default_factory=lambda: os.getenv("BASE_URL"))
    REMEMBER_COOKIE_NAME: str = field(
        default_factory=lambda: os.getenv(
            "REMEMBER_COOKIE_NAME", "proto_remember_token"
        )
    )
    REMEMBER_COOKIE_DURATION: str | int = field(
        default_factory=lambda: os.getenv("REMEMBER_COOKIE_DURATION", f"{14 * 86400}")
    )
    REMEMBER_COOKIE_SECURE: bool = field(
        default_factory=lambda: os.getenv("REMEMBER_COOKIE_SECURE") is not None
    )
    SESSION_PROTECTION: str = field(
        default_factory=lambda: os.getenv("SESSION_PROTECTION", "strong").lower()
    )

    # Has info related to OIDC authentication
    OIDC_CLIENT_SECRETS = "oidc_client_secrets.json"

    # "openid" is required; additional values request additional claims.  E.g.
    # "profile" for user profile information.  Default is "openid email".
    # https://openid.net/specs/openid-connect-core-1_0.html#ScopeClaims
    OIDC_SCOPES = "openid profile"

    def __post_init__(self) -> None:
        self.REMEMBER_COOKIE_DURATION = int(self.REMEMBER_COOKIE_DURATION)
        _validate_session_protection(self.SESSION_PROTECTION)


login_manager = LoginManager()


def create_app(include_test_users: bool = True) -> Flask:
    """Create and configure an instance of the Flask application.

    Returns:
        The configured Flask application.
    """
    # create and configure the app
    app = Flask(__name__)
    app.config.from_object(Config())

    api: Api = Api(
        app,
        title="Prototype Flask Application",
        version="0.0.0",
        doc=app.config["SWAGGER_PATH"],
        prefix="/api",
        url_scheme=app.config["BASE_URL"],
    )

    _register_routes(api)

    # Add a rule for a simple demo webpage intended for browsers.  We can
    # exercise OIDC authentication through this endpoint.
    app.add_url_rule("/ui", view_func=welcome_page_protected, methods=["GET"])

    # Demo a webpage which does not require authentication.  Registering it
    # with the "/" path causes it to be the redirect destination after OIDC
    # user logout, so there is someplace to go.
    app.add_url_rule("/", view_func=welcome_page_unprotected, methods=["GET"])

    login_manager.user_loader(SERVICES.user.load_user)
    login_manager.init_app(app)
    login_manager.login_view = "login"

    oidc = OpenIDConnect()
    # Mount /login, /logout, /authorize endpoints under this prefix.
    oidc.init_app(app, prefix="/oidc")

    @app.before_request
    def set_g_oidc():
        """
        For easy access to flask-oidc from other modules, so they don't have to
        import this module and risk import cycles.
        """
        g.oidc = oidc

    if include_test_users:
        _register_test_users_in_db()

    return app


def _register_routes(api: Api) -> None:
    """Register the application's routes.

    Args:
        api: A flask-restx API instance.
        root: The root path of the API.

    Note:
        Registering flask-restx namespaces does the same thing as registering Flask
        blueprints.
    """
    from .controllers import auth_api, foo_api, hello_api, test_api, user_api, world_api

    api.add_namespace(auth_api, path="/auth")
    api.add_namespace(user_api, path="/user")
    api.add_namespace(hello_api, path="/hello")
    api.add_namespace(test_api, path="/test")
    api.add_namespace(world_api, path="/world")
    api.add_namespace(foo_api, path="/foo")


def _register_test_users_in_db() -> None:
    """Register test users in the simple key-value data store.

    This registers the following users and passwords into the "users table":

    - user:password
    - joe:hashed
    """
    db["users"]["1"] = User(
        id=1,
        alternative_id=uuid.uuid4().hex,
        name="user",
        password=SERVICES.password.hash("password"),
        deleted=False,
    )
    db["users"]["2"] = User(
        id=2,
        alternative_id=uuid.uuid4().hex,
        name="joe",
        password=SERVICES.password.hash("hashed"),
        deleted=False,
    )


@login_required
def welcome_page_protected():
    """
    Create a simple demo welcome web page for a logged in user.  For OIDC
    users, show some of the OIDC authentication info.
    """

    if g.oidc.user_loggedin:
        oidc_auth_token_json = json.dumps(session["oidc_auth_token"], indent=4)
        oidc_auth_profile = session.get("oidc_auth_profile")
        if oidc_auth_profile:
            oidc_auth_profile_json = json.dumps(oidc_auth_profile, indent=4)
        else:
            oidc_auth_profile_json = None

        oidc_info = f"""oidc_auth_token:
        <pre>
{oidc_auth_token_json}
        </pre>
"""

        if oidc_auth_profile_json:
            oidc_info += f"""
        oidc_auth_profile:
        <pre>
{oidc_auth_profile_json}
        </pre>
"""
    else:
        oidc_info = ""

    resp_html = f"""\
<!DOCTYPE html>
<html lang="en">
    <head>
        <title>Welcome to Dioptra!</title>
    </head>

    <body>
        <h2>Welcome to Dioptra, {current_user.name}!</h2>

        {oidc_info}

        <h2><a href="/api/auth/logout">Click to Logout</a></h2>
    </body>
</html>
"""

    return resp_html


def welcome_page_unprotected():
    """
    Create a simple web page which does not require login to access.  If you
    are logged in though, it will show your username.
    """

    if current_user.is_authenticated:
        login_info = "You are logged in as: " + current_user.name
        logout_link = '<h2><a href="/api/auth/logout">Click to Logout</a></h2>'
    else:
        login_info = "You are not logged in."
        logout_link = ""

    resp_html = f"""\
<!DOCTYPE html>
<html lang="en">
    <head>
        <title>Welcome to Dioptra!</title>
    </head>

    <body>
        <h2>Welcome to Dioptra!</h2>

        {login_info}
        {logout_link}
    </body>
</html>
"""

    return resp_html
