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
"""Test suite for user and authentication operations.

This module contains a set of tests that validate the CRUD operations and additional
functionalities for the user entity and auth endpoint. The tests ensure that users
can register, login, logout, change their password, access account information, and
delete their accounts. The tests also check that the "remember me" cookie functionality
works as expected.
"""
from __future__ import annotations

import platform
import time
from functools import singledispatch
from pathlib import Path
from typing import Any, Iterable, overload

import pytest
import requests
import structlog
from flask import Flask
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from injector import Injector
from requests import Response as RequestsResponse
from requests import Session as RequestsSession
from structlog.stdlib import BoundLogger
from werkzeug.test import TestResponse

from dioptra.restapi.db import db as restapi_db
from dioptra.restapi.routes import AUTH_ROUTE, USER_ROUTE, V0_ROOT

from .conftest import wait_for_healthcheck_success
from .lib.server import FlaskTestServer

LOGGER: BoundLogger = structlog.stdlib.get_logger()

FAKE_USERNAME = "new_user"
FAKE_EMAIL = "new_user@dioptra.com"
FAKE_PASSWORD = "new_password"
FAKE_PASSWORD_UPDATED = "updated_password"


# -- Fixtures --------------------------------------------------------------------------


@pytest.fixture
def flask_test_server_short_memory(
    tmp_path: Path, http_client: RequestsSession
) -> Iterable[None]:
    """Start a Flask test server with a short "remember me" cookie duration.

    Args:
        tmp_path: The path to the temporary directory.
        http_client: A Requests session client.
    """
    sqlite_path = tmp_path / "dioptra-test.db"
    server = FlaskTestServer(
        sqlite_path=sqlite_path, extra_env={"DIOPTRA_REMEMBER_COOKIE_DURATION": "1"}
    )
    server.upgrade_db()
    with server:
        wait_for_healthcheck_success(http_client)
        yield


@pytest.fixture
def second_http_client() -> Iterable[requests.Session]:
    """A Requests session for simulating access from a second device.

    Yields:
        A Requests session.
    """
    with requests.Session() as s:
        yield s


# -- Fixture Overrides -----------------------------------------------------------------
# The following fixtures are overrides of fixtures defined in conftest.py. These
# overrides are necessary because the tests in this module require login functionality
# to be enabled. These overrides can be removed once the other tests have been updated
# to respect the login functionality.


@pytest.fixture
def app(dependency_modules: list[Any]) -> Flask:
    from dioptra.restapi import create_app

    injector = Injector(dependency_modules)
    app = create_app(env="test", injector=injector)

    yield app


@pytest.fixture
def db(app: Flask) -> SQLAlchemy:
    with app.app_context():
        restapi_db.drop_all()
        restapi_db.create_all()
        yield restapi_db
        restapi_db.drop_all()
        restapi_db.session.commit()


@pytest.fixture(autouse=True)
def seed_database(db):
    from dioptra.restapi.db.legacy_models import job_statuses

    db.session.execute(
        job_statuses.insert(),
        [
            {"status": "queued"},
            {"status": "started"},
            {"status": "deferred"},
            {"status": "finished"},
            {"status": "failed"},
        ],
    )
    db.session.commit()


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()


# -- Actions ---------------------------------------------------------------------------


@singledispatch
def register_fake_user(client) -> dict[str, Any]:
    """Register a fake user account using the API.

    Args:
        client: The client to use to make the request. This can be either a Flask test
            client or a Requests session.

    Returns:
        A dict containing the user_id, username, and email_address of the newly
        registered user.
    """
    raise NotImplementedError


@register_fake_user.register
def _(client: FlaskClient) -> dict[str, Any]:
    response = client.post(
        f"/{V0_ROOT}/{USER_ROUTE}",
        json={
            "username": FAKE_USERNAME,
            "emailAddress": FAKE_EMAIL,
            "password": FAKE_PASSWORD,
            "confirmPassword": FAKE_PASSWORD,
        },
        follow_redirects=True,
    ).get_json()
    return {
        "user_id": response["userId"],
        "username": response["username"],
        "email_address": response["emailAddress"],
    }


@register_fake_user.register
def _(client: RequestsSession) -> dict[str, Any]:
    response_full = client.post(
        f"http://localhost:5000/{V0_ROOT}/{USER_ROUTE}",
        json={
            "username": FAKE_USERNAME,
            "emailAddress": FAKE_EMAIL,
            "password": FAKE_PASSWORD,
            "confirmPassword": FAKE_PASSWORD,
        },
        allow_redirects=True,
    )
    response = response_full.json()
    return {
        "user_id": response["userId"],
        "username": response["username"],
        "email_address": response["emailAddress"],
    }


