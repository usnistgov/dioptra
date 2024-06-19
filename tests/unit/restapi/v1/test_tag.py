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
"""Test suite for tag operations.

This module contains a set of tests that validate the CRUD operations and additional
functionalities for the tag entity. The tests ensure that the tags can be
registered, renamed, deleted, and queried as expected through the REST API.
"""
from typing import Any

import pytest
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from werkzeug.test import TestResponse

from dioptra.restapi.routes import V1_ROOT, V1_TAGS_ROUTE

from ..lib import actions, helpers

# -- Actions ---------------------------------------------------------------------------


def modify_tag(
    client: FlaskClient,
    tag_id: int,
    new_name: str,
) -> TestResponse:
    """Rename a tag using the API.

    Args:
        client: The Flask test client.
        tag_id: The id of the tag to rename.
        new_name: The new name to assign to the tag.

    Returns:
        The response from the API.
    """
    payload: dict[str, Any] = {"name": new_name}

    return client.put(
        f"/{V1_ROOT}/{V1_TAGS_ROUTE}/{tag_id}",
        json=payload,
        follow_redirects=True,
    )


def delete_tag(
    client: FlaskClient,
    tag_id: int,
) -> TestResponse:
    """Delete a tag using the API.

    Args:
        client: The Flask test client.
        tag_id: The id of the tag to delete.

    Returns:
        The response from the API.
    """

    return client.delete(
        f"/{V1_ROOT}/{V1_TAGS_ROUTE}/{tag_id}",
        follow_redirects=True,
    )


# -- Assertions ------------------------------------------------------------------------


def assert_tag_response_contents_matches_expectations(
    response: dict[str, Any], expected_contents: dict[str, Any]
) -> None:
    expected_keys = {
        "id",
        "group",
        "user",
        "createdOn",
        "lastModifiedOn",
        "name",
    }
    assert set(response.keys()) == expected_keys

    # Validate the non-Ref fields
    assert isinstance(response["id"], int)
    assert isinstance(response["name"], str)
    assert isinstance(response["createdOn"], str)
    assert isinstance(response["lastModifiedOn"], str)

    assert response["name"] == expected_contents["name"]

    assert helpers.is_iso_format(response["createdOn"])
    assert helpers.is_iso_format(response["lastModifiedOn"])

    # Validate the UserRef structure
    assert isinstance(response["user"]["id"], int)
    assert isinstance(response["user"]["username"], str)
    assert isinstance(response["user"]["url"], str)
    assert response["user"]["id"] == expected_contents["user_id"]

    # Validate the GroupRef structure
    assert isinstance(response["group"]["id"], int)
    assert isinstance(response["group"]["name"], str)
    assert isinstance(response["group"]["url"], str)
    assert response["group"]["id"] == expected_contents["group_id"]


def assert_retrieving_tag_by_id_works(
    client: FlaskClient,
    tag_id: int,
    expected: dict[str, Any],
) -> None:
    """Assert that retrieving a tag by id works.

    Args:
        client: The Flask test client.
        tag_id: The id of the tag to retrieve.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = client.get(f"/{V1_ROOT}/{V1_TAGS_ROUTE}/{tag_id}", follow_redirects=True)
    assert response.status_code == 200 and response.get_json() == expected


def assert_retrieving_tags_works(
    client: FlaskClient,
    expected: list[dict[str, Any]],
    group_id: int | None = None,
    search: str | None = None,
    paging_info: dict[str, Any] | None = None,
) -> None:
    """Assert that retrieving all tags works.

    Args:
        client: The Flask test client.
        expected: The expected response from the API.
        group_id: The group ID used in query parameters.
        search: The search string used in query parameters.
        paging_info: The paging information used in query parameters.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """

    query_string: dict[str, Any] = {}

    if group_id is not None:
        query_string["groupId"] = group_id

    if search is not None:
        query_string["search"] = search

    if paging_info is not None:
        query_string["index"] = paging_info["index"]
        query_string["pageLength"] = paging_info["page_length"]

    response = client.get(
        f"/{V1_ROOT}/{V1_TAGS_ROUTE}",
        query_string=query_string,
        follow_redirects=True,
    )
    assert response.status_code == 200 and response.get_json()["data"] == expected


def assert_registering_existing_tag_name_fails(
    client: FlaskClient, name: str, group_id: int
) -> None:
    """Assert that registering a tag with an existing name fails.

    Args:
        client: The Flask test client.
        name: The name to assign to the new tag.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = actions.register_tag(client, name=name, group_id=group_id)
    assert response.status_code == 400


def assert_tag_name_matches_expected_name(
    client: FlaskClient, tag_id: int, expected_name: str
) -> None:
    """Assert that the name of a tag matches the expected name.

    Args:
        client: The Flask test client.
        tag_id: The id of the tag to retrieve.
        expected_name: The expected name of the tag.

    Raises:
        AssertionError: If the response status code is not 200 or if the name of the
            tag does not match the expected name.
    """
    response = client.get(
        f"/{V1_ROOT}/{V1_TAGS_ROUTE}/{tag_id}",
        follow_redirects=True,
    )
    assert response.status_code == 200 and response.get_json()["name"] == expected_name


