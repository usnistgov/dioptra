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

"""Test suite for experiment operations.

This module contains a set of tests that validate the supported CRUD operations and
additional functionalities for the experiment entity. The tests ensure that the
experiments can be registered, retrieved, and deleted as expected through the REST API.
"""

from typing import Any

import pytest
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from werkzeug.test import TestResponse

from dioptra.restapi.routes import V1_EXPERIMENTS_ROUTE, V1_ROOT

from ..lib import actions, asserts, helpers

# -- Actions ---------------------------------------------------------------------------


def modify_experiment(
    client: FlaskClient,
    experiment_id: int,
    new_name: str,
    new_entrypoints: list[int],
    new_description: str,
) -> TestResponse:
    """Modify an experiment using the API.

    Args:
        client: The Flask test client.
        experiment_id: The id of the experiment to modify.
        new_name: The new name to assign to the experiment.
        new_entrypoints: The new entrypoints to associate with the experiment.
        new_description: The new description to assign to the experiment.

    Returns:
        The response from the API.
    """

    payload = {
        "name": new_name,
        "entrypoints": new_entrypoints,
        "description": new_description,
    }

    return client.put(
        f"/{V1_ROOT}/{V1_EXPERIMENTS_ROUTE}/{experiment_id}",
        json=payload,
        follow_redirects=True,
    )


def delete_experiment_with_id(client: FlaskClient, experiment_id: int) -> TestResponse:
    """Delete an experiment using the API.

    Args:
        client: The Flask test client.
        experiment_id: The id of the experiment to delete.

    Returns:
        The response from the API.
    """
    return client.delete(
        f"/{V1_ROOT}/{V1_EXPERIMENTS_ROUTE}/{experiment_id}",
        follow_redirects=True,
    )


# -- Assertions ------------------------------------------------------------------------


def assert_experiment_response_contents_matches_expectations(
    response: dict[str, Any], expected_contents: dict[str, Any]
) -> None:
    """Assert that the experiment response is valid.

    Args:
        response: The actual response from the API.
        expected_contents: The expected response from the API.

    Raises:
        AssertionError: If the API response does not match the expected response or
        if the response contents are not valid.
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
        "entrypoints",
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

    # Validate the EntryPointRef structure
    for entrypoint in response["entrypoints"]:
        assert isinstance(entrypoint["id"], int)
        assert isinstance(entrypoint["url"], str)
        assert isinstance(entrypoint["name"], str)
        assert isinstance(entrypoint["group"]["id"], int)
        assert isinstance(entrypoint["group"]["url"], str)
        assert isinstance(entrypoint["group"]["name"], str)

    # Validate the TagRef structure
    for tag in response["tags"]:
        assert isinstance(tag["id"], int)
        assert isinstance(tag["name"], str)
        assert isinstance(tag["url"], str)


def assert_retrieving_experiment_by_id_works(
    client: FlaskClient,
    experiment_id: int,
    expected: dict[str, Any],
) -> None:
    """Assert that retrieving an experiment by id works.

    Args:
        client: The Flask test client.
        experiment_id: The id of the experiment to retrieve.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = client.get(
        f"/{V1_ROOT}/{V1_EXPERIMENTS_ROUTE}/{experiment_id}", follow_redirects=True
    )
    assert response.status_code == 200 and response.get_json() == expected


def assert_experiment_entrypoints_matches_expected_entrypoints(
    client: FlaskClient,
    experiment_id: int,
    expected_entrypoints: dict[str, Any],
) -> None:
    """Assert that an experiment's associated entrypoints can be updated for an
    experiment with specified id.

    Args:
        client: The Flask test client.
        experiment_id: The id of the experiment to add entrypoints.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = client.get(
        f"/{V1_ROOT}/{V1_EXPERIMENTS_ROUTE}/{experiment_id}",
        follow_redirects=True,
    )
    assert response.status_code == 200
    response_entrypoints = [
        entrypoint["id"] for entrypoint in response.get_json()["entrypoints"]
    ]
    assert response_entrypoints == expected_entrypoints


def assert_retrieving_all_experiments_works(
    client: FlaskClient,
    expected: list[dict[str, Any]],
    group_id: int | None = None,
    search: str | None = None,
    paging_info: dict[str, Any] | None = None,
) -> None:
    """Assert that retrieving all experiments works.

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
        f"/{V1_ROOT}/{V1_EXPERIMENTS_ROUTE}",
        query_string=query_string,
        follow_redirects=True,
    )
    assert response.status_code == 200 and response.get_json()["data"] == expected


