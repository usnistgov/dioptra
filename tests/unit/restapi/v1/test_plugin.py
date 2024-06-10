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
from typing import Any, List

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


def modify_plugin_file(
    client: FlaskClient,
    plugin_id: int,
    plugin_file_id: int,
    new_name: str,
    new_description: str,
) -> TestResponse:
    """Rename a plugin file using the API.

    Args:
        client: The Flask test client.
        plugin_id: The id of the plugin to with plugin files.
        plugin_file_id: The id of the plugin file to rename.
        new_name: The new name to assign to the plugin file.
        new_description: The new description to assign to the plugin file.

    Returns:
        The response from the API.
    """
    payload: dict[str, Any] = {"name": new_name, "description": new_description}

    return client.put(
        f"/{V1_ROOT}/{V1_PLUGINS_ROUTE}/{plugin_id}/files/{plugin_file_id}",
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


def delete_plugin_file_with_id(
    client: FlaskClient,
    plugin_id: int,
    plugin_file_id: int,
) -> TestResponse:
    """Delete a plugin file using the API.

    Args:
        client: The Flask test client.
        plugin_id: The id of the plugin with files.
        plugin_file_id: The id of the plugin file to delete.

    Returns:
        The response from the API.
    """
    return client.delete(
        f"/{V1_ROOT}/{V1_PLUGINS_ROUTE}/{plugin_id}/files/{plugin_file_id}",
        follow_redirects=True,
    )


def delete_all_plugin_files(client: FlaskClient, plugin_id: int) -> None:
    """Delete all plugin files for a plugin using the API.

    Args:
        client: The Flask test client.
        plugin_id: The id of the plugin with files to delele.

    Returns:
        The response from the API.
    """
    return client.delete(
        f"/{V1_ROOT}/{V1_PLUGINS_ROUTE}/{plugin_id}/files/",
        follow_redirects=True,
    )


def delete_all_plugin_tasks(
    client: FlaskClient, 
    plugin_id: int, 
    plugin_file_id: int,
) -> TestResponse:
    """Delete all plugin tasks for a plugin with file using the API.

    Args:
        client: The Flask test client.
        plugin_id: The id of the plugin with a plugin file.
        plugin_file_id: the id of the plugin file with tasks to delete.

    Returns:
        The response from the API.
    """
    payload: dict[str, Any] = {}
    return client.put(
        f"/{V1_ROOT}/{V1_PLUGINS_ROUTE}/{plugin_id}/files/{plugin_file_id}",
        json=payload,
        follow_redirects=True,
    )

# -- Assertions Plugins ----------------------------------------------------------------


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

# -- Assertions Plugin Files -----------------------------------------------------------


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
        "snapshotId",
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
    assert isinstance(response["snapshotId"], int)
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
        f"/{V1_ROOT}/{V1_PLUGINS_ROUTE}/{plugin_id}/files/{plugin_file_id}", follow_redirects=True
    )
    assert response.status_code == 200 and response.get_json() == expected


def assert_retrieving_plugin_files_works(
    client: FlaskClient,
    expected: list[dict[str, Any]],
    plugin_id: int,
    paging_info: dict[str, Any] | None = None,   
) -> None:
    """Assert that retrieving all plugin files works.

    Args:
        client: The Flask test client.
        expected: The expected response from the API.
        plugin_id: The plugin ID the files are registered too.
        group_id: The group ID used in query parameters.
        search: The search string used in query parameters.
        paging_info: The paging information used in query parameters.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """

    query_string: dict[str, Any] = {}

    if paging_info is not None:
        query_string["index"] = paging_info["index"]
        query_string["pageLength"] = paging_info["page_length"]

    response = client.get(
        f"/{V1_ROOT}/{V1_PLUGINS_ROUTE}/{plugin_id}/files",
        query_string=query_string,
        follow_redirects=True,
    )
    assert response.status_code == 200 and response.get_json()["data"] == expected


