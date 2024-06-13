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

from ..lib import actions, helpers

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
        "name",
        "jobs",
        #       "entrypoints",
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

    # Validate the JobRef structure
    for job in response["jobs"]:
        assert isinstance(job["id"], int)
        assert isinstance(job["url"], str)
        for group in job["group"]:
            assert isinstance(group["id"], int)
            assert isinstance(group["url"], str)
            assert isinstance(group["name", str])

    # Validate the EntryPointRef structure
    # for entrypoint in response["entrypoints"]:
    #     assert isinstance(entrypoint["id"], int)
    #     assert isinstance(entrypoint["url"], str)
    #     assert isinstance(entrypoint["name"], str)
    #     for group in entrypoint["group"]:
    #         assert isinstance(group["id"], int)
    #         assert isinstance(group["url"], str)
    #         assert isinstance(group["name", str])

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
    assert response.get_json()["entrypoints"] == expected_entrypoints


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
        query_string["query"] = search

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
    print(experiment1_expected)  # TEST
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
      that countains 'experiment'.
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
        search="name:*experiment*",
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
    print(experiment2_expected)  # TEST

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


@pytest.mark.skip(reason="entrypoints not yet implmented")
def test_experiment_get_entrypoints(
    client: FlaskClient, db: SQLAlchemy, auth_account: dict[str, Any]
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
    entrypoints = [1, 2, 3]
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
            "entrypoints": entrypoints,
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