def assert_experiment_name_matches_expected_name(
    client: FlaskClient, experiment_id: int, expected_name: str
) -> None:
    """Assert that the name of an experiment matches the expected name.

    Args:
        client: The Flask test client.
        experiment_id: The id of the experiment to retrieve.
        expected_name: The expected name of the experiment.

    Raises:
        AssertionError: If the response status code is not 200 or if the name of the
            experiment does not match the expected name.
    """
    response = client.get(
        f"/{V1_ROOT}/{V1_EXPERIMENTS_ROUTE}/{experiment_id}",
        follow_redirects=True,
    )
    assert response.status_code == 200 and response.get_json()["name"] == expected_name


def assert_experiment_is_not_found(
    client: FlaskClient,
    experiment_id: int,
) -> None:
    """Assert that an experiment is not found.

    Args:
        client: The Flask test client.
        experiment_id: The id of the experiment to retrieve.

    Raises:
        AssertionError: If the response status code is not 404.
    """
    response = client.get(
        f"/{V1_ROOT}/{V1_EXPERIMENTS_ROUTE}/{experiment_id}",
        follow_redirects=True,
    )
    assert response.status_code == 404


# -- Tests -----------------------------------------------------------------------------


def test_create_experiment(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
) -> None:
    """Test that experiments can be registered and retrieved using the API.

    Given an authenticated user, this test validates the following sequence of actions:

    - A user registers an experiment named "experiment1".
    - The response is valid and matches the expected values of the registration request.
    - The user is able to retrieve information about the experiment using the
      experiment id.
    """

    name = "experiment1"
    user_id = auth_account["id"]
    group_id = auth_account["default_group_id"]
    description = "test description"

    experiment1_response = actions.register_experiment(
        client,
        name=name,
        group_id=group_id,
        description=description,
    )
    experiment1_expected = experiment1_response.get_json()
    assert_experiment_response_contents_matches_expectations(
        response=experiment1_expected,
        expected_contents={
            "name": name,
            "user_id": user_id,
            "group_id": group_id,
            "description": description,
        },
    )
    assert_retrieving_experiment_by_id_works(
        client,
        experiment_id=experiment1_expected["id"],
        expected=experiment1_expected,
    )


def test_experiment_get_all(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_experiments: dict[str, Any],
) -> None:
    """Test that all experiments can be retrieved.

    Given an authenticated user and registered experiments, this test validates the
        following sequence of actions:

    - A user registers three experiments, "experiment1", "experiment2", and
      "experiment3".
    - The user is able to retrieve a list of all registered experiments.
    - The returned list of experiments matches the full list of registered experiments.
    """
    experiment1_expected = registered_experiments["experiment1"]
    experiment2_expected = registered_experiments["experiment2"]
    experiment3_expected = registered_experiments["experiment3"]
    experiment_expected_list = [
        experiment1_expected,
        experiment2_expected,
        experiment3_expected,
    ]

    assert_retrieving_all_experiments_works(client, expected=experiment_expected_list)