@overload
def login(client: FlaskClient, username: str, password: str) -> TestResponse: ...


@overload
def login(
    client: RequestsSession, username: str, password: str
) -> RequestsResponse: ...


@singledispatch
def login(client, username, password):
    """Login to the API.

    Args:
        client: The client to use to make the request. This can be either a Flask test
            client or a Requests session.
        username: The username of the account.
        password: The password of the account.

    Returns:
        The response object from the request. If client is a Flask test client, this
        will be a Werkzeug test response. If client is a Requests session, this will
        be a Requests response.
    """
    raise NotImplementedError


@login.register
def _(client: FlaskClient, username: str, password: str) -> TestResponse:
    return client.post(
        f"/{V0_ROOT}/{AUTH_ROUTE}/login",
        json={"username": username, "password": password},
    )


@login.register
def _(client: RequestsSession, username: str, password: str) -> RequestsResponse:
    return client.post(
        f"http://localhost:5000/{V0_ROOT}/{AUTH_ROUTE}/login",
        json={"username": username, "password": password},
    )


@overload
def logout(client: FlaskClient, everywhere: bool) -> TestResponse: ...


@overload
def logout(client: RequestsSession, everywhere: bool) -> RequestsResponse: ...


@singledispatch
def logout(client, everywhere):
    """Logout of the API.

    Args:
        client: The client to use to make the request. This can be either a Flask test
            client or a Requests session.
        everywhere: If True, log out from all devices.

    Returns:
        The response object from the request. If client is a Flask test client, this
        will be a Werkzeug test response. If client is a Requests session, this will
        be a Requests response.
    """
    raise NotImplementedError


@logout.register
def _(client: FlaskClient, everywhere: bool) -> TestResponse:
    return client.post(
        f"/{V0_ROOT}/{AUTH_ROUTE}/logout", params={"everywhere": everywhere}
    )


@logout.register
def _(client: RequestsSession, everywhere: bool) -> RequestsResponse:
    return client.post(
        f"http://localhost:5000/{V0_ROOT}/{AUTH_ROUTE}/logout",
        params={"everywhere": everywhere},
    )


@overload
def change_password(
    client: FlaskClient, user_id: int, current_password: str, new_password: str
) -> TestResponse: ...


@overload
def change_password(
    client: RequestsSession, user_id: int, current_password: str, new_password: str
) -> RequestsResponse: ...


@singledispatch
def change_password(client, user_id: int, current_password, new_password):
    """Change the password of the specified user account using the API.

    Args:
        client: The client to use to make the request. This can be either a Flask test
            client or a Requests session.
        user_id: The ID of the user account.
        current_password: The current password of the account.
        new_password: The new password for the account.

    Returns:
        The response object from the request. If client is a Flask test client, this
        will be a Werkzeug test response. If client is a Requests session, this will
        be a Requests response.
    """
    raise NotImplementedError


@change_password.register
def _(
    client: FlaskClient, user_id: int, current_password: str, new_password: str
) -> TestResponse:
    return client.post(
        f"/{V0_ROOT}/{USER_ROUTE}/password",
        json={
            "userId": user_id,
            "currentPassword": current_password,
            "newPassword": new_password,
        },
        follow_redirects=True,
    )


@change_password.register
def _(
    client: RequestsSession, user_id: int, current_password: str, new_password: str
) -> RequestsResponse:
    return client.post(
        f"http://localhost:5000/{V0_ROOT}/{USER_ROUTE}/password",
        json={
            "userId": user_id,
            "currentPassword": current_password,
            "newPassword": new_password,
        },
        allow_redirects=True,
    )


@overload
def change_current_user_password(
    client: FlaskClient, current_password: str, new_password: str
) -> TestResponse: ...


@overload
def change_current_user_password(
    client: RequestsSession, current_password: str, new_password: str
) -> RequestsResponse: ...


@singledispatch
def change_current_user_password(client, current_password, new_password):
    """Change the password of the current user account using the API.

    Args:
        client: The client to use to make the request. This can be either a Flask test
            client or a Requests session.
        current_password: The current password of the account.
        new_password: The new password for the account.

    Returns:
        The response object from the request. If client is a Flask test client, this
        will be a Werkzeug test response. If client is a Requests session, this will
        be a Requests response.
    """
    raise NotImplementedError


