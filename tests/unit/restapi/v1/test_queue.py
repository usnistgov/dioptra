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
"""Test suite for queue operations.

This module contains a set of tests that validate the CRUD operations and additional
functionalities for the queue entity. The tests ensure that the queues can be
registered, renamed, deleted, and locked/unlocked as expected through the REST API.
"""
from http import HTTPStatus
from typing import Any

import pytest
from flask_sqlalchemy import SQLAlchemy

from dioptra.client.base import DioptraResponseProtocol
from dioptra.client.client import DioptraClient

from ..lib import helpers, routines

# -- Assertions ------------------------------------------------------------------------


def assert_queue_response_contents_matches_expectations(
    response: dict[str, Any], expected_contents: dict[str, Any]
) -> None:
    """Assert that queue response contents is valid.

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
        "snapshot",
        "group",
        "user",
        "createdOn",
        "lastModifiedOn",
        "latestSnapshot",
        "hasDraft",
        "name",
        "description",
        "tags",
    }
    assert set(response.keys()) == expected_keys

    # Validate the non-Ref fields
    assert isinstance(response["id"], int)
    assert isinstance(response["snapshot"], int)
    assert isinstance(response["name"], str)
    assert isinstance(response["description"], str)
    assert isinstance(response["createdOn"], str)
    assert isinstance(response["lastModifiedOn"], str)
    assert isinstance(response["latestSnapshot"], bool)
    assert isinstance(response["hasDraft"], bool)

    assert response["name"] == expected_contents["name"]
    assert response["description"] == expected_contents["description"]

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

    # Validate the TagRef structure
    for tag in response["tags"]:
        assert isinstance(tag["id"], int)
        assert isinstance(tag["name"], str)
        assert isinstance(tag["url"], str)


def assert_retrieving_queue_by_id_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    queue_id: int,
    expected: dict[str, Any],
) -> None:
    """Assert that retrieving a queue by id works.

    Args:
        dioptra_client: The Dioptra client.
        queue_id: The id of the queue to retrieve.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = dioptra_client.queues.get_by_id(queue_id)
    assert response.status_code == HTTPStatus.OK and response.json() == expected


