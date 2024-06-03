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
"""Test suite for plugin operations.

This module contains a set of tests that validate the CRUD operations and additional
functionalities for the plugin entity. The tests ensure that the plugins can be
registered, renamed, and deleted as expected through the REST API.
"""
import textwrap
from typing import Any

import pytest
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from werkzeug.test import TestResponse

from dioptra.restapi.routes import V1_PLUGINS_ROUTE, V1_ROOT

from ..lib import actions, helpers

# -- Actions ---------------------------------------------------------------------------


def modify_plugin(
    client: FlaskClient,
    plugin_id: int,
    new_name: str,
    new_description: str,
) -> TestResponse:
    """Rename a plugin using the API.

    Args:
        client: The Flask test client.
        plugin_id: The id of the plugin to rename.
        new_name: The new name to assign to the plugin.
        new_description: The new description to assign to the plugin.

    Returns:
        The response from the API.
    """
    payload: dict[str, Any] = {"name": new_name, "description": new_description}

    return client.put(
        f"/{V1_ROOT}/{V1_PLUGINS_ROUTE}/{plugin_id}",
        json=payload,
        follow_redirects=True,
    )


def delete_plugin_with_id(
    client: FlaskClient,
    plugin_id: int,
) -> TestResponse:
    """Delete a plugin using the API.

    Args:
        client: The Flask test client.
        plugin_id: The id of the plugin to delete.

    Returns:
        The response from the API.
    """
    return client.delete(
        f"/{V1_ROOT}/{V1_PLUGINS_ROUTE}/{plugin_id}",
        follow_redirects=True,
    )


# -- Assertions ------------------------------------------------------------------------


def assert_plugin_response_contents_matches_expectations(
    response: dict[str, Any], expected_contents: dict[str, Any]
) -> None:
    """Assert that plugin response contents is valid.

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
        "name",
        "description",
        "files",
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

    # Validate the TagRef structure
    for tag in response["tags"]:
        assert isinstance(tag["id"], int)
        assert isinstance(tag["name"], str)
        assert isinstance(tag["url"], str)

    # Validate the PluginFileRef structure
    for file in response["files"]:
        assert isinstance(file["id"], int)
        assert isinstance(file["url"], str)
        assert isinstance(file["plugin_id"], int)
        assert isinstance(file["filename"], str)


def assert_plugin_file_response_contents_matches_expectations(
    response: dict[str, Any], expected_contents: dict[str, Any]
) -> None:
    """Assert that plugin file response contents is valid.

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
        "filename",
        "description",
        "contents",
        "tasks",
    }
    assert set(response.keys()) == expected_keys

    # Validate the non-Ref fields
    assert isinstance(response["id"], int)
    assert isinstance(response["snapshot"], int)
    assert isinstance(response["filename"], str)
    assert isinstance(response["description"], str)
    assert isinstance(response["contents"], str)
    assert isinstance(response["createdOn"], str)
    assert isinstance(response["lastModifiedOn"], str)
    assert isinstance(response["latestSnapshot"], bool)
    
    assert response["filename"] == expected_contents["filename"]
    assert response["description"] == expected_contents["description"]
    assert response["contents"] == expected_contents["contents"]

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
    assert response["group"]["id"] == expected_contents["group"]["id"]

    # Validate the PluginTask structure
    for task in response["tasks"]:
        assert isinstance(task["name"], str)

        # Validate PluginTaskParameter Structure for inputs and outputs
        for param in task["input_params"] + task["output_params"]:
            assert isinstance(param["number"], int)
            assert isinstance(param["name"], str)

            # Validate PluginParameterTypeRef structure
            assert isinstance(param["plugin_param_type"]["id"], int)
            assert isinstance(param["plugin_param_type"]["name"], str)

            # Validate the GroupRef structure
            assert isinstance(param["plugin_param_type"]["group"]["id"], int)
            assert isinstance(param["plugin_param_type"]["group"]["name"], str)
            assert isinstance(param["plugin_param_type"]["group"]["url"], str)
    