@change_current_user_password.register
def _(client: FlaskClient, current_password: str, new_password: str) -> TestResponse:
    return client.post(
        f"/{V0_ROOT}/{USER_ROUTE}/current/password",
        json={
            "currentPassword": current_password,
            "newPassword": new_password,
        },
        follow_redirects=True,
    )


@change_current_user_password.register
def _(
    client: RequestsSession, current_password: str, new_password: str
) -> RequestsResponse:
    return client.post(
        f"http://localhost:5000/{V0_ROOT}/{USER_ROUTE}/current/password",
        json={
            "currentPassword": current_password,
            "newPassword": new_password,
        },
        allow_redirects=True,
    )


@overload
def delete_current_user(client: FlaskClient, password: str) -> TestResponse: ...


@overload
def delete_current_user(client: RequestsSession, password: str) -> RequestsResponse: ...


@singledispatch
def delete_current_user(client, password):
    """Delete the current user account using the API.

    Args:
        client: The client to use to make the request. This can be either a Flask test
            client or a Requests session.
        password: The password of the account.

    Returns:
        The response object from the request. If client is a Flask test client, this
        will be a Werkzeug test response. If client is a Requests session, this will
        be a Requests response.
    """
    raise NotImplementedError


@delete_current_user.register
def _(client: FlaskClient, password: str) -> TestResponse:
    return client.delete(
        f"/{V0_ROOT}/{USER_ROUTE}/current",
        json={"password": password},
        follow_redirects=True,
    )


@delete_current_user.register
def _(client: RequestsSession, password: str) -> RequestsResponse:
    return client.delete(
        f"http://localhost:5000/{V0_ROOT}/{USER_ROUTE}/current",
        json={"password": password},
        allow_redirects=True,
    )


# -- Assertions ------------------------------------------------------------------------


@singledispatch
def assert_current_user_context_inaccessible(client) -> None:
    """Assert that the current user context is inaccessible.

    Args:
        client: The client to use to make the request. This can be either a Flask test
            client or a Requests session.

    Raises:
        AssertionError: If the response status code is not 401, meaning that the
            current user context is accessible.
    """
    raise NotImplementedError


@assert_current_user_context_inaccessible.register
def _(client: FlaskClient) -> None:
    response = client.get(f"/{V0_ROOT}/{USER_ROUTE}/current", follow_redirects=True)
    assert response.status_code == 401


@assert_current_user_context_inaccessible.register
def _(client: RequestsSession) -> None:
    response = client.get(
        f"http://localhost:5000/{V0_ROOT}/{USER_ROUTE}/current", allow_redirects=True
    )
    assert response.status_code == 401


@singledispatch
def assert_current_user_context_accessible(client, expected: dict[str, Any]) -> None:
    """Assert that the current user context is accessible.

    Args:
        client: The client to use to make the request. This can be either a Flask test
            client or a Requests session.
        expected: A dict containing the expected user_id, username, and email_address
            of the current user.

    Raises:
        AssertionError: If the response status code is not 200, meaning that the
            current user context is inaccessible.
    """
    raise NotImplementedError


@assert_current_user_context_accessible.register
def _(client: FlaskClient, expected: dict[str, Any]) -> None:
    response = client.get(
        f"/{V0_ROOT}/{USER_ROUTE}/current", follow_redirects=True
    ).get_json()
    received = {
        "user_id": response["userId"],
        "username": response["username"],
        "email_address": response["emailAddress"],
    }
    assert received == expected


@assert_current_user_context_accessible.register
def _(client: RequestsSession, expected: dict[str, Any]) -> None:
    response = client.get(
        f"http://localhost:5000/{V0_ROOT}/{USER_ROUTE}/current", allow_redirects=True
    ).json()
    received = {
        "user_id": response["userId"],
        "username": response["username"],
        "email_address": response["emailAddress"],
    }
    assert received == expected


@singledispatch
def assert_user_info_accessible(client, user_id: int, expected: dict[str, Any]) -> None:
    """Assert that the info for a given user is accessible.

    Args:
        client: The client to use to make the request. This can be either a Flask test
            client or a Requests session.
        user_id: The ID of the user account.
        expected: A dict containing the expected user_id, username, and email_address
            of the user.

    Raises:
        AssertionError: If the response status code is not 200, meaning that the
            info for a given user is inaccessible.
    """
    raise NotImplementedError


