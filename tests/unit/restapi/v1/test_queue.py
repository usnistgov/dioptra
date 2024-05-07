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
from __future__ import annotations

from typing import Any

import pytest
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from werkzeug.test import TestResponse

from dioptra.restapi.routes import V1_QUEUES_ROUTE, V1_ROOT

from ..lib import actions, helpers

# -- Actions ---------------------------------------------------------------------------


def modify_queue(
    client: FlaskClient,
    queue_id: int,
    new_name: str,
    new_description: str,
) -> TestResponse:
    """Rename a queue using the API.

    Args:
        client: The Flask test client.
        queue_id: The id of the queue to rename.
        new_name: The new name to assign to the queue.
        new_description: The new description to assign to the queue.

    Returns:
        The response from the API.
    """
    payload = {"name": new_name, "description": new_description}

    return client.put(
        f"/{V1_ROOT}/{V1_QUEUES_ROUTE}/{queue_id}",
        json=payload,
        follow_redirects=True,
    )


def delete_queue_with_id(
    client: FlaskClient,
    queue_id: int,
) -> TestResponse:
    """Delete a queue using the API.

    Args:
        client: The Flask test client.
        queue_id: The id of the queue to delete.

    Returns:
        The response from the API.
    """

    return client.delete(
        f"/{V1_ROOT}/{V1_QUEUES_ROUTE}/{queue_id}",
        follow_redirects=True,
    )


# -- Assertions ------------------------------------------------------------------------


def assert_queue_response_contents_matches_expectations(
    response: dict[str, Any], expected_contents: dict[str, Any]
) -> None:
    expected_keys = {
        "id",
        "snapshotId",
        "group",
        "user",
        "createdOn",
        "lastModifiedOn",
        "latestSnapshot",
        "name",
        "description",
        "tags",
    }
    assert set(response.keys()) == expected_keys

    # Validate the non-Ref fields
    assert isinstance(response["id"], int)
    assert isinstance(response["snapshotId"], int)
    assert isinstance(response["name"], str)
    assert isinstance(response["description"], str)
    assert isinstance(response["createdOn"], str)
    assert isinstance(response["lastModifiedOn"], str)
    assert isinstance(response["latestSnapshot"], bool)

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
    client: FlaskClient,
    queue_id: int,
    expected: dict[str, Any],
) -> None:
    """Assert that retrieving a queue by id works.

    Args:
        client: The Flask test client.
        queue_id: The id of the queue to retrieve.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = client.get(
        f"/{V1_ROOT}/{V1_QUEUES_ROUTE}/{queue_id}", follow_redirects=True
    )
    assert response.status_code == 200 and response.get_json() == expected


def assert_retrieving_queues_works(
    client: FlaskClient,
    expected: list[dict[str, Any]],
    group_id: int | None = None,
    search: str | None = None,
    paging_info: dict[str, Any] | None = None,
) -> None:
    """Assert that retrieving all queues works.

    Args:
        client: The Flask test client.
        expected: The expected response from the API.
        Q: The search query parameters.
        G: The group query parameters.
        P: The paging query parameters.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """

    query_string = {}
    if group_id is not None:
        query_string["groupId"] = group_id
    if search is not None:
        query_string["query"] = search
    if paging_info is not None:
        query_string["index"] = paging_info["index"]
        query_string["pageLength"] = paging_info["page_length"]

    response = client.get(
        f"/{V1_ROOT}/{V1_QUEUES_ROUTE}",
        query_string=query_string,
        follow_redirects=True,
    )
    assert response.status_code == 200 and response.get_json()["data"] == expected


def assert_registering_existing_queue_name_fails(
    client: FlaskClient, name: str, group_id: int
) -> None:
    """Assert that registering a queue with an existing name fails.

    Args:
        client: The Flask test client.
        name: The name to assign to the new queue.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = actions.register_queue(client, name=name, group_id=group_id)
    assert response.status_code == 400


def assert_queue_name_matches_expected_name(
    client: FlaskClient, queue_id: int, expected_name: str
) -> None:
    """Assert that the name of a queue matches the expected name.

    Args:
        client: The Flask test client.
        queue_id: The id of the queue to retrieve.
        expected_name: The expected name of the queue.

    Raises:
        AssertionError: If the response status code is not 200 or if the name of the
            queue does not match the expected name.
    """
    response = client.get(
        f"/{V1_ROOT}/{V1_QUEUES_ROUTE}/{queue_id}",
        follow_redirects=True,
    )
    assert response.status_code == 200 and response.get_json()["name"] == expected_name


def assert_queue_is_not_found(
    client: FlaskClient,
    queue_id: int,
) -> None:
    """Assert that a queue is not found.

    Args:
        client: The Flask test client.
        queue_id: The id of the queue to retrieve.

    Raises:
        AssertionError: If the response status code is not 404.
    """
    response = client.get(
        f"/{V1_ROOT}/{V1_QUEUES_ROUTE}/{queue_id}",
        follow_redirects=True,
    )
    assert response.status_code == 404


