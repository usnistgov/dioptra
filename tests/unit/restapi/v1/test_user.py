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
    """Change the current user password using the API."""
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
    """Change a user password using its ID using the API."""
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
    to_ignore = ["lastLoginOn", "lastModifiedOn"]
    response_info_filtered = {
        k: v for k, v in response.get_json().items() if k not in to_ignore
    }
    expected_filtered = {k: v for k, v in expected.items() if k not in to_ignore}
    assert response.status_code == 200 and response_info_filtered == expected_filtered


def assert_retrieving_all_users_works(
    client: FlaskClient,
    expected: list[dict[str, Any]],
) -> None:
    """Assert that retrieving all queues works.

    Args:
        client: The Flask test client.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = client.get(
        f"/{V1_ROOT}/{V1_USERS_ROUTE}",
        query_string={},
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
    """Assert that logging in using a username and password works.

    Args:
        client: The Flask test client.
        username: The username of the user to be logged in.
        password: The password of the user to be logged in.

    Raises:
        AssertionError: If the response status code is not 200.
    """
    assert actions.login(client, username, password).status_code == 200


def assert_user_does_not_exist(
    client: FlaskClient,
    username: str,
    password: str,
):
    """Assert that the user does not exist.

    Args:
        client: The Flask test client.
        username: The username of the user to be logged in.
        password: The password of the user to be logged in.

    Raises:
        AssertionError: If the response status code is not 404.
    """
    assert actions.login(client, username, password).status_code == 404


def assert_login_is_unauthorized(
    client: FlaskClient,
    username: str,
    password: str,
):
    """Assert that logging in using a username and password is unauthorized.

    Args:
        client: The Flask test client.
        username: The username of the user to be logged in.
        password: The password of the user to be logged in.

    Raises:
        AssertionError: If the response status code is not 403.
    """
    assert actions.login(client, username, password).status_code == 403


def assert_new_password_cannot_be_existing(
    client: FlaskClient,
    password: str,
    user_id: str = None,
):
    """Assert that changing a user (current or otherwise) password to the
    existing password fails.

    Args:
        client (FlaskClient): The Flask test client.
        password (str): The existing password of the user.
        user_id (str, optional): The user id. If this is not passed,
        we assume we are the current user. Defaults to None.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    # Means we are the current user.
    if not user_id:
        assert (
            change_current_user_password(client, password, password).status_code == 403
        )
    else:
        assert (
            change_user_password(client, user_id, password, password).status_code == 403
        )


# -- Tests -------------------------------------------------------------


def test_create_user(
    client: FlaskClient,
    db: SQLAlchemy,
) -> None:
    """Test that we can create a user and its response is expected.

    This test validates the following sequence of actions:

    - Register a new user using the username, email, and password.
    - Assert that the response matches what we expect to see, i.e. CurrentUser
    schema information.
    - Login with the user that we just created.
    - Assert that retrieving the current user works.
    - Finally, assert that we can retrieve the current user by ID and it matches
    our expectations.
    """
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

    actions.login(client, username, password).get_json()
    assert_retrieving_current_user_works(client, expected=user_response)

    # Getting a user by id returns UserSchema.
    user_expected = {
        k: v for k, v in user_response.items() if k in ["username", "email", "id"]
    }
    assert_retrieving_user_by_id_works(client, user_expected["id"], user_expected)


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
    user_expected_list = [
        {"username": user["username"], "email": user["email"], "id": user["id"]}
        for user in list(registered_users.values())
    ]
    assert_retrieving_users_works(client, expected=user_expected_list)


def test_user_search_query(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_users: dict[str, Any],
) -> None:
    """Test that users can be found using a search query.

    Given an authenticated user and registered users, this test validates the following
    sequence of actions:

    - The user is able to retrieve a list of all users that match the query.
    - The returned list of users matches the expected matches from the query.
    """
    user_expected_list = [
        {"username": user["username"], "email": user["email"], "id": user["id"]}
        for user in list(registered_users.values())[:2]
    ]
    assert_retrieving_users_works(
        client, expected=user_expected_list, search="username:*user*"
    )
    assert_retrieving_users_works(
        client, expected=user_expected_list, search="username:'*user*'"
    )
    assert_retrieving_users_works(
        client, expected=user_expected_list, search='username:"user?"'
    )
    assert_retrieving_users_works(
        client, expected=user_expected_list, search="username:user?,email:user*"
    )
    assert_retrieving_users_works(client, expected=[], search=r"username:\*user*")
    assert_retrieving_users_works(client, expected=[], search="email:user?")