@assert_user_info_accessible.register
def _(client: FlaskClient, user_id: int, expected: dict[str, Any]) -> None:
    response = client.get(
        f"/{V0_ROOT}/{USER_ROUTE}/{user_id}", follow_redirects=True
    ).get_json()
    received = {
        "user_id": response["userId"],
        "username": response["username"],
        "email_address": response["emailAddress"],
    }
    assert received == expected


@assert_user_info_accessible.register
def _(client: RequestsSession, user_id: int, expected: dict[str, Any]) -> None:
    response = client.get(
        f"http://localhost:5000/{V0_ROOT}/{USER_ROUTE}/{user_id}", allow_redirects=True
    ).json()
    received = {
        "user_id": response["userId"],
        "username": response["username"],
        "email_address": response["emailAddress"],
    }
    assert received == expected


@singledispatch
def assert_user_info_inaccessible(client, user_id: int) -> None:
    """Assert that the info for a given user is inaccessible.

    Args:
        client: The client to use to make the request. This can be either a Flask test
            client or a Requests session.
        user_id: The ID of the user account.

    Raises:
        AssertionError: If the response status code is not 401, meaning that the
            info for a given user is accessible.
    """
    raise NotImplementedError


@assert_user_info_inaccessible.register
def _(client: FlaskClient, user_id: int) -> None:
    response = client.get(f"/{V0_ROOT}/{USER_ROUTE}/{user_id}", follow_redirects=True)
    assert response.status_code == 401


@assert_user_info_inaccessible.register
def _(client: RequestsSession, user_id: int) -> None:
    response = client.get(
        f"http://localhost:5000/{V0_ROOT}/{USER_ROUTE}/{user_id}", allow_redirects=True
    )
    assert response.status_code == 401


# -- Tests -----------------------------------------------------------------------------


def test_user_registration(client: FlaskClient, db: SQLAlchemy) -> None:
    """Test account registration and that the user can access content after logging in.

    This test validates the following sequence of actions:

    - A user creates a new account.
    - The user is unable to retrieve account info via the /current endpoint before
      logging in.
    - The user logs in.
    - The user is able to retrieve account info via the /current endpoint after logging
      in.
    """
    register_response = register_fake_user(client)

    with client:
        assert_current_user_context_inaccessible(client)
        login(client, username=FAKE_USERNAME, password=FAKE_PASSWORD)
        assert_current_user_context_accessible(client, expected=register_response)


@pytest.mark.skipif(
    platform.system() == "Windows", reason="Test server subprocess hangs on Windows"
)
def test_logout(
    http_client: RequestsSession,
    second_http_client: RequestsSession,
    flask_test_server: None,
) -> None:
    """Test the user logout functionality for multiple concurrent sessions.

    This test validates the following sequence of actions:

    - A user creates a new account.
    - The user logs in using two different clients and is able to access account info
      using both clients.
    - The user logs out on client 1.
    - The user is unable to retrieve account info using client 1, but is able to
      retrieve account info using client 2.
    - The user logs in again using client 1.
    - The user issues a "logout everywhere" command using client 1.
    - The user is unable to retrieve account info using client 1 or client 2.

    Note:
        This test starts a Flask test server in a subprocess and uses requests Sessions
        to simulate logging in on multiple devices. The Flask test client is not capable
        of simulating multiple devices.
    """
    register_response = register_fake_user(http_client)

    # Login on client 1 and client 2
    login(http_client, username=FAKE_USERNAME, password=FAKE_PASSWORD)
    login(second_http_client, username=FAKE_USERNAME, password=FAKE_PASSWORD)
    assert_current_user_context_accessible(http_client, expected=register_response)
    assert_current_user_context_accessible(
        second_http_client, expected=register_response
    )

    # Logout on client 1
    logout(http_client, everywhere=False)
    assert_current_user_context_inaccessible(http_client)
    assert_current_user_context_accessible(
        second_http_client, expected=register_response
    )

    # Login again on client 1
    login(http_client, username=FAKE_USERNAME, password=FAKE_PASSWORD)
    assert_current_user_context_accessible(http_client, expected=register_response)
    assert_current_user_context_accessible(
        second_http_client, expected=register_response
    )

    # Issue a "logout everywhere" command on client 1
    logout(http_client, everywhere=True)
    assert_current_user_context_inaccessible(http_client)
    assert_current_user_context_inaccessible(second_http_client)


