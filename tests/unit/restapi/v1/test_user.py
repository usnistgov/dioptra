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
"""Test suite for user operations.
This module contains a set of tests that validate the CRUD operations and additional
functionalities for the user entity. The tests ensure that the users can be
registered, modified, and deleted as expected through the REST API.
"""
from __future__ import annotations

from typing import Any

import pytest
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from werkzeug.test import TestResponse

from dioptra.restapi.routes import V1_ROOT, V1_USERS_ROUTE

from ..lib import actions, helpers

# -- Actions ---------------------------------------------------------------------------


def modify_current_user(
    client: FlaskClient,
    new_username: str,
    new_email: str,
) -> TestResponse:
    """Change the current user's email using the API.

    Args:
        client The Flask test client.
        new_email: The new email to assign to the user.

    Returns:
        The response from the API.
    """

    payload = {"username": new_username, "email": new_email}

    return client.put(
        f"/{V1_ROOT}/{V1_USERS_ROUTE}/current", json=payload, follow_redirects=True
    )


def delete_current_user(
    client: FlaskClient,
    password: str,
) -> TestResponse:
    """Delete the current user using the API.

    Args:
        client: The Flask test client.

    Returns:
        The response from the API.
    """
    payload = {"password": password}
    return client.delete(
        f"/{V1_ROOT}/{V1_USERS_ROUTE}/current", json=payload, follow_redirects=True
    )


def change_current_user_password(
    client: FlaskClient,
    old_password: str,
    new_password: str,
):
    payload = {
        "oldPassword": old_password,
        "newPassword": new_password,
        "confirmNewPassword": new_password,
    }
    return client.post(
        f"/{V1_ROOT}/{V1_USERS_ROUTE}/current/password",
        json=payload,
        follow_redirects=True,
    )


def change_user_password(
    client: FlaskClient, user_id: int, old_password: str, new_password: str
):

    payload = {
        "oldPassword": old_password,
        "newPassword": new_password,
        "confirmNewPassword": new_password,
    }
    return client.post(
        f"/{V1_ROOT}/{V1_USERS_ROUTE}/{user_id}/password",
        json=payload,
        follow_redirects=True,
    )


# -- Assertions ----------------------------------------------------------------


def assert_user_response_contents_matches_expectations(
    response: dict[str, Any],
    expected_contents: dict[str, Any],
    current_user: bool = False,
) -> None:
    """Assert that user response contents is valid.

    Args:
        response: The actual response from the API.
        expected_contents: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response or if the response contents is not
            valid.
    """
    # TODO: NOT TOO SURE ABOUT THIS ONE...
    expected_keys = {
        "username",
        "email",
        "id",
    }
    if current_user:
        expected_keys.update(
            {
                "groups",
                "createdOn",
                "lastModifiedOn",
                "lastLoginOn",
                "passwordExpiresOn",
            }
        )
    assert set(response.keys()) == expected_keys

    # Validate non-Ref fields
    assert isinstance(response["username"], str)
    assert isinstance(response["email"], str)
    assert isinstance(response["id"], int)

    assert response["username"] == expected_contents["username"]
    assert response["email"] == expected_contents["email"]

    if current_user:
        assert isinstance(response["createdOn"], str)
        assert isinstance(response["lastModifiedOn"], str)
        assert isinstance(response["lastLoginOn"], (str, type(None)))
        assert isinstance(response["passwordExpiresOn"], str)

        assert helpers.is_iso_format(response["createdOn"])
        assert helpers.is_iso_format(response["lastModifiedOn"])
        if response["lastLoginOn"] is not None:
            assert helpers.is_iso_format(response["lastLoginOn"])
        assert helpers.is_iso_format(response["passwordExpiresOn"])

        # Validate the GroupRef structure
        assert isinstance(response["groups"][0]["id"], int)
        assert isinstance(response["groups"][0]["name"], str)
        assert isinstance(response["groups"][0]["url"], str)


def assert_retrieving_user_by_id_works(
    client: FlaskClient, user_id: int, expected: dict[str, Any]
) -> None:
    """Assert that retrieving a user by id works.

    Args:
        client: The Flask test client.
        user_id: The id of the user to retrieve.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = client.get(
        f"/{V1_ROOT}/{V1_USERS_ROUTE}/{user_id}", follow_redirects=True
    )
    assert response.status_code == 200 and response.get_json() == expected


def assert_retrieving_current_user_works(
    client: FlaskClient,
    expected: dict[str, Any],
) -> None:
    """Assert that retrieving the current user works.

    Args:
        client: The Flask test client.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = client.get(f"/{V1_ROOT}/{V1_USERS_ROUTE}/current", follow_redirects=True)
    assert response.status_code == 200 and response.get_json() == expected