def assert_registering_existing_plugin_file_name_fails(
    client: FlaskClient,
    plugin_id: int,
    group_id: int,
    existing_filename: str, 
    contents: str,
) -> None:
    """Assert that registering a plugin file with an existing name fails.

    Args:
        client: The Flask test client.
        plugin_id: The ID of the plugin with files.
        group_id: The group ID of the user that registered the plugin file.
        existing_filename: An existing filename to assign to the new plugin file.
        contents: The string that reprents the contents of the file as plain text.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = actions.register_plugin(
        client,
        plugin_id=plugin_id,
        group_id=group_id,
        filename=existing_filename, 
        contents=contents,
    )
    assert response.status_code == 400


def assert_plugin_file_name_matches_expected_name(
    client: FlaskClient, 
    plugin_id: int,
    plugin_file_id: int,
    expected_name: str,
) -> None:
    """Assert that the name of a plugin file matches the expected name.

    Args:
        client: The Flask test client.
        plugin_id: The id of the plugin with files.
        plugin_file_id: The id of the plugin file to retrieve.
        expected_name: The expected name of the plugin file.

    Raises:
        AssertionError: If the response status code is not 200 or if the name of the
            plugin does not match the expected name.
    """
    response = client.get(
        f"/{V1_ROOT}/{V1_PLUGINS_ROUTE}/{plugin_id}/files/{plugin_file_id}",
        follow_redirects=True,
    )
    assert response.status_code == 200 and response.get_json()["filename"] == expected_name


def assert_cannot_rename_plugin_file_with_existing_name(
    client: FlaskClient,
    plugin_id: int,
    plugin_file_id: int,
    existing_name: str,
    existing_description: str,
) -> None:
    """Assert that renaming a plugin file with an existing name fails.

    Args:
        client: The Flask test client.
        plugin_id: The id of the plugin with files.
        plugin_file_id: The id of the plugin file to rename.
        existing_name: The name of an existing plugin file.
        existing_description: The  current description of the plugin file.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = modify_plugin_file(
        client=client,
        plugin_id=plugin_id,
        plugin_file_id=plugin_file_id,
        new_name=existing_name,
        new_description=existing_description,
    )
    assert response.status_code == 400


def assert_plugin_file_is_not_found(
    client: FlaskClient,
    plugin_id: int,
    plugin_file_id: int,
) -> None:
    """Assert that a plugin file is not found.

    Args:
        client: The Flask test client.
        plugin_id: The id of the plugin with files.
        plugin_file_id: The id of the plugin file to retrieve.

    Raises:
        AssertionError: If the response status code is not 404.
    """
    response = client.get(
        f"/{V1_ROOT}/{V1_PLUGINS_ROUTE}/{plugin_id}/files/{plugin_file_id}",
        follow_redirects=True,
    )
    assert response.status_code == 404


# -- Assertions Plugin Tasks -----------------------------------------------------------


def assert_plugin_task_response_contents_matches_expectations(
    response: List[dict[str, Any]], expected_contents: dict[str, Any]
) -> None:
    """Assert that plugin task response contents is valid.

    Args:
        response: The actual response from the API.
        expected_contents: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response or if the response contents is not
            valid.
    """
    for task in response:
        expected_keys = {
            "name",
            "input_params",
            "output_params",
        }
        assert set(task.keys()) == expected_keys

        # Validate the non-Ref fields
        assert isinstance(task["name"], str)
        assert task["name"] == expected_contents["name"]

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


