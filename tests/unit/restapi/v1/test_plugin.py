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

from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from werkzeug.test import TestResponse

from dioptra.restapi.routes import (
    V1_PLUGIN_FILES_ROUTE,
    V1_PLUGIN_PARAMETER_TYPES_ROUTE,
    V1_PLUGINS_ROUTE,
    V1_ROOT,
)

from ..lib import actions, asserts, helpers

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
    new_contents: str,
    new_description: str,
    new_tasks: list[dict[str, Any]] | None = None,
) -> TestResponse:
    """Rename a plugin file using the API.

    Args:
        client: The Flask test client.
        plugin_id: The id of the plugin to with plugin files.
        plugin_file_id: The id of the plugin file to rename.
        new_name: The new name to assign to the plugin file.
        new_description: The new description to assign to the plugin file.
        new_tasks: The new tasks to assign to the plugin file.

    Returns:
        The response from the API.
    """
    payload: dict[str, Any] = {
        "filename": new_name,
        "description": new_description,
        "contents": new_contents,
        "tasks": new_tasks or [],
    }

    return client.put(
        f"/{V1_ROOT}/{V1_PLUGINS_ROUTE}/{plugin_id}/files/{plugin_file_id}",
        json=payload,
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


def delete_all_plugin_files(client: FlaskClient, plugin_id: int) -> TestResponse:
    """Delete all plugin files for a plugin using the API.

    Args:
        client: The Flask test client.
        plugin_id: The id of the plugin with files to delete.

    Returns:
        The response from the API.
    """
    return client.delete(
        f"/{V1_ROOT}/{V1_PLUGINS_ROUTE}/{plugin_id}/files",
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
        "hasDraft",
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
    assert isinstance(response["hasDraft"], bool)

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
    response = actions.register_plugin(
        client, name=name, description="", group_id=group_id
    )
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
        "snapshot",
        "group",
        "user",
        "createdOn",
        "lastModifiedOn",
        "latestSnapshot",
        "hasDraft",
        "filename",
        "description",
        "contents",
        "tasks",
        "tags",
        "plugin",
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
    assert isinstance(response["hasDraft"], bool)

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
    assert response["group"]["id"] == expected_contents["group_id"]

    # Validate the PluginTask structure
    for task in response["tasks"]:
        assert isinstance(task["name"], str)

        # Validate PluginTaskParameter Structure for inputs and outputs
        for param in task["inputParams"] + task["outputParams"]:
            assert isinstance(param["name"], str)

            # Validate PluginParameterTypeRef structure
            assert isinstance(param["parameterType"]["id"], int)
            assert isinstance(param["parameterType"]["name"], str)
            assert isinstance(param["parameterType"]["url"], str)

            # Validate the GroupRef structure
            assert isinstance(param["parameterType"]["group"]["id"], int)
            assert isinstance(param["parameterType"]["group"]["name"], str)
            assert isinstance(param["parameterType"]["group"]["url"], str)


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
        f"/{V1_ROOT}/{V1_PLUGINS_ROUTE}/{plugin_id}/files/{plugin_file_id}",
        follow_redirects=True,
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


def assert_registering_existing_plugin_filename_fails(
    client: FlaskClient,
    plugin_id: int,
    existing_filename: str,
    contents: str,
    description: str,
) -> None:
    """Assert that registering a plugin file with an existing name fails.

    Args:
        client: The Flask test client.
        plugin_id: The ID of the plugin with files.
        existing_filename: An existing filename to assign to the new plugin file.
        contents: The string that represents the contents of the file as plain text.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = actions.register_plugin_file(
        client,
        plugin_id=plugin_id,
        filename=existing_filename,
        contents=contents,
        description=description,
    )
    assert response.status_code == 400


def assert_plugin_filename_matches_expected_name(
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
    assert (
        response.status_code == 200 and response.get_json()["filename"] == expected_name
    )


def assert_cannot_rename_plugin_file_with_existing_name(
    client: FlaskClient,
    plugin_id: int,
    plugin_file_id: int,
    existing_name: str,
    existing_contents: str,
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
        new_contents=existing_contents,
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


# -- Tests Plugins ---------------------------------------------------------------------


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

    Given an authenticated user and registered plugins, this test validates the
    following sequence of actions:

    - A user registers three plugins, "plugin1", "plugin2", "plugin3".
    - The user is able to retrieve a list of all registered plugins.
    - The returned list of plugins matches the full list of registered plugins.
    """
    plugin_expected_list = list(registered_plugins.values())
    assert_retrieving_plugins_works(client, expected=plugin_expected_list)


def test_plugin_search_query(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugins: dict[str, Any],
) -> None:
    """Test that plugins can be queried with a search term.

    Given an authenticated user and registered plugins, this test validates the
    following sequence of actions:

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

    Given an authenticated user and registered plugins, this test validates the
    following sequence of actions:

    - The user is able to retrieve a list of all registered plugins that are owned
      by the default group.
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

    Given an authenticated user and registered plugins, this test validates the
    following sequence of actions:

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

    Given an authenticated user and registered plugins, this test validates the
    following sequence of actions:

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
        new_description=plugin_to_rename["description"],
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

    Given an authenticated user and registered plugins, this test validates the
    following sequence of actions:

    - The user deletes a plugin by referencing its id.
    - The user attempts to retrieve information about the deleted plugin.
    - The request fails with an appropriate error message and response code.
    """
    plugin_to_delete = registered_plugins["plugin1"]
    delete_plugin_with_id(client, plugin_id=plugin_to_delete["id"])
    assert_plugin_is_not_found(client, plugin_id=plugin_to_delete["id"])


# -- Tests Plugin Files ----------------------------------------------------------------


def test_register_plugin_file(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugins: dict[str, Any],
    registered_plugin_parameter_types: dict[str, Any],
) -> None:
    """Test that plugin files can be correctly registered to a plugin and retrieved
    using the API.

    Given an authenticated user and a registered plugin, this test validates the
    following sequence of actions:

    - The user registers a plugin file named "my_plugin_file.py".
    - The response is valid matches the expected values given the registration request.
    - The user is able to retrieve information about the plugin using the plugin id.
    """
    registered_plugin = registered_plugins["plugin1"]
    filename = "my_plugin_file.py"
    description = "The first plugin file."
    contents = textwrap.dedent(
        """from dioptra import pyplugs

        @pyplugs.register
        def hello_world(name: str) -> str:
            return f"Hello, {name}!"
        """
    )
    user_id = auth_account["id"]
    string_parameter_type = registered_plugin_parameter_types["plugin_param_type3"]
    tasks = [
        {
            "name": "hello_world",
            "inputParams": [
                {"name": "name", "parameterType": string_parameter_type["id"]}
            ],
            "outputParams": [
                {
                    "name": "hello_world_message",
                    "parameterType": string_parameter_type["id"],
                }
            ],
        }
    ]
    string_url = (
        f"/{V1_ROOT}/{V1_PLUGIN_PARAMETER_TYPES_ROUTE}/{string_parameter_type['id']}"
    )
    expected_tasks = [
        {
            "name": "hello_world",
            "inputParams": [
                {
                    "name": "name",
                    "parameterType": {
                        "id": string_parameter_type["id"],
                        "group": string_parameter_type["group"],
                        "url": string_url,
                        "name": string_parameter_type["name"],
                    },
                }
            ],
            "outputParams": [
                {
                    "name": "hello_world_message",
                    "parameterType": {
                        "id": string_parameter_type["id"],
                        "group": string_parameter_type["group"],
                        "url": string_url,
                        "name": string_parameter_type["name"],
                    },
                }
            ],
        }
    ]

    plugin_file_response = actions.register_plugin_file(
        client,
        plugin_id=registered_plugin["id"],
        filename=filename,
        description=description,
        contents=contents,
        tasks=tasks,
    )
    plugin_file_expected = plugin_file_response.get_json()

    assert_plugin_file_response_contents_matches_expectations(
        response=plugin_file_expected,
        expected_contents={
            "filename": filename,
            "description": description,
            "contents": contents,
            "user_id": user_id,
            "group_id": registered_plugin["group"]["id"],
            "tasks": expected_tasks,
        },
    )
    assert_retrieving_plugin_file_by_id_works(
        client,
        plugin_id=registered_plugin["id"],
        plugin_file_id=plugin_file_expected["id"],
        expected=plugin_file_expected,
    )


def test_plugin_file_get_all(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugin_with_files: dict[str, Any],
) -> None:
    """Test that all plugin files can be retrieved.

    Given an authenticated user and a registered plugin with plugin files, this test
    validates the following sequence of actions:

    - A user registers three plugin files, "plugin_file1", "plugin_file2",
      "plugin_file3" to the plugin.
    - The user is able to retrieve a list of all registered plugin files.
    - The returned list of plugin files matches the full list of registered plugin
      files.
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

    plugin_file_expected_list: list[dict[str, Any]] = []

    delete_all_plugin_files(client, plugin_id=registered_plugin["id"])

    assert_retrieving_plugin_files_works(
        client,
        plugin_id=registered_plugin["id"],
        expected=plugin_file_expected_list,
    )


def test_cannot_register_existing_plugin_filename(
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

    assert_registering_existing_plugin_filename_fails(
        client,
        plugin_id=registered_plugin["id"],
        existing_filename=existing_plugin_file["filename"],
        contents=existing_plugin_file["contents"],
        description=existing_plugin_file["description"],
    )


def test_rename_plugin_file(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugin_with_files: dict[str, Any],
) -> None:
    """Test that a plugin file can be renamed.

    Given an authenticated user and a registered plugin with plugin files, this test
    validates the following sequence of actions:

    - The user issues a request to change the name of a plugin file.
    - The user retrieves information about the same plugin file and it reflects the name
      change.
    - The user issues a request to change the name of a plugin file to an existing
      plugin file's name.
    - The request fails with an appropriate error message and response code.
    """
    registered_plugin = registered_plugin_with_files["plugin"]
    plugin_file_to_rename = registered_plugin_with_files["plugin_file1"]
    existing_plugin_file = registered_plugin_with_files["plugin_file2"]
    updated_plugin_filename = "new_name.py"

    modify_plugin_file(
        client,
        plugin_id=registered_plugin["id"],
        plugin_file_id=plugin_file_to_rename["id"],
        new_name=updated_plugin_filename,
        new_contents=plugin_file_to_rename["contents"],
        new_description=plugin_file_to_rename["description"],
    )
    assert_plugin_filename_matches_expected_name(
        client,
        plugin_id=registered_plugin["id"],
        plugin_file_id=plugin_file_to_rename["id"],
        expected_name=updated_plugin_filename,
    )
    assert_cannot_rename_plugin_file_with_existing_name(
        client,
        plugin_id=registered_plugin["id"],
        plugin_file_id=plugin_file_to_rename["id"],
        existing_name=existing_plugin_file["filename"],
        existing_contents=existing_plugin_file["contents"],
        existing_description=plugin_file_to_rename["description"],
    )


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


# -- Tests Plugin Drafts ---------------------------------------------------------------


def test_manage_existing_plugin_draft(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugins: dict[str, Any],
) -> None:
    """Test that a draft of an existing plugin can be created and managed by the user

    Given an authenticated user and registered plugins, this test validates the
    following sequence of actions:

    - The user creates a draft of an existing plugin
    - The user retrieves information about the draft and gets the expected response
    - The user attempts to create another draft of the same existing plugin
    - The request fails with an appropriate error message and response code.
    - The user modifies the name of the plugin in the draft
    - The user retrieves information about the draft and gets the expected response
    - The user deletes the draft
    - The user attempts to retrieve information about the deleted draft.
    - The request fails with an appropriate error message and response code.
    """
    plugin = registered_plugins["plugin1"]
    name = "draft"
    new_name = "draft2"
    description = "description"

    # test creation
    payload = {"name": name, "description": description}
    expected = {
        "user_id": auth_account["id"],
        "group_id": plugin["group"]["id"],
        "resource_id": plugin["id"],
        "resource_snapshot_id": plugin["snapshot"],
        "num_other_drafts": 0,
        "payload": payload,
    }
    response = actions.create_existing_resource_draft(
        client,
        resource_route=V1_PLUGINS_ROUTE,
        resource_id=plugin["id"],
        payload=payload,
    ).get_json()
    asserts.assert_draft_response_contents_matches_expectations(response, expected)
    asserts.assert_retrieving_draft_by_resource_id_works(
        client,
        resource_route=V1_PLUGINS_ROUTE,
        resource_id=plugin["id"],
        expected=response,
    )
    asserts.assert_creating_another_existing_draft_fails(
        client, resource_route=V1_PLUGINS_ROUTE, resource_id=plugin["id"]
    )

    # test modification
    payload = {"name": new_name, "description": description}
    expected = {
        "user_id": auth_account["id"],
        "group_id": plugin["group"]["id"],
        "resource_id": plugin["id"],
        "resource_snapshot_id": plugin["snapshot"],
        "num_other_drafts": 0,
        "payload": payload,
    }
    response = actions.modify_existing_resource_draft(
        client,
        resource_route=V1_PLUGINS_ROUTE,
        resource_id=plugin["id"],
        payload=payload,
    ).get_json()
    asserts.assert_draft_response_contents_matches_expectations(response, expected)

    # test deletion
    actions.delete_existing_resource_draft(
        client, resource_route=V1_PLUGINS_ROUTE, resource_id=plugin["id"]
    )
    asserts.assert_existing_draft_is_not_found(
        client, resource_route=V1_PLUGINS_ROUTE, resource_id=plugin["id"]
    )


def test_manage_new_plugin_drafts(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
) -> None:
    """Test that drafts of plugin can be created and managed by the user

    Given an authenticated user, this test validates the following sequence of actions:

    - The user creates two plugin drafts
    - The user retrieves information about the drafts and gets the expected response
    - The user modifies the description of the plugin in the first draft
    - The user retrieves information about the draft and gets the expected response
    - The user deletes the first draft
    - The user attempts to retrieve information about the deleted draft.
    - The request fails with an appropriate error message and response code.
    """
    group_id = auth_account["groups"][0]["id"]
    drafts: dict[str, Any] = {
        "draft1": {"name": "plugin1", "description": "new plugin"},
        "draft2": {"name": "plugin2", "description": None},
    }

    # test creation
    draft1_expected = {
        "user_id": auth_account["id"],
        "group_id": group_id,
        "payload": drafts["draft1"],
    }
    draft1_response = actions.create_new_resource_draft(
        client,
        resource_route=V1_PLUGINS_ROUTE,
        group_id=group_id,
        payload=drafts["draft1"],
    ).get_json()
    asserts.assert_draft_response_contents_matches_expectations(
        draft1_response, draft1_expected
    )
    asserts.assert_retrieving_draft_by_id_works(
        client,
        resource_route=V1_PLUGINS_ROUTE,
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
        resource_route=V1_PLUGINS_ROUTE,
        group_id=group_id,
        payload=drafts["draft2"],
    ).get_json()
    asserts.assert_draft_response_contents_matches_expectations(
        draft2_response, draft2_expected
    )
    asserts.assert_retrieving_draft_by_id_works(
        client,
        resource_route=V1_PLUGINS_ROUTE,
        draft_id=draft2_response["id"],
        expected=draft2_response,
    )
    asserts.assert_retrieving_drafts_works(
        client,
        resource_route=V1_PLUGINS_ROUTE,
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
        resource_route=V1_PLUGINS_ROUTE,
        draft_id=draft1_response["id"],
        payload=draft1_mod,
    ).get_json()
    asserts.assert_draft_response_contents_matches_expectations(
        response, draft1_mod_expected
    )

    # test deletion
    actions.delete_new_resource_draft(
        client, resource_route=V1_PLUGINS_ROUTE, draft_id=draft1_response["id"]
    )
    asserts.assert_new_draft_is_not_found(
        client, resource_route=V1_PLUGINS_ROUTE, draft_id=draft1_response["id"]
    )


def test_manage_existing_plugin_file_draft(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugin_with_files: dict[str, Any],
) -> None:
    """Test that a draft of an existing plugin file can be created and managed by the
    user

    Given an authenticated user and registered plugin files, this test validates the
    following sequence of actions:

    - The user creates a draft of an existing plugin file
    - The user retrieves information about the draft and gets the expected response
    - The user attempts to create another draft of the same existing plugin file
    - The request fails with an appropriate error message and response code.
    - The user modifies the name of the plugin file in the draft
    - The user retrieves information about the draft and gets the expected response
    - The user deletes the draft
    - The user attempts to retrieve information about the deleted draft.
    - The request fails with an appropriate error message and response code.
    """
    plugin_id = registered_plugin_with_files["plugin"]["id"]
    resource_route = f"{V1_PLUGINS_ROUTE}/{plugin_id}/{V1_PLUGIN_FILES_ROUTE}"
    plugin_file = registered_plugin_with_files["plugin_file1"]
    filename = "main.py"
    new_filename = "hello_world.py"
    description = "hello world plugin"
    contents = textwrap.dedent(
        """from dioptra import pyplugs

        @pyplugs.register
        def hello_world(name: str) -> str:
            return f"Hello, {name}!"
        """
    )

    # test creation
    payload = {"filename": filename, "description": description, "contents": contents}
    expected = {
        "user_id": auth_account["id"],
        "group_id": plugin_file["group"]["id"],
        "resource_id": plugin_file["id"],
        "resource_snapshot_id": plugin_file["snapshot"],
        "num_other_drafts": 0,
        "payload": payload,
    }
    response = actions.create_existing_resource_draft(
        client,
        resource_route=resource_route,
        resource_id=plugin_file["id"],
        payload=payload,
    ).get_json()
    asserts.assert_draft_response_contents_matches_expectations(response, expected)
    asserts.assert_retrieving_draft_by_resource_id_works(
        client,
        resource_route=resource_route,
        resource_id=plugin_file["id"],
        expected=response,
    )
    asserts.assert_creating_another_existing_draft_fails(
        client, resource_route=resource_route, resource_id=plugin_file["id"]
    )

    # test modification
    payload = {
        "filename": new_filename,
        "description": description,
        "contents": contents,
    }
    expected = {
        "user_id": auth_account["id"],
        "group_id": plugin_file["group"]["id"],
        "resource_id": plugin_file["id"],
        "resource_snapshot_id": plugin_file["snapshot"],
        "num_other_drafts": 0,
        "payload": payload,
    }
    response = actions.modify_existing_resource_draft(
        client,
        resource_route=resource_route,
        resource_id=plugin_file["id"],
        payload=payload,
    ).get_json()
    asserts.assert_draft_response_contents_matches_expectations(response, expected)

    # test deletion
    actions.delete_existing_resource_draft(
        client, resource_route=resource_route, resource_id=plugin_file["id"]
    )
    asserts.assert_existing_draft_is_not_found(
        client, resource_route=resource_route, resource_id=plugin_file["id"]
    )


def test_manage_new_plugin_file_drafts(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugins: dict[str, Any],
) -> None:
    """Test that drafts of plugin_file can be created and managed by the user

    Given an authenticated user, this test validates the following sequence of actions:

    - The user creates two plugin_file drafts
    - The user retrieves information about the drafts and gets the expected response
    - The user modifies the description of the plugin_file in the first draft
    - The user retrieves information about the draft and gets the expected response
    - The user deletes the first draft
    - The user attempts to retrieve information about the deleted draft.
    - The request fails with an appropriate error message and response code.
    """
    plugin_id = registered_plugins["plugin1"]["id"]
    resource_route = f"{V1_PLUGINS_ROUTE}/{plugin_id}/{V1_PLUGIN_FILES_ROUTE}"

    group_id = auth_account["groups"][0]["id"]
    contents = textwrap.dedent(
        """from dioptra import pyplugs

        @pyplugs.register
        def hello_world(name: str) -> str:
            return f"Hello, {name}!"
        """
    )
    drafts: dict[str, Any] = {
        "draft1": {
            "filename": "plugin_file1.py",
            "description": "new plugin_file",
            "contents": contents,
        },
        "draft2": {
            "filename": "plugin_file2.py",
            "description": None,
            "contents": contents,
        },
    }

    # test creation
    draft1_expected = {
        "user_id": auth_account["id"],
        "group_id": group_id,
        "payload": drafts["draft1"],
    }
    draft1_response = actions.create_new_resource_draft(
        client,
        resource_route=resource_route,
        group_id=None,
        payload=drafts["draft1"],
    ).get_json()
    asserts.assert_draft_response_contents_matches_expectations(
        draft1_response, draft1_expected
    )
    asserts.assert_retrieving_draft_by_id_works(
        client,
        resource_route=resource_route,
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
        resource_route=resource_route,
        group_id=None,
        payload=drafts["draft2"],
    ).get_json()
    asserts.assert_draft_response_contents_matches_expectations(
        draft2_response, draft2_expected
    )
    asserts.assert_retrieving_draft_by_id_works(
        client,
        resource_route=resource_route,
        draft_id=draft2_response["id"],
        expected=draft2_response,
    )
    asserts.assert_retrieving_drafts_works(
        client,
        resource_route=resource_route,
        expected=[draft1_response, draft2_response],
    )

    # test modification
    draft1_mod = {
        "filename": "draft_plugin.py",
        "description": "new description",
        "contents": contents,
    }
    draft1_mod_expected = {
        "user_id": auth_account["id"],
        "group_id": group_id,
        "payload": draft1_mod,
    }
    response = actions.modify_new_resource_draft(
        client,
        resource_route=resource_route,
        draft_id=draft1_response["id"],
        payload=draft1_mod,
    ).get_json()
    asserts.assert_draft_response_contents_matches_expectations(
        response, draft1_mod_expected
    )

    # test deletion
    actions.delete_new_resource_draft(
        client, resource_route=resource_route, draft_id=draft1_response["id"]
    )
    asserts.assert_new_draft_is_not_found(
        client, resource_route=resource_route, draft_id=draft1_response["id"]
    )


def test_manage_plugin_snapshots(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugins: dict[str, Any],
) -> None:
    """Test that different snapshots of a plugin can be retrieved by the user.

    Given an authenticated user and registered plugins, this test validates the following
    sequence of actions:

    - The user modifies a plugin
    - The user retrieves information about the original snapshot of the plugin and gets
      the expected response
    - The user retrieves information about the new snapshot of the plugin and gets the
      expected response
    - The user retrieves a list of all snapshots of the plugin and gets the expected
      response
    """
    plugin_to_rename = registered_plugins["plugin1"]
    modified_plugin = modify_plugin(
        client,
        plugin_id=plugin_to_rename["id"],
        new_name=plugin_to_rename["name"] + "modified",
        new_description=plugin_to_rename["description"],
    ).get_json()
    modified_plugin.pop("hasDraft")
    modified_plugin.pop("files")
    plugin_to_rename.pop("hasDraft")
    plugin_to_rename.pop("files")
    plugin_to_rename["latestSnapshot"] = False
    plugin_to_rename["lastModifiedOn"] = modified_plugin["lastModifiedOn"]
    asserts.assert_retrieving_snapshot_by_id_works(
        client,
        resource_route=V1_PLUGINS_ROUTE,
        resource_id=plugin_to_rename["id"],
        snapshot_id=plugin_to_rename["snapshot"],
        expected=plugin_to_rename,
    )
    asserts.assert_retrieving_snapshot_by_id_works(
        client,
        resource_route=V1_PLUGINS_ROUTE,
        resource_id=modified_plugin["id"],
        snapshot_id=modified_plugin["snapshot"],
        expected=modified_plugin,
    )
    expected_snapshots = [plugin_to_rename, modified_plugin]
    asserts.assert_retrieving_snapshots_works(
        client,
        resource_route=V1_PLUGINS_ROUTE,
        resource_id=plugin_to_rename["id"],
        expected=expected_snapshots,
    )


def test_manage_plugin_file_snapshots(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugin_with_files: dict[str, Any],
) -> None:
    """Test that different snapshots of a plugin file can be retrieved by the user.

    Given an authenticated user and registered plugin with files, this test validates
    the following sequence of actions:

    - The user modifies a plugin file
    - The user retrieves information about the original snapshot of the plugin file and
      gets the expected response
    - The user retrieves information about the new snapshot of the plugin file and gets
       the expected response
    - The user retrieves a list of all snapshots of the plugin file and gets the
      expected response
    """
    plugin_id = registered_plugin_with_files["plugin"]["id"]
    resource_route = f"{V1_PLUGINS_ROUTE}/{plugin_id}/{V1_PLUGIN_FILES_ROUTE}"
    plugin_file_to_rename = registered_plugin_with_files["plugin_file1"]
    contents = textwrap.dedent(
        """from dioptra import pyplugs

        @pyplugs.register
        def hello_world(name: str) -> str:
            return f"Hello, {name}!"
        """
    )

    modified_plugin_file = modify_plugin_file(
        client,
        plugin_id=plugin_id,
        plugin_file_id=plugin_file_to_rename["id"],
        new_name="modified_" + plugin_file_to_rename["filename"],
        new_contents=contents,
        new_description=plugin_file_to_rename["description"],
    ).get_json()
    modified_plugin_file.pop("hasDraft")
    modified_plugin_file.pop("plugin")
    plugin_file_to_rename.pop("hasDraft")
    plugin_file_to_rename.pop("plugin")
    plugin_file_to_rename["latestSnapshot"] = False
    plugin_file_to_rename["lastModifiedOn"] = modified_plugin_file["lastModifiedOn"]
    asserts.assert_retrieving_snapshot_by_id_works(
        client,
        resource_route=resource_route,
        resource_id=plugin_file_to_rename["id"],
        snapshot_id=plugin_file_to_rename["snapshot"],
        expected=plugin_file_to_rename,
    )
    asserts.assert_retrieving_snapshot_by_id_works(
        client,
        resource_route=resource_route,
        resource_id=modified_plugin_file["id"],
        snapshot_id=modified_plugin_file["snapshot"],
        expected=modified_plugin_file,
    )
    expected_snapshots = [plugin_file_to_rename, modified_plugin_file]
    asserts.assert_retrieving_snapshots_works(
        client,
        resource_route=resource_route,
        resource_id=plugin_file_to_rename["id"],
        expected=expected_snapshots,
    )


def test_tag_plugin(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugins: dict[str, Any],
    registered_tags: dict[str, Any],
) -> None:
    """Test that tags can applied to plugins.

    Given an authenticated user and registered plugins, this test validates the
    following sequence of actions:

    """
    plugin = registered_plugins["plugin1"]
    tags = [tag["id"] for tag in registered_tags.values()]

    # test append
    response = actions.append_tags(
        client,
        resource_route=V1_PLUGINS_ROUTE,
        resource_id=plugin["id"],
        tag_ids=[tags[0], tags[1]],
    )
    asserts.assert_tags_response_contents_matches_expectations(
        response.get_json(), [tags[0], tags[1]]
    )
    response = actions.append_tags(
        client,
        resource_route=V1_PLUGINS_ROUTE,
        resource_id=plugin["id"],
        tag_ids=[tags[1], tags[2]],
    )
    asserts.assert_tags_response_contents_matches_expectations(
        response.get_json(), [tags[0], tags[1], tags[2]]
    )

    # test remove
    actions.remove_tag(
        client,
        resource_route=V1_PLUGINS_ROUTE,
        resource_id=plugin["id"],
        tag_id=tags[1],
    )
    response = actions.get_tags(
        client, resource_route=V1_PLUGINS_ROUTE, resource_id=plugin["id"]
    )
    asserts.assert_tags_response_contents_matches_expectations(
        response.get_json(), [tags[0], tags[2]]
    )

    # test modify
    response = actions.modify_tags(
        client,
        resource_route=V1_PLUGINS_ROUTE,
        resource_id=plugin["id"],
        tag_ids=[tags[1], tags[2]],
    )
    asserts.assert_tags_response_contents_matches_expectations(
        response.get_json(), [tags[1], tags[2]]
    )

    # test delete
    response = actions.remove_tags(
        client, resource_route=V1_PLUGINS_ROUTE, resource_id=plugin["id"]
    )
    response = actions.get_tags(
        client, resource_route=V1_PLUGINS_ROUTE, resource_id=plugin["id"]
    )


def test_tag_plugin_file(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_plugin_with_files: dict[str, Any],
    registered_tags: dict[str, Any],
) -> None:
    """Test that tags can applied to plugin files.

    Given an authenticated user and registered plugin files, this test validates the
    following sequence of actions:

    """
    plugin_id = registered_plugin_with_files["plugin"]["id"]
    plugin_file = registered_plugin_with_files["plugin_file1"]
    tags = [tag["id"] for tag in registered_tags.values()]
    resource_route = f"{V1_PLUGINS_ROUTE}/{plugin_id}/{V1_PLUGIN_FILES_ROUTE}"

    # test append
    response = actions.append_tags(
        client,
        resource_route=resource_route,
        resource_id=plugin_file["id"],
        tag_ids=[tags[0], tags[1]],
    )
    asserts.assert_tags_response_contents_matches_expectations(
        response.get_json(), [tags[0], tags[1]]
    )
    response = actions.append_tags(
        client,
        resource_route=resource_route,
        resource_id=plugin_file["id"],
        tag_ids=[tags[1], tags[2]],
    )
    asserts.assert_tags_response_contents_matches_expectations(
        response.get_json(), [tags[0], tags[1], tags[2]]
    )

    # test remove
    actions.remove_tag(
        client,
        resource_route=resource_route,
        resource_id=plugin_file["id"],
        tag_id=tags[1],
    )
    response = actions.get_tags(
        client, resource_route=resource_route, resource_id=plugin_file["id"]
    )
    asserts.assert_tags_response_contents_matches_expectations(
        response.get_json(), [tags[0], tags[2]]
    )

    # test modify
    response = actions.modify_tags(
        client,
        resource_route=resource_route,
        resource_id=plugin_file["id"],
        tag_ids=[tags[1], tags[2]],
    )
    asserts.assert_tags_response_contents_matches_expectations(
        response.get_json(), [tags[1], tags[2]]
    )

    # test delete
    response = actions.remove_tags(
        client, resource_route=resource_route, resource_id=plugin_file["id"]
    )
    response = actions.get_tags(
        client, resource_route=resource_route, resource_id=plugin_file["id"]
    )
