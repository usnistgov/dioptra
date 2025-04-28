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
"""Test suite for plugin parameter type operations.

This module contains a set of tests that validate the CRUD operations and additional
functionalities for the plugin parameter type entity. The tests ensure that the plugin
parameter types can be submitted and retrieved as expected through the REST API.
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


def assert_retrieving_plugin_parameter_types_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol, DioptraResponseProtocol],
    expected: list[dict[str, Any]],
    group_id: int | None = None,
    sort_by: str | None = None,
    descending: bool | None = None,
    search: str | None = None,
    paging_info: dict[str, Any] | None = None,
) -> None:
    """Assert that retrieving plugin parameter types works.

    Args:
        client: The Flask test client.
        expected: The expected response from the API.
        group_id: The group of the plugin parameter type.
        search: The search query parameters.
        paging_info: The paging query parameters.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """

    assert_retrieving_resource_works(
        dioptra_client=dioptra_client.plugin_parameter_types,
        expected=expected,
        group_id=group_id,
        sort_by=sort_by,
        descending=descending,
        search=search,
        paging_info=paging_info,
    )


def assert_retrieving_plugin_parameter_type_by_id_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol, DioptraResponseProtocol],
    id: int,
    expected: dict[str, Any],
) -> None:
    """Assert that retrieving a plugin parameter type by id works.

    Args:
        client: The Flask test client.
        id: The id of the plugin parameter type to retrieve.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = dioptra_client.plugin_parameter_types.get_by_id(id)
    assert (
        response.status_code == HTTPStatus.OK
        and helpers.convert_response_to_dict(response) == expected
    )


def assert_plugin_parameter_type_name_matches_expected_name(
    dioptra_client: DioptraClient[DioptraResponseProtocol, DioptraResponseProtocol],
    id: int,
    expected_name: str,
) -> None:
    """Assert that the name of a plugin parameter type matches the expected name.

    Args:
        client: The Flask test client.
        id: The id of the plugin parameter type to retrieve.
        expected_name: The expected name of the plugin parameter type.

    Raises:
        AssertionError: If the response status code is not 200 or if the name of the
            experiment does not match the expected name.
    """
    response = dioptra_client.plugin_parameter_types.get_by_id(id)
    assert (
        response.status_code == HTTPStatus.OK
        and helpers.convert_response_to_dict(response)["name"] == expected_name
    )


def assert_deleting_plugin_parameter_type_by_id_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol, DioptraResponseProtocol],
    id: int,
    expected: dict[str, Any],
) -> None:
    """Assert that deleting a plugin parameter type by id works.

    Args:
        client: The Flask test client.
        id: The id of the plugin parameter type to delete.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 404 or if the API response
            does not match the expected response.
    """
    response = dioptra_client.plugin_parameter_types.delete_by_id(id)
    assert (
        response.status_code == HTTPStatus.OK
        and helpers.convert_response_to_dict(response) == expected
    )


def assert_plugin_parameter_type_is_not_found(
    dioptra_client: DioptraClient[DioptraResponseProtocol, DioptraResponseProtocol],
    id: int,
) -> None:
    """Assert that a plugin parameter type is not found.

    Args:
        client: The Flask test client.
        id: The id of the plugin parameter type to retrieve.

    Raises:
        AssertionError: If the response status code is not 404.
    """
    response = dioptra_client.plugin_parameter_types.get_by_id(id)
    assert response.status_code == HTTPStatus.NOT_FOUND


