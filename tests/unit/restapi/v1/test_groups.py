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
"""Test suite for group operations.

This module contains a set of tests that validate the CRUD operations and additional
functionalities for the group entity. The tests ensure that the groups can be
registered, queried, and renamed as expected through the REST API.
"""

from typing import Any

import pytest
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from werkzeug.test import TestResponse

from dioptra.restapi.routes import V1_GROUPS_ROUTE, V1_ROOT

from ..lib import actions, helpers

# -- Actions ---------------------------------------------------------------------------


def modify_group(
    client: FlaskClient,
    group_id: int,
    new_name: str,
) -> TestResponse:
    """Rename a group using the API.

    Args:
        client: The Flask test client.
        group_id: The id of the group to rename.
        new_name: The new name to assign to the group.
        new_description: The new description to assign to the group.

    Returns:
        The response from the API.
    """
    payload = {"name": new_name}

    return client.put(
        f"/{V1_ROOT}/{V1_GROUPS_ROUTE}/{group_id}",
        json=payload,
        follow_redirects=True,
    )


# -- Assertions ------------------------------------------------------------------------


def assert_group_response_contents_matches_expectations(
    response: dict[str, Any], expected_contents: dict[str, Any]
) -> None:
    """Assert that group response contents is valid.

    Args:
        response: The actual response from the API.
        expected_contents: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response or if the response contents is not
            valid.
    """
    expected_keys = {
        "id",
        "name",
        "user",
        "createdOn",
        "lastModifiedOn",
    }
    assert set(response.keys()) == expected_keys

    # Validate the non-Ref fields
    assert isinstance(response["id"], int)
    assert isinstance(response["name"], str)
    assert isinstance(response["createdOn"], str)
    assert isinstance(response["lastModifiedOn"], str)
    assert isinstance(response["latestSnapshot"], bool)

    assert response["name"] == expected_contents["name"]

    assert helpers.is_iso_format(response["createdOn"])
    assert helpers.is_iso_format(response["lastModifiedOn"])

    # Validate the UserRef structure
    assert isinstance(response["user"]["id"], int)
    assert isinstance(response["user"]["username"], str)
    assert isinstance(response["user"]["url"], str)
    assert response["user"]["id"] == expected_contents["user_id"]


def assert_retrieving_group_by_id_works(
    client: FlaskClient,
    group_id: int,
    expected: dict[str, Any],
) -> None:
    """Assert that retrieving a group by id works.

    Args:
        client: The Flask test client.
        group_id: The id of the group to retrieve.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = client.get(
        f"/{V1_ROOT}/{V1_GROUPS_ROUTE}/{group_id}", follow_redirects=True
    )
    assert response.status_code == 200 and response.get_json() == expected


def assert_retrieving_groups_works(
    client: FlaskClient,
    expected: list[dict[str, Any]],
    search: str | None = None,
    paging_info: dict[str, Any] | None = None,
) -> None:
    """Assert that retrieving all groups works.

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
        query_string["query"] = search

    if paging_info is not None:
        query_string["index"] = paging_info["index"]
        query_string["pageLength"] = paging_info["page_length"]

    response = client.get(
        f"/{V1_ROOT}/{V1_GROUPS_ROUTE}",
        query_string=query_string,
        follow_redirects=True,
    )
    assert response.status_code == 200 and response.get_json()["data"] == expected


def assert_registering_existing_group_name_fails(
    client: FlaskClient, name: str
) -> None:
    """Assert that registering a group with an existing name fails.

    Args:
        client: The Flask test client.
        name: The name to assign to the new group.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = actions.register_group(client, name=name)
    assert response.status_code == 400


def assert_group_name_matches_expected_name(
    client: FlaskClient, group_id: int, expected_name: str
) -> None:
    """Assert that the name of a group matches the expected name.

    Args:
        client: The Flask test client.
        group_id: The id of the group to retrieve.
        expected_name: The expected name of the group.

    Raises:
        AssertionError: If the response status code is not 200 or if the name of the
            group does not match the expected name.
    """
    response = client.get(
        f"/{V1_ROOT}/{V1_GROUPS_ROUTE}/{group_id}",
        follow_redirects=True,
    )
    assert response.status_code == 200 and response.get_json()["name"] == expected_name


def assert_cannot_rename_group_with_existing_name(
    client: FlaskClient,
    group_id: int,
    existing_name: str,
) -> None:
    """Assert that renaming a group with an existing name fails.

    Args:
        client: The Flask test client.
        group_id: The id of the group to rename.
        name: The name of an existing group.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = modify_group(
        client=client,
        group_id=group_id,
        new_name=existing_name,
    )
    assert response.status_code == 400