def assert_retrieving_all_users_works(
    client: FlaskClient,
    expected: list[dict[str, Any]],
    search: str | None = None,
    paging_info: dict[str, int] | None = None,
) -> None:
    """Assert that retrieving all queues works.

    Args:
        client: The Flask test client.
        expected: The expected response from the API.
        search: The search string used in query parameters.
        paging_info: The paging information used in query parameters.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    query_string = {}

    if search is not None:
        query_string["search"] = search

    if paging_info is not None:
        query_string["index"] = paging_info["index"]
        query_string["pageLength"] = paging_info["page_length"]

    response = client.get(
        f"/{V1_ROOT}/{V1_USERS_ROUTE}",
        query_string=query_string,
        follow_redirects=True,
    )
    assert response.status_code == 200 and response.get_json()["data"] == expected


def assert_retrieving_users_works(
    client: FlaskClient,
    expected: list[dict[str, Any]],
    search: str | None = None,
    paging_info: dict[str, int] | None = None,
) -> None:
    """Assert that retrieving all users works.

    Args:
        client: The Flask test client.
        expected: The expected response from the API.
        search: The search string used in query parameters.
        paging_info: The paging information used in query parameters.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    query_string = {}

    if search is not None:
        query_string["search"] = search

    if paging_info is not None:
        query_string["index"] = paging_info["index"]
        query_string["pageLength"] = paging_info["page_length"]

    response = client.get(
        f"/{V1_ROOT}/{V1_USERS_ROUTE}",
        query_string=query_string,
        follow_redirects=True,
    )
    assert response.status_code == 200 and response.get_json()["data"] == expected


def assert_registering_existing_username_fails(
    client: FlaskClient,
    existing_username: str,
    non_existing_email: str,
) -> None:
    """Assert that registering a user with an existing username fails.

    Args:
        client: The Flask test client.
        username: The username to assign to the new user.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    password = "supersecurepassword"
    response = actions.register_user(
        client, existing_username, non_existing_email, password
    )
    assert response.status_code == 400


def assert_registering_existing_email_fails(
    client: FlaskClient,
    non_existing_username: str,
    existing_email: str,
) -> None:
    """Assert that registering a user with an existing username fails.

    Args:
        client: The Flask test client.
        username: The username to assign to the new user.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    password = "supersecurepassword"
    response = actions.register_user(
        client, non_existing_username, existing_email, password
    )
    assert response.status_code == 400


def assert_user_username_matches_expected_name(
    client: FlaskClient, user_id: int, expected_name: str
) -> None:
    """Assert that the name of a user matches the expected name.

    Args:
        client: The Flask test client.
        user_id: The id of the user to retrieve.
        expected_name: The expected name of the user.

    Raises:
        AssertionError: If the response status code is not 200 or if the name of the
            user does not match the expected name.
    """
    response = client.get(
        f"/{V1_ROOT}/{V1_USERS_ROUTE}/{user_id}",
        follow_redirects=True,
    )
    assert response.status_code == 200 and response.get_json()["name"] == expected_name


def assert_current_user_username_matches_expected_name(
    client: FlaskClient, expected_name: str
) -> None:
    """Assert that the name of the current user matches the expected name.

    Args:
        client: The Flask test client.
        expected_name: The expected name of the user.

    Raises:
        AssertionError: If the response status code is not 200 or if the name of the
            user does not match the expected name.
    """
    response = client.get(
        f"/{V1_ROOT}/{V1_USERS_ROUTE}/current",
        follow_redirects=True,
    )
    assert response.status_code == 200 and response.get_json()["name"] == expected_name


def assert_user_is_not_found(
    client: FlaskClient,
    user_id: int,
) -> None:
    """Assert that a user is not found.

    Args:
        client: The Flask test client.
        user_id: The id of the user to retrieve.

    Raises:
        AssertionError: If the response status code is not 404.
    """
    response = client.get(
        f"/{V1_ROOT}/{V1_USERS_ROUTE}/{user_id}",
        follow_redirects=True,
    )
    assert response.status_code == 404


def assert_cannot_rename_user_with_existing_username(
    client: FlaskClient,
    existing_username: str,
) -> None:
    """Assert that renaming a user with an existing username fails.

    Args:
        client: The Flask test client.
        existing_username: The username of the existing user.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = modify_current_user(
        client=client,
        new_username=existing_username,
        new_email="new_email",
    )
    assert response.status_code == 400


def assert_cannot_rename_user_with_existing_email(
    client: FlaskClient,
    existing_email: str,
) -> None:
    """Assert that changing a user email with an existing email fails.

    Args:
        client: The Flask test client.
        existing_email: The email of the existing user.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = modify_current_user(
        client=client,
        new_username="new_username",
        new_email=existing_email,
    )
    assert response.status_code == 400