def test_experiment_search_query(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_experiments: dict[str, Any],
) -> None:
    """Test that experiments can be queried with a search term.

    Given an authenticated user and registered experiments, this test validates the
        following sequence of actions:

    - The user is able to retrieve a list of all registered experiments with a name
      that contains 'experiment'.
    - The returned list of experiments matches the expected matches from the query.
    """
    experiment1_expected = registered_experiments["experiment1"]
    experiment2_expected = registered_experiments["experiment2"]
    experiment3_expected = registered_experiments["experiment3"]
    experiment_expected_list = [
        experiment1_expected,
        experiment2_expected,
        experiment3_expected,
    ]

    assert_retrieving_all_experiments_works(
        client,
        expected=experiment_expected_list,
        search="description:*description*",
    )

    assert_retrieving_all_experiments_works(
        client,
        expected=experiment_expected_list,
        search="name:*experiment*",
    )

    assert_retrieving_all_experiments_works(
        client,
        expected=experiment_expected_list,
        search="*",
    )


def test_experiment_group_query(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_experiments: dict[str, Any],
) -> None:
    """Test that experiments can be retrieved using a group filter.

    Given an authenticated user and registered experiments, this test validates the
        following sequence of actions:

    - The user is able to retrieve a list of all registered experiments that are owned
      by the default group.
    - The returned list of experiments matches the expected list owned by the default
      group.
    """
    experiment1_expected = registered_experiments["experiment1"]
    experiment2_expected = registered_experiments["experiment2"]
    experiment3_expected = registered_experiments["experiment3"]
    experiment_expected_list = [
        experiment1_expected,
        experiment2_expected,
        experiment3_expected,
    ]

    assert_retrieving_all_experiments_works(
        client,
        expected=experiment_expected_list,
        group_id=auth_account["default_group_id"],
    )


def test_experiment_get_by_id(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_experiments: dict[str, Any],
) -> None:
    """Test that experiments can be retrieved by their unique ID.

    Given an authenticated user and registered experiments, this test validates the
        following sequence of actions:

    - The user is able to retrieve a single experiment by its ID.
    - The response is a single experiment with a matching ID.
    """
    experiment2_expected = registered_experiments["experiment2"]

    assert_retrieving_experiment_by_id_works(
        client,
        experiment_id=experiment2_expected["id"],
        expected=experiment2_expected,
    )


def test_rename_experiment(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_experiments: dict[str, Any],
) -> None:
    """Test that an experiment can be renamed.

    Given an authenticated user and registered experiments, this test validates the
    following sequence of actions:

    - The user issues a request to change the name of an experiment.
    - The user retrieves information about the same experiment and it reflects
      the name change.
    """
    updated_experiment_name = "experiment0"
    experiment_to_rename = registered_experiments["experiment1"]
    existing_description = experiment_to_rename["description"]
    modify_experiment(
        client,
        experiment_id=experiment_to_rename["id"],
        new_name=updated_experiment_name,
        new_description=existing_description,
        new_entrypoints=[],  # TODO use existing entrypoints
    )
    assert_experiment_name_matches_expected_name(
        client,
        experiment_id=experiment_to_rename["id"],
        expected_name=updated_experiment_name,
    )


def test_delete_experiment_by_id(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_experiments: dict[str, Any],
) -> None:
    """Test that an experiment can be deleted by referencing its id.

    Given an authenticated user and registered experiments, this test validates the
        following sequence of actions:

    - The user deletes the "experiment3" experiment by referencing its id.
    - The user attempts to retrieve information about the "experiment3" experiment,
      and the response indicates it is no longer found.
    """
    experiment_to_delete = registered_experiments["experiment3"]
    delete_experiment_with_id(client, experiment_id=experiment_to_delete["id"])
    assert_experiment_is_not_found(client, experiment_id=experiment_to_delete["id"])


def test_experiment_get_entrypoints(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_entrypoints: dict[str, Any],
) -> None:
    """Test that an experiment's associated entrypoints can be retrieved by referencing
    the experiment's id.

    This test validates the following sequence of actions:

    - A user registers an experiment named "experiment1".
    - The user is able to retrieve entrypoints information about the "experiment1"
      experiment that matches the information provided during registration.
    """
    name = "experiment1"
    user_id = auth_account["id"]
    group_id = auth_account["default_group_id"]
    description = "test description"
    entrypoints = [registered_entrypoints["entrypoint1"]["id"]]
    registration_response = actions.register_experiment(
        client,
        name=name,
        group_id=group_id,
        entrypoint_ids=entrypoints,
        description=description,
    )
    experiment_json = registration_response.get_json()
    experiment_id = experiment_json["id"]

    assert_experiment_response_contents_matches_expectations(
        response=experiment_json,
        expected_contents={
            "name": name,
            "user_id": user_id,
            "group_id": group_id,
            "entrypoint_ids": entrypoints,
            "description": description,
        },
    )

    assert_experiment_entrypoints_matches_expected_entrypoints(
        client,
        experiment_id=experiment_id,
        expected_entrypoints=entrypoints,
    )


