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
from typing import Any

from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from werkzeug.test import TestResponse

from dioptra.restapi.routes import V1_ENTRYPOINTS_ROUTE, V1_QUEUES_ROUTE, V1_ROOT

from ..lib import actions, asserts, helpers

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
    response = actions.register_queue(
        client, name=name, description="", group_id=group_id
    )
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


def assert_queue_is_not_associated_with_entrypoint(
    client: FlaskClient,
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
    response = client.get(
        f"/{V1_ROOT}/{V1_ENTRYPOINTS_ROUTE}/{entrypoint_id}",
        follow_redirects=True,
    )
    entrypoint = response.get_json()
    queue_ids = set(queue["id"] for queue in entrypoint["queues"])

    assert response.status_code == 200 and queue_id not in queue_ids


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
    user_id = auth_account["id"]
    group_id = auth_account["groups"][0]["id"]
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
        client, queue_id=queue1_expected["id"], expected=queue1_expected
    )


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
    queue_expected_list = list(registered_queues.values())
    assert_retrieving_queues_works(client, expected=queue_expected_list)


def test_queue_search_query(
    client: FlaskClient,
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
        client, expected=queue_expected_list, search="description:*queue*"
    )
    assert_retrieving_queues_works(
        client, expected=queue_expected_list, search="*queue*, name:tensorflow*"
    )
    queue_expected_list = list(registered_queues.values())
    assert_retrieving_queues_works(client, expected=queue_expected_list, search="*")


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
    queue_expected_list = list(registered_queues.values())
    assert_retrieving_queues_works(
        client,
        expected=queue_expected_list,
        group_id=auth_account["groups"][0]["id"],
    )


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
        group_id=existing_queue["group"]["id"],
    )


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

    modified_queue = modify_queue(
        client,
        queue_id=queue_to_rename["id"],
        new_name=updated_queue_name,
        new_description=queue_to_rename["description"],
    ).get_json()
    assert_queue_name_matches_expected_name(
        client, queue_id=queue_to_rename["id"], expected_name=updated_queue_name
    )
    queue_expected_list = [
        modified_queue,
        registered_queues["queue2"],
        registered_queues["queue3"],
    ]
    assert_retrieving_queues_works(client, expected=queue_expected_list)

    modified_queue = modify_queue(
        client,
        queue_id=queue_to_rename["id"],
        new_name=updated_queue_name,
        new_description=queue_to_rename["description"],
    ).get_json()
    assert_queue_name_matches_expected_name(
        client, queue_id=queue_to_rename["id"], expected_name=updated_queue_name
    )

    assert_cannot_rename_queue_with_existing_name(
        client,
        queue_id=queue_to_rename["id"],
        existing_name=existing_queue["name"],
        existing_description=queue_to_rename["description"],
    )


