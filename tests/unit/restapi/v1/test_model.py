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

from http import HTTPStatus
from typing import Any

import pytest

from dioptra.client.base import DioptraResponseProtocol
from dioptra.client.client import DioptraClient

from ..lib import asserts, helpers, routines
from ..test_utils import assert_retrieving_resource_works, assert_searchable_field_works

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
        "snapshotCreatedOn",
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
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    response = dioptra_client.models.get_by_id(model_id)
    assert response.status_code == HTTPStatus.OK and response.json() == expected


def assert_retrieving_models_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    expected: list[dict[str, Any]],
    group_id: int | None = None,
    sort_by: str | None = None,
    descending: bool | None = None,
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

    assert_retrieving_resource_works(
        dioptra_client=dioptra_client.models,
        expected=expected,
        group_id=group_id,
        sort_by=sort_by,
        descending=descending,
        search=search,
        paging_info=paging_info,
    )


def assert_registering_existing_model_name_fails(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    name: str,
    group_id: int,
) -> None:
    """Assert that registering a model with an existing name fails.

    Args:
        client: The Flask test client.
        name: The name to assign to the new model.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = dioptra_client.models.create(
        group_id=group_id, name=name, description=""
    )
    assert response.status_code == HTTPStatus.CONFLICT


def assert_model_name_matches_expected_name(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    model_id: int,
    expected_name: str,
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
    response = dioptra_client.models.get_by_id(model_id)
    assert (
        response.status_code == HTTPStatus.OK
        and response.json()["name"] == expected_name
    )


def assert_model_is_not_found(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    model_id: int,
) -> None:
    """Assert that a model is not found.

    Args:
        client: The Flask test client.
        model_id: The id of the model to retrieve.

    Raises:
        AssertionError: If the response status code is not 404.
    """
    response = dioptra_client.models.get_by_id(model_id)
    assert response.status_code == HTTPStatus.NOT_FOUND


def assert_cannot_rename_model_with_existing_name(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    response = dioptra_client.models.modify_by_id(
        model_id=model_id,
        name=existing_name,
        description=existing_description,
    )
    assert response.status_code == HTTPStatus.CONFLICT


def assert_retrieving_model_version_by_version_number_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    model_id: int,
    version_number: int,
    expected: dict[str, Any],
) -> None:
    """Assert that retrieving a model version by id works.

    Args:
        client: The Flask test client.
        model_id: The id of the model.
        model_version_id: The id of the model version to retrieve.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = dioptra_client.models.versions.get_by_id(
        model_id=model_id, version_number=version_number
    )
    assert response.status_code == HTTPStatus.OK and response.json() == expected


def assert_retrieving_model_versions_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
        query_string["page_length"] = paging_info["page_length"]

    response = dioptra_client.models.versions.get(model_id=model_id, **query_string)
    assert response.status_code == HTTPStatus.OK and response.json()["data"] == expected


def assert_model_version_description_matches_expected_description(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    response = dioptra_client.models.versions.get_by_id(
        model_id=model_id, version_number=version_number
    )
    assert (
        response.status_code == HTTPStatus.OK
        and response.json()["description"] == expected_description
    )


# -- Model Tests ---------------------------------------------------------------


def test_create_model(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
) -> None:
    """"""
    name = "my_model"
    description = "The first model."
    user_id = auth_account["id"]
    group_id = auth_account["groups"][0]["id"]
    model_response = dioptra_client.models.create(
        group_id=group_id, name=name, description=description
    )
    model_expected = model_response.json()
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
        dioptra_client, model_id=model_expected["id"], expected=model_expected
    )