@pytest.mark.skip(reason="entrypoints not yet implmented")
# @pytest.mark.parametrize(
#     "initial_entrypoints",
#     "new_entrypoints",
#     "expected_entrypoints",
#     [
#         ([1, 2, 3], [4], [1, 2, 3, 4]),
#         ([], [1, 2], [1, 2]),
#         ([1, 2, 3], [2], [1, 2, 3]),
#     ]
# )
def test_experiment_add_entrypoints(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    initial_entrypoints: list[int],
    new_entrypoints: list[int],
    expected_entrypoints: list[int],
) -> None:
    """Test that entrypoints can be added to and retrieved from an experiment using
    the API.

    Given an authenticated user, this test validates the following sequence of actions:

    - A user creates an experiment, "experiment1" with initial entrypoints.
    - The user is able to add an associated entry point to "experiment1".
    - The user is able to retrieve the same experiment's information, and it reflects
      the new entrypoint association.
    """
    name = "experiment1"
    description = "test description"
    user_id = auth_account["id"]
    group_id = auth_account["default_group_id"]

    experiment1_response = actions.register_experiment(
        client,
        name=name,
        group_id=group_id,
        entrypoints=initial_entrypoints,
        description=description,
    )
    experiment1_json = experiment1_response.get_json()
    experiment_id = experiment1_json["id"]
    assert_experiment_response_contents_matches_expectations(
        response=experiment1_json,
        expected_contents={
            "name": name,
            "user_id": user_id,
            "group_id": group_id,
            "entrypoints": initial_entrypoints,
            "description": description,
        },
    )

    modify_experiment(
        client,
        experiment_id=experiment1_json["id"],
        new_name=name,
        new_description=description,
        new_entrypoints=initial_entrypoints + new_entrypoints,
    )

    assert_experiment_entrypoints_matches_expected_entrypoints(
        client, experiment_id=experiment_id, expected_entrypoints=expected_entrypoints
    )


@pytest.mark.skip(reason="entrypoints not yet implmented")
# @pytest.mark.parametrize(
#     "initial_entrypoints", "new_entrypoints", "expected_entrypoints",
#     [
#         ([1, 2, 3], [4, 5], [4, 5]),
#         ([1, 2, 3], [2, 3, 4], [2, 3, 4]),
#         ([1, 2, 3], [], []),
#     ],
# )
def test_experiment_modify_entrypoints(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    initial_entrypoints: list[int],
    new_entrypoints: list[int],
    expected_entrypoints: list[int],
) -> None:
    """Test that entrypoints can be replaced and retrieved from an experiment using
    the API.

    Given an authenticated user, this test validates the following sequence of actions:

    - A user creates an experiment, "experiment1".
    - The user is able to replace associated entrypoints for "experiment1".
    - The user is able to retrieve the same experiment's information, and it reflects
      the new entrypoint associations.
    """
    name = "experiment1"
    description = "test description"
    user_id = auth_account["id"]
    group_id = auth_account["default_group_id"]

    experiment1_response = actions.register_experiment(
        client,
        name=name,
        group_id=group_id,
        entrypoints=initial_entrypoints,
        description=description,
    )
    experiment1_json = experiment1_response.get_json()
    experiment_id = experiment1_json["id"]
    assert_experiment_response_contents_matches_expectations(
        response=experiment1_json,
        expected_contents={
            "name": name,
            "user_id": user_id,
            "group_id": group_id,
            "entrypoints": initial_entrypoints,
            "description": description,
        },
    )
    modify_experiment(
        client,
        experiment_id=experiment_id,
        new_name=name,
        new_entrypoints=new_entrypoints,
        new_description=description,
    )

    assert_experiment_entrypoints_matches_expected_entrypoints(
        client,
        experiment_id=experiment_id,
        expected_entrypoints=expected_entrypoints,
    )


