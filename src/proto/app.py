"""The prototype Flask application.

This module contains the application factory function and the application's
configuration parameters.
"""
from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field

from flask import Flask
from flask_login import LoginManager
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
        url_scheme=app.config["BASE_URL"],
    )

    _register_routes(api)

    login_manager.user_loader(SERVICES.user.load_user)
    login_manager.init_app(app)

    if include_test_users:
        _register_test_users_in_db()

    return app


def _register_routes(api: Api, root: str = "api") -> None:
    """Register the application's routes.

    Args:
        api: A flask-restx API instance.
        root: The root path of the API.

    Note:
        Registering flask-restx namespaces does the same thing as registering Flask
        blueprints.
    """
    from .controllers import auth_api, foo_api, hello_api, test_api, user_api, world_api

    api.add_namespace(auth_api, path=f"/{root}/auth")
    api.add_namespace(user_api, path=f"/{root}/user")
    api.add_namespace(hello_api, path=f"/{root}/hello")
    api.add_namespace(test_api, path=f"/{root}/test")
    api.add_namespace(world_api, path=f"/{root}/world")
    api.add_namespace(foo_api, path=f"/{root}/foo")


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