def test_model_get_all(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    assert_retrieving_models_works(dioptra_client, expected=model_expected_list)


@pytest.mark.parametrize(
    "field, value, expected_count",
    [
        ("name", None, 1),
        ("description", None, 2),
        ("tag", "Foo", 0),
    ],
)
def test_model_searchable_fields(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_models: dict[str, Any],
    field: str,
    value: str | None,
    expected_count: int,
) -> None:
    model = registered_models["model1"]
    search_value = model[field] if value is None else value
    assert_searchable_field_works(
        dioptra_client=dioptra_client.models,
        term=field,
        value=search_value,
        expected_count=expected_count,
    )


@pytest.mark.parametrize(
    "sort_by, descending , expected",
    [
        ("name", True, ["model1", "model3", "model2"]),
        ("name", False, ["model2", "model3", "model1"]),
        ("createdOn", True, ["model3", "model2", "model1"]),
        ("createdOn", False, ["model1", "model2", "model3"]),
    ],
)
def test_model_sort(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_models: dict[str, Any],
    sort_by: str,
    descending: bool,
    expected: list[str],
) -> None:
    """Test that models can be sorted by column.

    Given an authenticated user and registered models, this test validates the following
    sequence of actions:

    - A user registers three models, "my_tensorflow_model", "model2", "model3".
    - The user is able to retrieve a list of all registered models sorted by a column
      ascending/descending.
    - The returned list of models matches the order in the parametrize lists above.
    """

    expected_models = [registered_models[expected_name] for expected_name in expected]
    assert_retrieving_models_works(
        dioptra_client, sort_by=sort_by, descending=descending, expected=expected_models
    )


def test_model_search_query(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
        dioptra_client, expected=model_expected_list, search="description:*model*"
    )
    model_expected_list = list(registered_models.values())[:1]
    assert_retrieving_models_works(
        dioptra_client,
        expected=model_expected_list,
        search="*model*, name:*tensorflow*",
    )
    model_expected_list = list(registered_models.values())
    assert_retrieving_models_works(
        dioptra_client, expected=model_expected_list, search="*"
    )


def test_model_group_query(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
        dioptra_client,
        expected=model_expected_list,
        group_id=auth_account["groups"][0]["id"],
    )


def test_cannot_register_existing_model_name(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
        dioptra_client,
        name=existing_model["name"],
        group_id=existing_model["group"]["id"],
    )


def test_rename_model(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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

    modified_model = dioptra_client.models.modify_by_id(
        model_id=model_to_rename["id"],
        name=updated_model_name,
        description=model_to_rename["description"],
    ).json()
    assert_model_name_matches_expected_name(
        dioptra_client, model_id=model_to_rename["id"], expected_name=updated_model_name
    )
    model_expected_list = [
        modified_model,
        registered_models["model2"],
        registered_models["model3"],
    ]
    assert_retrieving_models_works(dioptra_client, expected=model_expected_list)

    modified_model = dioptra_client.models.modify_by_id(
        model_id=model_to_rename["id"],
        name=updated_model_name,
        description=model_to_rename["description"],
    ).json()
    assert_model_name_matches_expected_name(
        dioptra_client, model_id=model_to_rename["id"], expected_name=updated_model_name
    )

    assert_cannot_rename_model_with_existing_name(
        dioptra_client,
        model_id=model_to_rename["id"],
        existing_name=existing_model["name"],
        existing_description=model_to_rename["description"],
    )


def test_delete_model_by_id(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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

    dioptra_client.models.delete_by_id(model_to_delete["id"])
    assert_model_is_not_found(dioptra_client, model_id=model_to_delete["id"])


def test_manage_existing_model_draft(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    # Requests data
    model = registered_models["model1"]
    name = "draft"
    new_name = "draft2"
    description = "description"

    # test creation
    draft = {"name": name, "description": description}
    draft_mod = {"name": new_name, "description": description}

    # Expected responses
    draft_expected = {
        "user_id": auth_account["id"],
        "group_id": model["group"]["id"],
        "resource_id": model["id"],
        "resource_snapshot_id": model["snapshot"],
        "num_other_drafts": 0,
        "payload": draft,
    }
    draft_mod_expected = {
        "user_id": auth_account["id"],
        "group_id": model["group"]["id"],
        "resource_id": model["id"],
        "resource_snapshot_id": model["snapshot"],
        "num_other_drafts": 0,
        "payload": draft_mod,
    }

    # Run routine: existing resource drafts tests
    routines.run_existing_resource_drafts_tests(
        dioptra_client.models,
        dioptra_client.models.modify_resource_drafts,
        dioptra_client.workflows,
        model["id"],
        draft=draft,
        draft_mod=draft_mod,
        draft_expected=draft_expected,
        draft_mod_expected=draft_mod_expected,
    )


def test_manage_new_model_drafts(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    # Requests data
    group_id = auth_account["groups"][0]["id"]
    drafts = {
        "draft1": {"name": "model1", "description": "new model"},
        "draft2": {"name": "model2", "description": None},
    }
    draft1_mod = {"name": "draft1", "description": "new description"}

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
        dioptra_client.models,
        dioptra_client.models.new_resource_drafts,
        dioptra_client.workflows,
        drafts=drafts,
        draft1_mod=draft1_mod,
        draft1_expected=draft1_expected,
        draft2_expected=draft2_expected,
        draft1_mod_expected=draft1_mod_expected,
        group_id=group_id,
    )


def test_manage_model_snapshots(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    modified_model = dioptra_client.models.modify_by_id(
        model_id=model_to_rename["id"],
        name=model_to_rename["name"] + "modified",
        description=model_to_rename["description"],
    ).json()
    modified_model["latestVersion"] = None
    modified_model["versions"] = []

    # Run routine: resource snapshots tests
    routines.run_resource_snapshots_tests(
        dioptra_client.models.snapshots,
        resource_to_rename=model_to_rename.copy(),
        modified_resource=modified_model.copy(),
    )


def test_tag_model(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    tag_ids = [tag["id"] for tag in registered_tags.values()]

    # Run routine: resource tag tests
    routines.run_resource_tag_tests(
        dioptra_client.models.tags,
        model["id"],
        tag_ids=tag_ids,
    )


# -- Tests Model Versions --------------------------------------------------------------


def test_create_model_version(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    model_version_response = dioptra_client.models.versions.create(
        model_id=model_id, artifact_id=artifact_id, description=description
    ).json()

    assert_model_version_response_contents_matches_expectations(
        response=model_version_response,
        expected_contents={
            "model_id": model_id,
            "artifact_id": artifact_id,
            "description": description,
        },
    )

    assert_retrieving_model_version_by_version_number_works(
        dioptra_client,
        model_id=model_id,
        version_number=model_version_response["versionNumber"],
        expected=model_version_response,
    )


def test_model_versions_get_all(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
        dioptra_client, model_id=model_id, expected=model_version_expected_list
    )


@pytest.mark.parametrize(
    "field, value, expected_count",
    [
        ("description", None, 1),
        ("tag", "Foo", 0),
    ],
)
def test_model_version_searchable_fields(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_models: dict[str, Any],
    registered_model_versions: dict[str, Any],
    field: str,
    value: str | None,
    expected_count: int,
) -> None:
    model_version = registered_model_versions["version1"]
    search_value = model_version[field] if value is None else value
    assert_searchable_field_works(
        dioptra_client=dioptra_client.models.versions,
        term=field,
        value=search_value,
        expected_count=expected_count,
        context={"model_id": registered_models["model1"]["id"]},
    )


def test_model_version_search_query(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_models: dict[str, Any],
    registered_model_versions: dict[str, Any],
) -> None:
    """Test that model versions can be queried with a search term.

    Given an authenticated user, registered model, and registered model versions
    this test validates the following sequence of actions:

    - The user is able to retrieve a list of all registered model versions with various
      queries.
    - The returned list of model versions matches the expected matches from the query.
    """
    model_id = registered_models["model1"]["id"]
    model_version_expected_list = list(registered_model_versions.values())[::4]
    assert_retrieving_model_versions_works(
        dioptra_client,
        model_id=model_id,
        expected=model_version_expected_list,
        search="description:*version*",
    )
    model_id = registered_models["model2"]["id"]
    model_version_expected_list = list(registered_model_versions.values())[1:-3]
    assert_retrieving_model_versions_works(
        dioptra_client,
        model_id=model_id,
        expected=model_version_expected_list,
        search="description:*version*",
    )
    model_id = registered_models["model2"]["id"]
    model_version_expected_list = [
        list(registered_model_versions.values())[n] for n in (1, 3)
    ]
    assert_retrieving_model_versions_works(
        dioptra_client,
        model_id=model_id,
        expected=model_version_expected_list,
        search="*",
    )


def test_modify_model_version(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_models: dict[str, Any],
    registered_model_versions: dict[str, Any],
) -> None:
    model_id = registered_models["model1"]["id"]
    model_version_number_to_modify = registered_model_versions["version1"][
        "versionNumber"
    ]
    new_description = "The new description"
    dioptra_client.models.versions.modify_by_id(
        model_id=model_id,
        version_number=model_version_number_to_modify,
        description=new_description,
    )
    assert_model_version_description_matches_expected_description(
        dioptra_client,
        model_id=model_id,
        version_number=model_version_number_to_modify,
        expected_description=new_description,
    )
