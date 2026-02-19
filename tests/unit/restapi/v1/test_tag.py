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
from http import HTTPStatus
from typing import Any

import pytest

from dioptra.client.base import DioptraResponseProtocol
from dioptra.client.client import DioptraClient

from ..lib import helpers
from ..test_utils import assert_retrieving_resource_works

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
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    tag_id: int,
    expected: dict[str, Any],
) -> None:
    """Assert that retrieving a tag by id works.

    Args:
        dioptra_client: The Dioptra client.
        tag_id: The id of the tag to retrieve.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = dioptra_client.tags.get_by_id(tag_id)
    assert response.status_code == HTTPStatus.OK and response.json() == expected


def assert_retrieving_tags_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    expected: list[dict[str, Any]],
    group_id: int | None = None,
    sort_by: str | None = None,
    descending: bool | None = None,
    search: str | None = None,
    paging_info: dict[str, Any] | None = None,
) -> None:
    """Assert that retrieving all tags works.

    Args:
        dioptra_client: The Dioptra client.
        expected: The expected response from the API.
        group_id: The group ID used in query parameters.
        search: The search string used in query parameters.
        paging_info: The paging information used in query parameters.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """

    assert_retrieving_resource_works(
        dioptra_client=dioptra_client.tags,
        expected=expected,
        group_id=group_id,
        sort_by=sort_by,
        descending=descending,
        search=search,
        paging_info=paging_info,
    )


def assert_registering_existing_tag_name_fails(
    dioptra_client: DioptraClient[DioptraResponseProtocol], name: str, group_id: int
) -> None:
    """Assert that registering a tag with an existing name fails.

    Args:
        dioptra_client: The Dioptra client.
        name: The name to assign to the new tag.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = dioptra_client.tags.create(group_id=group_id, name=name)
    assert response.status_code == HTTPStatus.CONFLICT


def assert_tag_name_matches_expected_name(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    tag_id: int,
    expected_name: str,
) -> None:
    """Assert that the name of a tag matches the expected name.

    Args:
        dioptra_client: The Dioptra client.
        tag_id: The id of the tag to retrieve.
        expected_name: The expected name of the tag.

    Raises:
        AssertionError: If the response status code is not 200 or if the name of the
            tag does not match the expected name.
    """
    response = dioptra_client.tags.get_by_id(tag_id)
    assert (
        response.status_code == HTTPStatus.OK
        and response.json()["name"] == expected_name
    )


def assert_tag_is_not_found(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    tag_id: int,
) -> None:
    """Assert that a tag is not found.

    Args:
        dioptra_client: The Dioptra client.
        tag_id: The id of the tag to retrieve.

    Raises:
        AssertionError: If the response status code is not 404.
    """
    response = dioptra_client.tags.get_by_id(tag_id)
    assert response.status_code == HTTPStatus.NOT_FOUND


def assert_cannot_rename_tag_with_existing_name(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    tag_id: int,
    existing_name: str,
) -> None:
    """Assert that renaming a tag with an existing name fails.

    Args:
        dioptra_client: The Dioptra client.
        tag_id: The id of the tag to rename.
        name: The name of an existing tag.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = dioptra_client.tags.modify_by_id(tag_id=tag_id, name=existing_name)
    assert response.status_code == HTTPStatus.CONFLICT


# -- Tests -----------------------------------------------------------------------------


def test_create_tag(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    tag_response = dioptra_client.tags.create(
        group_id=group_id,
        name=name,
    )
    tag_expected = tag_response.json()

    assert_tag_response_contents_matches_expectations(
        response=tag_expected,
        expected_contents={
            "name": name,
            "user_id": user_id,
            "group_id": group_id,
        },
    )
    assert_retrieving_tag_by_id_works(
        dioptra_client, tag_id=tag_expected["id"], expected=tag_expected
    )


@pytest.mark.parametrize(
    "sort_by, descending , expected",
    [
        ("name", True, ["tag2", "tag1", "tag3"]),
        ("name", False, ["tag3", "tag1", "tag2"]),
        ("createdOn", True, ["tag3", "tag2", "tag1"]),
        ("createdOn", False, ["tag1", "tag2", "tag3"]),
    ],
)
def test_tag_sort(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_tags: dict[str, Any],
    sort_by: str | None,
    descending: bool,
    expected: list[str],
) -> None:
    """Test that tags can be sorted by column.

    Given an authenticated user and registered tags, this test validates the following
    sequence of actions:

    - A user registers three tags, "tag_one", "tag_two", "name".
    - The user is able to retrieve a list of all registered tags sorted by a column
      ascending/descending.
    - The returned list of tags matches the order in the parametrize lists above.
    """

    expected_tags = [registered_tags[expected_name] for expected_name in expected]
    assert_retrieving_tags_works(
        dioptra_client, sort_by=sort_by, descending=descending, expected=expected_tags
    )


def test_tag_search_query(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
        dioptra_client,
        expected=tag_expected_list,
        search="name:*tag*",
    )


def test_cannot_register_existing_tag_name(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
        dioptra_client, name=existing_tag["name"], group_id=existing_tag["group"]["id"]
    )


def test_rename_tag(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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

    dioptra_client.tags.modify_by_id(tag_id=tag_to_rename["id"], name=updated_tag_name)
    assert_tag_name_matches_expected_name(
        dioptra_client, tag_id=tag_to_rename["id"], expected_name=updated_tag_name
    )
    assert_cannot_rename_tag_with_existing_name(
        dioptra_client,
        tag_id=tag_to_rename["id"],
        existing_name=existing_tag["name"],
    )


def test_delete_tag_by_id(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
        dioptra_client, tag_id=tag_expected["id"], expected=tag_expected
    )
    dioptra_client.tags.delete_by_id(tag_id=tag_expected["id"])
    assert_tag_is_not_found(dioptra_client, tag_id=tag_expected["id"])