def test_cannot_register_existing_username(
    client: FlaskClient,
    db: SQLAlchemy,
    registered_users: dict[str, Any],
) -> None:
    """Test that registering a user with an existing username fails.

    Given an authenticated user and registered users, this test validates the following
    sequence of actions:

    - One user is registered, "user1".
    - A new user is registered with the same email as user1, a different username.
    - The request fails with an appropriate error message and response code.
    """
    existing_user = registered_users["user1"]
    assert_registering_existing_username_fails(
        client,
        existing_username=existing_user["username"],
        non_existing_email="unique" + existing_user["email"],
    )


def test_cannot_register_existing_email(
    client: FlaskClient,
    db: SQLAlchemy,
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


def test_rename_current_user(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
) -> None:
    """Test that renaming the current user works.

    Given an authenticated user, this test validates the following sequence of actions:

    - A user modifies its username and we record the response from the API.
    - Retrieving the current user works and responds with the response we recorded
    that reflects the updated username.
    """
    new_username = "new_name"
    user = modify_current_user(client, new_username, auth_account["email"]).get_json()
    assert_retrieving_current_user_works(client, expected=user)


def test_user_authorization_failure(
    client: FlaskClient,
    db: SQLAlchemy,
    registered_users: dict[str, Any],
) -> None:
    """Test that a user providing an incorrect password cannot log in.

    Given an authenticated user, this test validates the following sequence of actions:

    - The current attempts to login with an incorrect password.
    - The user cannot log in.
    """
    username = registered_users["user2"]["username"]
    password = registered_users["user2"]["password"] + "incorrect"
    assert_login_is_unauthorized(client, username=username, password=password)


def test_delete_current_user(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
) -> None:
    """Test that deleting the current user works.

    Given an authenticated user, this test validates the following sequence of actions:

    - The current user deletes itself using its password.
    - The user can no longer log in.
    """
    username = auth_account["username"]
    password = auth_account["password"]
    delete_current_user(client, password)
    assert_user_does_not_exist(client, username=username, password=password)


def test_change_current_user_password(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
):
    """Test that changing the current user password works.

    Given an authenticated user, this test validates the following sequence of actions:

    - The current user changes its password, and it does not fail.
    - The current user is able to login with the new password.
    """
    username = auth_account["username"]
    old_password = auth_account["password"]
    new_password = "new_password"
    change_current_user_password(client, old_password, new_password)
    assert_login_works(client, username=username, password=new_password)


def test_change_user_password(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_users: dict[str, Any],
):
    """Test that changing a user password works.

    Given an authenticated user, this test validates the following sequence of actions:

    - Using its ID, a user's password is changed, and it does not fail.
    - This user is then able to login with the new password.
    """
    user_id = registered_users["user2"]["id"]
    username = registered_users["user2"]["username"]
    old_password = registered_users["user2"]["password"]
    new_password = "new_password"
    change_user_password(client, user_id, old_password, new_password)
    assert_login_works(client, username=username, password=new_password)


def test_new_password_cannot_be_existing(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
):
    """Test that changing a password and setting the new password as the
    old password fails.

    Given an authenticated user, this test validates the following sequence of actions:

    - The current user tries to set its new password which is the same as its existing
    password and this action fails.
    - The same password as the existing password for a user with an ID is attempted
    to be set and this action fails.
    """
    user_id = auth_account["id"]
    password = auth_account["password"]
    # test via /users/current
    assert_new_password_cannot_be_existing(client, password)
    # test via /users/{user_id}
    assert_new_password_cannot_be_existing(client, password, user_id)
