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
"""Test suite for entrypoint operations.

This module contains a set of tests that validate the CRUD operations and additional
functionalities for the entrypoint entity. The tests ensure that the entrypoints can be
registered, renamed, deleted, and locked/unlocked as expected through the REST API.
"""
import textwrap
from http import HTTPStatus
from typing import Any

import pytest
from sqlalchemy.orm import Session as DBSession

from dioptra.client.base import DioptraResponseProtocol, FieldNameCollisionError
from dioptra.client.client import DioptraClient

from ..lib import helpers, routines
from ..test_utils import assert_retrieving_resource_works

# -- Assertions ------------------------------------------------------------------------


def assert_entrypoint_response_contents_matches_expectations(
    response: dict[str, Any], expected_contents: dict[str, Any]
) -> None:
    """Assert that entrypoint response contents is valid.

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
        "snapshotCreatedOn",
        "lastModifiedOn",
        "latestSnapshot",
        "hasDraft",
        "name",
        "description",
        "taskGraph",
        "parameters",
        "plugins",
        "queues",
        "tags",
    }
    assert set(response.keys()) == expected_keys

    # Validate the non-Ref fields
    assert isinstance(response["id"], int)
    assert isinstance(response["snapshot"], int)
    assert isinstance(response["name"], str)
    assert isinstance(response["description"], str)
    assert isinstance(response["createdOn"], str)
    assert isinstance(response["snapshotCreatedOn"], str)
    assert isinstance(response["lastModifiedOn"], str)
    assert isinstance(response["latestSnapshot"], bool)
    assert isinstance(response["hasDraft"], bool)

    assert response["name"] == expected_contents["name"]
    assert response["description"] == expected_contents["description"]
    assert response["taskGraph"] == expected_contents["task_graph"]

    assert helpers.is_iso_format(response["createdOn"])
    assert helpers.is_iso_format(response["snapshotCreatedOn"])
    assert helpers.is_iso_format(response["lastModifiedOn"])

    # Validate PluginRef structure
    for plugin in response["plugins"]:
        assert isinstance(plugin["id"], int)
        assert isinstance(plugin["snapshotId"], int)
        assert isinstance(plugin["name"], str)
        assert isinstance(plugin["url"], str)
        for plugin_file in plugin["files"]:
            assert isinstance(plugin_file["id"], int)
            assert isinstance(plugin_file["snapshotId"], int)
            assert isinstance(plugin_file["filename"], str)
            assert isinstance(plugin_file["url"], str)

    # Validate the Queue IDs structure
    for queue in response["queues"]:
        assert isinstance(queue["id"], int)
        assert isinstance(queue["group"], dict)
        assert isinstance(queue["url"], str)

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
    assert response["tags"] == expected_contents["tags"]

    # Validate the EntryPointParameter structure
    for param in response["parameters"]:
        assert isinstance(param["name"], str)
        assert isinstance(param["defaultValue"], str)
        assert isinstance(param["parameterType"], str)
    assert response["parameters"] == expected_contents["parameters"]


def assert_retrieving_entrypoint_by_id_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    entrypoint_id: int,
    expected: dict[str, Any],
) -> None:
    """Assert that retrieving a entrypoint by id works.

    Args:
        client: The Flask test client.
        entrypoint_id: The id of the entrypoint to retrieve.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = dioptra_client.entrypoints.get_by_id(entrypoint_id)
    assert response.status_code == HTTPStatus.OK and response.json() == expected


def assert_retrieving_entrypoints_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    expected: list[dict[str, Any]],
    group_id: int | None = None,
    sort_by: str | None = None,
    descending: bool | None = None,
    search: str | None = None,
    paging_info: dict[str, Any] | None = None,
) -> None:
    """Assert that retrieving all entrypoints works.

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

    assert_retrieving_resource_works(
        dioptra_client=dioptra_client.entrypoints,
        expected=expected,
        group_id=group_id,
        sort_by=sort_by,
        descending=descending,
        search=search,
        paging_info=paging_info,
    )


def assert_registering_existing_entrypoint_name_fails(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    name: str,
    description: str,
    group_id: int,
    task_graph: str,
    parameters: list[dict[str, Any]],
    plugin_ids: list[int],
    queue_ids: list[int],
) -> None:
    """Assert that registering a entrypoint with an existing name fails.

    Args:
        client: The Flask test client.
        name: The name to assign to the new entrypoint.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = dioptra_client.entrypoints.create(
        group_id=group_id,
        name=name,
        task_graph=task_graph,
        description=description,
        parameters=parameters,
        queues=queue_ids,
        plugins=plugin_ids,
    )
    assert response.status_code == HTTPStatus.CONFLICT


def assert_entrypoint_name_matches_expected_name(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    entrypoint_id: int,
    expected_name: str,
) -> None:
    """Assert that the name of a entrypoint matches the expected name.

    Args:
        client: The Flask test client.
        entrypoint_id: The id of the entrypoint to retrieve.
        expected_name: The expected name of the entrypoint.

    Raises:
        AssertionError: If the response status code is not 200 or if the name of the
            entrypoint does not match the expected name.
    """
    response = dioptra_client.entrypoints.get_by_id(entrypoint_id)
    assert (
        response.status_code == HTTPStatus.OK
        and response.json()["name"] == expected_name
    )


