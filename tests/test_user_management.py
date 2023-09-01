from __future__ import annotations

import copy
import uuid
from typing import Iterable

import pytest
from flask import Flask
from flask.testing import FlaskClient

from proto import create_app
from proto.models import User, db
from proto.services import SERVICES


class TestUserRegistration(object):
    @pytest.fixture(scope="class")
    def app(self) -> Iterable[Flask]:
        app: Flask = create_app(include_test_users=False)
        yield app

    @pytest.fixture(scope="class")
    def client(self, app: Flask) -> FlaskClient:
        return app.test_client()

    @pytest.fixture(scope="class")
    def login(self, client: FlaskClient) -> Iterable[None]:
        with client:
            _ = client.post(
                "/api/auth/login",
                json={"username": "new_user", "password": "new_password"},
            )
            yield

    def test_db_users_is_empty(self) -> None:
        assert not db["users"]

    def test_protected_endpoint(self, client: FlaskClient) -> None:
        response = client.get("/api/world", follow_redirects=True)
        assert response.status_code == 401

    def test_register_new_user(self, client: FlaskClient):
        response = client.post(
            "/api/user",
            json={
                "name": "new_user",
                "password": "new_password",
                "confirmPassword": "new_password",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200

    def test_new_user_in_db(self) -> None:
        assert db["users"]["1"].name == "new_user"

    def test_protected_endpoint_after_login(self, client: FlaskClient, login) -> None:
        response = client.get("/api/world", follow_redirects=True)
        assert response.status_code == 200

    def test_new_user_logout(self, client: FlaskClient, login) -> None:
        response = client.post("/api/auth/logout")
        assert response.status_code == 200

    def test_protected_endpoint_after_logout(self, client: FlaskClient, login) -> None:
        response = client.get("/api/world", follow_redirects=True)
        assert response.status_code == 401


class TestChangePassword(object):
    @pytest.fixture(scope="class")
    def app(self) -> Iterable[Flask]:
        app: Flask = create_app(include_test_users=False)
        yield app

    @pytest.fixture(scope="class")
    def client(self, app: Flask) -> FlaskClient:
        return app.test_client()

    @pytest.fixture(scope="class")
    def user(self) -> Iterable[User]:
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

    @pytest.fixture(scope="class")
    def login(self, client: FlaskClient, user: User) -> Iterable[None]:
        with client:
            _ = client.post(
                "/api/auth/login",
                json={"username": "test_user", "password": "test_password"},
            )
            yield

    def test_change_password(self, client: FlaskClient, login: None) -> None:
        change_password_response = client.post(
            "/api/user/password",
            json={
                "currentPassword": "test_password",
                "newPassword": "updated_password",
            },
            follow_redirects=True,
        )
        assert change_password_response.status_code == 200

    def test_protected_endpoint_after_password_change(
        self, client: FlaskClient, login: None
    ) -> None:
        response = client.get("/api/world", follow_redirects=True)
        assert response.status_code == 401

    def test_login_with_new_password(self, client: FlaskClient, login: None) -> None:
        login_response = client.post(
            "/api/auth/login",
            json={"username": "test_user", "password": "updated_password"},
        )
        assert login_response.status_code == 200

    def test_protected_endpoint_after_relogin(
        self, client: FlaskClient, login: None
    ) -> None:
        response = client.get("/api/world", follow_redirects=True)
        assert response.status_code == 200