def test_delete_current_user(client: FlaskClient, db: SQLAlchemy) -> None:
    """Test that a logged in user can delete their account.

    This test validates the following sequence of actions:

    - A user creates a new account.
    - The user logs in and is able to access account info.
    - The user deletes their account.
    - The user is unable to access account info.
    """
    register_response = register_fake_user(client)
    user_id = register_response["user_id"]

    with client:
        login(client, username=FAKE_USERNAME, password=FAKE_PASSWORD)
        assert_user_info_accessible(client, user_id=user_id, expected=register_response)
        delete_current_user(client, password=FAKE_PASSWORD)
        assert_user_info_inaccessible(client, user_id=user_id)


def test_change_password(client: FlaskClient, db: SQLAlchemy) -> None:
    """Test that a user can change their password without logging in.

    This test validates the following sequence of actions:

    - A user creates a new account.
    - The user changes their account password without logging in.
    - The user logs in using the new password.
    - The user is able to access account info.
    """
    register_response = register_fake_user(client)
    user_id = register_response["user_id"]

    with client:
        change_password(
            client,
            user_id=user_id,
            current_password=FAKE_PASSWORD,
            new_password=FAKE_PASSWORD_UPDATED,
        )
        assert_user_info_inaccessible(client, user_id=user_id)
        login(client, username=FAKE_USERNAME, password=FAKE_PASSWORD_UPDATED)
        assert_user_info_accessible(client, user_id=user_id, expected=register_response)


@pytest.mark.skipif(
    platform.system() == "Windows", reason="Test server subprocess hangs on Windows"
)
def test_change_current_user_password(
    http_client: RequestsSession, flask_test_server: None
) -> None:
    """Test that a logged in user can change their password.

    This test validates the following sequence of actions:

    - A user creates a new account.
    - The user logs in using the original password.
    - The user changes their account password.
    - The password change automatically expires the user's session and the user is
      unable to access account info.
    - The user logs back in using the new password.
    - The user is able to access account info.

    Note:
        This test starts a Flask test server in a subprocess and uses a requests Session
        to communicate with the server. There is an unanticipated interaction between
        the Flask test client, the Flask-Login user load callback, and possibly
        something else in the Dioptra REST API that causes the session expiration after
        changing the password to not work. This behavior is limited to the test client
        and does not occur when using a Flask server.
    """
    register_response = register_fake_user(http_client)
    login(http_client, username=FAKE_USERNAME, password=FAKE_PASSWORD)
    change_current_user_password(
        http_client, current_password=FAKE_PASSWORD, new_password=FAKE_PASSWORD_UPDATED
    )
    assert_current_user_context_inaccessible(http_client)
    login(http_client, username=FAKE_USERNAME, password=FAKE_PASSWORD_UPDATED)
    assert_current_user_context_accessible(http_client, expected=register_response)


@pytest.mark.skipif(
    platform.system() == "Windows", reason="Test server subprocess hangs on Windows"
)
def test_access_restored_with_remember_me_cookie(
    http_client: RequestsSession, flask_test_server: None
) -> None:
    """Test that the "remember me" cookie functionality works as expected.

    This test validates the following sequence of actions:

    - A user creates a new account.
    - The user logs in.
    - The user clears the session cookies from the client (equivalent to closing the web
      browser).
    - The user is still able to access account info using the client (equivalent to
      reopening the web browser and revisiting the site)

    Note:
        This test starts a Flask test server in a subprocess and uses a requests Session
        to communicate with the server. The duration of the "remember me" cookie is
        configurable on the Flask test server.
    """
    register_response = register_fake_user(http_client)
    login(http_client, username=FAKE_USERNAME, password=FAKE_PASSWORD)
    http_client.cookies.clear_session_cookies()
    assert_current_user_context_accessible(http_client, expected=register_response)


@pytest.mark.skipif(
    platform.system() == "Windows", reason="Test server subprocess hangs on Windows"
)
def test_access_fails_after_remember_me_cookie_expires(
    http_client: RequestsSession, flask_test_server_short_memory: None
) -> None:
    """Test that the "remember me" cookie expiration functionality works as expected.

    This test validates the following sequence of actions:

    - A user creates a new account.
    - The user logs in.
    - The user clears the session cookies from the client (equivalent to closing the web
      browser).
    - The user waits for the "remember me" cookie to expire.
    - The user is unable to access account info using the client and needs to login
      again.

    Note:
        This test starts a Flask test server in a subprocess and uses a requests Session
        to communicate with the server. The duration of the "remember me" cookie is
        configurable on the Flask test server.
    """
    register_fake_user(http_client)
    login(http_client, username=FAKE_USERNAME, password=FAKE_PASSWORD)
    http_client.cookies.clear_session_cookies()
    time.sleep(2)
    assert_current_user_context_inaccessible(http_client)