def assert_retrieving_plugin_by_id_works(
    client: FlaskClient,
    plugin_id: int,
    expected: dict[str, Any],
) -> None:
    """Assert that retrieving a plugin by id works.

    Args:
        client: The Flask test client.
        plugin_id: The id of the plugin to retrieve.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = client.get(
        f"/{V1_ROOT}/{V1_PLUGINS_ROUTE}/{plugin_id}", follow_redirects=True
    )
    assert response.status_code == 200 and response.get_json() == expected


def assert_retrieving_plugin_file_by_id_works(
    client: FlaskClient,
    plugin_id: int,
    plugin_file_id: int,
    expected: dict[str, Any],
) -> None:
    """Assert that retrieving a plugin file by id works.

    Args:
        client: The Flask test client.
        plugin_id: The id of the plugin to that contains the file.
        plugin_file_id: The id of the plugin file to retrieve.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = client.get(
        f"/{V1_ROOT}/{V1_PLUGINS_ROUTE}/{plugin_id}", follow_redirects=True
    )
    assert response.status_code == 200 and response.get_json() == expected


def assert_retrieving_plugins_works(
    client: FlaskClient,
    expected: list[dict[str, Any]],
    group_id: int | None = None,
    search: str | None = None,
    paging_info: dict[str, Any] | None = None,
) -> None:
    """Assert that retrieving all plugins works.

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

    query_string["group_id"] = group_id

    if search is not None:
        query_string["search"] = search

    if paging_info is not None:
        query_string["index"] = paging_info["index"]
        query_string["pageLength"] = paging_info["page_length"]

    response = client.get(
        f"/{V1_ROOT}/{V1_PLUGINS_ROUTE}",
        query_string=query_string,
        follow_redirects=True,
    )
    assert response.status_code == 200 and response.get_json()["data"] == expected


def assert_registering_existing_plugin_name_fails(
    client: FlaskClient, name: str, group_id: int
) -> None:
    """Assert that registering a plugin with an existing name fails.

    Args:
        client: The Flask test client.
        name: The name to assign to the new plugin.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = actions.register_plugin(client, name=name, description="", group_id=group_id)
    assert response.status_code == 400


def assert_plugin_name_matches_expected_name(
    client: FlaskClient, plugin_id: int, expected_name: str
) -> None:
    """Assert that the name of a plugin matches the expected name.

    Args:
        client: The Flask test client.
        plugin_id: The id of the plugin to retrieve.
        expected_name: The expected name of the plugin.

    Raises:
        AssertionError: If the response status code is not 200 or if the name of the
            plugin does not match the expected name.
    """
    response = client.get(
        f"/{V1_ROOT}/{V1_PLUGINS_ROUTE}/{plugin_id}",
        follow_redirects=True,
    )
    assert response.status_code == 200 and response.get_json()["name"] == expected_name


def assert_plugin_is_not_found(
    client: FlaskClient,
    plugin_id: int,
) -> None:
    """Assert that a plugin is not found.

    Args:
        client: The Flask test client.
        plugin_id: The id of the plugin to retrieve.

    Raises:
        AssertionError: If the response status code is not 404.
    """
    response = client.get(
        f"/{V1_ROOT}/{V1_PLUGINS_ROUTE}/{plugin_id}",
        follow_redirects=True,
    )
    assert response.status_code == 404


