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
functionalities for the user entity. The tests ensure that the users can be registered,
modified, and deleted as expected through the REST API.
"""
from http import HTTPStatus
from typing import Any

from flask_sqlalchemy import SQLAlchemy

from dioptra.client.base import DioptraResponseProtocol
from dioptra.client.client import DioptraClient

from ..lib import helpers
from ..test_utils import assert_retrieving_resource_works

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
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    user_id: int,
    expected: dict[str, Any],
) -> None:
    """Assert that retrieving a user by id works.

    Args:
        dioptra_client: The Dioptra client.
        user_id: The id of the user to retrieve.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = dioptra_client.users.get_by_id(user_id)
    assert response.status_code == HTTPStatus.OK and response.json() == expected


def assert_retrieving_current_user_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    expected: dict[str, Any],
) -> None:
    """Assert that retrieving the current user works.

    Args:
        dioptra_client: The Dioptra client.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = dioptra_client.users.get_current()
    to_ignore = ["lastLoginOn", "lastModifiedOn"]
    response_info_filtered = {
        k: v for k, v in response.json().items() if k not in to_ignore
    }
    expected_filtered = {k: v for k, v in expected.items() if k not in to_ignore}
    assert (
        response.status_code == HTTPStatus.OK
        and response_info_filtered == expected_filtered
    )


def assert_retrieving_users_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    expected: list[dict[str, Any]],
    search: str | None = None,
    paging_info: dict[str, int] | None = None,
) -> None:
    """Assert that retrieving all users works.

    Args:
        dioptra_client: The Dioptra client.
        expected: The expected response from the API.
        search: The search string used in query parameters.
        paging_info: The paging information used in query parameters.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    assert_retrieving_resource_works(
        dioptra_client=dioptra_client.users,
        expected=expected,
        search=search,
        paging_info=paging_info,
    )


def assert_registering_existing_username_fails(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    existing_username: str,
    non_existing_email: str,
) -> None:
    """Assert that registering a user with an existing username fails.

    Args:
        dioptra_client: The Dioptra client.
        username: The username to assign to the new user.

    Raises:
        AssertionError: If the response status code is not 409.
    """
    password = "supersecurepassword"
    response = dioptra_client.users.create(
        username=existing_username, email=non_existing_email, password=password
    )
    assert response.status_code == HTTPStatus.CONFLICT


def assert_registering_existing_email_fails(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    non_existing_username: str,
    existing_email: str,
) -> None:
    """Assert that registering a user with an existing username fails.

    Args:
        dioptra_client: The Dioptra client.
        username: The username to assign to the new user.

    Raises:
        AssertionError: If the response status code is not 409.
    """
    password = "supersecurepassword"
    response = dioptra_client.users.create(
        username=non_existing_username, email=existing_email, password=password
    )
    assert response.status_code == HTTPStatus.CONFLICT


def assert_user_username_matches_expected_name(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    user_id: int,
    expected_name: str,
) -> None:
    """Assert that the name of a user matches the expected name.

    Args:
        dioptra_client: The Dioptra client.
        user_id: The id of the user to retrieve.
        expected_name: The expected name of the user.

    Raises:
        AssertionError: If the response status code is not 200 or if the name of the
            user does not match the expected name.
    """
    response = dioptra_client.users.get_by_id(user_id)
    assert (
        response.status_code == HTTPStatus.OK
        and response.json()["name"] == expected_name
    )


def assert_current_user_username_matches_expected_name(
    dioptra_client: DioptraClient[DioptraResponseProtocol], expected_name: str
) -> None:
    """Assert that the name of the current user matches the expected name.

    Args:
        dioptra_client: The Dioptra client.
        expected_name: The expected name of the user.

    Raises:
        AssertionError: If the response status code is not 200 or if the name of the
            user does not match the expected name.
    """
    response = dioptra_client.users.get_current()
    assert (
        response.status_code == HTTPStatus.OK
        and response.json()["name"] == expected_name
    )


def assert_user_is_not_found(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    user_id: int,
) -> None:
    """Assert that a user is not found.

    Args:
        dioptra_client: The Dioptra client.
        user_id: The id of the user to retrieve.

    Raises:
        AssertionError: If the response status code is not 404.
    """
    response = dioptra_client.users.get_by_id(user_id)
    assert response.status_code == HTTPStatus.NOT_FOUND


