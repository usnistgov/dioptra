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

from dioptra.restapi.queue.routes import BASE_ROUTE as QUEUE_BASE_ROUTE

# -- Actions ---------------------------------------------------------------------------


def register_queue(client: FlaskClient, name: str) -> TestResponse:
    """Register a queue using the API.

    Args:
        client: The Flask test client.
        name: The name to assign to the new queue.

    Returns:
        The response from the API.
    """
    return client.post(
        f"/api/{QUEUE_BASE_ROUTE}/",
        json={"name": name},
        follow_redirects=True,
    )


def rename_queue(
    client: FlaskClient,
    queue_id: int,
    new_name: str,
) -> TestResponse:
    """Rename a queue using the API.

    Args:
        client: The Flask test client.
        queue_id: The id of the queue to rename.
        new_name: The new name to assign to the queue.

    Returns:
        The response from the API.
    """
    return client.put(
        f"/api/{QUEUE_BASE_ROUTE}/{queue_id}",
        json={"name": new_name},
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
        f"/api/{QUEUE_BASE_ROUTE}/{queue_id}",
        follow_redirects=True,
    )


def delete_queue_with_name(
    client: FlaskClient,
    name: str,
) -> TestResponse:
    """Delete a queue using the API.

    Args:
        client: The Flask test client.
        name: The name of the queue to delete.

    Returns:
        The response from the API.
    """
    return client.delete(
        f"/api/{QUEUE_BASE_ROUTE}/name/{name}",
        follow_redirects=True,
    )


def lock_queue_with_id(
    client: FlaskClient,
    queue_id: int,
) -> TestResponse:
    """Lock a queue using the API.

    Args:
        client: The Flask test client.
        queue_id: The id of the queue to lock.

    Returns:
        The response from the API.
    """
    return client.put(
        f"/api/{QUEUE_BASE_ROUTE}/{queue_id}/lock",
        follow_redirects=True,
    )


def lock_queue_with_name(
    client: FlaskClient,
    name: str,
) -> TestResponse:
    """Lock a queue using the API.

    Args:
        client: The Flask test client.
        name: The name of the queue to lock.

    Returns:
        The response from the API.
    """
    return client.put(
        f"/api/{QUEUE_BASE_ROUTE}/name/{name}/lock",
        follow_redirects=True,
    )


def unlock_queue_with_id(
    client: FlaskClient,
    queue_id: int,
) -> TestResponse:
    """Unlock a queue using the API.

    Args:
        client: The Flask test client.
        queue_id: The id of the queue to unlock.

    Returns:
        The response from the API.
    """
    return client.delete(
        f"/api/{QUEUE_BASE_ROUTE}/{queue_id}/lock",
        follow_redirects=True,
    )


