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
from typing import Any

from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from werkzeug.test import TestResponse

from dioptra.restapi.routes import V1_ENTRYPOINTS_ROUTE, V1_EXPERIMENTS_ROUTE, V1_ROOT

from ..lib import actions, asserts, helpers

# -- Actions ---------------------------------------------------------------------------


def modify_entrypoint(
    client: FlaskClient,
    entrypoint_id: int,
    new_name: str,
    new_description: str,
    new_task_graph: str,
    new_parameters: list[dict[str, Any]],
    new_queue_ids: list[int],
) -> TestResponse:
    """Rename a entrypoint using the API.

    Args:
        client: The Flask test client.
        entrypoint_id: The id of the entrypoint to rename.
        new_name: The new name to assign to the entrypoint.
        new_description: The new description to assign to the entrypoint.

    Returns:
        The response from the API.
    """
    payload: dict[str, Any] = {
        "name": new_name,
        "description": new_description,
        "taskGraph": new_task_graph,
        "parameters": new_parameters,
        "queues": new_queue_ids,
    }

    return client.put(
        f"/{V1_ROOT}/{V1_ENTRYPOINTS_ROUTE}/{entrypoint_id}",
        json=payload,
        follow_redirects=True,
    )


def delete_entrypoint(
    client: FlaskClient,
    entrypoint_id: int,
) -> TestResponse:
    """Delete a entrypoint using the API.

    Args:
        client: The Flask test client.
        entrypoint_id: The id of the entrypoint to delete.

    Returns:
        The response from the API.
    """

    return client.delete(
        f"/{V1_ROOT}/{V1_ENTRYPOINTS_ROUTE}/{entrypoint_id}",
        follow_redirects=True,
    )


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
    assert isinstance(response["lastModifiedOn"], str)
    assert isinstance(response["latestSnapshot"], bool)
    assert isinstance(response["hasDraft"], bool)

    assert response["name"] == expected_contents["name"]
    assert response["description"] == expected_contents["description"]
    assert response["taskGraph"] == expected_contents["task_graph"]

    assert helpers.is_iso_format(response["createdOn"])
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
    client: FlaskClient,
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
    response = client.get(
        f"/{V1_ROOT}/{V1_ENTRYPOINTS_ROUTE}/{entrypoint_id}", follow_redirects=True
    )
    assert response.status_code == 200 and response.get_json() == expected


