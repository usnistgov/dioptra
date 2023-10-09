"""The prototype Flask application.

This module contains the application factory function and the application's
configuration parameters.
"""
from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from functools import wraps
from importlib.resources import files
from typing import Any, Callable, TypeVar, cast

from flask import Flask
from flask_login import LoginManager
from flask_restx import Api
from oso import Oso

from .models import (
    Group,
    GroupMembership,
    PrototypeResource,
    SharedPrototypeResource,
    User,
    db,
)
from .services import SERVICES

Function = Callable[..., Any]
T = TypeVar("T", bound=Function)


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


login_manager = LoginManager()
oso = Oso()

oso.register_class(User)  # type: ignore[no-untyped-call]
oso.register_class(Group)  # type: ignore[no-untyped-call]
oso.register_class(PrototypeResource)  # type: ignore[no-untyped-call]
oso.register_class(SharedPrototypeResource)  # type: ignore[no-untyped-call]
oso.load_files([str(files("proto").joinpath("authorization.polar"))])


def create_app(include_test_data: bool = True) -> Flask:
    """Create and configure an instance of the Flask application.

    Args:
        include_test_data: Whether or not to populate database with test data. Defaults
            to True.

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

    _init_oso(app)
    _register_routes(api)

    login_manager.user_loader(SERVICES.user.load_user)
    login_manager.init_app(app)

    if include_test_data:
        _init_test_db()

    return app


def run_once(func: T) -> T:
    """Create a decorator that ensures a function runs only once per Python session.

    This decorator is intended for registration-like actions that should only be
    executed once, but could be potentially be called multiple times during a Python
    session. The most common situation where this could happen is while running unit
    tests.

    Args:
        func: The function that should only run once.

    Returns:
        The decorated function that will run only once.
    """
    function_called_previously = False

    @wraps(func)
    def wrapper(*args, **kwargs):
        nonlocal function_called_previously

        if function_called_previously:
            return None

        func_output = func(*args, **kwargs)
        function_called_previously = True
        return func_output

    return cast(T, wrapper)


# @run_once
def _init_oso(app: Flask) -> None:
   
    #setattr(app, "oso", oso)
    app.oso = oso  # type: ignore[attr-defined]


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


def _init_test_db() -> None:
    _register_test_users_in_db()
    _register_test_groups_in_db()
    _register_group_memberships_in_db()
    _register_test_resources_in_db()
    _register_test_shared_resources_in_db()


def _register_test_users_in_db() -> None:
    """Register test users in the simple key-value data store.

    This registers the following users and passwords into the "users" table:

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


def _register_test_groups_in_db() -> None:
    """Register test groups in the simple key-value data store.

    This registers the following groups into the "groups" table:

    - user's Group
        - Creator: user
        - Owner: user
    - joe's Group
        - Creator: joe
        - Owner: joe
    """
    db["groups"]["1"] = Group(
        id=1,
        name="user's Group",
        creator_id=1,
        owner_id=1,
        deleted=False,
    )
    db["groups"]["2"] = Group(
        id=2,
        name="joe's Group",
        creator_id=2,
        owner_id=2,
        deleted=False,
    )


def _register_group_memberships_in_db() -> None:
    """Register test group memberships in the simple key-value data store.

    This adds the following users to the following groups with the following
    permissions:

    - user's Group
        - user: read, write, share_read, share_write
    - joe's Group
        - user: read, share_read
        - joe: read, write, share_read, share_write
    """
    db["group_memberships"]["1"] = GroupMembership(
        user_id=1,
        group_id=1,
        read=True,
        write=True,
        share_read=True,
        share_write=True,
    )
    db["group_memberships"]["2"] = GroupMembership(
        user_id=2,
        group_id=2,
        read=True,
        write=True,
        share_read=True,
        share_write=True,
    )
    db["group_memberships"]["3"] = GroupMembership(
        user_id=1,
        group_id=2,
        read=True,
        write=False,
        share_read=True,
        share_write=False,
    )


def _register_test_resources_in_db() -> None:
    """Register test resources in the simple key-value data store.

    This creates two resources:

    - Resource 1
        - Creator: user
        - Owner: user's Group
    - Resource 2
        - Creator: joe
        - Owner: joe's Group
    """
    db["resources"]["1"] = PrototypeResource(
        id=1,
        creator_id=1,
        owner_id=1,
        deleted=False,
    )
    db["resources"]["2"] = PrototypeResource(
        id=2,
        creator_id=2,
        owner_id=2,
        deleted=False,
    )


def _register_test_shared_resources_in_db() -> None:
    """Register a shared resource in the simple key-value data store.

    The information for the shared resource is as follows:

    - Resource 2
        - Owner: joe's Group
        - Shared with: user's Group
        - Shared created by: user
        - Permissions: read
    """
    db["shared_resources"]["1"] = SharedPrototypeResource(
        id=1,
        creator_id=1,
        resource_id=2,
        group_id=1,
        deleted=False,
        readable=True,
        writable=False,
    )
