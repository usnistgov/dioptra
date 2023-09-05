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

from .models import Group, Dioptra_Resource, User, Role, db
from .services import SERVICES


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


def create_app() -> Flask:
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

    _register_test_users_in_db()
    _register_test_groups_in_db()
    _register_test_resources_in_db()
    _give_users_roles_on_groups()

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
    - notallowed:password
    - tester:testing
    """
    db["users"]["1"] = User(
        id=1,
        alternative_id=uuid.uuid4().hex,
        name="user",
        password=SERVICES.password.hash("password"),
        deleted=False,
        roles=[],
    )
    db["users"]["2"] = User(
        id=2,
        alternative_id=uuid.uuid4().hex,
        name="joe",
        password=SERVICES.password.hash("hashed"),
        deleted=False,
        roles=[],
    )
    db["users"]["3"] = User(
        id=3,
        alternative_id=uuid.uuid4().hex,
        name="not_allowed",
        password=SERVICES.password.hash("password"),
        deleted=False,
        roles=[],
    )

    db["users"]["4"] = User(
        id=4,
        alternative_id=uuid.uuid4().hex,
        name="tester",
        password=SERVICES.password.hash("testing"),
        deleted=False,
        roles=[],
    )


def _register_test_groups_in_db() -> None:
    """Register test groups in the simple key-value data store.

    This registers the following groups into the "groups table":

    - testers
    - devs
    - attackers
    - my_group (unused currently)

    """
    db["groups"]["testers"] = Group(
        id=1,
        alternative_id=uuid.uuid4().hex,
        name="testers",
        # owner=db["users"]["1"],
        deleted=False,
        is_public=False,
    )
    db["groups"]["devs"] = Group(
        id=2,
        alternative_id=uuid.uuid4().hex,
        name="devs",
        # owner=db["users"]["2"],
        deleted=False,
        is_public=False,
    )

    db["groups"]["attackers"] = Group(
        id=3,
        alternative_id=uuid.uuid4().hex,
        name="attackers",
        # owner=db["users"]["2"],
        deleted=False,
        is_public=False,
    )

    db["groups"]["my_group"] = Group(
        id=4,
        alternative_id=uuid.uuid4().hex,
        name="my_group",
        # owner=db["users"]["2"],
        deleted=False,
        is_public=False,
    )


def _register_test_resources_in_db() -> None:
    """Register test resources in the simple key-value data store.

    This registers the following resources into the "resources table":

    - foo
    - test
    - hello
    - world

    """
    db["resources"]["foo"] = Dioptra_Resource(
        id=1,
        alternative_id=uuid.uuid4().hex,
        name="foo",
        owner=db["groups"]["devs"],
        is_public=False,
        shared_with=[],
        deleted=False,
    )
    db["resources"]["test"] = Dioptra_Resource(
        id=2,
        alternative_id=uuid.uuid4().hex,
        name="test",
        owner=db["groups"]["testers"],
        is_public=False,
        shared_with=[],  # what if we share with the owning group?
        deleted=False,
    )

    db["resources"]["hello"] = Dioptra_Resource(
        id=3,
        alternative_id=uuid.uuid4().hex,
        name="hello",
        owner=db["groups"]["testers"],
        is_public=True,
        shared_with=[],
        deleted=False,
    )

    db["resources"]["world"] = Dioptra_Resource(
        id=5,
        alternative_id=uuid.uuid4().hex,
        name="world",
        owner=db["groups"]["attackers"],
        is_public=False,
        shared_with=[],
        deleted=False,
    )


def _give_users_roles_on_groups() -> None:
    """This creates the following roles and assigns them to users in the simple
    key-value data store.

    - user 1 given admin for group attackers
    - user 2 given reader for group devs
    - user 4 given reader for group attackers
    - user 4 given writer for group attackers
    """

    db["users"]["1"].add_role(Role(name="admin", resource=db["groups"]["attackers"]))
    db["users"]["2"].add_role(Role(name="reader", resource=db["groups"]["devs"]))
    # User 3 has no roles and should be able to access nothing.
    db["users"]["4"].add_role(Role(name="writer", resource=db["groups"]["attackers"]))
    db["users"]["4"].add_role(Role(name="reader", resource=db["groups"]["attackers"]))