def assert_tag_is_not_found(
    client: FlaskClient,
    tag_id: int,
) -> None:
    """Assert that a tag is not found.

    Args:
        client: The Flask test client.
        tag_id: The id of the tag to retrieve.

    Raises:
        AssertionError: If the response status code is not 404.
    """
    response = client.get(
        f"/{V1_ROOT}/{V1_TAGS_ROUTE}/{tag_id}",
        follow_redirects=True,
    )
    assert response.status_code == 404


def assert_cannot_rename_tag_with_existing_name(
    client: FlaskClient,
    tag_id: int,
    existing_name: str,
) -> None:
    """Assert that renaming a tag with an existing name fails.

    Args:
        client: The Flask test client.
        tag_id: The id of the tag to rename.
        name: The name of an existing tag.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = modify_tag(
        client=client,
        tag_id=tag_id,
        new_name=existing_name,
    )
    assert response.status_code == 400


# -- Tests -----------------------------------------------------------------------------


def test_create_tag(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
) -> None:
    """Test that tags can be registered and retrieved using the API.

    This test validates the following sequence of actions:

    - A user registers a tag: {name: "tag"}
    - The user is able to retrieve information about the tag using the
      tag id.
    - The returned information matches the information that was provided
      during registration.
    """
    name = "tag"
    user_id = auth_account["default_group_id"]
    group_id = auth_account["default_group_id"]
    tag_response = actions.register_tag(
        client,
        name=name,
        group_id=group_id,
    )
    tag_expected = tag_response.get_json()

    assert_tag_response_contents_matches_expectations(
        response=tag_expected,
        expected_contents={
            "name": name,
            "user_id": user_id,
            "group_id": group_id,
        },
    )
    assert_retrieving_tag_by_id_works(
        client, tag_id=tag_expected["id"], expected=tag_expected
    )


def test_tag_search_query(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_tags: dict[str, Any],
) -> None:
    """Test that tags can be registered and retrieved using the API with search terms.

    This test validates the following sequence of actions:

    - A user registers three tags: "tag1", "tag2", "tag3".
    - The user is able to retrieve a list of all registered tags with the string "tag"
      contained within the name.
    - In all cases, the returned information matches the information that was provided
      during registration.
    """
    tag1_expected = registered_tags["tag1"]
    tag2_expected = registered_tags["tag2"]
    tag_expected_list = [tag1_expected, tag2_expected]

    assert_retrieving_tags_works(
        client,
        expected=tag_expected_list,
        search="name:*tag*",
    )


def test_cannot_register_existing_tag_name(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_tags: dict[str, Any],
) -> None:
    """Test that registering a tag with an existing name fails.

    This test validates the following sequence of actions:

    - A user registers a tag named "tag1".
    - The user attempts to register a second tag with the same name, which fails.
    """
    existing_tag = registered_tags["tag1"]

    assert_registering_existing_tag_name_fails(
        client, name=existing_tag["name"], group_id=existing_tag["group"]["id"]
    )


def test_rename_tag(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_tags: dict[str, Any],
) -> None:
    """Test that a tag can be renamed.

    This test validates the following sequence of actions:

    - A user registers a tag named "ML: Object Recognition".
    - The user is able to retrieve information about the "ML: Object Recognition" tag
      that matches the information that was provided during registration.
    - The user renames this same tag to "new_name".
    - The user retrieves information about the same tag and it reflects the name
      change.
    """
    updated_tag_name = "new_name"
    tag_to_rename = registered_tags["tag1"]
    existing_tag = registered_tags["tag2"]

    modify_tag(
        client,
        tag_id=tag_to_rename["id"],
        new_name=updated_tag_name,
    )
    assert_tag_name_matches_expected_name(
        client, tag_id=tag_to_rename["id"], expected_name=updated_tag_name
    )
    assert_cannot_rename_tag_with_existing_name(
        client,
        tag_id=tag_to_rename["id"],
        existing_name=existing_tag["name"],
    )


def test_delete_tag_by_id(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_tags: dict[str, Any],
) -> None:
    """Test that a tag can be deleted by referencing its id.

    This test validates the following sequence of actions:

    - A user registers a tag.
    - The user is able to retrieve information about the tag that
      matches the information that was provided during registration.
    - The user deletes the tag by referencing its id.
    - The user attempts to retrieve information about the tag, which
      is no longer found.
    """
    tag_expected = registered_tags["tag1"]

    assert_retrieving_tag_by_id_works(
        client, tag_id=tag_expected["id"], expected=tag_expected
    )
    delete_tag(client, tag_id=tag_expected["id"])
    assert_tag_is_not_found(client, tag_id=tag_expected["id"])