def assert_login_works(
    client: FlaskClient,
    username: str,
    password: str,
):
    assert actions.login(client, username, password).status_code == 200


# -- Tests -------------------------------------------------------------


@pytest.mark.v1
def test_create_user(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
) -> None:
    username = "user"
    email = "user@example.org"
    password = "supersecurepassword"

    # Posting a user returns CurrentUserSchema.
    user_response = actions.register_user(client, username, email, password).get_json()
    assert_user_response_contents_matches_expectations(
        response=user_response,
        expected_contents={
            "username": username,
            "email": email,
        },
        current_user=True,
    )

    user_response = actions.login(client, username, password).get_json()

    assert_user_response_contents_matches_expectations(
        response=user_response,
        expected_contents={
            "username": username,
            "email": email,
        },
        current_user=True,
    )

    assert_retrieving_current_user_works(client, expected=user_response)

    # Getting a user by id returns UserSchema.
    user_expected = {k:v for k,v in user_expected.items() if k in ["username", "email", "id"]}
    assert_retrieving_user_by_id_works(client, user_expected["id"], user_expected)


@pytest.mark.v1
def test_user_get_all(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_users: dict[str, Any],
) -> None:
    """Test that all users can be retrieved.

    Given an authenticated user and registered users, this test validates the following
    sequence of actions:

    - Three users are registered, "user1", "user2", "user3".
    - The user is able to retrieve a list of all registered users.
    - The returned list of users matches the full list of registered users.
    """

    user1_expected = {
        k: v
        for k, v in registered_users["user1"].items()
        if k in ["username", "email", "id"]
    }
    user2_expected = {
        k: v
        for k, v in registered_users["user2"].items()
        if k in ["username", "email", "id"]
    }
    user3_expected = {
        k: v
        for k, v in registered_users["user3"].items()
        if k in ["username", "email", "id"]
    }

    user_expected_list = [user1_expected, user2_expected, user3_expected]

    assert_retrieving_users_works(client, expected=user_expected_list)


@pytest.mark.v1
def test_user_search_query(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_users: dict[str, Any],
) -> None:
    user_expected_list = [
        {"username": user["username"], "email": user["email"], "id": user["id"]}
        for user in list(registered_users.values())
    ]
    assert_retrieving_all_users_works(client, expected=user_expected_list)


@pytest.mark.v1
def test_cannot_register_existing_username(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_users: dict[str, Any],
) -> None:
    existing_user = registered_users["user1"]
    assert_registering_existing_username_fails(
        client,
        existing_username=existing_user["username"],
        non_existing_email="unique" + existing_user["email"],
    )


@pytest.mark.v1
def test_cannot_register_existing_email(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_users: dict[str, Any],
) -> None:
    """Test that registering a user with an existing email fails.

    Given an authenticated user and registered users, this test validates the following
    sequence of actions:

    - One user is registered, "user1".
    - A new user is registered with the same email as user1, but _not_ the same email.
    - The request fails with an appropriate error message and response code.
    """
    existing_user = registered_users["user1"]
    assert_registering_existing_email_fails(
        client,
        non_existing_username="unique" + existing_user["username"],
        existing_email=existing_user["email"],
    )


@pytest.mark.v1
def test_rename_current_user(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
):
    new_username = "new_name"

    user = modify_current_user(client, new_username, auth_account["email"]).get_json()
    assert_retrieving_current_user_works(client, expected=user)


@pytest.mark.v1
def test_delete_current_user(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_users: dict[str, Any],
) -> None:
    delete_current_user(client, registered_users["user1"]["password"])
    assert_user_is_not_found(client, user_id=registered_users["user1"]["id"])


@pytest.mark.v1
def test_change_current_user_password(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_users: dict[str, Any],
):
    new_password = "new_password"
    old_password = registered_users["user1"]["password"]
    change_current_user_password(client, old_password, new_password)
    assert_login_works(client, username="user1", password=new_password)


@pytest.mark.v1
def test_change_user_password(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_users: dict[str, Any],
):
    new_password = "new_password"
    old_password = registered_users["user2"]["password"]
    user_id = registered_users["user2"]["id"]
    change_user_password(client, user_id, old_password, new_password)
    assert_login_works(client, username="user2", password=new_password)


@pytest.mark.v1
def test_new_password_cannot_be_existing(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_users: dict[str, Any],
):
    old_password = new_password = registered_users["user1"]
    assert (
        change_current_user_password(client, old_password, new_password).status_code
        == 400
    )

    old_password = new_password = registered_users["user2"]
    user_id = registered_users["user2"]["id"]
    assert (
        change_user_password(client, user_id, old_password, new_password).status_code
        == 400
    )