def assert_entrypoint_is_not_found(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    entrypoint_id: int,
) -> None:
    """Assert that a entrypoint is not found.

    Args:
        client: The Flask test client.
        entrypoint_id: The id of the entrypoint to retrieve.

    Raises:
        AssertionError: If the response status code is not 404.
    """
    response = dioptra_client.queues.get_by_id(entrypoint_id)
    assert response.status_code == HTTPStatus.NOT_FOUND


def assert_entrypoint_is_not_associated_with_experiment(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    experiment_id: int,
    entrypoint_id: int,
) -> None:
    """Assert that an entrypoint is not associated with an experiment

    Args:
        client: The Flask test client.
        experiment_id: The id of the experiment to retrieve.
        entrypoint_id: The id of the entrypoint to check for association.

    Raises:
        AssertionError: If the response status code is not 200 or if the queue id
            is in the list of queues associated with the entrypoint.
    """
    response = dioptra_client.experiments.get_by_id(experiment_id)
    experiment = response.json()
    entrypoint_ids = set(entrypoint["id"] for entrypoint in experiment["entrypoints"])
    assert response.status_code == HTTPStatus.OK and entrypoint_id not in entrypoint_ids


def assert_cannot_rename_entrypoint_with_existing_name(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    entrypoint_id: int,
    existing_name: str,
    existing_description: str,
    existing_task_graph: str,
    existing_parameters: list[dict[str, Any]],
    existing_queue_ids: list[int],
) -> None:
    """Assert that renaming a entrypoint with an existing name fails.

    Args:
        client: The Flask test client.
        entrypoint_id: The id of the entrypoint to rename.
        existing_name: str,
        existing_description: str,
        existing_task_graph: str,
        existing_parameters: list[dict[str, Any]],
        existing_queue_ids: list[int],

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = dioptra_client.entrypoints.modify_by_id(
        entrypoint_id=entrypoint_id,
        name=existing_name,
        task_graph=existing_task_graph,
        description=existing_description,
        parameters=existing_parameters,
        queues=existing_queue_ids,
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def assert_entrypoint_must_have_unique_param_names(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    name: str,
    description: str,
    group_id: int,
    task_graph: str,
    parameters: list[dict[str, Any]],
    plugin_ids: list[int],
    queue_ids: list[int],
) -> None:
    response = dioptra_client.entrypoints.create(
        group_id=group_id,
        name=name,
        task_graph=task_graph,
        description=description,
        parameters=parameters,
        queues=queue_ids,
        plugins=plugin_ids,
    )
    assert response.status_code == HTTPStatus.CONFLICT


def assert_retrieving_all_queues_for_entrypoint_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    entrypoint_id: int,
    expected: list[Any],
) -> None:
    response = dioptra_client.entrypoints.queues.get(entrypoint_id)
    assert (
        response.status_code == HTTPStatus.OK
        and [queue_ref["id"] for queue_ref in response.json()] == expected
    )


def assert_append_queues_to_entrypoint_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    entrypoint_id: int,
    queue_ids: list[int],
    expected: list[Any],
) -> None:
    response = dioptra_client.entrypoints.queues.create(
        entrypoint_id=entrypoint_id, queue_ids=queue_ids
    )
    assert (
        response.status_code == HTTPStatus.OK
        and [queue_ref["id"] for queue_ref in response.json()] == expected
    )


def assert_retrieving_all_plugin_snapshots_for_entrypoint_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    entrypoint_id: int,
    expected: list[int],
) -> None:
    response = dioptra_client.entrypoints.plugins.get(entrypoint_id)
    assert (
        response.status_code == HTTPStatus.OK
        and [plugin_snapshot["id"] for plugin_snapshot in response.json()] == expected
    )


def assert_append_plugins_to_entrypoint_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    entrypoint_id: int,
    plugin_ids: list[int],
    expected: list[int],
) -> None:
    response = dioptra_client.entrypoints.plugins.create(
        entrypoint_id=entrypoint_id, plugin_ids=plugin_ids
    )
    response_json = response.json()
    assert (
        response.status_code == HTTPStatus.OK
        and [plugin_snapshot["id"] for plugin_snapshot in response_json] == expected
    )


def assert_retrieving_plugin_snapshots_by_id_for_entrypoint_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    entrypoint_id: int,
    plugin_id: int,
    expected: int,
) -> None:
    response = dioptra_client.entrypoints.plugins.get_by_id(
        entrypoint_id=entrypoint_id, plugin_id=plugin_id
    )
    assert response.status_code == HTTPStatus.OK and response.json()["id"] == expected


def assert_registering_entrypoint_with_no_queues_succeeds(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    entry_point: dict[str, Any],
    assert_message: str,
) -> None:
    """Assert that registering entryPoint with empty queues, plugins and/or params is OK

    Args:
        dioptra_client (DioptraClient[DioptraResponseProtocol]): the restAPI client
        entry_point (dict[str, Any]): Dict packed with stuffed data for creating entry-point
        assert_message (str): Failed evaluation message for the assert to report
    """

    def assert_correct_emptiness(
        entry_point: dict[str, Any], entity_name: str, entry_point_data: dict[str, Any]
    ):
        # For empties - the empties are stored
        if not entry_point[entity_name] and entity_name in entry_point_data:
            assert not bool(entry_point_data[entity_name])
        # For non-empties - the non-empties match
        if entry_point[entity_name] and entity_name in entry_point_data:
            assert entry_point_data[entity_name] == entry_point[entity_name]

    entrypoint_response = None
    entrypoint_response = dioptra_client.entrypoints.create(
        group_id=entry_point["group_id"],
        name=entry_point["name"],
        task_graph=entry_point["task_graph"],
        description=entry_point["description"],
        parameters=entry_point["parameters"],
        queues=entry_point["queues"],
        plugins=entry_point["plugins"],
    )
    assert (
        entrypoint_response and entrypoint_response.status_code == HTTPStatus.OK
    ), assert_message
    # Assert the return values match what was expected
    entry_point_data = entrypoint_response.json()
    assert_correct_emptiness(entry_point, "queues", entry_point_data)
    assert_correct_emptiness(entry_point, "parameters", entry_point_data)
    assert_correct_emptiness(entry_point, "plugins", entry_point_data)


# -- Tests -----------------------------------------------------------------------------


def test_create_entrypoint(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_plugin_with_files: dict[str, Any],
    registered_queues: dict[str, Any],
) -> None:
    """Test that entrypoints can be correctly registered and retrieved using the API.

    Given an authenticated user, registered plugins, and registered queues, this test
    validates the following sequence of actions:

    - The user registers a entrypoint named "tensorflow_cpu".
    - The response is valid matches the expected values given the registration request.
    - The user is able to retrieve information about the entrypoint using the entrypoint
      id.
    """
    name = "my_entrypoint"
    description = "The first entrypoint."
    user_id = auth_account["id"]
    group_id = auth_account["groups"][0]["id"]
    task_graph = textwrap.dedent(
        """# my entrypoint graph
        graph:
          message:
            my_entrypoint: $name
        """
    )
    parameters = [
        {
            "name": "my_entrypoint_param_1",
            "defaultValue": "my_value",
            "parameterType": "string",
        },
        {
            "name": "my_entrypoint_param_2",
            "defaultValue": "my_value",
            "parameterType": "string",
        },
    ]
    plugin_ids = [registered_plugin_with_files["plugin"]["id"]]
    queue_ids = [queue["id"] for queue in list(registered_queues.values())]
    entrypoint_response = dioptra_client.entrypoints.create(
        group_id=group_id,
        name=name,
        task_graph=task_graph,
        description=description,
        parameters=parameters,
        queues=queue_ids,
        plugins=plugin_ids,
    )
    entrypoint_expected = entrypoint_response.json()
    assert_entrypoint_response_contents_matches_expectations(
        response=entrypoint_expected,
        expected_contents={
            "name": name,
            "description": description,
            "user_id": user_id,
            "group_id": group_id,
            "task_graph": task_graph,
            "parameters": parameters,
            "plugin_ids": plugin_ids,
            "queue_ids": queue_ids,
            "tags": [],
        },
    )
    assert_retrieving_entrypoint_by_id_works(
        dioptra_client,
        entrypoint_id=entrypoint_expected["id"],
        expected=entrypoint_expected,
    )

    # Testing that parameter names must be unique
    bad_parameters = [
        {
            "name": "not_unique",
            "defaultValue": "my_value",
            "parameterType": "string",
        },
        {
            "name": "not_unique",
            "defaultValue": "my_value",
            "parameterType": "string",
        },
    ]
    assert_entrypoint_must_have_unique_param_names(
        dioptra_client,
        name=name,
        description=description,
        group_id=group_id,
        task_graph=task_graph,
        parameters=bad_parameters,
        plugin_ids=plugin_ids,
        queue_ids=queue_ids,
    )


def test_entrypoint_get_all(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_entrypoints: dict[str, Any],
) -> None:
    """Test that all entrypoints can be retrieved.

    Given an authenticated user and registered entrypoints, this test validates the
    following sequence of actions:

    - A user registers three entrypoints:
      "tensorflow_cpu",
      "tensorflow_gpu",
      "pytorch_cpu".
    - The user is able to retrieve a list of all registered entrypoints.
    - The returned list of entrypoints matches the full list of registered entrypoints.
    """
    entrypoint_expected_list = list(registered_entrypoints.values())
    assert_retrieving_entrypoints_works(
        dioptra_client, expected=entrypoint_expected_list
    )


@pytest.mark.parametrize(
    "sortBy, descending , expected",
    [
        (
            "name",
            True,
            ["entrypoint2", "entrypoint3", "entrypoint1", "entrypoint_no_params"],
        ),
        (
            "name",
            False,
            ["entrypoint_no_params", "entrypoint1", "entrypoint3", "entrypoint2"],
        ),
        (
            "createdOn",
            True,
            ["entrypoint_no_params", "entrypoint3", "entrypoint2", "entrypoint1"],
        ),
        (
            "createdOn",
            False,
            ["entrypoint1", "entrypoint2", "entrypoint3", "entrypoint_no_params"],
        ),
    ],
)
def test_entrypoint_sort(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_entrypoints: dict[str, Any],
    sortBy: str,
    descending: bool,
    expected: list[str],
) -> None:
    """Test that entrypoints can be sorted by column.

    Given an authenticated user and registered entrypoints, this test validates the
    following sequence of actions:

    - A user registers three entrypoints:
      "entrypoint_one",
      "entrypoint_two",
      "entrypoint_three".
    - The user is able to retrieve a list of all registered entrypoints sorted by a
      column ascending/descending.
    - The returned list of entrypoints matches the order in the parametrize lists above.
    """

    expected_entrypoints = [
        registered_entrypoints[expected_name] for expected_name in expected
    ]
    assert_retrieving_entrypoints_works(
        dioptra_client,
        sort_by=sortBy,
        descending=descending,
        expected=expected_entrypoints,
    )


def test_entrypoint_search_query(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_entrypoints: dict[str, Any],
) -> None:
    """Test that entrypoints can be queried with a search term.

    Given an authenticated user and registered entrypoints, this test validates the
    following sequence of actions:

    - The user is able to retrieve a list of all registered entrypoints with various
      queries.
    - The returned list of entrypoints matches the expected matches from the query.
    """
    entrypoint_expected_list = list(registered_entrypoints.values())[:2]
    assert_retrieving_entrypoints_works(
        dioptra_client,
        expected=entrypoint_expected_list,
        search="description:*entrypoint*",
    )
    entrypoint_expected_list = list(registered_entrypoints.values())
    assert_retrieving_entrypoints_works(
        dioptra_client, expected=entrypoint_expected_list, search="*"
    )


def test_entrypoint_group_query(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_entrypoints: dict[str, Any],
) -> None:
    """Test that entrypoints can retrieved using a group filter.

    Given an authenticated user and registered entrypoints, this test validates the
    following sequence of actions:

    - The user is able to retrieve a list of all registered entrypoints that are owned
      by the default group.
    - The returned list of entrypoints matches the expected list owned by the default
      group.
    """
    entrypoint_expected_list = list(registered_entrypoints.values())
    assert_retrieving_entrypoints_works(
        dioptra_client,
        expected=entrypoint_expected_list,
        group_id=auth_account["groups"][0]["id"],
    )


def test_cannot_register_existing_entrypoint_name(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_entrypoints: dict[str, Any],
    registered_plugin_with_files: dict[str, Any],
    registered_queues: dict[str, Any],
) -> None:
    """Test that registering a entrypoint with an existing name fails.

    Given an authenticated user and registered entrypoints, this test validates the
    following sequence of actions:

    - The user attempts to register a second entrypoint with the same name.
    - The request fails with an appropriate error message and response code.
    """
    existing_entrypoint = registered_entrypoints["entrypoint1"]
    plugin_ids = [registered_plugin_with_files["plugin"]["id"]]
    queue_ids = [queue["id"] for queue in list(registered_queues.values())]

    assert_registering_existing_entrypoint_name_fails(
        dioptra_client,
        name=existing_entrypoint["name"],
        description="",
        group_id=existing_entrypoint["group"]["id"],
        task_graph="",
        parameters=[],
        plugin_ids=plugin_ids,
        queue_ids=queue_ids,
    )


def test_rename_entrypoint(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_entrypoints: dict[str, Any],
) -> None:
    """Test that a entrypoint can be renamed.

    Given an authenticated user and registered entrypoints, this test validates the
    following sequence of actions:

    - The user issues a request to change the name of a entrypoint.
    - The user retrieves information about the same entrypoint and it reflects the name
      change.
    - The user issues a request to change the name of the entrypoint to the existing
      name.
    - The user retrieves information about the same entrypoint and verifies the name
      remains unchanged.
    - The user issues a request to change the name of a entrypoint to an existing
      entrypoint's name.
    - The request fails with an appropriate error message and response code.
    """
    updated_entrypoint_name = "new_entrypoint_name"
    entrypoint_to_rename = registered_entrypoints["entrypoint1"]
    existing_entrypoint = registered_entrypoints["entrypoint2"]
    queue_ids = [queue["id"] for queue in entrypoint_to_rename["queues"]]

    modified_entrypoint = dioptra_client.entrypoints.modify_by_id(
        entrypoint_id=entrypoint_to_rename["id"],
        name=updated_entrypoint_name,
        task_graph=entrypoint_to_rename["taskGraph"],
        description=entrypoint_to_rename["description"],
        parameters=entrypoint_to_rename["parameters"],
        queues=queue_ids,
    ).json()
    assert_entrypoint_name_matches_expected_name(
        dioptra_client,
        entrypoint_id=entrypoint_to_rename["id"],
        expected_name=updated_entrypoint_name,
    )
    entrypoint_expected_list = [
        modified_entrypoint,
        registered_entrypoints["entrypoint2"],
        registered_entrypoints["entrypoint3"],
        registered_entrypoints["entrypoint_no_params"],
    ]
    assert_retrieving_entrypoints_works(
        dioptra_client, expected=entrypoint_expected_list
    )

    modified_entrypoint = dioptra_client.entrypoints.modify_by_id(
        entrypoint_id=entrypoint_to_rename["id"],
        name=updated_entrypoint_name,
        task_graph=entrypoint_to_rename["taskGraph"],
        description=entrypoint_to_rename["description"],
        parameters=entrypoint_to_rename["parameters"],
        queues=queue_ids,
    ).json()
    assert_entrypoint_name_matches_expected_name(
        dioptra_client,
        entrypoint_id=entrypoint_to_rename["id"],
        expected_name=updated_entrypoint_name,
    )

    assert_cannot_rename_entrypoint_with_existing_name(
        dioptra_client,
        entrypoint_id=entrypoint_to_rename["id"],
        existing_name=existing_entrypoint["name"],
        existing_description=entrypoint_to_rename["description"],
        existing_task_graph=entrypoint_to_rename["taskGraph"],
        existing_parameters=entrypoint_to_rename["parameters"],
        existing_queue_ids=entrypoint_to_rename["queues"],
    )


def test_delete_entrypoint_by_id(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_experiments: dict[str, Any],
) -> None:
    """Test that a entrypoint can be deleted by referencing its id.

    Given an authenticated user and registered entrypoints, this test validates the
    following sequence of actions:

    - The user deletes a entrypoint by referencing its id.
    - The user attempts to retrieve information about the deleted entrypoint.
    - The request fails with an appropriate error message and response code.
    - The entrypoint is no longer associated with the experiment.
    """
    experiment = registered_experiments["experiment1"]
    entrypoint_to_delete = experiment["entrypoints"][0]
    dioptra_client.entrypoints.delete_by_id(entrypoint_to_delete["id"])
    assert_entrypoint_is_not_found(
        dioptra_client, entrypoint_id=entrypoint_to_delete["id"]
    )
    assert_entrypoint_is_not_associated_with_experiment(
        dioptra_client,
        experiment_id=experiment["id"],
        entrypoint_id=entrypoint_to_delete["id"],
    )


def test_manage_existing_entrypoint_draft(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_entrypoints: dict[str, Any],
) -> None:
    """Test that a draft of an existing entrypoint can be created and managed by
        the user

    Given an authenticated user and registered entrypoints, this test validates the
    following sequence of actions:

    - The user creates a draft of an existing entrypoint
    - The user retrieves information about the draft and gets the expected response
    - The user attempts to create another draft of the same existing entrypoint
    - The request fails with an appropriate error message and response code.
    - The user modifies the name of the entrypoint in the draft
    - The user retrieves information about the draft and gets the expected response
    - The user deletes the draft
    - The user attempts to retrieve information about the deleted draft.
    - The request fails with an appropriate error message and response code.
    """
    # Requests data
    entrypoint = registered_entrypoints["entrypoint1"]
    name = "draft"
    new_name = "draft2"
    description = "description"
    task_graph = textwrap.dedent(
        """# my entrypoint graph
        graph:
          message:
            my_entrypoint: $name
        """
    )
    parameters = [
        {
            "name": "my_entrypoint_param",
            "defaultValue": "my_value",
            "parameterType": "string",
        }
    ]
    queue_ids = [queue["id"] for queue in entrypoint["queues"]]

    # test creation
    draft = {
        "name": name,
        "description": description,
        "task_graph": task_graph,
        "parameters": parameters,
        "queues": queue_ids,
    }
    draft_mod = {
        "name": new_name,
        "description": description,
        "task_graph": task_graph,
        "parameters": parameters,
        "queues": queue_ids,
    }

    # Expected responses
    draft_expected = {
        "user_id": auth_account["id"],
        "group_id": entrypoint["group"]["id"],
        "resource_id": entrypoint["id"],
        "resource_snapshot_id": entrypoint["snapshot"],
        "num_other_drafts": 0,
        "payload": {
            "name": name,
            "description": description,
            "taskGraph": task_graph,
            "parameters": parameters,
            "queues": queue_ids,
        },
    }
    draft_mod_expected = {
        "user_id": auth_account["id"],
        "group_id": entrypoint["group"]["id"],
        "resource_id": entrypoint["id"],
        "resource_snapshot_id": entrypoint["snapshot"],
        "num_other_drafts": 0,
        "payload": {
            "name": new_name,
            "description": description,
            "taskGraph": task_graph,
            "parameters": parameters,
            "queues": queue_ids,
        },
    }

    # Run routine: existing resource drafts tests
    routines.run_existing_resource_drafts_tests(
        dioptra_client.entrypoints,
        dioptra_client.entrypoints.modify_resource_drafts,
        dioptra_client.workflows,
        entrypoint["id"],
        draft=draft,
        draft_mod=draft_mod,
        draft_expected=draft_expected,
        draft_mod_expected=draft_mod_expected,
    )


def test_manage_new_entrypoint_drafts(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_queues: dict[str, Any],
    registered_plugins: dict[str, Any],
) -> None:
    """Test that drafts of entrypoint can be created and managed by the user

    Given an authenticated user, this test validates the following sequence of actions:

    - The user creates two entrypoint drafts
    - The user retrieves information about the drafts and gets the expected response
    - The user modifies the description of the entrypoint in the first draft
    - The user retrieves information about the draft and gets the expected response
    - The user deletes the first draft
    - The user attempts to retrieve information about the deleted draft.
    - The request fails with an appropriate error message and response code.
    """
    # Requests data
    group_id = auth_account["groups"][0]["id"]
    drafts = {
        "draft1": {
            "name": "entrypoint1",
            "description": "new entrypoint",
            "task_graph": "graph",
            "parameters": [],
            "plugins": [],
            "queues": [],
        },
        "draft2": {
            "name": "entrypoint2",
            "description": "entrypoint",
            "task_graph": "graph",
            "parameters": [],
            "queues": [
                registered_queues["queue1"]["id"],
                registered_queues["queue3"]["id"],
            ],
            "plugins": [registered_plugins["plugin2"]["id"]],
        },
    }
    draft1_mod = {
        "name": "draft1",
        "description": "new description",
        "task_graph": "graph",
        "parameters": [],
        "plugins": [],
        "queues": [],
    }

    # Expected responses
    draft1_expected = {
        "user_id": auth_account["id"],
        "group_id": group_id,
        "payload": {
            "name": "entrypoint1",
            "description": "new entrypoint",
            "taskGraph": "graph",
            "parameters": [],
            "plugins": [],
            "queues": [],
        },
    }
    draft2_expected = {
        "user_id": auth_account["id"],
        "group_id": group_id,
        "payload": {
            "name": "entrypoint2",
            "description": "entrypoint",
            "taskGraph": "graph",
            "parameters": [],
            "queues": [
                registered_queues["queue1"]["id"],
                registered_queues["queue3"]["id"],
            ],
            "plugins": [registered_plugins["plugin2"]["id"]],
        },
    }
    draft1_mod_expected = {
        "user_id": auth_account["id"],
        "group_id": group_id,
        "payload": {
            "name": "draft1",
            "description": "new description",
            "taskGraph": "graph",
            "parameters": [],
            "plugins": [],
            "queues": [],
        },
    }

    # Run routine: existing resource drafts tests
    routines.run_new_resource_drafts_tests(
        dioptra_client.entrypoints,
        dioptra_client.entrypoints.new_resource_drafts,
        dioptra_client.workflows,
        drafts=drafts,
        draft1_mod=draft1_mod,
        draft1_expected=draft1_expected,
        draft2_expected=draft2_expected,
        draft1_mod_expected=draft1_mod_expected,
        group_id=group_id,
    )


def test_client_raises_error_on_field_name_collision(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_entrypoints: dict[str, Any],
) -> None:
    """
    Test that the client errors out if both task_graph and taskGraph are passed as
    keyword arguments to either the create and modify draft resource sub-collection
    clients.

    Given an authenticated user, this test validates the following sequence of actions:

    - The user prepares a payload for either the create or modify draft resource
      sub-collection client. The payload contains both task_graph an taskGraph as keys.
    - The user submits a create new resource request using the payload, which raises
      a FieldNameCollisionError.
    - The user submits a modify resource draft request using the payload, which raises
        a FieldNameCollisionError.
    """
    entrypoint = registered_entrypoints["entrypoint1"]
    group_id = auth_account["groups"][0]["id"]
    name = "draft"
    description = "description"
    task_graph = textwrap.dedent(
        """# my entrypoint graph
        graph:
          message:
            my_entrypoint: $name
        """
    )
    parameters = [
        {
            "name": "my_entrypoint_param",
            "defaultValue": "my_value",
            "parameterType": "string",
        }
    ]
    plugin_ids = [plugin["id"] for plugin in entrypoint["plugins"]]
    queue_ids = [queue["id"] for queue in entrypoint["queues"]]

    draft = {
        "name": name,
        "description": description,
        "task_graph": task_graph,
        "taskGraph": task_graph,
        "parameters": parameters,
        "plugins": plugin_ids,
        "queues": queue_ids,
    }

    with pytest.raises(FieldNameCollisionError):
        dioptra_client.entrypoints.new_resource_drafts.create(
            group_id=group_id,
            **draft,
        )

    with pytest.raises(FieldNameCollisionError):
        dioptra_client.entrypoints.modify_resource_drafts.modify(
            entrypoint["id"],
            resource_snapshot_id=entrypoint["snapshot"],
            **draft,
        )


def test_manage_entrypoint_snapshots(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_entrypoints: dict[str, Any],
) -> None:
    """Test that different snapshots of a entrypoint can be retrieved by the user.

    Given an authenticated user and registered entrypoints, this test validates the
    following sequence of actions:

    - The user modifies a entrypoint
    - The user retrieves information about the original snapshot of the entrypoint and
      gets the expected response
    - The user retrieves information about the new snapshot of the entrypoint and gets
      the expected response
    - The user retrieves a list of all snapshots of the entrypoint and gets the expected
      response
    """
    entrypoint_to_rename = registered_entrypoints["entrypoint1"]
    queue_ids = [queue["id"] for queue in entrypoint_to_rename["queues"]]
    modified_entrypoint = dioptra_client.entrypoints.modify_by_id(
        entrypoint_id=entrypoint_to_rename["id"],
        name=entrypoint_to_rename["name"] + "modified",
        task_graph=entrypoint_to_rename["taskGraph"],
        description=entrypoint_to_rename["description"],
        parameters=entrypoint_to_rename["parameters"],
        queues=queue_ids,
    ).json()

    # Run routine: resource snapshots tests
    routines.run_resource_snapshots_tests(
        dioptra_client.entrypoints.snapshots,
        resource_to_rename=entrypoint_to_rename.copy(),
        modified_resource=modified_entrypoint.copy(),
        drop_additional_fields=["queues"],
    )


def test_tag_entrypoint(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_entrypoints: dict[str, Any],
    registered_tags: dict[str, Any],
) -> None:
    """Test that different versions of a entrypoint can be retrieved by the user.

    Given an authenticated user and registered entrypoints, this test validates the
    following sequence of actions:

    """
    entrypoint = registered_entrypoints["entrypoint1"]
    tag_ids = [tag["id"] for tag in registered_tags.values()]

    # Run routine: resource tag tests
    routines.run_resource_tag_tests(
        dioptra_client.entrypoints.tags,
        entrypoint["id"],
        tag_ids=tag_ids,
    )


def test_get_all_queues_for_entrypoint(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_queues: dict[str, Any],
    registered_entrypoints: dict[str, Any],
) -> None:
    """Test that queues associated with entrypoints can be retrieved.
    Given an authenticated user, registered entrypoints, and registered queues,
    this test validates the following sequence of actions:
    - A user retrieves a list of all queue refs associated with the entrypoints.
    """
    entrypoint_id = registered_entrypoints["entrypoint1"]["id"]
    expected_queue_ids = [queue["id"] for queue in list(registered_queues.values())]
    assert_retrieving_all_queues_for_entrypoint_works(
        dioptra_client,
        entrypoint_id=entrypoint_id,
        expected=expected_queue_ids,
    )


def test_append_queues_to_entrypoint(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_queues: dict[str, Any],
    registered_entrypoints: dict[str, Any],
) -> None:
    """Test that queues can be appended to entrypoints.
    Given an authenticated user, registered entrypoints, and registered queues,
    this test validates the following sequence of actions:
    - A user adds new queue to the list of associated queues with the entrypoint.
    - A user can then retreive the new list that includes all old and new queues refs.
    """
    entrypoint_id = registered_entrypoints["entrypoint3"]["id"]
    queue_ids_to_append = [
        queue["id"] for queue in list(registered_queues.values())[1:]
    ]
    expected_queue_ids = [queue["id"] for queue in list(registered_queues.values())]
    assert_append_queues_to_entrypoint_works(
        dioptra_client,
        entrypoint_id=entrypoint_id,
        queue_ids=queue_ids_to_append,
        expected=expected_queue_ids,
    )


def test_modify_queues_for_entrypoint(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_queues: dict[str, Any],
    registered_entrypoints: dict[str, Any],
) -> None:
    """Test that the list of associated queues with entrypoints can be modified.
    Given an authenticated user, registered entrypoints, and registered queues,
    this test validates the following sequence of actions:
    - A user modifies the list of queues associated with an entrypoint.
    - A user retrieves the list of all the new queues associated with the experiemnts.
    """
    entrypoint_id = registered_entrypoints["entrypoint3"]["id"]
    expected_queue_ids = [queue["id"] for queue in list(registered_queues.values())]
    dioptra_client.entrypoints.queues.modify_by_id(
        entrypoint_id=entrypoint_id, queue_ids=expected_queue_ids
    )
    assert_retrieving_all_queues_for_entrypoint_works(
        dioptra_client,
        entrypoint_id=entrypoint_id,
        expected=expected_queue_ids,
    )


def test_delete_all_queues_for_entrypoint(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_entrypoints: dict[str, Any],
) -> None:
    """Test that the list of all associated queues can be deleted from a entrypoint.
    Given an authenticated user and registered entrypoints, this test validates the
    following sequence of actions:
    - A user deletes the list of associated queues with the entrypoint.
    - A user retrieves an empty list of associated queues with the entrypoint.
    """
    entrypoint_id = registered_entrypoints["entrypoint1"]["id"]
    dioptra_client.entrypoints.queues.delete(entrypoint_id)
    assert_retrieving_all_queues_for_entrypoint_works(
        dioptra_client,
        entrypoint_id=entrypoint_id,
        expected=[],
    )


def test_delete_queue_by_id_for_entrypoint(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_queues: dict[str, Any],
    registered_entrypoints: dict[str, Any],
) -> None:
    """Test that queues associated with the entrypoint can be deleted by id.
    Given an authenticated user, registered entrypoints, and registered queues,
    this test validates the following sequence of actions:
    - A user deletes an associated queue with the entrypoint.
    - A user retrieves a list of associated queues that does not include the deleted.
    """
    entrypoint_id = registered_entrypoints["entrypoint1"]["id"]
    queue_id_to_delete = registered_queues["queue1"]["id"]
    expected_queue_ids = [queue["id"] for queue in list(registered_queues.values())[1:]]
    dioptra_client.entrypoints.queues.delete_by_id(
        entrypoint_id=entrypoint_id, queue_id=queue_id_to_delete
    )
    assert_retrieving_all_queues_for_entrypoint_works(
        dioptra_client,
        entrypoint_id=entrypoint_id,
        expected=expected_queue_ids,
    )


def test_get_plugin_snapshots_for_entrypoint(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_plugin_with_files: dict[str, Any],
    registered_entrypoints: dict[str, Any],
) -> None:
    """Test that plugins associated with entrypoints can be retrieved.
    Given an authenticated user, registered entrypoints, and registered plugins,
    this test validates the following sequence of actions:
    - A user retrieves a list of all plugin refs associated with the entrypoints.
    """
    entrypoint_id = registered_entrypoints["entrypoint1"]["id"]
    expected_plugin_ids = [registered_plugin_with_files["plugin"]["id"]]
    assert_retrieving_all_plugin_snapshots_for_entrypoint_works(
        dioptra_client,
        entrypoint_id=entrypoint_id,
        expected=expected_plugin_ids,
    )


def test_append_plugins_to_entrypoint(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_plugin_with_files: dict[str, Any],
    registered_entrypoints: dict[str, Any],
) -> None:
    """Test that plugins can be appended to entrypoints.
    Given an authenticated user, registered entrypoints, and registered plugins,
    this test validates the following sequence of actions:
    - A user adds new plugin to the list of associated plugins with the entrypoint.
    - A user can then retreive the new list that includes all old and new plugins refs.
    """
    entrypoint_id = registered_entrypoints["entrypoint3"]["id"]
    expected_plugin_ids = [registered_plugin_with_files["plugin"]["id"]]
    assert_append_plugins_to_entrypoint_works(
        dioptra_client,
        entrypoint_id=entrypoint_id,
        plugin_ids=expected_plugin_ids,
        expected=expected_plugin_ids,
    )


def test_get_plugin_snapshot_by_id_for_entrypoint(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_plugin_with_files: dict[str, Any],
    registered_entrypoints: dict[str, Any],
) -> None:
    """Test that plugins associated with entrypoints can be retrieved by id.
    Given an authenticated user, registered entrypoints, and registered plugins,
    this test validates the following sequence of actions:
    - A user retrieves a plugin ref associated with the entrypoints by its id.
    """
    entrypoint_id = registered_entrypoints["entrypoint1"]["id"]
    expected_plugin_id = registered_plugin_with_files["plugin"]["id"]
    assert_retrieving_plugin_snapshots_by_id_for_entrypoint_works(
        dioptra_client,
        entrypoint_id=entrypoint_id,
        plugin_id=expected_plugin_id,
        expected=expected_plugin_id,
    )


def test_delete_plugin_snapshot_by_id_for_entrypoint(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_plugin_with_files: dict[str, Any],
    registered_entrypoints: dict[str, Any],
) -> None:
    """Test that plugins associated with the entrypoint can be deleted by id.
    Given an authenticated user, registered entrypoints, and registered plugins,
    this test validates the following sequence of actions:
    - A user deletes an associated plugin with the entrypoint.
    - A user retrieves a list of associated plugins that does not include the deleted.
    """
    entrypoint_id = registered_entrypoints["entrypoint1"]["id"]
    plugin_id_to_delete = registered_plugin_with_files["plugin"]["id"]
    dioptra_client.entrypoints.plugins.delete_by_id(
        entrypoint_id=entrypoint_id, plugin_id=plugin_id_to_delete
    )
    assert_retrieving_all_plugin_snapshots_for_entrypoint_works(
        dioptra_client,
        entrypoint_id=entrypoint_id,
        expected=[],
    )


def test_create_entrypoint_with_empty_queues_plugins_params(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
) -> None:
    """Verify that API can register entry-point with empty arrays for queues, plugins, and params

    Args:
        dioptra_client (DioptraClient[DioptraResponseProtocol]): Client
        auth_account (dict[str, Any]): Account
    """
    user_id = auth_account["id"]
    group_id = auth_account["groups"][0]["id"]
    empty_entry_point = {
        "user_id": user_id,
        "group_id": group_id,
        "name": "test_entrypoint_3Empties",
        "description": "new test entrypoint #1 With 3 []s",
        "task_graph": "graph:    message:    my_entrypoint: $name",
        "parameters": [],
        "plugins": [],
        "queues": [],
        "task_graph": textwrap.dedent(
            f"""# my entrypoint graph
                graph:
                message:
                    my_entrypoint:  "test_entrypoint_3Empties"
                """
        ),
    }
    assert_registering_entrypoint_with_no_queues_succeeds(
        dioptra_client=dioptra_client,
        entry_point=empty_entry_point,
        assert_message="Failed to create EntryPoint with 3 EMPTY entities: [queues=[], plugins=[], parameters=[]]",
    )


def test_create_entrypoint_with_none_queues_plugins_params(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
) -> None:
    """Tests that queues, plugins and parameters can be None-s

    Args:
        dioptra_client (DioptraClient[DioptraResponseProtocol]): Client
        auth_account (dict[str, Any]): Account
    """
    user_id = auth_account["id"]
    group_id = auth_account["groups"][0]["id"]
    none_entry_point = {
        "user_id": user_id,
        "group_id": group_id,
        "name": "test_entrypoint_3Nones",
        "description": "new test entrypoint #2 With 3 Nones",
        "task_graph": "graph:    message:    my_entrypoint: $name",
        "parameters": None,
        "plugins": None,
        "queues": None,
        "task_graph": textwrap.dedent(
            f"""# my entrypoint graph
                graph:
                message:
                    my_entrypoint:  "test_entrypoint_3Nones"
                """
        ),
    }
    assert_registering_entrypoint_with_no_queues_succeeds(
        dioptra_client=dioptra_client,
        entry_point=none_entry_point,
        assert_message="Failed to create EntryPoint with 3 None entities: [queues=None, plugins=None, parameters=None]",
    )
