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

from ..lib import actions, asserts, helpers

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


def modify_model_version(
    client: FlaskClient,
    model_id: int,
    version_number: int,
    new_description: str | None,
) -> TestResponse:
    """Change the description of a model version using the API.

    Args:
        client: The Flask test client.
        model_id: The id of the model to rename.
        new_description: The new description to assign to the model.

    Returns:
        The response from the API.
    """
    payload = {"description": new_description}

    return client.put(
        f"/{V1_ROOT}/{V1_MODELS_ROUTE}/{model_id}/versions/{version_number}",
        json=payload,
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
    # Check expected keys
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

    # Check basic response types for base resources
    asserts.assert_base_resource_contents_match_expectations(response)

    # Check basic response types for model
    assert isinstance(response["name"], str)
    assert isinstance(response["description"], str)
    assert isinstance(response["versions"], list)

    assert response["name"] == expected_contents["name"]
    assert response["description"] == expected_contents["description"]
    assert response["versions"] == expected_contents["versions"]
    assert response["latestVersion"] == expected_contents["latest_version"]

    # Check Refs for base resources
    asserts.assert_user_ref_contents_matches_expectations(
        user=response["user"], expected_user_id=expected_contents["user_id"]
    )
    asserts.assert_group_ref_contents_matches_expectations(
        group=response["group"], expected_group_id=expected_contents["group_id"]
    )
    asserts.assert_tag_ref_contents_matches_expectations(tags=response["tags"])


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

    # assert response["versionNumber"] == expected_contents["version_number"]
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


def assert_retrieving_model_version_by_version_number_works(
    client: FlaskClient, model_id: int, version_number: int, expected: dict[str, Any]
) -> None:
    """Assert that retrieving a model version by id works.

    Args:
        client: The Flask test client.
        model_id: The id of the model.
        model_verison_id: The id of the model version to retrieve.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = client.get(
        f"/{V1_ROOT}/{V1_MODELS_ROUTE}/{model_id}/versions/{version_number}",
        follow_redirects=True,
    )
    assert response.status_code == 200 and response.get_json() == expected


def assert_retrieving_model_versions_works(
    client: FlaskClient,
    model_id: int,
    expected: dict[str, Any],
    search: str | None = None,
    paging_info: dict[str, Any] | None = None,
) -> None:
    """"""
    query_string: dict[str, Any] = {}

    if search is not None:
        query_string["search"] = search

    if paging_info is not None:
        query_string["index"] = paging_info["index"]
        query_string["pageLength"] = paging_info["page_length"]

    response = client.get(
        f"/{V1_ROOT}/{V1_MODELS_ROUTE}/{model_id}/versions",
        query_string=query_string,
        follow_redirects=True,
    )
    assert response.status_code == 200 and response.get_json()["data"] == expected


def assert_model_version_description_matches_expected_description(
    client: FlaskClient,
    model_id: int,
    version_number: int,
    expected_description: str,
) -> None:
    """Assert that the description of a model version matches the expected description.

    Args:
        client: The Flask test client.
        model_id: The id of the model.
        version_number: The version number of the model version to retrieve.
        expected_description: The expected description of the model version.

    Raises:
        AssertionError: If the response status code is not 200 or if the name of the
            model does not match the expected name.
    """
    response = client.get(
        f"/{V1_ROOT}/{V1_MODELS_ROUTE}/{model_id}/versions/{version_number}",
        follow_redirects=True,
    )
    assert (
        response.status_code == 200
        and response.get_json()["description"] == expected_description
    )


# -- Model Tests ---------------------------------------------------------------


def test_create_model(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
) -> None:
    """"""
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
    updated_model_name = "new_model_name"
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


def test_manage_existing_model_draft(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_models: dict[str, Any],
) -> None:
    """Test that a draft of an existing model can be created and managed by the user

    Given an authenticated user and registered models, this test validates the following
    sequence of actions:

    - The user creates a draft of an existing model
    - The user retrieves information about the draft and gets the expected response
    - The user attempts to create another draft of the same existing model
    - The request fails with an appropriate error message and response code.
    - The user modifies the name of the model in the draft
    - The user retrieves information about the draft and gets the expected response
    - The user deletes the draft
    - The user attempts to retrieve information about the deleted draft.
    - The request fails with an appropriate error message and response code.
    """
    model = registered_models["model1"]
    name = "draft"
    new_name = "draft2"
    description = "description"

    # test creation
    payload = {"name": name, "description": description}
    expected = {
        "user_id": auth_account["id"],
        "group_id": model["group"]["id"],
        "resource_id": model["id"],
        "resource_snapshot_id": model["snapshot"],
        "num_other_drafts": 0,
        "payload": payload,
    }
    response = actions.create_existing_resource_draft(
        client, resource_route=V1_MODELS_ROUTE, resource_id=model["id"], payload=payload
    ).get_json()
    asserts.assert_draft_response_contents_matches_expectations(response, expected)
    asserts.assert_retrieving_draft_by_resource_id_works(
        client,
        resource_route=V1_MODELS_ROUTE,
        resource_id=model["id"],
        expected=response,
    )
    asserts.assert_creating_another_existing_draft_fails(
        client, resource_route=V1_MODELS_ROUTE, resource_id=model["id"]
    )

    # test modification
    payload = {"name": new_name, "description": description}
    expected = {
        "user_id": auth_account["id"],
        "group_id": model["group"]["id"],
        "resource_id": model["id"],
        "resource_snapshot_id": model["snapshot"],
        "num_other_drafts": 0,
        "payload": payload,
    }
    response = actions.modify_existing_resource_draft(
        client,
        resource_route=V1_MODELS_ROUTE,
        resource_id=model["id"],
        payload=payload,
    ).get_json()
    asserts.assert_draft_response_contents_matches_expectations(response, expected)

    # test deletion
    actions.delete_existing_resource_draft(
        client, resource_route=V1_MODELS_ROUTE, resource_id=model["id"]
    )
    asserts.assert_existing_draft_is_not_found(
        client, resource_route=V1_MODELS_ROUTE, resource_id=model["id"]
    )


def test_manage_new_model_drafts(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
) -> None:
    """Test that drafts of model can be created and managed by the user

    Given an authenticated user, this test validates the following sequence of actions:

    - The user creates two model drafts
    - The user retrieves information about the drafts and gets the expected response
    - The user modifies the description of the model in the first draft
    - The user retrieves information about the draft and gets the expected response
    - The user deletes the first draft
    - The user attempts to retrieve information about the deleted draft.
    - The request fails with an appropriate error message and response code.
    """
    group_id = auth_account["groups"][0]["id"]
    drafts = {
        "draft1": {"name": "model1", "description": "new model"},
        "draft2": {"name": "model2", "description": None},
    }

    # test creation
    draft1_expected = {
        "user_id": auth_account["id"],
        "group_id": group_id,
        "payload": drafts["draft1"],
    }
    draft1_response = actions.create_new_resource_draft(
        client,
        resource_route=V1_MODELS_ROUTE,
        group_id=group_id,
        payload=drafts["draft1"],
    ).get_json()
    asserts.assert_draft_response_contents_matches_expectations(
        draft1_response, draft1_expected
    )
    asserts.assert_retrieving_draft_by_id_works(
        client,
        resource_route=V1_MODELS_ROUTE,
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
        resource_route=V1_MODELS_ROUTE,
        group_id=group_id,
        payload=drafts["draft2"],
    ).get_json()
    asserts.assert_draft_response_contents_matches_expectations(
        draft2_response, draft2_expected
    )
    asserts.assert_retrieving_draft_by_id_works(
        client,
        resource_route=V1_MODELS_ROUTE,
        draft_id=draft2_response["id"],
        expected=draft2_response,
    )
    asserts.assert_retrieving_drafts_works(
        client,
        resource_route=V1_MODELS_ROUTE,
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
        resource_route=V1_MODELS_ROUTE,
        draft_id=draft1_response["id"],
        payload=draft1_mod,
    ).get_json()
    asserts.assert_draft_response_contents_matches_expectations(
        response, draft1_mod_expected
    )

    # test deletion
    actions.delete_new_resource_draft(
        client, resource_route=V1_MODELS_ROUTE, draft_id=draft1_response["id"]
    )
    asserts.assert_new_draft_is_not_found(
        client, resource_route=V1_MODELS_ROUTE, draft_id=draft1_response["id"]
    )


def test_manage_model_snapshots(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_models: dict[str, Any],
    registered_model_versions: dict[str, Any],
) -> None:
    """Test that different snapshots of a model can be retrieved by the user.

    Given an authenticated user and registered models, this test validates the following
    sequence of actions:

    - The user modifies a model
    - The user retrieves information about the original snapshot of the model and gets
      the expected response
    - The user retrieves information about the new snapshot of the model and gets the
      expected response
    - The user retrieves a list of all snapshots of the model and gets the expected
      response
    """
    model_to_rename = registered_models["model1"]
    modified_model = modify_model(
        client,
        model_id=model_to_rename["id"],
        new_name=model_to_rename["name"] + "modified",
        new_description=model_to_rename["description"],
    ).get_json()
    modified_model["latestVersion"] = None
    modified_model["versions"] = []
    modified_model.pop("hasDraft")
    model_to_rename.pop("hasDraft")
    model_to_rename["latestSnapshot"] = False
    model_to_rename["lastModifiedOn"] = modified_model["lastModifiedOn"]
    asserts.assert_retrieving_snapshot_by_id_works(
        client,
        resource_route=V1_MODELS_ROUTE,
        resource_id=model_to_rename["id"],
        snapshot_id=model_to_rename["snapshot"],
        expected=model_to_rename,
    )
    asserts.assert_retrieving_snapshot_by_id_works(
        client,
        resource_route=V1_MODELS_ROUTE,
        resource_id=modified_model["id"],
        snapshot_id=modified_model["snapshot"],
        expected=modified_model,
    )
    expected_snapshots = [model_to_rename, modified_model]
    asserts.assert_retrieving_snapshots_works(
        client,
        resource_route=V1_MODELS_ROUTE,
        resource_id=model_to_rename["id"],
        expected=expected_snapshots,
    )


def test_tag_model(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_models: dict[str, Any],
    registered_tags: dict[str, Any],
) -> None:
    """Test that tags can applied to models.

    Given an authenticated user, registered models, and registered tags this test
    validates the following sequence of actions:

    - The user appends tags to a model
    - The user retrieves information about the tags of the model and gets
      the expected response
    - The user removes a tag from a model
    - The user retrieves information about the tags of the model and gets
      the expected response
    - The user modifies a tag from a model
    - The user retrieves information about the tags of the model and gets
      the expected response
    - The user removes all tags from a model
    - The user attempts to retrieve information about the tags of the model and gets
      the gets the expected response of no tags
    """
    model = registered_models["model1"]
    tags = [tag["id"] for tag in registered_tags.values()]

    # test append
    response = actions.append_tags(
        client,
        resource_route=V1_MODELS_ROUTE,
        resource_id=model["id"],
        tag_ids=[tags[0], tags[1]],
    )
    asserts.assert_tags_response_contents_matches_expectations(
        response.get_json(), [tags[0], tags[1]]
    )
    response = actions.append_tags(
        client,
        resource_route=V1_MODELS_ROUTE,
        resource_id=model["id"],
        tag_ids=[tags[1], tags[2]],
    )
    asserts.assert_tags_response_contents_matches_expectations(
        response.get_json(), [tags[0], tags[1], tags[2]]
    )

    # test remove
    actions.remove_tag(
        client, resource_route=V1_MODELS_ROUTE, resource_id=model["id"], tag_id=tags[1]
    )
    response = actions.get_tags(
        client, resource_route=V1_MODELS_ROUTE, resource_id=model["id"]
    )
    asserts.assert_tags_response_contents_matches_expectations(
        response.get_json(), [tags[0], tags[2]]
    )

    # test modify
    response = actions.modify_tags(
        client,
        resource_route=V1_MODELS_ROUTE,
        resource_id=model["id"],
        tag_ids=[tags[1], tags[2]],
    )
    asserts.assert_tags_response_contents_matches_expectations(
        response.get_json(), [tags[1], tags[2]]
    )

    # test delete
    response = actions.remove_tags(
        client, resource_route=V1_MODELS_ROUTE, resource_id=model["id"]
    )
    response = actions.get_tags(
        client, resource_route=V1_MODELS_ROUTE, resource_id=model["id"]
    )
    asserts.assert_tags_response_contents_matches_expectations(response.get_json(), [])


# -- Tests Model Versions --------------------------------------------------------------


def test_create_model_version(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_models: dict[str, Any],
    registered_artifacts: dict[str, Any],
) -> None:
    """Test that model version can be correctly registered and retrieved using the API.

    Given an authenticated user, registered models, and registered artifacts this test
    validates the following sequence of actions:

    - The user registers a model version.
    - The response is valid and matches the expected values given the registration
      request.
    - The user is able to retrieve information about the model version using the version
      number.
    """
    model_id = registered_models["model1"]["id"]
    artifact_id = registered_artifacts["artifact1"]["id"]
    description = "The model version."
    model_version_response = actions.register_model_version(
        client, model_id=model_id, artifact_id=artifact_id, description=description
    ).get_json()

    assert_model_version_response_contents_matches_expectations(
        response=model_version_response,
        expected_contents={
            "model_id": model_id,
            "artifact_id": artifact_id,
            "description": description,
        },
    )

    assert_retrieving_model_version_by_version_number_works(
        client,
        model_id=model_id,
        version_number=model_version_response["versionNumber"],
        expected=model_version_response,
    )


def test_model_versions_get_all(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_models: dict[str, Any],
    registered_model_versions: dict[str, Any],
) -> None:
    """Test that all model versions can be retrieved.

    Given an authenticated user, registered model, and registered model versions
    this test validates the following sequence of actions:

    - The user is able to retrieve a list of all registered model versions.
    - The returned list of models matches the full list of registered models.
    """
    model_id = registered_models["model1"]["id"]
    model_version_expected_list = list(registered_model_versions.values())[::4]
    assert_retrieving_model_versions_works(
        client, model_id=model_id, expected=model_version_expected_list
    )


def test_model_version_search_query(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_models: dict[str, Any],
    registered_model_versions: dict[str, Any],
) -> None:
    """Test that model verisons can be queried with a search term.

    Given an authenticated user, registered model, and registered model versions
    this test validates the following sequence of actions:

    - The user is able to retrieve a list of all registered model verisons with various
      queries.
    - The returned list of model versions matches the expected matches from the query.
    """
    model_id = registered_models["model1"]["id"]
    model_version_expected_list = list(registered_model_versions.values())[::4]
    assert_retrieving_model_versions_works(
        client,
        model_id=model_id,
        expected=model_version_expected_list,
        search="description:*version*",
    )
    model_id = registered_models["model2"]["id"]
    model_version_expected_list = list(registered_model_versions.values())[1:-3]
    assert_retrieving_model_versions_works(
        client,
        model_id=model_id,
        expected=model_version_expected_list,
        search="description:*version*",
    )
    model_id = registered_models["model2"]["id"]
    model_version_expected_list = [
        list(registered_model_versions.values())[n] for n in (1, 3)
    ]
    assert_retrieving_model_versions_works(
        client,
        model_id=model_id,
        expected=model_version_expected_list,
        search="*",
    )


def test_modify_model_version(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_models: dict[str, Any],
    registered_model_versions: dict[str, Any],
) -> None:
    model_id = registered_models["model1"]["id"]
    model_version_number_to_modify = registered_model_versions["version1"][
        "versionNumber"
    ]
    new_description = "The new description"
    modify_model_version(
        client,
        model_id=model_id,
        version_number=model_version_number_to_modify,
        new_description=new_description,
    )
    assert_model_version_description_matches_expected_description(
        client,
        model_id=model_id,
        version_number=model_version_number_to_modify,
        expected_description=new_description,
    )