def assert_retrieving_entrypoints_works(
    client: FlaskClient,
    expected: list[dict[str, Any]],
    group_id: int | None = None,
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

    query_string: dict[str, Any] = {}

    if group_id is not None:
        query_string["groupId"] = group_id

    if search is not None:
        query_string["search"] = search

    if paging_info is not None:
        query_string["index"] = paging_info["index"]
        query_string["pageLength"] = paging_info["page_length"]

    response = client.get(
        f"/{V1_ROOT}/{V1_ENTRYPOINTS_ROUTE}",
        query_string=query_string,
        follow_redirects=True,
    )

    assert response.status_code == 200 and response.get_json()["data"] == expected


def assert_registering_existing_entrypoint_name_fails(
    client: FlaskClient,
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
    response = actions.register_entrypoint(
        client,
        name=name,
        description=description,
        group_id=group_id,
        task_graph=task_graph,
        parameters=parameters,
        plugin_ids=plugin_ids,
        queue_ids=queue_ids,
    )
    assert response.status_code == 400


def assert_entrypoint_name_matches_expected_name(
    client: FlaskClient, entrypoint_id: int, expected_name: str
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
    response = client.get(
        f"/{V1_ROOT}/{V1_ENTRYPOINTS_ROUTE}/{entrypoint_id}",
        follow_redirects=True,
    )
    assert response.status_code == 200 and response.get_json()["name"] == expected_name


def assert_entrypoint_is_not_found(
    client: FlaskClient,
    entrypoint_id: int,
) -> None:
    """Assert that a entrypoint is not found.

    Args:
        client: The Flask test client.
        entrypoint_id: The id of the entrypoint to retrieve.

    Raises:
        AssertionError: If the response status code is not 404.
    """
    response = client.get(
        f"/{V1_ROOT}/{V1_ENTRYPOINTS_ROUTE}/{entrypoint_id}",
        follow_redirects=True,
    )
    assert response.status_code == 404


def assert_entrypoint_is_not_associated_with_experiment(
    client: FlaskClient,
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
    response = client.get(
        f"/{V1_ROOT}/{V1_EXPERIMENTS_ROUTE}/{experiment_id}",
        follow_redirects=True,
    )
    experiment = response.get_json()
    print(experiment)
    entrypoint_ids = set(entrypoint["id"] for entrypoint in experiment["entrypoints"])

    assert response.status_code == 200 and entrypoint_id not in entrypoint_ids


def assert_cannot_rename_entrypoint_with_existing_name(
    client: FlaskClient,
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
    response = modify_entrypoint(
        client,
        entrypoint_id=entrypoint_id,
        new_name=existing_name,
        new_description=existing_description,
        new_task_graph=existing_task_graph,
        new_parameters=existing_parameters,
        new_queue_ids=existing_queue_ids,
    )
    assert response.status_code == 400


def assert_entrypoint_must_have_unique_param_names(
    client: FlaskClient,
    name: str,
    description: str,
    group_id: int,
    task_graph: str,
    parameters: list[dict[str, Any]],
    plugin_ids: list[int],
    queue_ids: list[int],
) -> None:
    response = actions.register_entrypoint(
        client,
        name=name,
        description=description,
        group_id=group_id,
        task_graph=task_graph,
        parameters=parameters,
        plugin_ids=plugin_ids,
        queue_ids=queue_ids,
    )
    assert response.status_code == 400


# -- Tests -----------------------------------------------------------------------------


def test_create_entrypoint(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugin_with_files: dict[str, Any],
    registered_queues: dict[str, Any],
) -> None:
    """Test that entrypoints can be correctly registered and retrieved using the API.

    Given an authenticated user, registered plugins, and registered queues, this test
    validates the following sequence of actions:

    - The user registers a entrypoint named "tensorflow_cpu".
    - The response is valid matches the expected values given the registration request.
    - The user is able to retrieve information about the entrypoint using the entrypoint id.
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
    entrypoint_response = actions.register_entrypoint(
        client,
        name=name,
        description=description,
        group_id=group_id,
        task_graph=task_graph,
        parameters=parameters,
        plugin_ids=plugin_ids,
        queue_ids=queue_ids,
    )
    entrypoint_expected = entrypoint_response.get_json()
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
        client, entrypoint_id=entrypoint_expected["id"], expected=entrypoint_expected
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
        client,
        name=name,
        description=description,
        group_id=group_id,
        task_graph=task_graph,
        parameters=bad_parameters,
        plugin_ids=plugin_ids,
        queue_ids=queue_ids,
    )


def test_entrypoint_get_all(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_entrypoints: dict[str, Any],
) -> None:
    """Test that all entrypoints can be retrieved.

    Given an authenticated user and registered entrypoints, this test validates the following
    sequence of actions:

    - A user registers three entrypoints, "tensorflow_cpu", "tensorflow_gpu", "pytorch_cpu".
    - The user is able to retrieve a list of all registered entrypoints.
    - The returned list of entrypoints matches the full list of registered entrypoints.
    """
    entrypoint_expected_list = list(registered_entrypoints.values())[:3]
    assert_retrieving_entrypoints_works(client, expected=entrypoint_expected_list)


def test_entrypoint_search_query(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_entrypoints: dict[str, Any],
) -> None:
    """Test that entrypoints can be queried with a search term.

    Given an authenticated user and registered entrypoints, this test validates the following
    sequence of actions:

    - The user is able to retrieve a list of all registered entrypoints with various queries.
    - The returned list of entrypoints matches the expected matches from the query.
    """
    entrypoint_expected_list = list(registered_entrypoints.values())[:2]
    assert_retrieving_entrypoints_works(
        client, expected=entrypoint_expected_list, search="description:*entrypoint*"
    )
    entrypoint_expected_list = list(registered_entrypoints.values())[:3]
    assert_retrieving_entrypoints_works(
        client, expected=entrypoint_expected_list, search="*"
    )


def test_entrypoint_group_query(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_entrypoints: dict[str, Any],
) -> None:
    """Test that entrypoints can retrieved using a group filter.

    Given an authenticated user and registered entrypoints, this test validates the following
    sequence of actions:

    - The user is able to retrieve a list of all registered entrypoints that are owned by the
      default group.
    - The returned list of entrypoints matches the expected list owned by the default group.
    """
    entrypoint_expected_list = list(registered_entrypoints.values())[:3]
    assert_retrieving_entrypoints_works(
        client,
        expected=entrypoint_expected_list,
        group_id=auth_account["groups"][0]["id"],
    )


def test_cannot_register_existing_entrypoint_name(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_entrypoints: dict[str, Any],
    registered_plugin_with_files: dict[str, Any],
    registered_queues: dict[str, Any],
) -> None:
    """Test that registering a entrypoint with an existing name fails.

    Given an authenticated user and registered entrypoints, this test validates the following
    sequence of actions:

    - The user attempts to register a second entrypoint with the same name.
    - The request fails with an appropriate error message and response code.
    """
    existing_entrypoint = registered_entrypoints["entrypoint1"]
    plugin_ids = [registered_plugin_with_files["plugin"]["id"]]
    queue_ids = [queue["id"] for queue in list(registered_queues.values())]

    assert_registering_existing_entrypoint_name_fails(
        client,
        name=existing_entrypoint["name"],
        description="",
        group_id=existing_entrypoint["group"]["id"],
        task_graph="",
        parameters=[],
        plugin_ids=plugin_ids,
        queue_ids=queue_ids,
    )


def test_rename_entrypoint(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_entrypoints: dict[str, Any],
) -> None:
    """Test that a entrypoint can be renamed.

    Given an authenticated user and registered entrypoints, this test validates the following
    sequence of actions:

    - The user issues a request to change the name of a entrypoint.
    - The user retrieves information about the same entrypoint and it reflects the name
      change.
    - The user issues a request to change the name of the entrypoint to the existing name.
    - The user retrieves information about the same entrypoint and verifies the name remains
      unchanged.
    - The user issues a request to change the name of a entrypoint to an existing entrypoint's
      name.
    - The request fails with an appropriate error message and response code.
    """
    updated_entrypoint_name = "new_entrypoint_name"
    entrypoint_to_rename = registered_entrypoints["entrypoint1"]
    existing_entrypoint = registered_entrypoints["entrypoint2"]
    queue_ids = [queue["id"] for queue in entrypoint_to_rename["queues"]]

    modified_entrypoint = modify_entrypoint(
        client,
        entrypoint_id=entrypoint_to_rename["id"],
        new_name=updated_entrypoint_name,
        new_description=entrypoint_to_rename["description"],
        new_task_graph=entrypoint_to_rename["taskGraph"],
        new_parameters=entrypoint_to_rename["parameters"],
        new_queue_ids=queue_ids,
    ).get_json()
    assert_entrypoint_name_matches_expected_name(
        client,
        entrypoint_id=entrypoint_to_rename["id"],
        expected_name=updated_entrypoint_name,
    )
    entrypoint_expected_list = [
        modified_entrypoint,
        registered_entrypoints["entrypoint2"],
        registered_entrypoints["entrypoint3"],
    ]
    assert_retrieving_entrypoints_works(client, expected=entrypoint_expected_list)

    modified_entrypoint = modify_entrypoint(
        client,
        entrypoint_id=entrypoint_to_rename["id"],
        new_name=updated_entrypoint_name,
        new_description=entrypoint_to_rename["description"],
        new_task_graph=entrypoint_to_rename["taskGraph"],
        new_parameters=entrypoint_to_rename["parameters"],
        new_queue_ids=entrypoint_to_rename["queues"],
    ).get_json()
    assert_entrypoint_name_matches_expected_name(
        client,
        entrypoint_id=entrypoint_to_rename["id"],
        expected_name=updated_entrypoint_name,
    )

    assert_cannot_rename_entrypoint_with_existing_name(
        client,
        entrypoint_id=entrypoint_to_rename["id"],
        existing_name=existing_entrypoint["name"],
        existing_description=entrypoint_to_rename["description"],
        existing_task_graph=entrypoint_to_rename["taskGraph"],
        existing_parameters=entrypoint_to_rename["parameters"],
        existing_queue_ids=entrypoint_to_rename["queues"],
    )


def test_delete_entrypoint_by_id(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_experiments: dict[str, Any],
) -> None:
    """Test that a entrypoint can be deleted by referencing its id.

    Given an authenticated user and registered entrypoints, this test validates the following
    sequence of actions:

    - The user deletes a entrypoint by referencing its id.
    - The user attempts to retrieve information about the deleted entrypoint.
    - The request fails with an appropriate error message and response code.
    - The entrypoint is no longer associated with the experiment.
    """
    experiment = registered_experiments["experiment1"]
    entrypoint_to_delete = experiment["entrypoints"][0]

    delete_entrypoint(client, entrypoint_id=entrypoint_to_delete["id"])
    assert_entrypoint_is_not_found(client, entrypoint_id=entrypoint_to_delete["id"])
    assert_entrypoint_is_not_associated_with_experiment(
        client, experiment_id=experiment["id"], entrypoint_id=entrypoint_to_delete["id"]
    )


def test_manage_existing_entrypoint_draft(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_entrypoints: dict[str, Any],
) -> None:
    """Test that a draft of an existing entrypoint can be created and managed by the user

    Given an authenticated user and registered entrypoints, this test validates the following
    sequence of actions:

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
    plugin_ids = [plugin["id"] for plugin in entrypoint["plugins"]]
    queue_ids = [queue["id"] for queue in entrypoint["queues"]]

    # test creation
    payload = {
        "name": name,
        "description": description,
        "taskGraph": task_graph,
        "parameters": parameters,
        "plugins": plugin_ids,
        "queues": queue_ids,
    }
    expected = {
        "user_id": auth_account["id"],
        "group_id": entrypoint["group"]["id"],
        "resource_id": entrypoint["id"],
        "resource_snapshot_id": entrypoint["snapshot"],
        "num_other_drafts": 0,
        "payload": payload,
    }
    response = actions.create_existing_resource_draft(
        client,
        resource_route=V1_ENTRYPOINTS_ROUTE,
        resource_id=entrypoint["id"],
        payload=payload,
    ).get_json()
    asserts.assert_draft_response_contents_matches_expectations(response, expected)
    asserts.assert_retrieving_draft_by_resource_id_works(
        client,
        resource_route=V1_ENTRYPOINTS_ROUTE,
        resource_id=entrypoint["id"],
        expected=response,
    )
    asserts.assert_creating_another_existing_draft_fails(
        client, resource_route=V1_ENTRYPOINTS_ROUTE, resource_id=entrypoint["id"]
    )

    # test modification
    payload = {"name": new_name, "description": description, "taskGraph": task_graph}
    expected = {
        "user_id": auth_account["id"],
        "group_id": entrypoint["group"]["id"],
        "resource_id": entrypoint["id"],
        "resource_snapshot_id": entrypoint["snapshot"],
        "num_other_drafts": 0,
        "payload": payload,
    }
    response = actions.modify_existing_resource_draft(
        client,
        resource_route=V1_ENTRYPOINTS_ROUTE,
        resource_id=entrypoint["id"],
        payload=payload,
    ).get_json()
    asserts.assert_draft_response_contents_matches_expectations(response, expected)

    # test deletion
    actions.delete_existing_resource_draft(
        client, resource_route=V1_ENTRYPOINTS_ROUTE, resource_id=entrypoint["id"]
    )
    asserts.assert_existing_draft_is_not_found(
        client, resource_route=V1_ENTRYPOINTS_ROUTE, resource_id=entrypoint["id"]
    )


def test_manage_new_entrypoint_drafts(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
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
    group_id = auth_account["groups"][0]["id"]
    drafts = {
        "draft1": {
            "name": "entrypoint1",
            "description": "new entrypoint",
            "taskGraph": "graph",
        },
        "draft2": {
            "name": "entrypoint2",
            "description": "entrypoint",
            "taskGraph": "graph",
            "queues": [1, 3],
            "plugins": [2],
        },
    }

    # test creation
    draft1_expected = {
        "user_id": auth_account["id"],
        "group_id": group_id,
        "payload": drafts["draft1"],
    }
    draft1_response = actions.create_new_resource_draft(
        client,
        resource_route=V1_ENTRYPOINTS_ROUTE,
        group_id=group_id,
        payload=drafts["draft1"],
    ).get_json()
    asserts.assert_draft_response_contents_matches_expectations(
        draft1_response, draft1_expected
    )
    asserts.assert_retrieving_draft_by_id_works(
        client,
        resource_route=V1_ENTRYPOINTS_ROUTE,
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
        resource_route=V1_ENTRYPOINTS_ROUTE,
        group_id=group_id,
        payload=drafts["draft2"],
    ).get_json()
    asserts.assert_draft_response_contents_matches_expectations(
        draft2_response, draft2_expected
    )
    asserts.assert_retrieving_draft_by_id_works(
        client,
        resource_route=V1_ENTRYPOINTS_ROUTE,
        draft_id=draft2_response["id"],
        expected=draft2_response,
    )
    asserts.assert_retrieving_drafts_works(
        client,
        resource_route=V1_ENTRYPOINTS_ROUTE,
        expected=[draft1_response, draft2_response],
    )

    # test modification
    draft1_mod = {
        "name": "draft1",
        "description": "new description",
        "taskGraph": "graph",
    }
    draft1_mod_expected = {
        "user_id": auth_account["id"],
        "group_id": group_id,
        "payload": draft1_mod,
    }
    response = actions.modify_new_resource_draft(
        client,
        resource_route=V1_ENTRYPOINTS_ROUTE,
        draft_id=draft1_response["id"],
        payload=draft1_mod,
    ).get_json()
    asserts.assert_draft_response_contents_matches_expectations(
        response, draft1_mod_expected
    )

    # test deletion
    actions.delete_new_resource_draft(
        client, resource_route=V1_ENTRYPOINTS_ROUTE, draft_id=draft1_response["id"]
    )
    asserts.assert_new_draft_is_not_found(
        client, resource_route=V1_ENTRYPOINTS_ROUTE, draft_id=draft1_response["id"]
    )


def test_manage_entrypoint_snapshots(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_entrypoints: dict[str, Any],
) -> None:
    """Test that different snapshots of a entrypoint can be retrieved by the user.

    Given an authenticated user and registered entrypoints, this test validates the following
    sequence of actions:

    - The user modifies a entrypoint
    - The user retrieves information about the original snapshot of the entrypoint and gets
      the expected response
    - The user retrieves information about the new snapshot of the entrypoint and gets the
      expected response
    - The user retrieves a list of all snapshots of the entrypoint and gets the expected
      response
    """
    entrypoint_to_rename = registered_entrypoints["entrypoint1"]
    queue_ids = [queue["id"] for queue in entrypoint_to_rename["queues"]]
    modified_entrypoint = modify_entrypoint(
        client,
        entrypoint_id=entrypoint_to_rename["id"],
        new_name=entrypoint_to_rename["name"] + "modified",
        new_description=entrypoint_to_rename["description"],
        new_task_graph=entrypoint_to_rename["taskGraph"],
        new_parameters=entrypoint_to_rename["parameters"],
        new_queue_ids=queue_ids,
    ).get_json()
    entrypoint_to_rename["latestSnapshot"] = False
    entrypoint_to_rename["lastModifiedOn"] = modified_entrypoint["lastModifiedOn"]
    entrypoint_to_rename.pop("queues")
    entrypoint_to_rename.pop("hasDraft")
    asserts.assert_retrieving_snapshot_by_id_works(
        client,
        resource_route=V1_ENTRYPOINTS_ROUTE,
        resource_id=entrypoint_to_rename["id"],
        snapshot_id=entrypoint_to_rename["snapshot"],
        expected=entrypoint_to_rename,
    )
    modified_entrypoint.pop("queues")
    modified_entrypoint.pop("hasDraft")
    asserts.assert_retrieving_snapshot_by_id_works(
        client,
        resource_route=V1_ENTRYPOINTS_ROUTE,
        resource_id=modified_entrypoint["id"],
        snapshot_id=modified_entrypoint["snapshot"],
        expected=modified_entrypoint,
    )
    expected_snapshots = [entrypoint_to_rename, modified_entrypoint]
    asserts.assert_retrieving_snapshots_works(
        client,
        resource_route=V1_ENTRYPOINTS_ROUTE,
        resource_id=entrypoint_to_rename["id"],
        expected=expected_snapshots,
    )


def test_tag_entrypoint(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_entrypoints: dict[str, Any],
    registered_tags: dict[str, Any],
) -> None:
    """Test that different versions of a entrypoint can be retrieved by the user.

    Given an authenticated user and registered entrypoints, this test validates the following
    sequence of actions:

    """
    entrypoint = registered_entrypoints["entrypoint1"]
    tags = [tag["id"] for tag in registered_tags.values()]

    # test append
    response = actions.append_tags(
        client,
        resource_route=V1_ENTRYPOINTS_ROUTE,
        resource_id=entrypoint["id"],
        tag_ids=[tags[0], tags[1]],
    )
    asserts.assert_tags_response_contents_matches_expectations(
        response.get_json(), [tags[0], tags[1]]
    )
    response = actions.append_tags(
        client,
        resource_route=V1_ENTRYPOINTS_ROUTE,
        resource_id=entrypoint["id"],
        tag_ids=[tags[1], tags[2]],
    )
    asserts.assert_tags_response_contents_matches_expectations(
        response.get_json(), [tags[0], tags[1], tags[2]]
    )

    # test remove
    actions.remove_tag(
        client,
        resource_route=V1_ENTRYPOINTS_ROUTE,
        resource_id=entrypoint["id"],
        tag_id=tags[1],
    )
    response = actions.get_tags(
        client, resource_route=V1_ENTRYPOINTS_ROUTE, resource_id=entrypoint["id"]
    )
    asserts.assert_tags_response_contents_matches_expectations(
        response.get_json(), [tags[0], tags[2]]
    )

    # test modify
    response = actions.modify_tags(
        client,
        resource_route=V1_ENTRYPOINTS_ROUTE,
        resource_id=entrypoint["id"],
        tag_ids=[tags[1], tags[2]],
    )
    asserts.assert_tags_response_contents_matches_expectations(
        response.get_json(), [tags[1], tags[2]]
    )

    # test delete
    response = actions.remove_tags(
        client, resource_route=V1_ENTRYPOINTS_ROUTE, resource_id=entrypoint["id"]
    )
    response = actions.get_tags(
        client, resource_route=V1_ENTRYPOINTS_ROUTE, resource_id=entrypoint["id"]
    )
    asserts.assert_tags_response_contents_matches_expectations(response.get_json(), [])
