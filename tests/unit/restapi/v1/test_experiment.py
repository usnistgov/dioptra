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
from http import HTTPStatus
from typing import Any

import pytest
from flask_sqlalchemy import SQLAlchemy

from dioptra.client.base import DioptraResponseProtocol
from dioptra.client.client import DioptraClient

from ..lib import helpers, routines
from ..test_utils import assert_retrieving_resource_works

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
        "snapshotCreatedOn",
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
    assert isinstance(response["snapshotCreatedOn"], str)
    assert isinstance(response["lastModifiedOn"], str)
    assert isinstance(response["latestSnapshot"], bool)

    assert response["name"] == expected_contents["name"]
    assert response["description"] == expected_contents["description"]

    assert helpers.is_iso_format(response["createdOn"])
    assert helpers.is_iso_format(response["snapshotCreatedOn"])
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
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    response = dioptra_client.experiments.get_by_id(experiment_id)
    assert response.status_code == HTTPStatus.OK and response.json() == expected


def assert_experiment_entrypoints_matches_expected_entrypoints(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    response = dioptra_client.experiments.get_by_id(experiment_id)
    response_entrypoints = [
        entrypoint["id"] for entrypoint in response.json()["entrypoints"]
    ]
    assert (
        response.status_code == HTTPStatus.OK
        and response_entrypoints == expected_entrypoints
    )


def assert_retrieving_all_experiments_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    expected: list[dict[str, Any]],
    group_id: int | None = None,
    sort_by: str | None = None,
    descending: bool | None = None,
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
    assert_retrieving_resource_works(
        dioptra_client=dioptra_client.experiments,
        expected=expected,
        group_id=group_id,
        sort_by=sort_by,
        descending=descending,
        search=search,
        paging_info=paging_info,
    )


def assert_experiment_name_matches_expected_name(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    experiment_id: int,
    expected_name: str,
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
    response = dioptra_client.experiments.get_by_id(experiment_id)
    assert (
        response.status_code == HTTPStatus.OK
        and response.json()["name"] == expected_name
    )


def assert_experiment_is_not_found(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    experiment_id: int,
) -> None:
    """Assert that an experiment is not found.

    Args:
        client: The Flask test client.
        experiment_id: The id of the experiment to retrieve.

    Raises:
        AssertionError: If the response status code is not 404.
    """
    response = dioptra_client.experiments.get_by_id(experiment_id)
    assert response.status_code == HTTPStatus.NOT_FOUND


def assert_retrieving_all_entrypoints_for_experiment_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    experiment_id: int,
    expected: list[int],
) -> None:
    response = dioptra_client.experiments.entrypoints.get(experiment_id)
    assert (
        response.status_code == HTTPStatus.OK
        and [entrypoint_ref["id"] for entrypoint_ref in response.json()] == expected
    )


def assert_append_entrypoints_to_experiment_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    experiment_id: int,
    entrypoint_ids: list[int],
    expected: list[int],
) -> None:
    response = dioptra_client.experiments.entrypoints.create(
        experiment_id=experiment_id,
        entrypoint_ids=entrypoint_ids,
    )
    assert (
        response.status_code == HTTPStatus.OK
        and [entrypoint_ref["id"] for entrypoint_ref in response.json()] == expected
    )


# -- Tests -----------------------------------------------------------------------------


def test_create_experiment(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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

    experiment1_response = dioptra_client.experiments.create(
        group_id=group_id,
        name=name,
        description=description,
    )
    experiment1_expected = experiment1_response.json()
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
        dioptra_client,
        experiment_id=experiment1_expected["id"],
        expected=experiment1_expected,
    )


