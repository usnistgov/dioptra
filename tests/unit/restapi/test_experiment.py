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
from __future__ import annotations

from typing import Any

from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from werkzeug.test import TestResponse

from dioptra.restapi.routes import EXPERIMENT_ROUTE, V0_ROOT

# -- Actions ---------------------------------------------------------------------------


def register_experiment(client: FlaskClient, name: str) -> TestResponse:
    """Register an experiment using the API.

    Args:
        client: The Flask test client.
        name: The name to assign to the new experiment.

    Returns:
        The response from the API.
    """
    return client.post(
        f"/{V0_ROOT}/{EXPERIMENT_ROUTE}/",
        json={"name": name},
        follow_redirects=True,
    )


def rename_experiment(client: FlaskClient, id: int, new_name: str) -> TestResponse:
    """Rename an experiment using the API.

    Args:
        client: The Flask test client.
        id: The id of the experiment to rename.
        new_name: The new name to assign to the experiment.

    Returns:
        The response from the API.
    """
    return client.put(
        f"/{V0_ROOT}/{EXPERIMENT_ROUTE}/{id}",
        json={"name": new_name},
        follow_redirects=True,
    )


def delete_experiment_with_name(client: FlaskClient, name: str) -> TestResponse:
    """Delete an experiment using the API.

    Args:
        client: The Flask test client.
        name: The name of the experiment to delete.

    Returns:
        The response from the API.
    """
    return client.delete(
        f"/{V0_ROOT}/{EXPERIMENT_ROUTE}/name/{name}",
        follow_redirects=True,
    )


def delete_experiment_with_id(client: FlaskClient, id: int) -> TestResponse:
    """Delete an experiment using the API.

    Args:
        client: The Flask test client.
        id: The id of the experiment to delete.

    Returns:
        The response from the API.
    """
    return client.delete(
        f"/{V0_ROOT}/{EXPERIMENT_ROUTE}/{id}",
        follow_redirects=True,
    )


# -- Assertions ------------------------------------------------------------------------


def assert_retrieving_experiment_by_name_works(
    client: FlaskClient, name: str, expected: dict[str, Any]
) -> None:
    """Assert that retrieving a experiment by name works.

    Args:
        client: The Flask test client.
        name: The name of the experiment to retrieve.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = client.get(
        f"/{V0_ROOT}/{EXPERIMENT_ROUTE}/name/{name}", follow_redirects=True
    )
    assert response.status_code == 200 and response.get_json() == expected


def assert_retrieving_experiment_by_id_works(
    client: FlaskClient, id: int, expected: dict[str, Any]
) -> None:
    """Assert that retrieving an experiment by id works.

    Args:
        client: The Flask test client.
        id: The id of the experiment to retrieve.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = client.get(f"/{V0_ROOT}/{EXPERIMENT_ROUTE}/{id}", follow_redirects=True)
    assert response.status_code == 200 and response.get_json() == expected


def assert_retrieving_all_experiments_works(
    client: FlaskClient, expected: list[dict[str, Any]]
) -> None:
    """Assert that retrieving all experiments works.

    Args:
        client: The Flask test client.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = client.get(f"/{V0_ROOT}/{EXPERIMENT_ROUTE}", follow_redirects=True)
    assert response.status_code == 200 and response.get_json()["data"] == expected


def assert_experiment_name_matches_expected_name(
    client: FlaskClient, id: int, expected_name: str
) -> None:
    """Assert that the name of an experiment matches the expected name.

    Args:
        client: The Flask test client.
        id: The id of the experiment to retrieve.
        expected_name: The expected name of the experiment.

    Raises:
        AssertionError: If the response status code is not 200 or if the name of the
            experiment does not match the expected name.
    """
    response = client.get(
        f"/{V0_ROOT}/{EXPERIMENT_ROUTE}/{id}",
        follow_redirects=True,
    )
    assert response.status_code == 200 and response.get_json()["name"] == expected_name


def assert_registering_existing_experiment_name_fails(
    client: FlaskClient, name: str
) -> None:
    """Assert that registering an experiment with an existing name fails.

    Args:
        client: The Flask test client.
        name: The name to assign to the new experiment.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = register_experiment(client, name=name)
    assert response.status_code == 400