def unlock_queue_with_name(
    client: FlaskClient,
    name: str,
) -> TestResponse:
    """Unlock a queue using the API.

    Args:
        client: The Flask test client.
        name: The name of the queue to unlock.

    Returns:
        The response from the API.
    """
    return client.delete(
        f"/api/{QUEUE_BASE_ROUTE}/name/{name}/lock",
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
    response = client.get(f"/api/{QUEUE_BASE_ROUTE}/{queue_id}", follow_redirects=True)
    assert response.status_code == 200 and response.get_json() == expected


def assert_retrieving_queue_by_name_works(
    client: FlaskClient,
    queue_name: str,
    expected: dict[str, Any],
) -> None:
    """Assert that retrieving a queue by name works.

    Args:
        client: The Flask test client.
        queue_name: The name of the queue to retrieve.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = client.get(
        f"/api/{QUEUE_BASE_ROUTE}/name/{queue_name}", follow_redirects=True
    )
    assert response.status_code == 200 and response.get_json() == expected


def assert_retrieving_all_queues_works(
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
    response = client.get(f"/api/{QUEUE_BASE_ROUTE}", follow_redirects=True)
    assert response.status_code == 200 and response.get_json() == expected


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
        f"/api/{QUEUE_BASE_ROUTE}/{queue_id}",
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
        f"/api/{QUEUE_BASE_ROUTE}/{queue_id}",
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
        f"/api/{QUEUE_BASE_ROUTE}",
        follow_redirects=True,
    )
    assert len(response.get_json()) == expected


def assert_page_data_matches(
    client: FlaskClient, index: int, page_length: int, expected: list[dict[str, Any]]
) -> None:
    """Assert that the returned page matches the expected page.
    Args:
        client: The Flask test client.
        expected: The expected page.
    Raises:
        AssertionError: If the response status code is not 200 or if the number of
            experiments does not match the expected number.
    """

    response = client.get(
        f"/api/{QUEUE_BASE_ROUTE}?index={index}&page_length={page_length}",
        follow_redirects=True,
    )

    page = response.get_json()
    assert response.status_code == 200 and page == expected


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
    queue1_response = register_queue(client, name="tensorflow_cpu")
    queue2_response = register_queue(client, name="pytorch_cpu")
    queue1_expected = queue1_response.get_json()
    queue2_expected = queue2_response.get_json()
    queue_expected_list = [queue1_expected, queue2_expected]
    assert_retrieving_queue_by_id_works(
        client, queue_id=queue1_expected["queueId"], expected=queue1_expected
    )
    assert_retrieving_queue_by_name_works(
        client, queue_name=queue1_expected["name"], expected=queue1_expected
    )
    assert_retrieving_queue_by_id_works(
        client, queue_id=queue2_expected["queueId"], expected=queue2_expected
    )
    assert_retrieving_queue_by_name_works(
        client, queue_name=queue2_expected["name"], expected=queue2_expected
    )
    assert_retrieving_all_queues_works(client, expected=queue_expected_list)


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


def test_delete_queue_by_name(client: FlaskClient, db: SQLAlchemy) -> None:
    """Test that a queue can be deleted by referencing its name.

    This test validates the following sequence of actions:

    - A user registers a queue named "tensorflow_cpu".
    - The user is able to retrieve information about the "tensorflow_cpu" queue that
      matches the information that was provided during registration.
    - The user deletes the "tensorflow_cpu" queue by referencing its name.
    - The user attempts to retrieve information about the "tensorflow_cpu" queue, which
      is no longer found.
    """
    queue_name = "tensorflow_cpu"
    registration_response = register_queue(client, name=queue_name)
    queue_json = registration_response.get_json()
    assert_retrieving_queue_by_id_works(
        client, queue_id=queue_json["queueId"], expected=queue_json
    )
    delete_queue_with_name(client, name=queue_json["name"])
    assert_queue_is_not_found(client, queue_id=queue_json["queueId"])


def test_lock_queue_by_id(client: FlaskClient, db: SQLAlchemy) -> None:
    """Test that a queue can be locked by referencing its id.

    This test validates the following sequence of actions:

    - A user registers two queues, "tensorflow_cpu" and "tensorflow_gpu".
    - The user requests a list of all queues, which returns a list of length 2.
    - The user locks the "tensorflow_gpu" queue by referencing its id.
    - The user requests a list of all queues, which returns a list of length 1.
    - The user unlocks the "tensorflow_gpu" queue by referencing its id.
    - The user requests a list of all queues, which returns a list of length 2.
    """
    register_queue(client, name="tensorflow_cpu")
    response = register_queue(client, name="tensorflow_gpu")
    queue_json = response.get_json()
    tensorflow_gpu_queue_id = queue_json["queueId"]
    assert_queue_count_matches_expected_count(client, expected=2)
    lock_queue_with_id(client, queue_id=tensorflow_gpu_queue_id)
    assert_queue_count_matches_expected_count(client, expected=1)
    unlock_queue_with_id(client, queue_id=tensorflow_gpu_queue_id)
    assert_queue_count_matches_expected_count(client, expected=2)


def test_lock_queue_by_name(client: FlaskClient, db: SQLAlchemy) -> None:
    """Test that a queue can be locked by referencing its name.

    This test validates the following sequence of actions:

    - A user registers two queues, "tensorflow_cpu" and "tensorflow_gpu".
    - The user requests a list of all queues, which returns a list of length 2.
    - The user locks the "tensorflow_gpu" queue by referencing its name.
    - The user requests a list of all queues, which returns a list of length 1.
    - The user unlocks the "tensorflow_gpu" queue by referencing its name.
    - The user requests a list of all queues, which returns a list of length 2.
    """
    register_queue(client, name="tensorflow_cpu")
    response = register_queue(client, name="tensorflow_gpu")
    queue_json = response.get_json()
    tensorflow_gpu_name = queue_json["name"]
    assert_queue_count_matches_expected_count(client, expected=2)
    lock_queue_with_name(client, name=tensorflow_gpu_name)
    assert_queue_count_matches_expected_count(client, expected=1)
    unlock_queue_with_name(client, name=tensorflow_gpu_name)
    assert_queue_count_matches_expected_count(client, expected=2)


def test_queue_paging(client: FlaskClient, db: SQLAlchemy) -> None:
    """Tests that queues can be retrieved according to paging information:
        Scenario: Queue Paging
            Given I am an authorized user,
            I need to be able to select an index and page length,
            in order to display a page of queues.
    This test validates by following these actions:
    - A user registers two queues, "queue1", "queue2", and "queue3".
    - The user is able to retrieve a page after specifying the index and page length.
    - The returned page of queues matches the information that was provided
      during registration.
    """

    queue1_expected = register_queue(client, name="queue1").get_json()
    queue2_expected = register_queue(client, name="queue2").get_json()
    register_queue(client, name="queue3")
    data = [
        queue1_expected,
        queue2_expected,
    ]
    index = 0
    page_length = 2
    is_complete = False
    page_expected = {
        "page": data,
        "index": index,
        "is_complete": is_complete,
        "first": f"/api/queue?index=0&page_length={page_length}",
        "next": f"/api/queue?index={index+page_length}&page_length={page_length}",
        "prev": f"/api/queue?index=0&page_length={page_length}",
    }
    assert_page_data_matches(client, index=0, page_length=2, expected=page_expected)