def assert_retrieving_queues_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    expected: list[dict[str, Any]],
    group_id: int | None = None,
    search: str | None = None,
    paging_info: dict[str, Any] | None = None,
) -> None:
    """Assert that retrieving all queues works.

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

    query_string: dict[str, Any] = {}

    if group_id is not None:
        query_string["group_id"] = group_id

    if search is not None:
        query_string["search"] = search

    if paging_info is not None:
        query_string["index"] = paging_info["index"]
        query_string["page_length"] = paging_info["page_length"]

    response = dioptra_client.queues.get(**query_string)
    assert response.status_code == HTTPStatus.OK and response.json()["data"] == expected


def assert_sorting_queue_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    expected: list[str],
    sort_by: str | None,
    descending: bool | None,
    group_id: int | None = None,
    search: str | None = None,
    paging_info: dict[str, Any] | None = None,
) -> None:
    """Assert that queues can be sorted by column ascending/descending.

    Args:
        client: The Flask test client.
        expected: The expected order of queue ids after sorting.
            See test_queue_sort for expected orders.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """

    query_string: dict[str, Any] = {}

    if descending is not None:
        query_string["descending"] = descending

    if sort_by is not None:
        query_string["sort_by"] = sort_by

    if group_id is not None:
        query_string["group_id"] = group_id

    if search is not None:
        query_string["search"] = search

    if paging_info is not None:
        query_string["index"] = paging_info["index"]
        query_string["page_length"] = paging_info["page_length"]

    response = dioptra_client.queues.get(**query_string)
    response_data = response.json()
    queue_ids = [queue["id"] for queue in response_data["data"]]
    assert response.status_code == HTTPStatus.OK and queue_ids == expected


def assert_registering_existing_queue_name_fails(
    dioptra_client: DioptraClient[DioptraResponseProtocol], name: str, group_id: int
) -> None:
    """Assert that registering a queue with an existing name fails.

    Args:
        dioptra_client: The Dioptra client.
        name: The name to assign to the new queue.

    Raises:
        AssertionError: If the response status code is not 409.
    """
    response = dioptra_client.queues.create(
        group_id=group_id, name=name, description=""
    )
    assert response.status_code == HTTPStatus.CONFLICT


def assert_queue_name_matches_expected_name(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    queue_id: int,
    expected_name: str,
) -> None:
    """Assert that the name of a queue matches the expected name.

    Args:
        dioptra_client: The Dioptra client.
        queue_id: The id of the queue to retrieve.
        expected_name: The expected name of the queue.

    Raises:
        AssertionError: If the response status code is not 200 or if the name of the
            queue does not match the expected name.
    """
    response = dioptra_client.queues.get_by_id(queue_id)
    assert (
        response.status_code == HTTPStatus.OK
        and response.json()["name"] == expected_name
    )


def assert_queue_is_not_found(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    queue_id: int,
) -> None:
    """Assert that a queue is not found.

    Args:
        dioptra_client: The Dioptra client.
        queue_id: The id of the queue to retrieve.

    Raises:
        AssertionError: If the response status code is not 404.
    """
    response = dioptra_client.queues.get_by_id(queue_id)
    assert response.status_code == HTTPStatus.NOT_FOUND


def assert_queue_is_not_associated_with_entrypoint(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    entrypoint_id: int,
    queue_id: int,
) -> None:
    """Assert that a queue is associated with an entrypoint

    Args:
        client: The Flask test client.
        entrypoint_id: The id of the entrypoint to retrieve.
        queue_id: The id of the queue to check for association.

    Raises:
        AssertionError: If the response status code is not 200 or if the queue id
            is in the list of queues associated with the entrypoint.
    """
    response = dioptra_client.entrypoints.get_by_id(entrypoint_id)
    entrypoint = response.json()
    queue_ids = set(queue["id"] for queue in entrypoint["queues"])
    assert response.status_code == HTTPStatus.OK and queue_id not in queue_ids


def assert_cannot_rename_queue_with_existing_name(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    queue_id: int,
    existing_name: str,
    existing_description: str,
) -> None:
    """Assert that renaming a queue with an existing name fails.

    Args:
        dioptra_client: The Dioptra client.
        queue_id: The id of the queue to rename.
        name: The name of an existing queue.

    Raises:
        AssertionError: If the response status code is not 409.
    """
    response = dioptra_client.queues.modify_by_id(
        queue_id=queue_id,
        name=existing_name,
        description=existing_description,
    )
    assert response.status_code == HTTPStatus.CONFLICT


# -- Tests -----------------------------------------------------------------------------


def test_create_queue(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
) -> None:
    """Test that queues can be correctly registered and retrieved using the API.

    Given an authenticated user, this test validates the following sequence of actions:

    - The user registers a queue named "tensorflow_cpu".
    - The response is valid matches the expected values given the registration request.
    - The user is able to retrieve information about the queue using the queue id.
    """
    name = "tensorflow_cpu"
    description = "The first queue."
    user_id = auth_account["id"]
    group_id = auth_account["groups"][0]["id"]
    queue1_response = dioptra_client.queues.create(
        group_id=group_id, name=name, description=description
    )
    queue1_expected = queue1_response.json()
    assert_queue_response_contents_matches_expectations(
        response=queue1_expected,
        expected_contents={
            "name": name,
            "description": description,
            "user_id": user_id,
            "group_id": group_id,
        },
    )
    assert_retrieving_queue_by_id_works(
        dioptra_client, queue_id=queue1_expected["id"], expected=queue1_expected
    )


def test_queue_get_all(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_queues: dict[str, Any],
) -> None:
    """Test that all queues can be retrieved.

    Given an authenticated user and registered queues, this test validates the following
    sequence of actions:

    - A user registers three queues, "tensorflow_cpu", "tensorflow_gpu", "pytorch_cpu".
    - The user is able to retrieve a list of all registered queues.
    - The returned list of queues matches the full list of registered queues.
    """
    queue_expected_list = list(registered_queues.values())
    assert_retrieving_queues_works(dioptra_client, expected=queue_expected_list)


@pytest.mark.parametrize(
    "sort_by,descending,expected",
    [
        (None, None, ["queue1", "queue2", "queue3"]),
        ("name", True, ["queue2", "queue1", "queue3"]),
        ("name", False, ["queue3", "queue1", "queue2"]),
        ("createdOn", True, ["queue3", "queue2", "queue1"]),
        ("createdOn", False, ["queue1", "queue2", "queue3"]),
    ],
)
def test_queue_sort(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_queues: dict[str, Any],
    sort_by: str | None,
    descending: bool,
    expected: list[str],
) -> None:
    """Test that queues can be sorted by column.

    Given an authenticated user and registered queues, this test validates the following
    sequence of actions:

    - A user registers three queues, "tensorflow_cpu", "tensorflow_gpu", "pytorch_cpu".
    - The user is able to retrieve a list of all registered queues sorted by a column
      ascending/descending.
    - The returned list of queues matches the order in the parametrize lists above.
    """

    expected_ids = [
        registered_queues[expected_name]["id"] for expected_name in expected
    ]
    assert_sorting_queue_works(
        dioptra_client, sort_by=sort_by, descending=descending, expected=expected_ids
    )


def test_queue_search_query(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_queues: dict[str, Any],
) -> None:
    """Test that queues can be queried with a search term.

    Given an authenticated user and registered queues, this test validates the following
    sequence of actions:

    - The user is able to retrieve a list of all registered queues with various queries.
    - The returned list of queues matches the expected matches from the query.
    """
    queue_expected_list = list(registered_queues.values())[:2]
    assert_retrieving_queues_works(
        dioptra_client, expected=queue_expected_list, search="description:*queue*"
    )
    assert_retrieving_queues_works(
        dioptra_client, expected=queue_expected_list, search="*queue*, name:tensorflow*"
    )
    queue_expected_list = list(registered_queues.values())
    assert_retrieving_queues_works(
        dioptra_client, expected=queue_expected_list, search="*"
    )


def test_queue_group_query(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_queues: dict[str, Any],
) -> None:
    """Test that queues can retrieved using a group filter.

    Given an authenticated user and registered queues, this test validates the following
    sequence of actions:

    - The user is able to retrieve a list of all registered queues that are owned by the
      default group.
    - The returned list of queues matches the expected list owned by the default group.
    """
    queue_expected_list = list(registered_queues.values())
    assert_retrieving_queues_works(
        dioptra_client,
        expected=queue_expected_list,
        group_id=auth_account["groups"][0]["id"],
    )


def test_cannot_register_existing_queue_name(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_queues: dict[str, Any],
) -> None:
    """Test that registering a queue with an existing name fails.

    Given an authenticated user and registered queues, this test validates the following
    sequence of actions:

    - The user attempts to register a second queue with the same name.
    - The request fails with an appropriate error message and response code.
    """
    existing_queue = registered_queues["queue1"]

    assert_registering_existing_queue_name_fails(
        dioptra_client,
        name=existing_queue["name"],
        group_id=existing_queue["group"]["id"],
    )


def test_rename_queue(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_queues: dict[str, Any],
) -> None:
    """Test that a queue can be renamed.

    Given an authenticated user and registered queues, this test validates the following
    sequence of actions:

    - The user issues a request to change the name of a queue.
    - The user retrieves information about the same queue and it reflects the name
      change.
    - The user issues a request to change the name of the queue to the existing name.
    - The user retrieves information about the same queue and verifies the name remains
      unchanged.
    - The user issues a request to change the name of a queue to an existing queue's
      name.
    - The request fails with an appropriate error message and response code.
    """
    updated_queue_name = "tensorflow_tpu"
    queue_to_rename = registered_queues["queue1"]
    existing_queue = registered_queues["queue2"]

    modified_queue = dioptra_client.queues.modify_by_id(
        queue_id=queue_to_rename["id"],
        name=updated_queue_name,
        description=queue_to_rename["description"],
    ).json()
    assert_queue_name_matches_expected_name(
        dioptra_client, queue_id=queue_to_rename["id"], expected_name=updated_queue_name
    )
    queue_expected_list = [
        modified_queue,
        registered_queues["queue2"],
        registered_queues["queue3"],
    ]
    assert_retrieving_queues_works(dioptra_client, expected=queue_expected_list)

    modified_queue = dioptra_client.queues.modify_by_id(
        queue_id=queue_to_rename["id"],
        name=updated_queue_name,
        description=queue_to_rename["description"],
    ).json()
    assert_queue_name_matches_expected_name(
        dioptra_client, queue_id=queue_to_rename["id"], expected_name=updated_queue_name
    )

    assert_cannot_rename_queue_with_existing_name(
        dioptra_client,
        queue_id=queue_to_rename["id"],
        existing_name=existing_queue["name"],
        existing_description=queue_to_rename["description"],
    )


def test_delete_queue_by_id(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_queues: dict[str, Any],
    registered_entrypoints: dict[str, Any],
) -> None:
    """Test that a queue can be deleted by referencing its id.

    Given an authenticated user and registered queues, this test validates the following
    sequence of actions:

    - The user deletes a queue by referencing its id.
    - The user attempts to retrieve information about the deleted queue.
    - The request fails with an appropriate error message and response code.
    - The queue is no longer associated with the entrypoint.
    """
    entrypoint = registered_entrypoints["entrypoint1"]
    queue_to_delete = entrypoint["queues"][0]

    dioptra_client.queues.delete_by_id(queue_to_delete["id"])
    assert_queue_is_not_found(dioptra_client, queue_id=queue_to_delete["id"])
    assert_queue_is_not_associated_with_entrypoint(
        dioptra_client, entrypoint_id=entrypoint["id"], queue_id=queue_to_delete["id"]
    )


def test_manage_existing_queue_draft(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_queues: dict[str, Any],
) -> None:
    """Test that a draft of an existing queue can be created and managed by the user

    Given an authenticated user and registered queues, this test validates the following
    sequence of actions:

    - The user creates a draft of an existing queue
    - The user retrieves information about the draft and gets the expected response
    - The user attempts to create another draft of the same existing queue
    - The request fails with an appropriate error message and response code.
    - The user modifies the name of the queue in the draft
    - The user retrieves information about the draft and gets the expected response
    - The user deletes the draft
    - The user attempts to retrieve information about the deleted draft.
    - The request fails with an appropriate error message and response code.
    """
    # Requests data
    queue = registered_queues["queue1"]
    name = "draft"
    new_name = "draft2"
    description = "description"

    # test creation
    draft = {"name": name, "description": description}
    draft_mod = {"name": new_name, "description": description}

    # Expected responses
    draft_expected = {
        "user_id": auth_account["id"],
        "group_id": queue["group"]["id"],
        "resource_id": queue["id"],
        "resource_snapshot_id": queue["snapshot"],
        "num_other_drafts": 0,
        "payload": draft,
    }
    draft_mod_expected = {
        "user_id": auth_account["id"],
        "group_id": queue["group"]["id"],
        "resource_id": queue["id"],
        "resource_snapshot_id": queue["snapshot"],
        "num_other_drafts": 0,
        "payload": draft_mod,
    }

    # Run routine: existing resource drafts tests
    routines.run_existing_resource_drafts_tests(
        dioptra_client.queues.modify_resource_drafts,
        queue["id"],
        draft=draft,
        draft_mod=draft_mod,
        draft_expected=draft_expected,
        draft_mod_expected=draft_mod_expected,
    )


def test_manage_new_queue_drafts(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
) -> None:
    """Test that drafts of queue can be created and managed by the user

    Given an authenticated user, this test validates the following sequence of actions:

    - The user creates two queue drafts
    - The user retrieves information about the drafts and gets the expected response
    - The user modifies the description of the queue in the first draft
    - The user retrieves information about the draft and gets the expected response
    - The user deletes the first draft
    - The user attempts to retrieve information about the deleted draft.
    - The request fails with an appropriate error message and response code.
    """
    # Requests data
    group_id = auth_account["groups"][0]["id"]
    drafts: dict[str, Any] = {
        "draft1": {"name": "queue1", "description": "new queue"},
        "draft2": {"name": "queue2", "description": None},
    }
    draft1_mod = {"name": "draft1", "description": "new description"}

    # Expected responses
    draft1_expected = {
        "user_id": auth_account["id"],
        "group_id": group_id,
        "payload": drafts["draft1"],
    }
    draft2_expected = {
        "user_id": auth_account["id"],
        "group_id": group_id,
        "payload": drafts["draft2"],
    }
    draft1_mod_expected = {
        "user_id": auth_account["id"],
        "group_id": group_id,
        "payload": draft1_mod,
    }

    # Run routine: existing resource drafts tests
    routines.run_new_resource_drafts_tests(
        dioptra_client.queues.new_resource_drafts,
        drafts=drafts,
        draft1_mod=draft1_mod,
        draft1_expected=draft1_expected,
        draft2_expected=draft2_expected,
        draft1_mod_expected=draft1_mod_expected,
        group_id=group_id,
    )


def test_manage_queue_snapshots(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_queues: dict[str, Any],
) -> None:
    """Test that different snapshots of a queue can be retrieved by the user.

    Given an authenticated user and registered queues, this test validates the following
    sequence of actions:

    - The user modifies a queue
    - The user retrieves information about the original snapshot of the queue and gets
      the expected response
    - The user retrieves information about the new snapshot of the queue and gets the
      expected response
    - The user retrieves a list of all snapshots of the queue and gets the expected
      response
    """
    queue_to_rename = registered_queues["queue1"]
    modified_queue = dioptra_client.queues.modify_by_id(
        queue_id=queue_to_rename["id"],
        name=queue_to_rename["name"] + "modified",
        description=queue_to_rename["description"],
    ).json()

    # Run routine: resource snapshots tests
    routines.run_resource_snapshots_tests(
        dioptra_client.queues.snapshots,
        resource_to_rename=queue_to_rename.copy(),
        modified_resource=modified_queue.copy(),
    )


def test_tag_queue(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_queues: dict[str, Any],
    registered_tags: dict[str, Any],
) -> None:
    """Test that tags can applied to queues.

    Given an authenticated user and registered queues, this test validates the following
    sequence of actions:

    """
    queue = registered_queues["queue1"]
    tag_ids = [tag["id"] for tag in registered_tags.values()]

    # Run routine: resource tag tests
    routines.run_resource_tag_tests(
        dioptra_client.queues.tags,
        queue["id"],
        tag_ids=tag_ids,
    )
