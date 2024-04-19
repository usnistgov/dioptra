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

from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from werkzeug.test import TestResponse

from dioptra.restapi.routes import QUEUE_ROUTE, V1_ROOT
from dioptra.restapi.utils import slugify

# -- Actions ---------------------------------------------------------------------------


def register_queue(
    client: FlaskClient,
    name: str,
    group_id: int | None,
    description: str | None,
) -> TestResponse:
    """Register a queue using the API.

    Args:
        client: The Flask test client.
        name: The name to assign to the new queue.
        group_id: The group to create the new queue in.
        description: The description of the new queue.

    Returns:
        The response from the API.
    """

    payload = {"name": name}

    if description:
        payload["description"] = description
    if group_id:
        payload["group_id"] = group_id

    return client.post(
        f"/{V1_ROOT}/{QUEUE_ROUTE}/",
        json=payload,
        follow_redirects=True,
    )


def rename_queue(
    client: FlaskClient,
    queue_id: int,
    new_name: str,
    new_description: str | None,
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
    payload = {"name": new_name}
    if new_description:
        payload["description"] = new_description

    return client.put(
        f"/{V1_ROOT}/{QUEUE_ROUTE}/{queue_id}",
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
        f"/{V1_ROOT}/{QUEUE_ROUTE}/{queue_id}",
        follow_redirects=True,
    )


# -- Assertions ------------------------------------------------------------------------


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
    response = client.get(f"/{V1_ROOT}/{QUEUE_ROUTE}/{queue_id}", follow_redirects=True)
    assert response.status_code == 200 and response.get_json() == expected


# TODO handle Q,G,P
def assert_retrieving_all_queues_works(
    client: FlaskClient,
    expected: list[dict[str, Any]],
    Q: dict[str, Any],
    G: dict[str, Any],
    P: dict[str, Any],
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

    payload = {}

    if Q:
        payload.update(Q)
    if G:
        payload.update(G)
    if P:
        payload.update(P)

    response = client.get(
        f"/{V1_ROOT}/{QUEUE_ROUTE}", payload=payload, follow_redirects=True
    )
    assert response.status_code == 200 and response.get_json()["data"] == expected


def assert_registering_existing_queue_name_fails(
    client: FlaskClient, name: str
) -> None:
    """Assert that registering a queue with an existing name fails.

    Args:
        client: The Flask test client.
        name: The name to assign to the new queue.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = register_queue(client, name=name)
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
        f"/{V1_ROOT}/{QUEUE_ROUTE}/{queue_id}",
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
        f"/{V1_ROOT}/{QUEUE_ROUTE}/{queue_id}",
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
        f"/{V1_ROOT}/{QUEUE_ROUTE}",
        follow_redirects=True,
    )
    assert len(response.get_json()["data"]) == expected


# -- Tests -----------------------------------------------------------------------------


def test_queue_registration(client: FlaskClient, db: SQLAlchemy) -> None:
    """Test that queues can be registered and retrieved using the API.

    This test validates the following sequence of actions:

    - A user registers two queues, "tensorflow_cpu" and "tensorflow_gpu".
    - The user is able to retrieve information about each queue using either the
      queue id or the unique queue name.
    - The user is able to retrieve a list of all registered queues.
    - In all cases, the returned information matches the information that was provided
      during registration.
    """
    queue1_response = register_queue(
        client, name="tensorflow_cpu", description="The first queue.", group_id=1
    )
    queue2_response = register_queue(
        client, name="pytorch_cpu", description="The second queue.", group_id=1
    )
    queue1_expected = queue1_response.get_json()
    queue2_expected = queue2_response.get_json()
    queue_expected_list = [queue1_expected, queue2_expected]
    assert_retrieving_queue_by_id_works(
        client, queue_id=queue1_expected["queueId"], expected=queue1_expected
    )

    assert_retrieving_queue_by_id_works(
        client, queue_id=queue2_expected["queueId"], expected=queue2_expected
    )

    assert_retrieving_all_queues_works(client, expected=queue_expected_list)


def test_queue_search_query(client: FlaskClient, db: SQLAlchemy) -> None:
    """Test that queues can be registered and retrieved using the API  with search terms.

    This test validates the following sequence of actions:

    - A user registers three queues, "tensorflow_cpu", "tensorflow_gpu", "pytorch_cpu".
    - The user is able to retrieve a list of all registered queues with a description
      that contains 'queue'.
    - In all cases, the returned information matches the information that was provided
      during registration.
    """
    queue1_response = register_queue(
        client, name="tensorflow_cpu", description="The first queue.", group_id=1
    )
    queue2_response = register_queue(
        client, name="tensorflow_gpu", description="The second queue.", group_id=1
    )

    queue3_response = register_queue(
        client, name="pytorch_cpu", description="Not retrieved.", group_id=1
    )

    queue1_expected = queue1_response.get_json()
    queue2_expected = queue2_response.get_json()
    queue3_expected = queue3_response.get_json()

    queue_expected_list = [queue1_expected, queue2_expected]

    assert_retrieving_queue_by_id_works(
        client, queue_id=queue3_response["queueId"], expected=queue3_expected
    )

    # TODO the query field must be updated when the grammar for searches is updated.
    search_parameters = {"query": "*queue*", "field": "description"}

    assert_retrieving_all_queues_works(
        client, expected=queue_expected_list, Q=search_parameters
    )


def test_queue_group_query(client: FlaskClient, db: SQLAlchemy) -> None:
    """Test that queues can be registered and retrieved using the API  with search terms.

    This test validates the following sequence of actions:

    - A user registers three queues, "tensorflow_cpu", "tensorflow_gpu", "pytorch_cpu".
    - The user is able to retrieve a list of all registered queues with a description
      that are part of group 1.
    - In all cases, the returned information matches the information that was provided
      during registration.
    """
    queue1_response = register_queue(
        client, name="tensorflow_cpu", description="The first queue.", group_id=1
    )
    queue2_response = register_queue(
        client, name="tensorflow_gpu", description="The second queue.", group_id=1
    )
    queue3_response = register_queue(
        client, name="pytorch_cpu", description="Not retrieved.", group_id=2
    )

    queue1_expected = queue1_response.get_json()
    queue2_expected = queue2_response.get_json()
    queue3_expected = queue3_response.get_json()

    queue_expected_list = [queue1_expected, queue2_expected]

    assert_retrieving_queue_by_id_works(
        client, queue_id=queue3_response["queueId"], expected=queue3_expected
    )

    search_parameters = {"group_id": 1}

    assert_retrieving_all_queues_works(
        client, expected=queue_expected_list, G=search_parameters
    )


def test_cannot_register_existing_queue_name(
    client: FlaskClient, db: SQLAlchemy
) -> None:
    """Test that registering a queue with an existing name fails.

    This test validates the following sequence of actions:

    - A user registers a queue named "tensorflow_cpu".
    - The user attempts to register a second queue with the same name, which fails.
    """
    queue_name = "tensorflow_cpu"
    register_queue(client, name="tensorflow_cpu")
    assert_registering_existing_queue_name_fails(client, name=queue_name)


def test_rename_queue(client: FlaskClient, db: SQLAlchemy) -> None:
    """Test that a queue can be renamed.

    This test validates the following sequence of actions:

    - A user registers a queue named "tensorflow_cpu".
    - The user is able to retrieve information about the "tensorflow_cpu" queue that
      matches the information that was provided during registration.
    - The user renames this same queue to "tensorflow_gpu".
    - The user retrieves information about the same queue and it reflects the name
      change.
    """
    queue_name = "tensorflow_cpu"
    updated_queue_name = "tensorflow_gpu"
    registration_response = register_queue(client, name=queue_name)
    queue_json = registration_response.get_json()
    assert_queue_name_matches_expected_name(
        client, queue_id=queue_json["queueId"], expected_name=queue_name
    )
    rename_queue(client, queue_id=queue_json["queueId"], new_name=updated_queue_name)
    assert_queue_name_matches_expected_name(
        client, queue_id=queue_json["queueId"], expected_name=updated_queue_name
    )


def test_delete_queue_by_id(client: FlaskClient, db: SQLAlchemy) -> None:
    """Test that a queue can be deleted by referencing its id.

    This test validates the following sequence of actions:

    - A user registers a queue named "tensorflow_cpu".
    - The user is able to retrieve information about the "tensorflow_cpu" queue that
      matches the information that was provided during registration.
    - The user deletes the "tensorflow_cpu" queue by referencing its id.
    - The user attempts to retrieve information about the "tensorflow_cpu" queue, which
      is no longer found.
    """
    queue_name = "tensorflow_cpu"
    registration_response = register_queue(client, name=queue_name)
    queue_json = registration_response.get_json()
    assert_retrieving_queue_by_id_works(
        client, queue_id=queue_json["queueId"], expected=queue_json
    )
    delete_queue_with_id(client, queue_id=queue_json["queueId"])
    assert_queue_is_not_found(client, queue_id=queue_json["queueId"])