def assert_experiment_is_not_found(client: FlaskClient, id: int) -> None:
    """Assert that an experiment is not found.

    Args:
        client: The Flask test client.
        id: The id of the experiment to retrieve.

    Raises:
        AssertionError: If the response status code is not 404.
    """
    response = client.get(
        f"/{V0_ROOT}/{EXPERIMENT_ROUTE}/{id}",
        follow_redirects=True,
    )
    assert response.status_code == 404


def assert_experiment_count_matches_expected_count(
    client: FlaskClient, expected: int
) -> None:
    """Assert that the number of experiments matches the expected number.

    Args:
        client: The Flask test client.
        expected: The expected number of experiments.

    Raises:
        AssertionError: If the response status code is not 200 or if the number of
            experiments does not match the expected number.
    """
    response = client.get(
        f"/{V0_ROOT}/{EXPERIMENT_ROUTE}",
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
        f"/{V0_ROOT}/{EXPERIMENT_ROUTE}?index={index}&pageLength={page_length}",
        follow_redirects=True,
    )
    
    page = response.get_json()
    assert response.status_code == 200 and page == expected


# -- Tests -----------------------------------------------------------------------------


def test_register_experiment(client: FlaskClient, db: SQLAlchemy) -> None:
    """Tests that experiments can be registered following the scenario below::

        Scenario: Registering an Experiment
            Given I am an authorized user,
            I need to be able to submit a register request,
            in order to register an experiment.

    This test validates by following these actions:

    - A user registers two experiments, "mnist_name" and "mnist_id".
    - The user is able to retrieve information about each experiment using the
      experiment id or the unique experiment name.
    - In both cases, the returned information matches the information that was provided
      during registration.
    """
    experiment1_expected = register_experiment(client, name="mnist_name").get_json()
    experiment2_expected = register_experiment(client, name="mnist_id").get_json()
    assert_retrieving_experiment_by_name_works(
        client, name=experiment1_expected["name"], expected=experiment1_expected
    )
    assert_retrieving_experiment_by_id_works(
        client, id=experiment1_expected["experimentId"], expected=experiment1_expected
    )
    assert_retrieving_experiment_by_name_works(
        client, name=experiment2_expected["name"], expected=experiment2_expected
    )
    assert_retrieving_experiment_by_id_works(
        client, id=experiment2_expected["experimentId"], expected=experiment2_expected
    )


def test_cannot_register_existing_experiment_name(
    client: FlaskClient, db: SQLAlchemy
) -> None:
    """Test that registering a experiment with an existing name fails.

    This test validates the following sequence of actions:

    - A user registers an experiment named "error".
    - The user attempts to register a second experiment with the same name, which fails.
    """
    register_experiment(client, name="error")
    assert_registering_existing_experiment_name_fails(client, name="error")


def test_retrieve_experiment(client: FlaskClient, db: SQLAlchemy) -> None:
    """Test that an experiment can be retrieved following the scenario below::

        Scenario: Get an Experiment
            Given I am an authorized user and an experiment exists,
            I need to be able to submit a get request
            in order to retrieve that experiment using its name and id as identifiers.

    This test validates by following these actions:

    - A user registers an experiment named "retrieve".
    - The user is able to retrieve information about the "retrieve" experiment that
      matches the information that was provided during registration using its name and
      id as identifiers.
    - In all cases, the returned information matches the information that was provided
      during registration.
    """
    experiment_expected = register_experiment(client, name="retrieve").get_json()
    assert_retrieving_experiment_by_name_works(
        client, name=experiment_expected["name"], expected=experiment_expected
    )
    assert_retrieving_experiment_by_id_works(
        client, id=experiment_expected["experimentId"], expected=experiment_expected
    )


def test_list_experiments(client: FlaskClient, db: SQLAlchemy) -> None:
    """Test that the list of experiments can be renamed following the scenario below::

        Scenario: Get the List of Registered Experiments
            Given I am an authorized user and a set of experiments exist,
            I need to be able to submit a get request
            in order to retrieve the list of registered experiments.

    This test validates by following these actions:

    - A user registers a set of experiments named "mnist1", "mnist2" and "mnist3".
    - The user is able to retrieve information about the experiments that
      matches the information that was provided during registration.
    - The user is able to retrieve a list of all registered experiments.
    - The returned list of experiments matches the information that was provided
      during registration.
    """
    experiment1_expected = register_experiment(client, name="mnist1").get_json()
    experiment2_expected = register_experiment(client, name="mnist2").get_json()
    experiment3_expected = register_experiment(client, name="mnist3").get_json()
    experiment_expected_list = [
        experiment1_expected,
        experiment2_expected,
        experiment3_expected,
    ]
    assert_retrieving_all_experiments_works(client, expected=experiment_expected_list)