def assert_cannot_rename_invalid_plugin_parameter_type(
    dioptra_client: DioptraClient[DioptraResponseProtocol, DioptraResponseProtocol],
    id: int,
    json_payload: dict[str, Any],
) -> None:
    """Assert that attempting to rename a Plugin Parameter Type with invalid
    parameters using the API fails.

    Args:
        client: The Flask test client.
        id: The id of the plugin parameter type to rename.
        json_payload: The full payload to be sent to the API.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = dioptra_client.plugin_parameter_types.modify_by_id(
        plugin_parameter_type_id=id, **json_payload
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def assert_cannot_create_invalid_plugin_parameter_type(
    dioptra_client: DioptraClient[DioptraResponseProtocol, DioptraResponseProtocol],
    json_payload: dict[str, Any],
) -> None:
    """Assert that attempting to create a Plugin Parameter Type with invalid
    parameters using the API fails.

    Args:
        client: The Flask test client.
        json_payload: The full payload to be sent to the API.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = dioptra_client.plugin_parameter_types.create(**json_payload)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def assert_cannot_create_existing_plugin_parameter_type(
    dioptra_client: DioptraClient[DioptraResponseProtocol, DioptraResponseProtocol],
    name: str,
    group_id: int,
) -> None:
    """Assert that attempting to create a Plugin Parameter Type with an existing
    name using the API fails.

    Args:
        client: The Flask test client.
        name: The name of the plugin parameter type.
        group_id: The group of the plugin parameter type.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = dioptra_client.plugin_parameter_types.create(
        group_id=group_id, name=name, description="", structure={}
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def assert_cannot_rename_plugin_parameter_type_to_existing_name(
    dioptra_client: DioptraClient[DioptraResponseProtocol, DioptraResponseProtocol],
    id: int,
    existing_name: str,
    new_structure: dict[str, Any] | None,
    new_description: str | None,
) -> None:
    """Assert that attempting to rename a Plugin Parameter Type to an existing
    name using the API fails.

    Args:
        client: The Flask test client.
        id: The id of the plugin parameter type to rename.
        existing_name: The name of an existing plugin parameter type.
        new_structure: The new structure to assign to the plugin parameter type.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = dioptra_client.plugin_parameter_types.modify_by_id(
        plugin_parameter_type_id=id,
        name=existing_name,
        structure=new_structure,
        description=new_description,
    )
    assert response.status_code == HTTPStatus.CONFLICT


def assert_cannot_delete_invalid_plugin_parameter_type(
    dioptra_client: DioptraClient[DioptraResponseProtocol, DioptraResponseProtocol],
    id: Any,
) -> None:
    """Assert that attempting to delete a Plugin Parameter Type with invalid
    parameters using the API fails.

    Args:
        client: The Flask test client.
        id: The id of the plugin parameter type to delete.
        json_payload: The full payload to be sent to the API.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = dioptra_client.plugin_parameter_types.delete_by_id(
        plugin_parameter_type_id=id
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def assert_plugin_parameter_type_content_matches_expectations(
    response: dict[str, Any], expected_contents: dict[str, Any]
) -> None:
    """Assert that a Plugin Parameter Type's fields match the expected values.

    Args:
        response: The response to check.
        expected_contents: The expected values for the response.
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
        "structure",
        "description",
        "tags",
    }
    assert set(response.keys()) == expected_keys

    # Validate the non-Ref fields
    assert isinstance(response["id"], int)
    assert isinstance(response["snapshot"], int)
    assert isinstance(response["name"], str)
    assert isinstance(response["structure"], (dict, type(None)))
    assert isinstance(response["description"], (str, type(None)))
    assert isinstance(response["createdOn"], str)
    assert isinstance(response["snapshotCreatedOn"], str)
    assert isinstance(response["lastModifiedOn"], str)
    assert isinstance(response["latestSnapshot"], bool)
    assert isinstance(response["hasDraft"], bool)

    assert response["name"] == expected_contents["name"]
    assert response["structure"] == expected_contents["structure"]
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


# -- Tests -----------------------------------------------------------------------------