@pytest.mark.skip(reason="entrypoints not yet implmented")
# @pytest.mark.parametrize(
#     "initial_entrypoints", "entrypoints_to_remove", "expected_entrypoints",
#     [
#         ([1, 2, 3], [2, 3], [3]),
#         ([1, 2, 3], [4], [1, 2, 3]),
#         ([], [1], []),
#     ]
# )
def test_experiment_remove_entrypoints(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    initial_entrypoints: list[int],
    entrypoints_to_remove: list[int],
    expected_entrypoints: list[int],
) -> None:
    """Test that entrypoints can be removed from an experiment using the API.

    Given an authenticated user, this test validates the following sequence of actions:

    - A user creates an experiment, "experiment1".
    - The user is able to remove associated entrypoints for "experiment1".
    - The user is able to retrieve the same experiment's information, and it reflects
      the new entrypoint associations.
    """
    name = "experiment1"
    description = "test description"
    user_id = auth_account["id"]
    group_id = auth_account["default_group_id"]

    experiment1_response = actions.register_experiment(
        client,
        name=name,
        group_id=group_id,
        entrypoints=initial_entrypoints,
        description=description,
    )
    experiment1_json = experiment1_response.get_json()
    experiment_id = experiment1_json["id"]
    assert_experiment_response_contents_matches_expectations(
        response=experiment1_json,
        expected_contents={
            "name": name,
            "user_id": user_id,
            "group_id": group_id,
            "entrypoints": initial_entrypoints,
            "description": description,
        },
    )

    updated_entrypoints = []
    for entry in initial_entrypoints:
        if entry not in entrypoints_to_remove:
            updated_entrypoints.append(entry)

    modify_experiment(
        client,
        experiment_id=experiment_id,
        new_name=name,
        new_entrypoints=updated_entrypoints,
        new_description=description,
    )

    assert_experiment_entrypoints_matches_expected_entrypoints(
        client,
        experiment_id=experiment_id,
        expected_entrypoints=expected_entrypoints,
    )


def test_manage_existing_experiment_draft(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_experiments: dict[str, Any],
) -> None:
    """Test that a draft of an existing experiment can be created and managed by the user

    Given an authenticated user and registered experiments, this test validates the
    following sequence of actions:

    - The user creates a draft of an existing experiment
    - The user retrieves information about the draft and gets the expected response
    - The user attempts to create another draft of the same existing experiment
    - The request fails with an appropriate error message and response code.
    - The user modifies the name of the experiment in the draft
    - The user retrieves information about the draft and gets the expected response
    - The user deletes the draft
    - The user attempts to retrieve information about the deleted draft.
    - The request fails with an appropriate error message and response code.
    """
    experiment = registered_experiments["experiment1"]
    name = "draft"
    new_name = "draft2"
    description = "description"

    # test creation
    payload = {"name": name, "description": description, "entrypoints": [1]}
    expected = {
        "user_id": auth_account["id"],
        "group_id": experiment["group"]["id"],
        "resource_id": experiment["id"],
        "resource_snapshot_id": experiment["snapshot"],
        "num_other_drafts": 0,
        "payload": payload,
    }
    response = actions.create_existing_resource_draft(
        client,
        resource_route=V1_EXPERIMENTS_ROUTE,
        resource_id=experiment["id"],
        payload=payload,
    ).get_json()
    asserts.assert_draft_response_contents_matches_expectations(response, expected)
    asserts.assert_retrieving_draft_by_resource_id_works(
        client,
        resource_route=V1_EXPERIMENTS_ROUTE,
        resource_id=experiment["id"],
        expected=response,
    )
    asserts.assert_creating_another_existing_draft_fails(
        client, resource_route=V1_EXPERIMENTS_ROUTE, resource_id=experiment["id"]
    )

    # test modification
    payload = {"name": new_name, "description": description, "entrypoints": [3, 2]}
    expected = {
        "user_id": auth_account["id"],
        "group_id": experiment["group"]["id"],
        "resource_id": experiment["id"],
        "resource_snapshot_id": experiment["snapshot"],
        "num_other_drafts": 0,
        "payload": payload,
    }
    response = actions.modify_existing_resource_draft(
        client,
        resource_route=V1_EXPERIMENTS_ROUTE,
        resource_id=experiment["id"],
        payload=payload,
    ).get_json()
    asserts.assert_draft_response_contents_matches_expectations(response, expected)

    # test deletion
    actions.delete_existing_resource_draft(
        client, resource_route=V1_EXPERIMENTS_ROUTE, resource_id=experiment["id"]
    )
    asserts.assert_existing_draft_is_not_found(
        client, resource_route=V1_EXPERIMENTS_ROUTE, resource_id=experiment["id"]
    )