def test_rename_experiment(client: FlaskClient, db: SQLAlchemy) -> None:
    """Test that an experiment can be renamed following the scenario below::

        Scenario: Rename an Experiment
            Given I am an authorized user and an experiment exists,
            I need to be able to submit a rename request
            in order to rename an experiment using its id as an identifier.

    This test validates by following these actions:

    - A user registers an experiment named "mnist".
    - The user is able to retrieve information about the "mnist" experiment that
      matches the information that was provided during registration.
    - The user renames this same experiment to "imagenet".
    - The user retrieves information about the same experiment and it reflects the name
      change.
    """
    start_name = "mnist"
    update_name = "imagenet"
    experiment_json = register_experiment(client, name=start_name).get_json()
    assert_experiment_name_matches_expected_name(
        client, id=experiment_json["experimentId"], expected_name=start_name
    )
    rename_experiment(client, id=experiment_json["experimentId"], new_name=update_name)
    assert_experiment_name_matches_expected_name(
        client, id=experiment_json["experimentId"], expected_name=update_name
    )


def test_delete_experiment(client: FlaskClient, db: SQLAlchemy) -> None:
    """Test that an experiment can be deleted following the scenario below::

        Scenario: Delete an Experiment
            Given I am an authorized user and an experiment exists,
            I need to be able to submit a delete request
            in order to delete an experiment, using its name and id as identifiers.

    This test validates by following these actions:

    - Deleting by name:
        - A user registers an experiment named "delete_name".
        - The user is able to retrieve information about the "delete_name" experiment
          that matches the information that was provided during registration.
        - The user deletes the "delete_name" experiment by referencing its name.
        - The user attempts to retrieve information about the "delete_name" experiment,
          which is no longer found.

    - Deleting by ID:
        - A user registers another experiment named "delete_id".
        - The user is able to retrieve information about the "delete_id" experiment that
          matches the information that was provided during registration.
        - The user deletes the "delete_id" experiment by referencing its id.
        - The user attempts to retrieve information about the "delete_id" experiment,
          which is no longer found.
    """
    name_by_name = "delete_name"
    experiment1_json = register_experiment(client, name=name_by_name).get_json()
    assert_retrieving_experiment_by_id_works(
        client, id=experiment1_json["experimentId"], expected=experiment1_json
    )
    delete_experiment_with_name(client, name=name_by_name)
    assert_experiment_is_not_found(client, id=experiment1_json["experimentId"])

    name_by_id = "delete_id"
    experiment2_json = register_experiment(client, name=name_by_id).get_json()
    assert_retrieving_experiment_by_id_works(
        client, id=experiment2_json["experimentId"], expected=experiment2_json
    )
    delete_experiment_with_id(client, id=experiment2_json["experimentId"])
    assert_experiment_is_not_found(client, id=experiment2_json["experimentId"])

def test_experiment_paging(client: FlaskClient, db: SQLAlchemy) -> None:
    """Tests that experiments can be retrieved according to paging information:

        Scenario: Experiment Paging
            Given I am an authorized user,
            I need to be able to select an index and page length,
            in order to display a page of experiments.

    This test validates by following these actions:

    - A user registers a set of experiments named "mnist1", "mnist2" and "mnist3".
    - The user is able to retrieve information about the experiments that
      matches the information that was provided during registration.
    - The user is able to retrieve a list of all registered experiments.
    - The returned list of experiments matches the information that was provided
      during registration.
    """
    
    experiment1_expected = register_experiment(client, name="mnist4").get_json()
    experiment2_expected = register_experiment(client, name="mnist5").get_json()
    register_experiment(client, name="mnist6").get_json()
    data = [
        experiment1_expected,
        experiment2_expected,
    ]
    index = 0
    page_length = 2
    isComplete = False
    page_expected = {
        "data": data,
        "index": index,
        "isComplete": isComplete,
        "first": f"/api/v0/experiment?index=0&pageLength={page_length}",
        "next": f"/api/v0/experiment?index={index+page_length}&pageLength={page_length}",
        "prev": f"/api/v0/experiment?index=0&pageLength={page_length}",
    }
    assert_page_data_matches(
        client, index=0, page_length=2, expected=page_expected
    )
    