def test_delete_queue_by_id(
    client: FlaskClient,
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

    delete_queue_with_id(client, queue_id=queue_to_delete["id"])
    assert_queue_is_not_found(client, queue_id=queue_to_delete["id"])
    assert_queue_is_not_associated_with_entrypoint(
        client, entrypoint_id=entrypoint["id"], queue_id=queue_to_delete["id"]
    )


def test_manage_existing_queue_draft(
    client: FlaskClient,
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
    queue = registered_queues["queue1"]
    name = "draft"
    new_name = "draft2"
    description = "description"

    # test creation
    payload = {"name": name, "description": description}
    expected = {
        "user_id": auth_account["id"],
        "group_id": queue["group"]["id"],
        "resource_id": queue["id"],
        "resource_snapshot_id": queue["snapshot"],
        "num_other_drafts": 0,
        "payload": payload,
    }
    response = actions.create_existing_resource_draft(
        client, resource_route=V1_QUEUES_ROUTE, resource_id=queue["id"], payload=payload
    ).get_json()
    asserts.assert_draft_response_contents_matches_expectations(response, expected)
    asserts.assert_retrieving_draft_by_resource_id_works(
        client,
        resource_route=V1_QUEUES_ROUTE,
        resource_id=queue["id"],
        expected=response,
    )
    asserts.assert_creating_another_existing_draft_fails(
        client, resource_route=V1_QUEUES_ROUTE, resource_id=queue["id"]
    )

    # test modification
    payload = {"name": new_name, "description": description}
    expected = {
        "user_id": auth_account["id"],
        "group_id": queue["group"]["id"],
        "resource_id": queue["id"],
        "resource_snapshot_id": queue["snapshot"],
        "num_other_drafts": 0,
        "payload": payload,
    }
    response = actions.modify_existing_resource_draft(
        client,
        resource_route=V1_QUEUES_ROUTE,
        resource_id=queue["id"],
        payload=payload,
    ).get_json()
    asserts.assert_draft_response_contents_matches_expectations(response, expected)

    # test deletion
    actions.delete_existing_resource_draft(
        client, resource_route=V1_QUEUES_ROUTE, resource_id=queue["id"]
    )
    asserts.assert_existing_draft_is_not_found(
        client, resource_route=V1_QUEUES_ROUTE, resource_id=queue["id"]
    )


def test_manage_new_queue_drafts(
    client: FlaskClient,
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
    group_id = auth_account["groups"][0]["id"]
    drafts = {
        "draft1": {"name": "queue1", "description": "new queue"},
        "draft2": {"name": "queue2", "description": None},
    }

    # test creation
    draft1_expected = {
        "user_id": auth_account["id"],
        "group_id": group_id,
        "payload": drafts["draft1"],
    }
    draft1_response = actions.create_new_resource_draft(
        client,
        resource_route=V1_QUEUES_ROUTE,
        group_id=group_id,
        payload=drafts["draft1"],
    ).get_json()
    asserts.assert_draft_response_contents_matches_expectations(
        draft1_response, draft1_expected
    )
    asserts.assert_retrieving_draft_by_id_works(
        client,
        resource_route=V1_QUEUES_ROUTE,
        draft_id=draft1_response["id"],
        expected=draft1_response,
    )
    draft2_expected = {
        "user_id": auth_account["id"],
        "group_id": group_id,
        "payload": drafts["draft2"],
    }
    draft2_response = actions.create_new_resource_draft(
        client,
        resource_route=V1_QUEUES_ROUTE,
        group_id=group_id,
        payload=drafts["draft2"],
    ).get_json()
    asserts.assert_draft_response_contents_matches_expectations(
        draft2_response, draft2_expected
    )
    asserts.assert_retrieving_draft_by_id_works(
        client,
        resource_route=V1_QUEUES_ROUTE,
        draft_id=draft2_response["id"],
        expected=draft2_response,
    )
    asserts.assert_retrieving_drafts_works(
        client,
        resource_route=V1_QUEUES_ROUTE,
        expected=[draft1_response, draft2_response],
    )

    # test modification
    draft1_mod = {"name": "draft1", "description": "new description"}
    draft1_mod_expected = {
        "user_id": auth_account["id"],
        "group_id": group_id,
        "payload": draft1_mod,
    }
    response = actions.modify_new_resource_draft(
        client,
        resource_route=V1_QUEUES_ROUTE,
        draft_id=draft1_response["id"],
        payload=draft1_mod,
    ).get_json()
    asserts.assert_draft_response_contents_matches_expectations(
        response, draft1_mod_expected
    )

    # test deletion
    actions.delete_new_resource_draft(
        client, resource_route=V1_QUEUES_ROUTE, draft_id=draft1_response["id"]
    )
    asserts.assert_new_draft_is_not_found(
        client, resource_route=V1_QUEUES_ROUTE, draft_id=draft1_response["id"]
    )


def test_manage_queue_snapshots(
    client: FlaskClient,
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
    modified_queue = modify_queue(
        client,
        queue_id=queue_to_rename["id"],
        new_name=queue_to_rename["name"] + "modified",
        new_description=queue_to_rename["description"],
    ).get_json()
    modified_queue.pop("hasDraft")
    queue_to_rename.pop("hasDraft")
    queue_to_rename["latestSnapshot"] = False
    queue_to_rename["lastModifiedOn"] = modified_queue["lastModifiedOn"]
    asserts.assert_retrieving_snapshot_by_id_works(
        client,
        resource_route=V1_QUEUES_ROUTE,
        resource_id=queue_to_rename["id"],
        snapshot_id=queue_to_rename["snapshot"],
        expected=queue_to_rename,
    )
    asserts.assert_retrieving_snapshot_by_id_works(
        client,
        resource_route=V1_QUEUES_ROUTE,
        resource_id=modified_queue["id"],
        snapshot_id=modified_queue["snapshot"],
        expected=modified_queue,
    )
    expected_snapshots = [queue_to_rename, modified_queue]
    asserts.assert_retrieving_snapshots_works(
        client,
        resource_route=V1_QUEUES_ROUTE,
        resource_id=queue_to_rename["id"],
        expected=expected_snapshots,
    )


def test_tag_queue(
    client: FlaskClient,
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
    tags = [tag["id"] for tag in registered_tags.values()]

    # test append
    response = actions.append_tags(
        client,
        resource_route=V1_QUEUES_ROUTE,
        resource_id=queue["id"],
        tag_ids=[tags[0], tags[1]],
    )
    asserts.assert_tags_response_contents_matches_expectations(
        response.get_json(), [tags[0], tags[1]]
    )
    response = actions.append_tags(
        client,
        resource_route=V1_QUEUES_ROUTE,
        resource_id=queue["id"],
        tag_ids=[tags[1], tags[2]],
    )
    asserts.assert_tags_response_contents_matches_expectations(
        response.get_json(), [tags[0], tags[1], tags[2]]
    )

    # test remove
    actions.remove_tag(
        client, resource_route=V1_QUEUES_ROUTE, resource_id=queue["id"], tag_id=tags[1]
    )
    response = actions.get_tags(
        client, resource_route=V1_QUEUES_ROUTE, resource_id=queue["id"]
    )
    asserts.assert_tags_response_contents_matches_expectations(
        response.get_json(), [tags[0], tags[2]]
    )

    # test modify
    response = actions.modify_tags(
        client,
        resource_route=V1_QUEUES_ROUTE,
        resource_id=queue["id"],
        tag_ids=[tags[1], tags[2]],
    )
    asserts.assert_tags_response_contents_matches_expectations(
        response.get_json(), [tags[1], tags[2]]
    )

    # test delete
    response = actions.remove_tags(
        client, resource_route=V1_QUEUES_ROUTE, resource_id=queue["id"]
    )
    response = actions.get_tags(
        client, resource_route=V1_QUEUES_ROUTE, resource_id=queue["id"]
    )
    asserts.assert_tags_response_contents_matches_expectations(response.get_json(), [])