def assert_cannot_rename_plugin_with_existing_name(
    client: FlaskClient,
    plugin_id: int,
    existing_name: str,
    existing_description: str,
) -> None:
    """Assert that renaming a plugin with an existing name fails.

    Args:
        client: The Flask test client.
        plugin_id: The id of the plugin to rename.
        name: The name of an existing plugin.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = modify_plugin(
        client=client,
        plugin_id=plugin_id,
        new_name=existing_name,
        new_description=existing_description,
    )
    assert response.status_code == 400


# -- Tests -----------------------------------------------------------------------------


def test_create_plugin(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
) -> None:
    """Test that plugins can be correctly registered and retrieved using the API.

    Given an authenticated user, this test validates the following sequence of actions:

    - The user registers a plugin named "my_plugin".
    - The response is valid matches the expected values given the registration request.
    - The user is able to retrieve information about the plugin using the plugin id.
    """
    name = "my_plugin"
    description = "The first plugin."
    user_id = auth_account["id"]
    group_id = auth_account["groups"][0]["id"]
    plugin_response = actions.register_plugin(
        client, name=name, description=description, group_id=group_id
    )
    plugin_expected = plugin_response.get_json()    
    assert_plugin_response_contents_matches_expectations(
        response=plugin_expected,
        expected_contents={
            "name": name,
            "description": description, 
            "user_id": user_id,
            "group_id": group_id,
        },
    )
    assert_retrieving_plugin_by_id_works(
        client, plugin_id=plugin_expected["id"], expected=plugin_expected
    )


def test_plugin_get_all(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugins: dict[str, Any],
) -> None:
    """Test that all plugins can be retrieved.

    Given an authenticated user and registered plugins, this test validates the following
    sequence of actions:

    - A user registers three plugins, "plugin1", "plugin2", "plugin3".
    - The user is able to retrieve a list of all registered plugins.
    - The returned list of plugins matches the full list of registered plugins.
    """
    plugin_expected_list = list(registered_plugins.values())
    assert_retrieving_plugins_works(client, expected=plugin_expected_list)


@pytest.mark.v1_test
def test_plugin_search_query(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugins: dict[str, Any],
) -> None:
    """Test that plugins can be queried with a search term.

    Given an authenticated user and registered plugins, this test validates the following
    sequence of actions:

    - The user is able to retrieve a list of all registered plugins with a description
      that contains 'plugin'.
    - The returned list of plugins matches the expected matches from the query.
    """
    plugin_expected_list = list(registered_plugins.values())[:2]
    assert_retrieving_plugins_works(
        client,
        expected=plugin_expected_list,
        search="description:*plugin*",
    )


def test_plugin_group_query(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugins: dict[str, Any],
) -> None:
    """Test that plugins can retrieved using a group filter.

    Given an authenticated user and registered plugins, this test validates the following
    sequence of actions:

    - The user is able to retrieve a list of all registered plugins that are owned by the
      default group.
    - The returned list of plugins matches the expected list owned by the default group.
    """
    plugin_expected_list = list(registered_plugins.values())
    assert_retrieving_plugins_works(
        client, expected=plugin_expected_list, group_id=auth_account["groups"][0]["id"]
    )


def test_cannot_register_existing_plugin_name(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugins: dict[str, Any],
) -> None:
    """Test that registering a plugin with an existing name fails.

    Given an authenticated user and registered plugins, this test validates the following
    sequence of actions:

    - The user attempts to register a second plugin with the same name.
    - The request fails with an appropriate error message and response code.
    """
    existing_plugin = registered_plugins["plugin1"]
    assert_registering_existing_plugin_name_fails(
        client,
        name=existing_plugin["name"],
        group_id=existing_plugin["group"]["id"],
    )


def test_rename_plugin(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugins: dict[str, Any],
) -> None:
    """Test that a plugin can be renamed.

    Given an authenticated user and registered plugins, this test validates the following
    sequence of actions:

    - The user issues a request to change the name of a plugin.
    - The user retrieves information about the same plugin and it reflects the name
      change.
    - The user issues a request to change the name of a plugin to an existing plugin's
      name.
    - The request fails with an appropriate error message and response code.
    """
    updated_plugin_name = "new_name"
    plugin_to_rename = registered_plugins["plugin1"]
    existing_plugin = registered_plugins["plugin2"]

    modified_plugin = modify_plugin(
        client,
        plugin_id=plugin_to_rename["id"],
        new_name=updated_plugin_name,
        new_description=plugin_to_rename["description"],
    ).get_json()
    assert_plugin_name_matches_expected_name(
        client, plugin_id=plugin_to_rename["id"], expected_name=updated_plugin_name
    )

    plugin_expected_list = [
        modified_plugin,
        registered_plugins["plugin2"],
        registered_plugins["plugin3"],
    ]
    assert_retrieving_plugins_works(client, expected=plugin_expected_list)

    modified_plugin = modify_plugin(
        client,
        plugin_id=plugin_to_rename["id"],
        new_name=updated_plugin_name,
        new_description=plugin_to_rename["description"]
    ).get_json()
    assert_plugin_name_matches_expected_name(
        client, plugin_id=plugin_to_rename["id"], expected_name=updated_plugin_name
    )
    assert_cannot_rename_plugin_with_existing_name(
        client,
        plugin_id=plugin_to_rename["id"],
        existing_name=existing_plugin["name"],
        existing_description=plugin_to_rename["description"],
    )


def test_delete_plugin_by_id(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugins: dict[str, Any],
) -> None:
    """Test that a plugin can be deleted by referencing its id.

    Given an authenticated user and registered plugins, this test validates the following
    sequence of actions:

    - The user deletes a plugin by referencing its id.
    - The user attempts to retrieve information about the deleted plugin.
    - The request fails with an appropriate error message and response code.
    """
    plugin_to_delete = registered_plugins["plugin1"]
    delete_plugin_with_id(client, plugin_id=plugin_to_delete["id"])
    assert_plugin_is_not_found(client, plugin_id=plugin_to_delete["id"])