def assert_queue_count_matches_expected_count(
    client: FlaskClient,
    expected: int,
) -> None:
    """Assert that the number of queues matches the expected number.

    Args:
        client: The Flask test client.
        expected: The expected number of queues.

    Raises:
        AssertionError: If the response status code is not 200 or if the number of
            queues does not match the expected number.
    """
    response = client.get(
        f"/{V1_ROOT}/{V1_QUEUES_ROUTE}",
        follow_redirects=True,
    )
    assert len(response.get_json()["data"]) == expected


def assert_cannot_rename_queue_with_existing_name(
    client: FlaskClient,
    queue_id: int,
    existing_name: str,
    existing_description: str,
) -> None:
    """Assert that renaming a queue with an existing name fails.
    Args:
        client: The Flask test client.
        queue_id: The id of the queue to rename.
        name: The name of an existing queue.
    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = modify_queue(
        client=client,
        queue_id=queue_id,
        new_name=existing_name,
        new_description=existing_description,
    )
    assert response.status_code == 400


# -- Tests -----------------------------------------------------------------------------


@pytest.mark.v1
def test_create_queue(
    client: FlaskClient,
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
    user_id = auth_account["user_id"]
    group_id = auth_account["default_group_id"]
    queue1_response = actions.register_queue(
        client, name=name, description=description, group_id=group_id
    )
    queue1_expected = queue1_response.get_json()
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
        client, queue_id=queue1_expected["queueId"], expected=queue1_expected
    )


@pytest.mark.v1
def test_queue_get_all(
    client: FlaskClient,
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
    queue1_expected = registered_queues["queue1"]
    queue2_expected = registered_queues["queue2"]
    queue3_expected = registered_queues["queue3"]
    queue_expected_list = [queue1_expected, queue2_expected, queue3_expected]

    assert_retrieving_queues_works(client, expected=queue_expected_list)


@pytest.mark.v1
def test_queue_search_query(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_queues: dict[str, Any],
) -> None:
    """Test that queues can be queried with a search term.

    Given an authenticated user and registered queues, this test validates the following
        sequence of actions:

    - The user is able to retrieve a list of all registered queues with a description
      that contains 'queue'.
    - The returned list of queues matches the expected matches from the query.
    """
    queue1_expected = registered_queues["queue1"]
    queue2_expected = registered_queues["queue2"]
    queue_expected_list = [queue1_expected, queue2_expected]

    assert_retrieving_queues_works(
        client,
        expected=queue_expected_list,
        search="description:*queue*",
    )


@pytest.mark.v1
def test_queue_group_query(
    client: FlaskClient,
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
    queue1_expected = registered_queues["queue1"]
    queue2_expected = registered_queues["queue2"]
    queue3_expected = registered_queues["queue3"]
    queue_expected_list = [queue1_expected, queue2_expected, queue3_expected]

    assert_retrieving_queues_works(
        client, expected=queue_expected_list, group_id=auth_account["default_group_id"]
    )


@pytest.mark.v1
def test_queue_id_get(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_queues: dict[str, Any],
) -> None:
    """Test that queues can be retrieved by their unique ID.

    Given an authenticated user and registered queues, this test validates the following
        sequence of actions:

    - The user is able to retrieve single queue by its ID.
    - The response is a single queue with a matching ID.
    """
    queue3_expected = registered_queues["queue3"]

    assert_retrieving_queue_by_id_works(
        client, queue_id=queue3_expected["queueId"], expected=queue3_expected
    )


@pytest.mark.v1
def test_cannot_register_existing_queue_name(
    client: FlaskClient,
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
        client,
        name=existing_queue["name"],
        group_id=existing_queue["group_id"],
    )


@pytest.mark.v1
def test_rename_queue(
    client: FlaskClient,
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
    - The user issues a request to change the name of a queue to an existing queue's
      name.
    - The request fails with an appropriate error message and response code.
    """
    updated_queue_name = "tensorflow_gpu"
    queue_to_rename = registered_queues["queue1"]
    existing_queue = registered_queues["queue2"]

    modify_queue(
        client,
        queue_id=queue_to_rename["queueId"],
        new_name=updated_queue_name,
        new_description=queue_to_rename["description"],
    )
    assert_queue_name_matches_expected_name(
        client, queue_id=queue_to_rename["queueId"], expected_name=updated_queue_name
    )
    assert_cannot_rename_queue_with_existing_name(
        client,
        queue_id=queue_to_rename["tagId"],
        existing_name=existing_queue["name"],
        existing_description=queue_to_rename["description"],
    )


@pytest.mark.v1
def test_delete_queue_by_id(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_queues: dict[str, Any],
) -> None:
    """Test that a queue can be deleted by referencing its id.

    This test validates the following sequence of actions:

    - The user deletes the "tensorflow_cpu" queue by referencing its id.
    - The user attempts to retrieve information about the queue and response indicates
      the queue is no longer found.
    """
    queue_to_delete = registered_queues["queue1"]

    delete_queue_with_id(client, queue_id=queue_to_delete["queueId"])
    assert_queue_is_not_found(client, queue_id=queue_to_delete["queueId"])