def test_manage_new_experiment_drafts(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
) -> None:
    """Test that drafts of experiment can be created and managed by the user

    Given an authenticated user, this test validates the following sequence of actions:

    - The user creates two experiment drafts
    - The user retrieves information about the drafts and gets the expected response
    - The user modifies the description of the experiment in the first draft
    - The user retrieves information about the draft and gets the expected response
    - The user deletes the first draft
    - The user attempts to retrieve information about the deleted draft.
    - The request fails with an appropriate error message and response code.
    """
    group_id = auth_account["groups"][0]["id"]
    drafts = {
        "draft1": {
            "name": "experiment1",
            "description": "my experiment",
            "entrypoints": [3],
        },
        "draft2": {"name": "experiment2", "description": None, "entrypoints": [3, 4]},
    }

    # test creation
    draft1_expected = {
        "user_id": auth_account["id"],
        "group_id": group_id,
        "payload": drafts["draft1"],
    }
    draft1_response = actions.create_new_resource_draft(
        client,
        resource_route=V1_EXPERIMENTS_ROUTE,
        group_id=group_id,
        payload=drafts["draft1"],
    ).get_json()
    asserts.assert_draft_response_contents_matches_expectations(
        draft1_response, draft1_expected
    )
    asserts.assert_retrieving_draft_by_id_works(
        client,
        resource_route=V1_EXPERIMENTS_ROUTE,
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
        resource_route=V1_EXPERIMENTS_ROUTE,
        group_id=group_id,
        payload=drafts["draft2"],
    ).get_json()
    asserts.assert_draft_response_contents_matches_expectations(
        draft2_response, draft2_expected
    )
    asserts.assert_retrieving_draft_by_id_works(
        client,
        resource_route=V1_EXPERIMENTS_ROUTE,
        draft_id=draft2_response["id"],
        expected=draft2_response,
    )
    asserts.assert_retrieving_drafts_works(
        client,
        resource_route=V1_EXPERIMENTS_ROUTE,
        expected=[draft1_response, draft2_response],
    )

    # test modification
    draft1_mod = {"name": "draft1", "description": "new description", "entrypoints": []}
    draft1_mod_expected = {
        "user_id": auth_account["id"],
        "group_id": group_id,
        "payload": draft1_mod,
    }
    response = actions.modify_new_resource_draft(
        client,
        resource_route=V1_EXPERIMENTS_ROUTE,
        draft_id=draft1_response["id"],
        payload=draft1_mod,
    ).get_json()
    asserts.assert_draft_response_contents_matches_expectations(
        response, draft1_mod_expected
    )

    # test deletion
    actions.delete_new_resource_draft(
        client, resource_route=V1_EXPERIMENTS_ROUTE, draft_id=draft1_response["id"]
    )
    asserts.assert_new_draft_is_not_found(
        client, resource_route=V1_EXPERIMENTS_ROUTE, draft_id=draft1_response["id"]
    )