def test_get_all_plugin_parameter_types(
    dioptra_client: DioptraClient[DioptraResponseProtocol, DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugin_parameter_types: dict[str, Any],
) -> None:
    """Test that all Plugin Parameter Types can be retrieved.

        Scenario: Get a List of Plugin Parameter Types
            Given I am an authorized user,
            I need to be able to submit a GET request with optional query parameters
            in order to retrieve a list of plugin parameter types matching the
            parameters.

    This test validates this scenario by following these actions:

    - The user is able to retrieve a list of all plugin parameter types.
    - The returned list of plugin parameter types match the full list of existing plugin
      parameter types.
    """
    plugin_param_type_expected_list = list(registered_plugin_parameter_types.values())
    assert_retrieving_plugin_parameter_types_works(
        dioptra_client=dioptra_client, expected=plugin_param_type_expected_list
    )


@pytest.mark.parametrize(
    "sort_by, descending , expected",
    [
        (
            "name",
            True,
            [
                "string",
                "number",
                "null",
                "plugin_param_type2",
                "plugin_param_type3",
                "integer",
                "plugin_param_type1",
                "boolean",
                "any",
            ],
        ),
        (
            "name",
            False,
            [
                "any",
                "boolean",
                "plugin_param_type1",
                "integer",
                "plugin_param_type3",
                "plugin_param_type2",
                "null",
                "number",
                "string",
            ],
        ),
        (
            "createdOn",
            True,
            [
                "plugin_param_type3",
                "plugin_param_type2",
                "plugin_param_type1",
                "null",
                "boolean",
                "number",
                "integer",
                "string",
                "any",
            ],
        ),
        (
            "createdOn",
            False,
            [
                "any",
                "string",
                "integer",
                "number",
                "boolean",
                "null",
                "plugin_param_type1",
                "plugin_param_type2",
                "plugin_param_type3",
            ],
        ),
    ],
)
def test_plugin_parameter_type_sort(
    dioptra_client: DioptraClient[DioptraResponseProtocol, DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugin_parameter_types: dict[str, Any],
    sort_by: str | None,
    descending: bool,
    expected: list[str],
) -> None:
    """Test that plugin param types can be sorted by column.

    Given an authenticated user and registered types, this test validates the following
    sequence of actions:

    - A user registers three types, "image_shape", "model_output", "model".
    - The user is able to retrieve a list of all registered types sorted by a column
      ascending/descending.
    - The returned list of plugin param types matches the order in the parametrize lists
      above.
    """

    expected_plugin_parameter_types = [
        registered_plugin_parameter_types[expected_name] for expected_name in expected
    ]
    assert_retrieving_plugin_parameter_types_works(
        dioptra_client,
        sort_by=sort_by,
        descending=descending,
        expected=expected_plugin_parameter_types,
    )


def test_plugin_parameter_type_search_query(
    dioptra_client: DioptraClient[DioptraResponseProtocol, DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugin_parameter_types: dict[str, Any],
) -> None:
    """Test that multiple Plugin Parameter Types can be retrieved using search terms.

    Given an authenticated user and registered plugin parameter types, this test
    validates this scenario by following these actions:

    - The user is able to retrieve 2 lists of the submitted plugin parameter types
      using different query parameters.
    - The returned lists of plugin parameter types match the searches provided
      during both submissions.
    """
    assert_retrieving_plugin_parameter_types_works(
        dioptra_client,
        expected=[registered_plugin_parameter_types["string"]],
        search="name:string",
    )
    assert_retrieving_plugin_parameter_types_works(
        dioptra_client,
        expected=[
            registered_plugin_parameter_types["plugin_param_type2"],
            registered_plugin_parameter_types["plugin_param_type3"],
        ],
        search="*model*",
    )
    plugin_param_type_expected_list = list(registered_plugin_parameter_types.values())
    assert_retrieving_plugin_parameter_types_works(
        dioptra_client, expected=plugin_param_type_expected_list, search="*"
    )


def test_plugin_parameter_type_group_query(
    dioptra_client: DioptraClient[DioptraResponseProtocol, DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugin_parameter_types: dict[str, Any],
) -> None:
    """Test that Plugin Parameter Types can be retrieved using a group filter.

    Given an authenticated user and registered plugin parameter types, this test
    validates this scenario by following these actions:

    - The user is able to retrieve a list of all submitted plugin parameter types
      owned by the default group.
    - The returned list of plugin parameter types matches the expected list owned by
      the default group.
    """
    plugin_param_type_expected_list = list(registered_plugin_parameter_types.values())
    assert_retrieving_plugin_parameter_types_works(
        dioptra_client,
        expected=plugin_param_type_expected_list,
        group_id=auth_account["groups"][0]["id"],
    )


def test_create_plugin_parameter_type(
    dioptra_client: DioptraClient[DioptraResponseProtocol, DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
) -> None:
    """Test that Plugin Parameter Types can be created using the API.

        Scenario: Create a Plugin Parameter Type
            Given I am an authorized user,
            I need to be able to submit a POST request with body parameters name
            group_id, and optional structure
            in order to create a new plugin parameter type.

    This test validates the following sequence of actions:
    - A user submits a POST request for a plugin parameter type.
    - The user retrieves information about one plugin parameter type using its id.
    - The returned information matches what was provided during creation.
    - This set of steps is repeated when testing using a missing parameter, extra
      parameter and a parameter with the wrong type during the POST request.
    - The second, third and fourth POST operations are expected to fail.
    """
    name = "test_plugin_param_type"
    user_id = auth_account["id"]
    group_id = auth_account["groups"][0]["id"]
    description = "This is a plugin parameter type"
    plugin_param_type1_response = dioptra_client.plugin_parameter_types.create(
        group_id=group_id,
        name=name,
        description=description,
    )
    plugin_param_type1_expected = helpers.convert_response_to_dict(
        plugin_param_type1_response
    )
    assert_plugin_parameter_type_content_matches_expectations(
        response=plugin_param_type1_expected,
        expected_contents={
            "name": name,
            "user_id": user_id,
            "group_id": group_id,
            "description": description,
            "structure": None,
        },
    )
    assert_retrieving_plugin_parameter_type_by_id_works(
        dioptra_client,
        id=plugin_param_type1_expected["id"],
        expected=plugin_param_type1_expected,
    )

    # Error case (wrong type)
    assert_cannot_create_invalid_plugin_parameter_type(
        dioptra_client,
        json_payload={
            "name": "plugin_param_type_1",
            "group_id": "invalid",
        },
    )


def test_get_plugin_parameter_type(
    dioptra_client: DioptraClient[DioptraResponseProtocol, DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugin_parameter_types: dict[str, Any],
) -> None:
    """Test that a Plugin Parameter Type can be retrieved following the scenario below:

        Scenario: Get a Plugin Parameter Type using its ID
            Given I am an authorized user and at least one plugin parameter type exists,
            I need to be able to submit a GET request with path parameter id
            in order to retrieve the plugin parameter type with the specified ID.

    This test validates this scenario by following these actions:

    - A user submits a POST request for two plugin parameter types.
    - The user retrieves information about one plugin parameter type using its id.
    - The returned information matches what was provided during creation.
    """
    plugin_param_type1_expected = registered_plugin_parameter_types[
        "plugin_param_type1"
    ]

    # Get a Plugin Parameter Type using its ID
    assert_retrieving_plugin_parameter_type_by_id_works(
        dioptra_client,
        id=plugin_param_type1_expected["id"],
        expected=plugin_param_type1_expected,
    )


def test_delete_plugin_parameter_type(
    dioptra_client: DioptraClient[DioptraResponseProtocol, DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugin_parameter_types: dict[str, Any],
) -> None:
    """Test that a Plugin Parameter Type can be deleted following the scenario below:

         Scenario: Delete a Plugin Parameter Type
              Given I am an authorized user and at least one plugin parameter type
              exists, I need to be able to submit a DELETE request with path parameter
              id in order to delete a plugin parameter type with the specified ID.

    This test validates these scenarios by following these actions:

     - A user submits a POST request for two plugin parameter types.
     - The user retrieves information about one plugin parameter type using its id.
     - The returned information matches what was provided during creation.
     - The plugin parameter type is then deleted.
     - A search by id for the deleted plugin parameter type should return a 404 error.
    """
    plugin_param_type1 = registered_plugin_parameter_types["plugin_param_type1"]

    # Delete a Plugin Parameter Type using its ID
    assert_retrieving_plugin_parameter_type_by_id_works(
        dioptra_client, id=plugin_param_type1["id"], expected=plugin_param_type1
    )
    dioptra_client.plugin_parameter_types.delete_by_id(plugin_param_type1["id"])
    assert_plugin_parameter_type_is_not_found(dioptra_client, plugin_param_type1["id"])


def test_modify_plugin_parameter_type(
    dioptra_client: DioptraClient[DioptraResponseProtocol, DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugin_parameter_types: dict[str, Any],
) -> None:
    """Test that a Plugin Parameter Type can be modified following the scenario below:

        Scenario: Modify an Existing Plugin Parameter Type
            Given I am an authorized user and at least one plugin parameter type exists,
            I need to be able to submit a PUT request with path parameter id and body
            parameters name and structure in order to update the plugin parameter type
            with the new name and structure parameters.

    This test validates this scenario by following these actions:

    - A user creates a plugin parameter type.
    - The user is able to retrieve information about the plugin parameter type that
      matches the information that was provided during creation.
    - The user modifies this same plugin parameter type.
    - The user retrieves information about the same plugin parameter type and it
      reflects the changes.
    - A user then attempts to modify a plugin parameter type with a missing parameter,
      extra parameter, and a parameter with the wrong type in the request.
    - Each of these cases causes an error to be returned.
    """
    plugin_param_type1 = registered_plugin_parameter_types["plugin_param_type1"]
    plugin_param_type2 = registered_plugin_parameter_types["plugin_param_type2"]
    plugin_param_type3 = registered_plugin_parameter_types["plugin_param_type3"]

    start_name = plugin_param_type1["name"]
    updated_name = "changed_name"
    updated_structure = {"key": "value"}

    # Modify an Existing Plugin Parameter Type
    assert_plugin_parameter_type_name_matches_expected_name(
        dioptra_client, id=plugin_param_type1["id"], expected_name=start_name
    )
    dioptra_client.plugin_parameter_types.modify_by_id(
        plugin_parameter_type_id=plugin_param_type1["id"],
        name=updated_name,
        description=plugin_param_type1["description"],
        structure=updated_structure,
    )
    assert_plugin_parameter_type_name_matches_expected_name(
        dioptra_client, id=plugin_param_type1["id"], expected_name=updated_name
    )

    # Error case (wrong type)
    assert_cannot_rename_invalid_plugin_parameter_type(
        dioptra_client,
        id=plugin_param_type2["id"],
        json_payload={"name": 42, "description": None, "structure": dict()},
    )

    # Attempt to rename a Plugin Parameter Type to an existing name
    assert_cannot_rename_plugin_parameter_type_to_existing_name(
        dioptra_client,
        id=plugin_param_type1["id"],
        existing_name=plugin_param_type3["name"],
        new_structure=None,
        new_description=None,
    )


def test_cannot_create_existing_plugin_parameter_type(
    dioptra_client: DioptraClient[DioptraResponseProtocol, DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugin_parameter_types: dict[str, Any],
) -> None:
    """Test that creating an existing Plugin Parameter Type produces an error.

    This test validates the following sequence of actions:
    - A user attempts to create a plugin parameter type with a name that already
      exists.
    - This causes a 400 error to be returned.
    """
    existing_plugin_param_type = registered_plugin_parameter_types["plugin_param_type1"]

    assert_cannot_create_existing_plugin_parameter_type(
        dioptra_client,
        name=existing_plugin_param_type,
        group_id=auth_account["groups"][0]["id"],
    )


def test_cannot_retrieve_nonexistent_plugin_parameter_type(
    dioptra_client: DioptraClient[DioptraResponseProtocol, DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
) -> None:
    """Test that retrieving an nonexistent Plugin Parameter Type produces an error.

    This test validates the following sequence of actions:
    - A user attempts to retrieve a plugin parameter type that doesn't exist.
    - This causes a 404 error to be returned.
    """
    assert_plugin_parameter_type_is_not_found(dioptra_client, id=42)


def test_manage_existing_plugin_parameter_type_draft(
    dioptra_client: DioptraClient[DioptraResponseProtocol, DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugin_parameter_types: dict[str, Any],
) -> None:
    """Test that a draft of an existing plugin parameter type can be created
    and managed by the user
    Given an authenticated user and registered plugin parameter types, this
    test validates the following sequence of actions:
    - The user creates a draft of an existing plugin parameter type
    - The user retrieves information about the draft and gets the expected response
    - The user attempts to create another draft of the same existing plugin
      parameter type
    - The request fails with an appropriate error message and response code.
    - The user modifies the name of the plugin parameter type in the draft
    - The user retrieves information about the draft and gets the expected response
    - The user deletes the draft
    - The user attempts to retrieve information about the deleted draft.
    - The request fails with an appropriate error message and response code.
    """
    # Requests data
    plugin_param_type = registered_plugin_parameter_types["plugin_param_type1"]
    name = "draft"
    new_name = "draft2"
    description = "description"

    # test creation
    draft = {"name": name, "description": description, "structure": None}
    draft_mod = {"name": new_name, "description": description, "structure": None}

    # Expected responses
    draft_expected = {
        "user_id": auth_account["id"],
        "group_id": plugin_param_type["group"]["id"],
        "resource_id": plugin_param_type["id"],
        "resource_snapshot_id": plugin_param_type["snapshot"],
        "num_other_drafts": 0,
        "payload": draft,
    }
    draft_mod_expected = {
        "user_id": auth_account["id"],
        "group_id": plugin_param_type["group"]["id"],
        "resource_id": plugin_param_type["id"],
        "resource_snapshot_id": plugin_param_type["snapshot"],
        "num_other_drafts": 0,
        "payload": draft_mod,
    }

    # Run routine: existing resource drafts tests
    routines.run_existing_resource_drafts_tests(
        dioptra_client.plugin_parameter_types,
        dioptra_client.plugin_parameter_types.modify_resource_drafts,
        dioptra_client.workflows,
        plugin_param_type["id"],
        draft=draft,
        draft_mod=draft_mod,
        draft_expected=draft_expected,
        draft_mod_expected=draft_mod_expected,
    )


def test_manage_new_plugin_parameter_type_drafts(
    dioptra_client: DioptraClient[DioptraResponseProtocol, DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
) -> None:
    """Test that drafts of plugin parameter type can be created and managed by the user
    Given an authenticated user, this test validates the following sequence of actions:
    - The user creates two plugin parameter type drafts
    - The user retrieves information about the drafts and gets the expected response
    - The user modifies the description of the plugin parameter type in the first draft
    - The user retrieves information about the draft and gets the expected response
    - The user deletes the first draft
    - The user attempts to retrieve information about the deleted draft.
    - The request fails with an appropriate error message and response code.
    """
    # Requests data
    group_id = auth_account["groups"][0]["id"]
    drafts = {
        "draft1": {
            "name": "plugin_parameter_type1",
            "description": "new plugin parameter type",
            "structure": None,
        },
        "draft2": {
            "name": "plugin_parameter_type2",
            "description": None,
            "structure": None,
        },
    }
    draft1_mod = {"name": "draft1", "description": "new description", "structure": None}

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

    # Run routine: new resource drafts tests
    routines.run_new_resource_drafts_tests(
        dioptra_client.plugin_parameter_types,
        dioptra_client.plugin_parameter_types.new_resource_drafts,
        dioptra_client.workflows,
        drafts=drafts,
        draft1_mod=draft1_mod,
        draft1_expected=draft1_expected,
        draft2_expected=draft2_expected,
        draft1_mod_expected=draft1_mod_expected,
        group_id=group_id,
    )


def test_manage_plugin_parameter_type_snapshots(
    dioptra_client: DioptraClient[DioptraResponseProtocol, DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugin_parameter_types: dict[str, Any],
) -> None:
    """Test that different snapshots of a plugin parameter type can be retrieved
    by the user.

    Given an authenticated user and registered plugin parameter types, this test
    validates the following sequence of actions:

    - The user modifies a plugin parameter type
    - The user retrieves information about the original snapshot of the plugin
      parameter type and gets the expected response
    - The user retrieves information about the new snapshot of the plugin
      parameter type and gets the expected response
    - The user retrieves a list of all snapshots of the plugin parameter type
      and gets the expected response
    """
    plugin_param_type_to_rename = registered_plugin_parameter_types[
        "plugin_param_type1"
    ]
    modified_plugin_param_type = helpers.convert_response_to_dict(
        dioptra_client.plugin_parameter_types.modify_by_id(
            plugin_parameter_type_id=plugin_param_type_to_rename["id"],
            name=plugin_param_type_to_rename["name"] + "modified",
            description=plugin_param_type_to_rename["description"],
            structure=plugin_param_type_to_rename["structure"],
        )
    )

    # Run routine: resource snapshots tests
    routines.run_resource_snapshots_tests(
        dioptra_client.plugin_parameter_types.snapshots,
        resource_to_rename=plugin_param_type_to_rename,
        modified_resource=modified_plugin_param_type,
    )


def test_tag_plugin_parameter_type(
    dioptra_client: DioptraClient[DioptraResponseProtocol, DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugin_parameter_types: dict[str, Any],
    registered_tags: dict[str, Any],
) -> None:
    """Test that tags can applied to plugin parameter types.

    Given an authenticated user and registered plugin parameter types, this test
    validates the following sequence of actions:
    """
    plugin_param_type = registered_plugin_parameter_types["plugin_param_type1"]
    tag_ids = [tag["id"] for tag in registered_tags.values()]

    # Run routine: resource tag tests
    routines.run_resource_tag_tests(
        dioptra_client.plugin_parameter_types.tags,
        plugin_param_type["id"],
        tag_ids=tag_ids,
    )