# -- Tests -----------------------------------------------------------------------------


@pytest.mark.v1
def test_create_group(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
) -> None:
    """Test that groups can be correctly registered and retrieved using the API.

    Given an authenticated user, this test validates the following sequence of actions:

    - The user registers a group named "new_group".
    - The response is valid matches the expected values given the registration request.
    - The user is able to retrieve information about the group using the group id^[1].
      
    [1] The group id is generated in the backend during the POST and is returned in the response.
    """
    name = "new_group"
    user_id = auth_account["user_id"]

    group_response = actions.register_group(client, name=name)
    group_expected = group_response.get_json()
   
    assert_group_response_contents_matches_expectations(
        response=group_expected,
        expected_contents={
            "name": name,
            "user_id": user_id,
        },
    )

    assert_retrieving_group_by_id_works(
        client, group_id=group_expected["groupId"], expected=group_expected
    )


@pytest.mark.v1
def test_group_search_query(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_groups: dict[str, Any],
) -> None:
    """Test that groups can be queried with a search term.

    Given an authenticated user and registered groups, this test validates the following
    sequence of actions:

    - The user is able to retrieve a list of all registered groups with a description
      that contains 'group'.
    - The returned list of groups matches the expected matches from the query.
    """
    group1_expected = registered_groups["group1"]
    group2_expected = registered_groups["group2"]
    group_expected_list = [group1_expected, group2_expected]

    assert_retrieving_groups_works(
        client,
        expected=group_expected_list,
        search="name:*group*",
    )


@pytest.mark.v1
def test_group_id_get(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_groups: dict[str, Any],
) -> None:
    """Test that groups can be retrieved by their unique ID.

    Given an authenticated user and registered groups, this test validates the following
    sequence of actions:

    - The user is able to retrieve single group by its ID.
    - The response is a single group with a matching ID.
    """
    group3_expected = registered_groups["group3"]

    assert_retrieving_group_by_id_works(
        client, group_id=group3_expected["groupId"], expected=group3_expected
    )


@pytest.mark.v1
def test_cannot_register_existing_group_name(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_groups: dict[str, Any],
) -> None:
    """Test that registering a group with an existing name fails.

    Given an authenticated user and registered groups, this test validates the following
    sequence of actions:

    - The user attempts to register a second group with the same name.
    - The request fails with an appropriate error message and response code.
    """
    existing_group = registered_groups["group1"]

    assert_registering_existing_group_name_fails(
        client,
        name=existing_group["name"],
    )


@pytest.mark.v1
def test_rename_group(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_groups: dict[str, Any],
) -> None:
    """Test that a group can be renamed.

    Given an authenticated user and registered groups, this test validates the following
    sequence of actions:

    - The user issues a request to change the name of a group.
    - The user retrieves information about the same group and it reflects the name
      change.
    - The user issues a request to change the name of a group to an existing group's
      name.
    - The request fails with an appropriate error message and response code.
    """
    updated_group_name = "updated_name"
    group_to_rename = registered_groups["group1"]
    existing_group = registered_groups["group2"]

    modify_group(
        client,
        group_id=group_to_rename["groupId"],
        new_name=updated_group_name,
    )

    assert_group_name_matches_expected_name(
        client, group_id=group_to_rename["groupId"], expected_name=updated_group_name
    )

    assert_cannot_rename_group_with_existing_name(
        client,
        group_id=group_to_rename["groupId"],
        existing_name=existing_group["name"],
    )