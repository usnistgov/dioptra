from __future__ import annotations

import copy
import uuid
from typing import Iterable

import pytest
from flask import Flask
from flask.testing import FlaskClient, FlaskCliRunner

from proto import create_app
from proto.models import User, db
from proto.services import SERVICES


@pytest.fixture()
def app() -> Iterable[Flask]:
    app: Flask = create_app(include_test_users=False)

    yield app


@pytest.fixture()
def client(app: Flask) -> FlaskClient:
    return app.test_client()


@pytest.fixture()
def runner(app: Flask) -> FlaskCliRunner:
    return app.test_cli_runner()


@pytest.fixture()
def user() -> Iterable[User]:
    """Add a test user.

    This registers the following user and password into the "users table":

    - test_user:test_password

    The users table is reset on teardown.
    """
    _user = User(
        id=1,
        alternative_id=uuid.uuid4().hex,
        name="test_user",
        password=SERVICES.password.hash("test_password"),
        deleted=False,
    )
    db["users"]["1"] = _user
    yield copy.copy(_user)
    db["users"] = {}


@pytest.fixture()
def login(client: FlaskClient, user: User) -> Iterable[None]:
    with client:
        _ = client.post(
            "/api/auth/login",
            json={"username": "test_user", "password": "test_password"},
        )
        yield
