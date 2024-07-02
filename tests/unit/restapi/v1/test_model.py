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
"""Test suite for model operations.

This module contains a set of tests that validate the CRUD operations and additional
functionalities for the model entity. The tests ensure that the models can be
registered, renamed, deleted, and locked/unlocked as expected through the REST API.
"""

from typing import Any

from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from werkzeug.test import TestResponse

from dioptra.restapi.routes import V1_MODELS_ROUTE, V1_ROOT

from ..lib import actions, helpers

# -- Actions ---------------------------------------------------------------------------


def modify_model(
    client: FlaskClient,
    model_id: int,
    new_name: str,
    new_description: str | None,
) -> TestResponse:
    """Rename a model using the API.

    Args:
        client: The Flask test client.
        model_id: The id of the model to rename.
        new_name: The new name to assign to the model.
        new_description: The new description to assign to the model.
        new_artifact_id: The new artifact to assign to the model.

    Returns:
        The response from the API.
    """
    payload = {
        "name": new_name,
        "description": new_description,
    }

    return client.put(
        f"/{V1_ROOT}/{V1_MODELS_ROUTE}/{model_id}",
        json=payload,
        follow_redirects=True,
    )


def delete_model_with_id(
    client: FlaskClient,
    model_id: int,
) -> TestResponse:
    """Delete a model using the API.

    Args:
        client: The Flask test client.
        model_id: The id of the model to delete.

    Returns:
        The response from the API.
    """

    return client.delete(
        f"/{V1_ROOT}/{V1_MODELS_ROUTE}/{model_id}",
        follow_redirects=True,
    )


# -- Assertions ------------------------------------------------------------------------


def assert_model_response_contents_matches_expectations(
    response: dict[str, Any], expected_contents: dict[str, Any]
) -> None:
    """Assert that model response contents is valid.

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
        "versions",
        "createdOn",
        "lastModifiedOn",
        "latestSnapshot",
        "hasDraft",
        "name",
        "description",
        "latestVersion",
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
    assert response["versions"] == expected_contents["versions"]

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

    # Validate the versions structure
    assert response["latestVersion"] == expected_contents["latest_version"]

    # Validate the TagRef structure
    for tag in response["tags"]:
        assert isinstance(tag["id"], int)
        assert isinstance(tag["name"], str)
        assert isinstance(tag["url"], str)


def assert_model_version_response_contents_matches_expectations(
    response: dict[str, Any], expected_contents: dict[str, Any]
) -> None:
    """Assert that model version response contents is valid.

    Args:
        response: The actual response from the API.
        expected_contents: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response or if the response contents is not
            valid.
    """
    expected_keys = {
        "model",
        "artifact",
        "versionNumber",
        "description",
        "createdOn",
    }
    assert set(response.keys()) == expected_keys

    # Validate the non-Ref fields
    assert isinstance(response["description"], str)
    assert isinstance(response["createdOn"], str)
    assert isinstance(response["versionNumber"], int)

    assert response["versionNumber"] == expected_contents["version_number"]
    assert response["description"] == expected_contents["description"]
    assert response["model"]["id"] == expected_contents["model_id"]
    assert response["artifact"]["id"] == expected_contents["artifact_id"]

    assert helpers.is_iso_format(response["createdOn"])


def assert_retrieving_model_by_id_works(
    client: FlaskClient,
    model_id: int,
    expected: dict[str, Any],
) -> None:
    """Assert that retrieving a model by id works.

    Args:
        client: The Flask test client.
        model_id: The id of the model to retrieve.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = client.get(
        f"/{V1_ROOT}/{V1_MODELS_ROUTE}/{model_id}", follow_redirects=True
    )
    assert response.status_code == 200 and response.get_json() == expected


def assert_retrieving_models_works(
    client: FlaskClient,
    expected: list[dict[str, Any]],
    group_id: int | None = None,
    search: str | None = None,
    paging_info: dict[str, Any] | None = None,
) -> None:
    """Assert that retrieving all models works.

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
        f"/{V1_ROOT}/{V1_MODELS_ROUTE}",
        query_string=query_string,
        follow_redirects=True,
    )
    assert response.status_code == 200 and response.get_json()["data"] == expected


def assert_registering_existing_model_name_fails(
    client: FlaskClient, name: str, group_id: int
) -> None:
    """Assert that registering a model with an existing name fails.

    Args:
        client: The Flask test client.
        name: The name to assign to the new model.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = actions.register_model(
        client, name=name, description="", group_id=group_id
    )
    assert response.status_code == 400


def assert_model_name_matches_expected_name(
    client: FlaskClient, model_id: int, expected_name: str
) -> None:
    """Assert that the name of a model matches the expected name.

    Args:
        client: The Flask test client.
        model_id: The id of the model to retrieve.
        expected_name: The expected name of the model.

    Raises:
        AssertionError: If the response status code is not 200 or if the name of the
            model does not match the expected name.
    """
    response = client.get(
        f"/{V1_ROOT}/{V1_MODELS_ROUTE}/{model_id}",
        follow_redirects=True,
    )
    assert response.status_code == 200 and response.get_json()["name"] == expected_name


def assert_model_is_not_found(
    client: FlaskClient,
    model_id: int,
) -> None:
    """Assert that a model is not found.

    Args:
        client: The Flask test client.
        model_id: The id of the model to retrieve.

    Raises:
        AssertionError: If the response status code is not 404.
    """
    response = client.get(
        f"/{V1_ROOT}/{V1_MODELS_ROUTE}/{model_id}",
        follow_redirects=True,
    )
    assert response.status_code == 404