def test_experiment_get_all(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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

    assert_retrieving_all_experiments_works(
        dioptra_client, expected=experiment_expected_list
    )


@pytest.mark.parametrize(
    "sortBy, descending , expected",
    [
        ("name", True, ["experiment3", "experiment2", "experiment1"]),
        ("name", False, ["experiment1", "experiment2", "experiment3"]),
        ("createdOn", True, ["experiment3", "experiment2", "experiment1"]),
        ("createdOn", False, ["experiment1", "experiment2", "experiment3"]),
    ],
)
def test_experiment_sort(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_experiments: dict[str, Any],
    sortBy: str,
    descending: bool,
    expected: list[str],
) -> None:
    """Test that experiments can be sorted by column.

    Given an authenticated user and registered experiments, this test validates the
      following sequence of actions:

    - A user registers three experiments: "experiment1", "experiment2", "experiment3".
    - The user is able to retrieve a list of all registered experiments sorted by a
      column ascending/descending.
    - The returned list of experiments matches the order in the parametrize lists above.
    """

    expected_experiments = [
        registered_experiments[expected_name] for expected_name in expected
    ]
    assert_retrieving_all_experiments_works(
        dioptra_client, expected=expected_experiments
    )


def test_experiment_search_query(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
        dioptra_client,
        expected=experiment_expected_list,
        search="description:*description*",
    )

    assert_retrieving_all_experiments_works(
        dioptra_client,
        expected=experiment_expected_list,
        search="name:*experiment*",
    )

    assert_retrieving_all_experiments_works(
        dioptra_client,
        expected=experiment_expected_list,
        search="*",
    )


def test_experiment_group_query(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
        dioptra_client,
        expected=experiment_expected_list,
        group_id=auth_account["default_group_id"],
    )


def test_experiment_get_by_id(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
        dioptra_client,
        experiment_id=experiment2_expected["id"],
        expected=experiment2_expected,
    )


def test_rename_experiment(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    dioptra_client.experiments.modify_by_id(
        experiment_id=experiment_to_rename["id"],
        name=updated_experiment_name,
        description=existing_description,
        entrypoints=[],
    )
    assert_experiment_name_matches_expected_name(
        dioptra_client,
        experiment_id=experiment_to_rename["id"],
        expected_name=updated_experiment_name,
    )


def test_delete_experiment_by_id(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    dioptra_client.experiments.delete_by_id(experiment_to_delete["id"])
    assert_experiment_is_not_found(
        dioptra_client, experiment_id=experiment_to_delete["id"]
    )


def test_experiment_get_entrypoints(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    registration_response = dioptra_client.experiments.create(
        group_id=group_id,
        name=name,
        description=description,
        entrypoints=entrypoints,
    )
    experiment_json = registration_response.json()
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
        dioptra_client,
        experiment_id=experiment_id,
        expected_entrypoints=entrypoints,
    )


@pytest.mark.skip(reason="entrypoints not yet implemented")
# @pytest.mark.parametrize(
#     "initial_entrypoints, new_entrypoints, expected_entrypoints",
#     [
#         ([1, 2, 3], [4], [1, 2, 3, 4]),
#         ([], [1, 2], [1, 2]),
#         ([1, 2, 3], [2], [1, 2, 3]),
#     ],
# )
def test_experiment_add_entrypoints(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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

    experiment1_response = dioptra_client.experiments.create(
        group_id=group_id,
        name=name,
        description=description,
        entrypoints=initial_entrypoints,
    )
    experiment1_json = experiment1_response.json()
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

    dioptra_client.experiments.modify_by_id(
        experiment_id=experiment_id,
        name=name,
        description=description,
        entrypoints=initial_entrypoints + new_entrypoints,
    )
    assert_experiment_entrypoints_matches_expected_entrypoints(
        dioptra_client,
        experiment_id=experiment_id,
        expected_entrypoints=expected_entrypoints,
    )


@pytest.mark.skip(reason="entrypoints not yet implemented")
# @pytest.mark.parametrize(
#     "initial_entrypoints, new_entrypoints, expected_entrypoints",
#     [
#         ([1, 2, 3], [4, 5], [4, 5]),
#         ([1, 2, 3], [2, 3, 4], [2, 3, 4]),
#         ([1, 2, 3], [], []),
#     ],
# )
def test_experiment_modify_entrypoints(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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

    experiment1_response = dioptra_client.experiments.create(
        group_id=group_id,
        name=name,
        description=description,
        entrypoints=initial_entrypoints,
    )
    experiment1_json = experiment1_response.json()
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

    dioptra_client.experiments.modify_by_id(
        experiment_id=experiment_id,
        name=name,
        description=description,
        entrypoints=new_entrypoints,
    )
    assert_experiment_entrypoints_matches_expected_entrypoints(
        dioptra_client,
        experiment_id=experiment_id,
        expected_entrypoints=expected_entrypoints,
    )


@pytest.mark.skip(reason="entrypoints not yet implemented")
# @pytest.mark.parametrize(
#     "initial_entrypoints, entrypoints_to_remove, expected_entrypoints",
#     [
#         ([1, 2, 3], [2, 3], [3]),
#         ([1, 2, 3], [4], [1, 2, 3]),
#         ([], [1], []),
#     ]
# )
def test_experiment_remove_entrypoints(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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

    experiment1_response = dioptra_client.experiments.create(
        group_id=group_id,
        name=name,
        description=description,
        entrypoints=initial_entrypoints,
    )
    experiment1_json = experiment1_response.json()
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

    dioptra_client.experiments.modify_by_id(
        experiment_id=experiment_id,
        name=name,
        description=description,
        entrypoints=updated_entrypoints,
    )
    assert_experiment_entrypoints_matches_expected_entrypoints(
        dioptra_client,
        experiment_id=experiment_id,
        expected_entrypoints=expected_entrypoints,
    )


def test_manage_existing_experiment_draft(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_experiments: dict[str, Any],
    registered_entrypoints: dict[str, Any],
) -> None:
    """Test that a draft of an existing experiment can be created and managed by the
        user

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
    # Requests data
    experiment = registered_experiments["experiment1"]
    name = "draft"
    new_name = "draft2"
    description = "description"

    # test creation
    draft = {
        "name": name,
        "description": description,
        "entrypoints": [registered_entrypoints["entrypoint1"]["id"]],
    }
    draft_mod = {
        "name": new_name,
        "description": description,
        "entrypoints": [
            registered_entrypoints["entrypoint3"]["id"],
            registered_entrypoints["entrypoint2"]["id"],
        ],
    }

    # Expected responses
    draft_expected = {
        "user_id": auth_account["id"],
        "group_id": experiment["group"]["id"],
        "resource_id": experiment["id"],
        "resource_snapshot_id": experiment["snapshot"],
        "num_other_drafts": 0,
        "payload": draft,
    }
    draft_mod_expected = {
        "user_id": auth_account["id"],
        "group_id": experiment["group"]["id"],
        "resource_id": experiment["id"],
        "resource_snapshot_id": experiment["snapshot"],
        "num_other_drafts": 0,
        "payload": draft_mod,
    }

    # Run routine: existing resource drafts tests
    routines.run_existing_resource_drafts_tests(
        dioptra_client.experiments,
        dioptra_client.experiments.modify_resource_drafts,
        dioptra_client.workflows,
        experiment["id"],
        draft=draft,
        draft_mod=draft_mod,
        draft_expected=draft_expected,
        draft_mod_expected=draft_mod_expected,
    )


def test_manage_new_experiment_drafts(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_entrypoints: dict[str, Any],
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
    # Requests data
    group_id = auth_account["groups"][0]["id"]
    drafts = {
        "draft1": {
            "name": "experiment1",
            "description": "my experiment",
            "entrypoints": [registered_entrypoints["entrypoint3"]["id"]],
        },
        "draft2": {
            "name": "experiment2",
            "description": None,
            "entrypoints": [
                registered_entrypoints["entrypoint2"]["id"],
                registered_entrypoints["entrypoint1"]["id"],
            ],
        },
    }
    draft1_mod = {"name": "draft1", "description": "new description", "entrypoints": []}

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
        dioptra_client.experiments,
        dioptra_client.experiments.new_resource_drafts,
        dioptra_client.workflows,
        drafts=drafts,
        draft1_mod=draft1_mod,
        draft1_expected=draft1_expected,
        draft2_expected=draft2_expected,
        draft1_mod_expected=draft1_mod_expected,
        group_id=group_id,
    )


def test_manage_experiment_snapshots(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    modified_experiment = dioptra_client.experiments.modify_by_id(
        experiment_id=experiment_to_rename["id"],
        name=experiment_to_rename["name"] + "modified",
        description=experiment_to_rename["description"],
        entrypoints=[],
    ).json()

    # Run routine: resource snapshots tests
    routines.run_resource_snapshots_tests(
        dioptra_client.experiments.snapshots,
        resource_to_rename=experiment_to_rename.copy(),
        modified_resource=modified_experiment.copy(),
        drop_additional_fields=["entrypoints"],
    )


def test_tag_experiment(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    tag_ids = [tag["id"] for tag in registered_tags.values()]

    # Run routine: resource tag tests
    routines.run_resource_tag_tests(
        dioptra_client.experiments.tags,
        experiment["id"],
        tag_ids=tag_ids,
    )


def test_get_all_entrypoints_for_experiment(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_entrypoints: dict[str, Any],
    registered_experiments: dict[str, Any],
) -> None:
    """Test that entrypoints associated with experiments can be retrieved.
    Given an authenticated user, registered experiments, and registered entrypoints,
    this test validates the following sequence of actions:
    - A user retrieves a list of all entrypoint refs associated with the experiment.
    """
    experiment_id = registered_experiments["experiment1"]["id"]
    expected_entrypoint_ids = [
        entrypoint["id"] for entrypoint in list(registered_entrypoints.values())
    ]
    assert_retrieving_all_entrypoints_for_experiment_works(
        dioptra_client,
        experiment_id=experiment_id,
        expected=expected_entrypoint_ids,
    )


def test_append_entrypoints_to_experiment(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_entrypoints: dict[str, Any],
    registered_experiments: dict[str, Any],
) -> None:
    """Test that entrypoints can be appended to experiments.
    Given an authenticated user, registered experiments, and registered entrypoints,
    this test validates the following sequence of actions:
    - A user adds new entrypoint to the list of associated entrypoints with the experiment.
    - A user can then retreive the new list that includes all old and new entrypoint refs.
    """
    experiment_id = registered_experiments["experiment3"]["id"]
    entrypoint_ids_to_append = [
        entrypoint["id"] for entrypoint in list(registered_entrypoints.values())[1:]
    ]
    expected_entrypoint_ids = [
        entrypoint["id"] for entrypoint in list(registered_entrypoints.values())
    ]
    assert_append_entrypoints_to_experiment_works(
        dioptra_client,
        experiment_id=experiment_id,
        entrypoint_ids=entrypoint_ids_to_append,
        expected=expected_entrypoint_ids,
    )


def test_modify_entrypoints_for_experiments(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_entrypoints: dict[str, Any],
    registered_experiments: dict[str, Any],
) -> None:
    """Test that the list of associated entrypoints with experiments can be modified.
    Given an authenticated user, registered experiments, and registered entrypoints,
    this test validates the following sequence of actions:
    - A user modifies the list of entrypoints associated with an experiment.
    - A user retrieves the list of all the new entrypoints associated with the experiemnts.
    """
    experiment_id = registered_experiments["experiment3"]["id"]
    expected_entrypoint_ids = [
        entrypoint["id"] for entrypoint in list(registered_entrypoints.values())
    ]
    dioptra_client.experiments.entrypoints.modify_by_id(
        experiment_id=experiment_id, entrypoint_ids=expected_entrypoint_ids
    )
    assert_retrieving_all_entrypoints_for_experiment_works(
        dioptra_client,
        experiment_id=experiment_id,
        expected=expected_entrypoint_ids,
    )


def test_delete_all_entrypoints_for_experiment(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_experiments: dict[str, Any],
) -> None:
    """Test that the list of all associated entrypoints can be deleted from a experiment.
    Given an authenticated user and registered experiments, this test validates the
    following sequence of actions:
    - A user deletes the list of associated entrypoints with the experiment.
    - A user retrieves an empty list of associated entrypoints with the experiment.
    """
    experiment_id = registered_experiments["experiment1"]["id"]
    dioptra_client.experiments.entrypoints.delete(experiment_id=experiment_id)
    assert_retrieving_all_entrypoints_for_experiment_works(
        dioptra_client, experiment_id=experiment_id, expected=[]
    )


def test_delete_entrypoints_by_id_for_experiment(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_entrypoints: dict[str, Any],
    registered_experiments: dict[str, Any],
) -> None:
    """Test that entrypoints associated with the experiments can be deleted by id.
    Given an authenticated user, registered experiments, and registered entrypoints,
    this test validates the following sequence of actions:
    - A user deletes an associated entrypoint with the experiment.
    - A user retrieves a list of associated entrypoints that does not include the deleted.
    """
    experiment_id = registered_experiments["experiment1"]["id"]
    entrypoint_to_delete = registered_entrypoints["entrypoint1"]["id"]
    expected_entrypoint_ids = [
        entrypoint["id"] for entrypoint in list(registered_entrypoints.values())[1:]
    ]
    dioptra_client.experiments.entrypoints.delete_by_id(
        experiment_id=experiment_id, entrypoint_id=entrypoint_to_delete
    )
    assert_retrieving_all_entrypoints_for_experiment_works(
        dioptra_client,
        experiment_id=experiment_id,
        expected=expected_entrypoint_ids,
    )