def assert_retrieving_plugin_tasks_works(
    client: FlaskClient,
    expected: list[dict[str, Any]],
    plugin_id: int,
    plugin_file_id: int,
) -> None:
    """Assert that retrieving all plugin files works.

    Args:
        client: The Flask test client.
        expected: The expected response from the API.
        plugin_id: The plugin ID the file is registered too.
        plugin_file_id: The plugin file ID the tasks are registered too.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = client.get(
        f"/{V1_ROOT}/{V1_PLUGINS_ROUTE}/{plugin_id}/files/{plugin_file_id}",
        follow_redirects=True,
    )
    assert response.status_code == 200 and response.get_json()["data"]["tasks"] == expected

# -- Tests Plugins -----------------------------------------------------------------------------


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



# -- Tests Plugin Files ----------------------------------------------------------------


@pytest.mark.v1_test
def test_register_plugin_file(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugins: dict[str, Any],
) -> None:
    """Test that plugin files can be correctly registered to a plugin and retrieved using the API.

    Given an authenticated user and a registered plugin, this test validates the following sequence of actions:

    - The user registers a plugin file named "my_plugin_file".
    - The response is valid matches the expected values given the registration request.
    - The user is able to retrieve information about the plugin using the plugin id.
    """
    registered_plugin = registered_plugins["plugin1"]
    filename = "my_plugin_file"
    description = "The first plugin file."
    contents = textwrap.dedent(
        """from dioptra import pyplugs

        @pyplugs.register
        def hello_world(name: str) -> str:
            return f"Hello, {name}!"
        """
    )   
    plugin_file_response = actions.register_plugin_file(
        client,
        plugin_id=registered_plugin["id"],
        filename=filename, 
        description=description, 
        group_id=auth_account["default_group_id"],
        contents=contents,
    )
    plugin_file_expected = plugin_file_response.get_json()
    
    assert_plugin_file_response_contents_matches_expectations(
        response=plugin_file_expected,
        expected_contents={
            "filename": filename,
            "description": description,
            "contents": contents,
            "user_id": auth_account["user_id"],
            "group_id": auth_account["default_group_id"],
        },
    )
    assert_retrieving_plugin_file_by_id_works(
        client, 
        plugin_id=registered_plugin["id"],
        plugin_file_id=plugin_file_expected["id"],
        expected=plugin_file_expected,
    )


@pytest.mark.v1_test
def test_plugin_file_get_all(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugin_with_files: dict[str, Any],
) -> None:
    """Test that all plugin files can be retrieved.

    Given an authenticated user and a registered plugin with plugin files, this 
    test validates the following sequence of actions:

    - A user registers three plugin files, "plugin_file1", "plugin_file2", "plugin_file3"
      to the plugin.
    - The user is able to retrieve a list of all registered plugin files.
    - The returned list of plugin files matches the full list of registered plugin files.
    """
    registered_plugin = registered_plugin_with_files["plugin"]
    plugin_file1_expected = registered_plugin_with_files["plugin_file1"]
    plugin_file2_expected = registered_plugin_with_files["plugin_file2"]
    plugin_file3_expected = registered_plugin_with_files["plugin_file3"]
    plugin_file_expected_list = [
        plugin_file1_expected, 
        plugin_file2_expected, 
        plugin_file3_expected,
    ]

    assert_retrieving_plugin_files_works(
        client,
        plugin_id=registered_plugin["id"],
        expected=plugin_file_expected_list,
    )


@pytest.mark.v1_test
def test_plugin_file_delete_all(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugin_with_files: dict[str, Any],
) -> None:
    """Test that all plugin files for a plugin can be deleted.
    
    Given an authenticated user and a registered plugin with plugin files, this 
    test validates the following sequence of actions:

    - The user deletes all plugin files by referencing the plugin id.
    - The user attempts to retrieve information about the deleted plugin files.
    - The returned list of plugin files is empty.
    """
    registered_plugin = registered_plugin_with_files["plugin"]
    plugin_file_expected_list = []

    delete_all_plugin_files(client, plugin_id=registered_plugin["id"])
    assert_retrieving_plugin_files_works(
        client,
        plugin_id=registered_plugin["id"],
        expected=plugin_file_expected_list,
    )


@pytest.mark.v1_test
def test_cannot_register_existing_plugin_file_name(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugin_with_files: dict[str, Any],
) -> None:
    """Test that registering a plugin file with an existing name fails.

    Given an authenticated user and a registered plugin with plugin files, this 
    test validates the following sequence of actions:

    - The user attempts to register a second plugin file with the same name.
    - The request fails with an appropriate error message and response code.
    """
    registered_plugin = registered_plugin_with_files["plugin"]
    existing_plugin_file = registered_plugin_with_files["plugin_file1"]

    assert_registering_existing_plugin_file_name_fails(
        client,
        plugin_id=registered_plugin["id"],
        group_id=existing_plugin_file["group"]["id"],
        existing_filename=existing_plugin_file["filename"], 
        contents=existing_plugin_file["contents"],
    )


@pytest.mark.v1_test
def test_rename_plugin_file(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugin_with_files: dict[str, Any],
) -> None:
    """Test that a plugin file can be renamed.

    Given an authenticated user and a registered plugin with plugin files, this 
    test validates the following sequence of actions:

    - The user issues a request to change the name of a plugin file.
    - The user retrieves information about the same plugin file and it reflects the name
      change.
    - The user issues a request to change the name of a plugin file to an existing plugin
      file's name.
    - The request fails with an appropriate error message and response code.
    """
    registered_plugin = registered_plugin_with_files["plugin"]
    plugin_file_to_rename = registered_plugin_with_files["plugin_file1"]
    existing_plugin_file = registered_plugin_with_files["plugin_file2"]
    updated_plugin_file_name = "new_name"

    modify_plugin_file(
        client,
        plugin_id=registered_plugin["id"],
        plugin_file_id=plugin_file_to_rename["id"],
        new_name=updated_plugin_file_name,
        new_description=plugin_file_to_rename["description"],
    )
    assert_plugin_file_name_matches_expected_name(
        client, 
        plugin_id=registered_plugin["id"],
        plugin_file_id=plugin_file_to_rename["id"],
        expected_name=updated_plugin_file_name,
    )
    assert_cannot_rename_plugin_file_with_existing_name(
        client,
        plugin_id=registered_plugin["id"],
        plugin_file_id=plugin_file_to_rename["id"],
        existing_name=existing_plugin_file["filename"],
        existing_description=plugin_file_to_rename["description"],
    )


@pytest.mark.v1_test
def test_delete_plugin_file_by_id(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugin_with_files: dict[str, Any],
) -> None:
    """Test that a plugin file can be deleted by referencing its id.

    Given an authenticated user and a registered plugin with plugin files, this 
    test validates the following sequence of actions:

    - The user deletes a plugin file by referencing its id.
    - The user attempts to retrieve information about the deleted plugin file.
    - The request fails with an appropriate error message and response code.
    """
    registered_plugin = registered_plugin_with_files["plugin"]
    plugin_file_to_delete = registered_plugin_with_files["plugin_file1"]

    delete_plugin_file_with_id(
        client, 
        plugin_id=registered_plugin["id"],
        plugin_file_id=plugin_file_to_delete["id"],
    )
    assert_plugin_file_is_not_found(
        client, 
        plugin_id=registered_plugin["id"],
        plugin_file_id=plugin_file_to_delete["id"],
    )


# -- Tests Plugin Tasks ----------------------------------------------------------------


@pytest.mark.v1_test
def test_register_plugin_task(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugin_with_files: dict[str, Any],
    registered_plugin_with_file_and_tasks: dict[str, Any],
) -> None:
    """Test that plugin tasks can be correctly registered to a plugin and retrieved using the API.

    Given an authenticated user, a registered plugin with files, and a registered plugin type parameter
    this test validates the following sequence of actions:

    - The user registers a plugin task named "my_plugin_task".
    - The response is valid matches the expected values given the registration request.
    - The user is able to retrieve information about the plugin using the plugin and plugin file IDs.
    """
    registered_plugin = registered_plugin_with_files["plugin"]
    registered_plugin_file = registered_plugin_with_files["plugin_file1"]
    registered_plugin_param_type = registered_plugin_with_file_and_tasks["plugin_parameter_type"]
    name = "my_plugin_task"
    input_params = [registered_plugin_param_type]
    output_params = [registered_plugin_param_type]
    task: dict[str, Any] = {
        "name": name,
        "input_params": input_params,
        "output_params": output_params,
    }
    plugin_file_response = actions.add_plugin_tasks_to_plugin_file(
        client,
        plugin_id=registered_plugin["id"],
        plugin_file_id=registered_plugin_file["id"],
        new_task=[task],
    ).get_json()
    plugin_task_expected_list = plugin_file_response["tasks"]

    assert_plugin_task_response_contents_matches_expectations(
        response=plugin_task_expected_list,
        expected_contents={
            "name": name,
            "input_params": input_params,
            "output_params": output_params,
        },
    )
    assert_retrieving_plugin_tasks_works(
        client,
        plugin_id=registered_plugin["id"],
        plugin_file_id=registered_plugin_file["id"],
        expected=plugin_task_expected_list,
    )


@pytest.mark.v1_test
def test_plugin_task_get_all(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugin_with_file_and_tasks: dict[str, Any],
) -> None:
    """Test that all plugin tasks can be retrieved.

    Given an authenticated user and a registered plugin with a plugin file and tasks, this 
    test validates the following sequence of actions:

    - A user registers three plugin tasks, "plugin_task1", "plugin_task2", "plugin_task3"
      to the plugin file.
    - The user is able to retrieve a list of all registered plugin tasks.
    - The returned list of plugin tasks matches the full list of registered plugin tasks.
    """
    registered_plugin = registered_plugin_with_file_and_tasks["plugin"]
    registered_plugin_file = registered_plugin_with_file_and_tasks["plugin_file"]
    plugin_task1_expected = registered_plugin_with_file_and_tasks["plugin_task1"]
    plugin_task2_expected = registered_plugin_with_file_and_tasks["plugin_task2"]
    plugin_task3_expected = registered_plugin_with_file_and_tasks["plugin_task3"]
    plugin_task_expected_list = [
        plugin_task1_expected, 
        plugin_task2_expected, 
        plugin_task3_expected,
    ]

    assert_retrieving_plugin_tasks_works(
        client,
        plugin_id=registered_plugin["id"],
        plugin_file_id=registered_plugin_file["id"],
        expected=plugin_task_expected_list,
    )


@pytest.mark.v1_test
def test_plugin_task_delete_all(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugin_with_file_and_tasks: dict[str, Any],
) -> None:
    """Test that all plugin tasks for a plugin file can be deleted.
    
    Given an authenticated user and a registered plugin with a plugin file and tasks, this 
    test validates the following sequence of actions:

    - The user deletes all plugin tasks by referencing the plugin and plugin file ids.
    - The user attempts to retrieve information about the deleted plugin tasks.
    - The returned list of plugin tasks is empty.
    """
    registered_plugin = registered_plugin_with_file_and_tasks["plugin"]
    registered_plugin_file = registered_plugin_with_file_and_tasks["plugin_file"]
    plugin_task_expected_list = []

    delete_all_plugin_tasks(
        client, 
        plugin_id=registered_plugin["id"],
        plugin_file_id=registered_plugin_file["id"],
    )
    assert_retrieving_plugin_tasks_works(
        client,
        plugin_id=registered_plugin["id"],
        plugin_file_id=registered_plugin_file["id"],
        expected=plugin_task_expected_list,
    )