def test_manage_experiment_snapshots(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_experiments: dict[str, Any],
) -> None:
    """Test that different snapshots of an experiment can be retrieved by the user.

    Given an authenticated user and registered experiments, this test validates the
    following sequence of actions:

    - The user modifies an experiment
    - The user retrieves information about the original snapshot of the experiment and
      gets the expected response
    - The user retrieves information about the new snapshot of the experiment and gets
      the expected response
    - The user retrieves a list of all snapshots of the experiment and gets the expected
      response
    """
    experiment_to_rename = registered_experiments["experiment1"]
    modified_experiment = modify_experiment(
        client,
        experiment_id=experiment_to_rename["id"],
        new_name=experiment_to_rename["name"] + "modified",
        new_description=experiment_to_rename["description"],
        new_entrypoints=[],  # TODO use existing entrypoints
    ).get_json()
    modified_experiment.pop("hasDraft")
    modified_experiment.pop("entrypoints")
    experiment_to_rename.pop("hasDraft")
    experiment_to_rename.pop("entrypoints")
    experiment_to_rename["latestSnapshot"] = False
    experiment_to_rename["lastModifiedOn"] = modified_experiment["lastModifiedOn"]
    asserts.assert_retrieving_snapshot_by_id_works(
        client,
        resource_route=V1_EXPERIMENTS_ROUTE,
        resource_id=experiment_to_rename["id"],
        snapshot_id=experiment_to_rename["snapshot"],
        expected=experiment_to_rename,
    )
    expected_snapshots = [experiment_to_rename, modified_experiment]
    asserts.assert_retrieving_snapshots_works(
        client,
        resource_route=V1_EXPERIMENTS_ROUTE,
        resource_id=experiment_to_rename["id"],
        expected=expected_snapshots,
    )


def test_tag_experiment(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_experiments: dict[str, Any],
    registered_tags: dict[str, Any],
) -> None:
    """Test that tags can applied to experiments.

    Given an authenticated user and registered experiments, this test validates the
    following sequence of actions:

    """
    experiment = registered_experiments["experiment1"]
    tags = [tag["id"] for tag in registered_tags.values()]

    # test append
    response = actions.append_tags(
        client,
        resource_route=V1_EXPERIMENTS_ROUTE,
        resource_id=experiment["id"],
        tag_ids=[tags[0], tags[1]],
    )
    asserts.assert_tags_response_contents_matches_expectations(
        response.get_json(), [tags[0], tags[1]]
    )
    response = actions.append_tags(
        client,
        resource_route=V1_EXPERIMENTS_ROUTE,
        resource_id=experiment["id"],
        tag_ids=[tags[1], tags[2]],
    )
    asserts.assert_tags_response_contents_matches_expectations(
        response.get_json(), [tags[0], tags[1], tags[2]]
    )

    # test remove
    actions.remove_tag(
        client,
        resource_route=V1_EXPERIMENTS_ROUTE,
        resource_id=experiment["id"],
        tag_id=tags[1],
    )
    response = actions.get_tags(
        client, resource_route=V1_EXPERIMENTS_ROUTE, resource_id=experiment["id"]
    )
    asserts.assert_tags_response_contents_matches_expectations(
        response.get_json(), [tags[0], tags[2]]
    )

    # test modify
    response = actions.modify_tags(
        client,
        resource_route=V1_EXPERIMENTS_ROUTE,
        resource_id=experiment["id"],
        tag_ids=[tags[1], tags[2]],
    )
    asserts.assert_tags_response_contents_matches_expectations(
        response.get_json(), [tags[1], tags[2]]
    )

    # test delete
    response = actions.remove_tags(
        client, resource_route=V1_EXPERIMENTS_ROUTE, resource_id=experiment["id"]
    )
    response = actions.get_tags(
        client, resource_route=V1_EXPERIMENTS_ROUTE, resource_id=experiment["id"]
    )
    asserts.assert_tags_response_contents_matches_expectations(response.get_json(), [])