def assert_cannot_rename_user_with_existing_username(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    existing_username: str,
) -> None:
    """Assert that renaming a user with an existing username fails.

    Args:
        dioptra_client: The Dioptra client.
        existing_username: The username of the existing user.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = dioptra_client.users.modify_current_user(
        username=existing_username,
        email="new_email",
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def assert_cannot_rename_user_with_existing_email(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    existing_email: str,
) -> None:
    """Assert that changing a user email with an existing email fails.

    Args:
        dioptra_client: The Dioptra client.
        existing_email: The email of the existing user.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = dioptra_client.users.modify_current_user(
        username="new_username",
        email=existing_email,
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def assert_login_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    username: str,
    password: str,
):
    """Assert that logging in using a username and password works.

    Args:
        dioptra_client: The Dioptra client.
        username: The username of the user to be logged in.
        password: The password of the user to be logged in.

    Raises:
        AssertionError: If the response status code is not 200.
    """
    assert dioptra_client.auth.login(username, password).status_code == HTTPStatus.OK


def assert_user_does_not_exist(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    username: str,
    password: str,
):
    """Assert that the user does not exist.

    Args:
        dioptra_client: The Dioptra client.
        username: The username of the user to be logged in.
        password: The password of the user to be logged in.

    Raises:
        AssertionError: If the response status code is not 404.
    """
    response = dioptra_client.auth.login(username, password)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def assert_login_is_unauthorized(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    username: str,
    password: str,
):
    """Assert that logging in using a username and password is unauthorized.

    Args:
        dioptra_client: The Dioptra client.
        username: The username of the user to be logged in.
        password: The password of the user to be logged in.

    Raises:
        AssertionError: If the response status code is not 401.
    """
    response = dioptra_client.auth.login(username, password)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def assert_new_password_cannot_be_existing(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    password: str,
    user_id: str | None = None,
):
    """Assert that changing a user (current or otherwise) password to the
    existing password fails.

    Args:
        client (FlaskClient): The Flask test client.
        password (str): The existing password of the user.
        user_id (str, optional): The user id. If this is not passed,
        we assume we are the current user. Defaults to None.

    Raises:
        AssertionError: If the response status code is not 403.
    """
    # Means we are the current user.
    if user_id is None:
        response = dioptra_client.users.change_current_user_password(password, password)
        assert response.status_code == HTTPStatus.FORBIDDEN
    else:
        response = dioptra_client.users.change_password_by_id(
            user_id, password, password
        )
        assert response.status_code == HTTPStatus.FORBIDDEN


# -- Tests -------------------------------------------------------------


def test_create_user(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    user_response = dioptra_client.users.create(username, email, password).json()
    assert_user_response_contents_matches_expectations(
        response=user_response,
        expected_contents={
            "username": username,
            "email": email,
        },
        current_user=True,
    )

    dioptra_client.auth.login(username, password)
    assert_retrieving_current_user_works(dioptra_client, expected=user_response)

    # Getting a user by id returns UserSchema.
    user_expected = {
        k: v for k, v in user_response.items() if k in ["username", "email", "id"]
    }
    assert_retrieving_user_by_id_works(
        dioptra_client, user_expected["id"], user_expected
    )


def test_user_get_all(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    assert_retrieving_users_works(dioptra_client, expected=user_expected_list)


def test_user_search_query(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
        dioptra_client, expected=user_expected_list, search="username:*user*"
    )
    assert_retrieving_users_works(
        dioptra_client, expected=user_expected_list, search="username:'*user*'"
    )
    assert_retrieving_users_works(
        dioptra_client, expected=user_expected_list, search='username:"user?"'
    )
    assert_retrieving_users_works(
        dioptra_client, expected=user_expected_list, search="username:user?,email:user*"
    )
    assert_retrieving_users_works(
        dioptra_client, expected=[], search=r"username:\*user*"
    )
    assert_retrieving_users_works(dioptra_client, expected=[], search="email:user?")


def test_cannot_register_existing_username(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
        dioptra_client,
        existing_username=existing_user["username"],
        non_existing_email="unique" + existing_user["email"],
    )


def test_cannot_register_existing_email(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
        dioptra_client,
        non_existing_username="unique" + existing_user["username"],
        existing_email=existing_user["email"],
    )


def test_rename_current_user(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    user = dioptra_client.users.modify_current_user(
        username=new_username,
        email=auth_account["email"],
    ).json()
    assert_retrieving_current_user_works(dioptra_client, expected=user)


def test_user_authorization_failure(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    assert_login_is_unauthorized(dioptra_client, username=username, password=password)


def test_delete_current_user(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    dioptra_client.users.delete_current_user(password)
    assert_user_does_not_exist(dioptra_client, username=username, password=password)


def test_change_current_user_password(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    dioptra_client.users.change_current_user_password(old_password, new_password)
    assert_login_works(dioptra_client, username=username, password=new_password)


def test_change_user_password(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    dioptra_client.users.change_password_by_id(user_id, old_password, new_password)
    assert_login_works(dioptra_client, username=username, password=new_password)


def test_new_password_cannot_be_existing(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    assert_new_password_cannot_be_existing(dioptra_client, password)
    # test via /users/{user_id}
    assert_new_password_cannot_be_existing(dioptra_client, password, user_id)