def assert_cannot_rename_model_with_existing_name(
    client: FlaskClient,
    model_id: int,
    existing_name: str,
    existing_description: str,
) -> None:
    """Assert that renaming a model with an existing name fails.

    Args:
        client: The Flask test client.
        model_id: The id of the model to rename.
        name: The name of an existing model.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = modify_model(
        client=client,
        model_id=model_id,
        new_name=existing_name,
        new_description=existing_description,
    )
    assert response.status_code == 400


# -- Model Tests ---------------------------------------------------------------


def test_create_model(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
) -> None:
    name = "my_model"
    description = "The first model."
    user_id = auth_account["id"]
    group_id = auth_account["groups"][0]["id"]
    model_response = actions.register_model(
        client, name=name, group_id=group_id, description=description
    )

    model_expected = model_response.get_json()
    assert_model_response_contents_matches_expectations(
        response=model_expected,
        expected_contents={
            "name": name,
            "description": description,
            "user_id": user_id,
            "group_id": group_id,
            "versions": [],
            "latest_version": None,
        },
    )

    assert_retrieving_model_by_id_works(
        client, model_id=model_expected["id"], expected=model_expected
    )


def test_model_get_all(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_models: dict[str, Any],
) -> None:
    """Test that all models can be retrieved.

    Given an authenticated user and registered models, this test validates the following
    sequence of actions:

    - A user registers three models, "tensorflow_cpu", "tensorflow_gpu", "pytorch_cpu".
    - The user is able to retrieve a list of all registered models.
    - The returned list of models matches the full list of registered models.
    """
    model_expected_list = list(registered_models.values())
    assert_retrieving_models_works(client, expected=model_expected_list)


def test_model_search_query(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_models: dict[str, Any],
) -> None:
    """Test that models can be queried with a search term.

    Given an authenticated user and registered models, this test validates the following
    sequence of actions:

    - The user is able to retrieve a list of all registered models with various queries.
    - The returned list of models matches the expected matches from the query.
    """
    model_expected_list = list(registered_models.values())[:2]
    assert_retrieving_models_works(
        client, expected=model_expected_list, search="description:*model*"
    )
    model_expected_list = list(registered_models.values())[:1]
    assert_retrieving_models_works(
        client, expected=model_expected_list, search="*model*, name:*tensorflow*"
    )
    model_expected_list = list(registered_models.values())
    assert_retrieving_models_works(client, expected=model_expected_list, search="*")


def test_model_group_query(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_models: dict[str, Any],
) -> None:
    """Test that models can retrieved using a group filter.

    Given an authenticated user and registered models, this test validates the following
    sequence of actions:

    - The user is able to retrieve a list of all registered models that are owned by the
      default group.
    - The returned list of models matches the expected list owned by the default group.
    """
    model_expected_list = list(registered_models.values())
    assert_retrieving_models_works(
        client,
        expected=model_expected_list,
        group_id=auth_account["groups"][0]["id"],
    )


def test_cannot_register_existing_model_name(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_models: dict[str, Any],
) -> None:
    """Test that registering a model with an existing name fails.

    Given an authenticated user and registered models, this test validates the following
    sequence of actions:

    - The user attempts to register a second model with the same name.
    - The request fails with an appropriate error message and response code.
    """
    existing_model = registered_models["model1"]

    assert_registering_existing_model_name_fails(
        client,
        name=existing_model["name"],
        group_id=existing_model["group"]["id"],
    )


def test_rename_model(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_models: dict[str, Any],
) -> None:
    """Test that a model can be renamed.

    Given an authenticated user and registered models, this test validates the following
    sequence of actions:

    - The user issues a request to change the name of a model.
    - The user retrieves information about the same model and it reflects the name
      change.
    - The user issues a request to change the name of the model to the existing name.
    - The user retrieves information about the same model and verifies the name remains
      unchanged.
    - The user issues a request to change the name of a model to an existing model's
      name.
    - The request fails with an appropriate error message and response code.
    """
    updated_model_name = "tensorflow_tpu"
    model_to_rename = registered_models["model1"]
    existing_model = registered_models["model2"]

    modified_model = modify_model(
        client,
        model_id=model_to_rename["id"],
        new_name=updated_model_name,
        new_description=model_to_rename["description"],
    ).get_json()
    assert_model_name_matches_expected_name(
        client, model_id=model_to_rename["id"], expected_name=updated_model_name
    )
    model_expected_list = [
        modified_model,
        registered_models["model2"],
        registered_models["model3"],
    ]
    assert_retrieving_models_works(client, expected=model_expected_list)

    modified_model = modify_model(
        client,
        model_id=model_to_rename["id"],
        new_name=updated_model_name,
        new_description=model_to_rename["description"],
    ).get_json()
    assert_model_name_matches_expected_name(
        client, model_id=model_to_rename["id"], expected_name=updated_model_name
    )

    assert_cannot_rename_model_with_existing_name(
        client,
        model_id=model_to_rename["id"],
        existing_name=existing_model["name"],
        existing_description=model_to_rename["description"],
    )


def test_delete_model_by_id(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_models: dict[str, Any],
) -> None:
    """Test that a model can be deleted by referencing its id.

    Given an authenticated user and registered models, this test validates the following
    sequence of actions:

    - The user deletes a model by referencing its id.
    - The user attempts to retrieve information about the deleted model.
    - The request fails with an appropriate error message and response code.
    """
    model_to_delete = registered_models["model1"]

    delete_model_with_id(client, model_id=model_to_delete["id"])
    assert_model_is_not_found(client, model_id=model_to_delete["id"])


# -- Tests Model Versions ----------------------------------------------------------------
