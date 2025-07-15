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
from http import HTTPStatus
from typing import Any

import pytest

from dioptra.client.base import DioptraResponseProtocol
from dioptra.client.client import DioptraClient
from dioptra.restapi.routes import V1_PLUGIN_PARAMETER_TYPES_ROUTE, V1_ROOT

from ..lib import helpers, routines
from ..test_utils import assert_retrieving_resource_works, match_normalized_json

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
        "snapshotCreatedOn",
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
    assert isinstance(response["snapshotCreatedOn"], str)
    assert isinstance(response["lastModifiedOn"], str)
    assert isinstance(response["latestSnapshot"], bool)
    assert isinstance(response["hasDraft"], bool)

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
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    response = dioptra_client.plugins.get_by_id(plugin_id)
    assert response.status_code == HTTPStatus.OK and response.json() == expected


def assert_retrieving_plugins_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    expected: list[dict[str, Any]],
    sort_by: str | None = None,
    descending: bool | None = None,
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

    assert_retrieving_resource_works(
        dioptra_client=dioptra_client.plugins,
        expected=expected,
        group_id=group_id,
        sort_by=sort_by,
        descending=descending,
        search=search,
        paging_info=paging_info,
    )


def assert_registering_existing_plugin_name_fails(
    dioptra_client: DioptraClient[DioptraResponseProtocol], name: str, group_id: int
) -> None:
    """Assert that registering a plugin with an existing name fails.

    Args:
        client: The Flask test client.
        name: The name to assign to the new plugin.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = dioptra_client.plugins.create(
        group_id=group_id, name=name, description=""
    )
    assert response.status_code == HTTPStatus.CONFLICT


def assert_plugin_name_matches_expected_name(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    plugin_id: int,
    expected_name: str,
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
    response = dioptra_client.plugins.get_by_id(plugin_id)
    assert (
        response.status_code == HTTPStatus.OK
        and response.json()["name"] == expected_name
    )


def assert_plugin_is_not_found(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    plugin_id: int,
) -> None:
    """Assert that a plugin is not found.

    Args:
        client: The Flask test client.
        plugin_id: The id of the plugin to retrieve.

    Raises:
        AssertionError: If the response status code is not 404.
    """
    response = dioptra_client.plugins.get_by_id(plugin_id)
    assert response.status_code == HTTPStatus.NOT_FOUND


def assert_cannot_rename_plugin_with_existing_name(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    response = dioptra_client.plugins.modify_by_id(
        plugin_id=plugin_id, name=existing_name, description=existing_description
    )
    assert response.status_code == HTTPStatus.CONFLICT


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
        "snapshotCreatedOn",
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
    assert isinstance(response["snapshotCreatedOn"], str)
    assert isinstance(response["lastModifiedOn"], str)
    assert isinstance(response["latestSnapshot"], bool)
    assert isinstance(response["hasDraft"], bool)

    assert response["filename"] == expected_contents["filename"]
    assert response["description"] == expected_contents["description"]
    assert response["contents"] == expected_contents["contents"]

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

    # Validate the PluginTask structure
    for task in response["tasks"]["functions"]:
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

    assert response["tasks"] == expected_contents["tasks"]


def assert_retrieving_plugin_file_by_id_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    response = dioptra_client.plugins.files.get_by_id(
        plugin_id=plugin_id, plugin_file_id=plugin_file_id
    )
    assert response.status_code == HTTPStatus.OK and response.json() == expected


def assert_retrieving_plugin_files_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    expected: list[dict[str, Any]],
    plugin_id: int,
    sort_by: str | None = None,
    descending: bool | None = None,
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

    if sort_by is not None:
        query_string["sort_by"] = sort_by

    if descending is not None:
        query_string["descending"] = descending

    if paging_info is not None:
        query_string["index"] = paging_info["index"]
        query_string["page_length"] = paging_info["page_length"]

    response = dioptra_client.plugins.files.get(plugin_id=plugin_id, **query_string)
    # A sort order was not given in the request, so we must not assume a
    # particular order in the response.
    assert response.status_code == HTTPStatus.OK and match_normalized_json(
        response, expected
    )


def assert_registering_existing_plugin_filename_fails(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    response = dioptra_client.plugins.files.create(
        plugin_id=plugin_id,
        filename=existing_filename,
        contents=contents,
        function_tasks=[],
        description=description,
    )
    assert response.status_code == HTTPStatus.CONFLICT


def assert_plugin_filename_matches_expected_name(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    response = dioptra_client.plugins.files.get_by_id(
        plugin_id=plugin_id, plugin_file_id=plugin_file_id
    )
    assert (
        response.status_code == HTTPStatus.OK
        and response.json()["filename"] == expected_name
    )


def assert_cannot_rename_plugin_file_with_existing_name(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    response = dioptra_client.plugins.files.modify_by_id(
        plugin_id=plugin_id,
        plugin_file_id=plugin_file_id,
        filename=existing_name,
        contents=existing_contents,
        function_tasks=[],
        description=existing_description,
    )
    assert response.status_code == HTTPStatus.CONFLICT


def assert_plugin_file_is_not_found(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    response = dioptra_client.plugins.files.get_by_id(
        plugin_id=plugin_id, plugin_file_id=plugin_file_id
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


# -- Assertions Plugin Tasks -----------------------------------------------------------


def assert_plugin_task_response_contents_matches_expectations(
    response: list[dict[str, Any]], expected_contents: dict[str, Any]
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
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    plugin_response = dioptra_client.plugins.create(
        group_id=group_id, name=name, description=description
    )
    plugin_expected = plugin_response.json()
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
        dioptra_client, plugin_id=plugin_expected["id"], expected=plugin_expected
    )


def test_plugin_get_all(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    assert_retrieving_plugins_works(dioptra_client, expected=plugin_expected_list)


@pytest.mark.parametrize(
    "sort_by, descending , expected",
    [
        ("name", True, ["plugin2", "plugin3", "plugin1"]),
        ("name", False, ["plugin1", "plugin3", "plugin2"]),
        ("createdOn", True, ["plugin3", "plugin2", "plugin1"]),
        ("createdOn", False, ["plugin1", "plugin2", "plugin3"]),
    ],
)
def test_plugin_sort(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_plugins: dict[str, Any],
    sort_by: str,
    descending: bool,
    expected: list[str],
) -> None:
    """Test that plugins can be sorted by column.

    Given an authenticated user and registered plugins, this test validates the
    following sequence of actions:

    - A user registers three plugins, "plugin_one", "plugin_two", "plugin_three".
    - The user is able to retrieve a list of all registered plugins sorted by a column
      ascending/descending.
    - The returned list of plugins matches the order in the parametrize lists above.
    """

    expected_plugins = [registered_plugins[expected_name] for expected_name in expected]
    assert_retrieving_plugins_works(
        dioptra_client=dioptra_client,
        sort_by=sort_by,
        descending=descending,
        expected=expected_plugins,
    )


def test_plugin_search_query(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
        dioptra_client=dioptra_client,
        expected=plugin_expected_list,
        search="description:*plugin*",
    )


def test_plugin_group_query(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
        dioptra_client,
        expected=plugin_expected_list,
        group_id=auth_account["groups"][0]["id"],
    )


def test_cannot_register_existing_plugin_name(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
        dioptra_client,
        name=existing_plugin["name"],
        group_id=existing_plugin["group"]["id"],
    )


def test_rename_plugin(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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

    modified_plugin = dioptra_client.plugins.modify_by_id(
        plugin_id=plugin_to_rename["id"],
        name=updated_plugin_name,
        description=plugin_to_rename["description"],
    ).json()
    assert_plugin_name_matches_expected_name(
        dioptra_client,
        plugin_id=plugin_to_rename["id"],
        expected_name=updated_plugin_name,
    )

    plugin_expected_list = [
        modified_plugin,
        registered_plugins["plugin2"],
        registered_plugins["plugin3"],
    ]
    assert_retrieving_plugins_works(dioptra_client, expected=plugin_expected_list)

    modified_plugin = dioptra_client.plugins.modify_by_id(
        plugin_id=plugin_to_rename["id"],
        name=updated_plugin_name,
        description=plugin_to_rename["description"],
    ).json()
    assert_plugin_name_matches_expected_name(
        dioptra_client,
        plugin_id=plugin_to_rename["id"],
        expected_name=updated_plugin_name,
    )
    assert_cannot_rename_plugin_with_existing_name(
        dioptra_client,
        plugin_id=plugin_to_rename["id"],
        existing_name=existing_plugin["name"],
        existing_description=plugin_to_rename["description"],
    )


def test_delete_plugin_by_id(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    dioptra_client.plugins.delete_by_id(plugin_id=plugin_to_delete["id"])
    assert_plugin_is_not_found(dioptra_client, plugin_id=plugin_to_delete["id"])


# -- Tests Plugin Files ----------------------------------------------------------------


def test_register_plugin_file(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
        def hello_world(given_name: str, family_name: str) -> str:
            return f"Hello, {given_name} {family_name}!"
        """
    )
    user_id = auth_account["id"]
    string_parameter_type = registered_plugin_parameter_types["plugin_param_type3"]
    function_tasks = [
        {
            "name": "hello_world",
            "inputParams": [
                {"name": "given_name", "parameterType": string_parameter_type["id"]},
                {"name": "family_name", "parameterType": string_parameter_type["id"]},
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
    expected_function_tasks = [
        {
            "id": 1,  # can this be hardcoded?
            "name": "hello_world",
            "inputParams": [
                {
                    "name": "given_name",
                    "parameterType": {
                        "id": string_parameter_type["id"],
                        "group": string_parameter_type["group"],
                        "url": string_url,
                        "name": string_parameter_type["name"],
                    },
                    "required": True,
                },
                {
                    "name": "family_name",
                    "parameterType": {
                        "id": string_parameter_type["id"],
                        "group": string_parameter_type["group"],
                        "url": string_url,
                        "name": string_parameter_type["name"],
                    },
                    "required": True,
                },
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

    plugin_file_response = dioptra_client.plugins.files.create(
        plugin_id=registered_plugin["id"],
        filename=filename,
        description=description,
        contents=contents,
        function_tasks=function_tasks,
    )
    plugin_file_expected = plugin_file_response.json()

    assert_plugin_file_response_contents_matches_expectations(
        response=plugin_file_expected,
        expected_contents={
            "filename": filename,
            "description": description,
            "contents": contents,
            "user_id": user_id,
            "group_id": registered_plugin["group"]["id"],
            "tasks": {"functions": expected_function_tasks, "artifacts": []},
        },
    )
    assert_retrieving_plugin_file_by_id_works(
        dioptra_client,
        plugin_id=registered_plugin["id"],
        plugin_file_id=plugin_file_expected["id"],
        expected=plugin_file_expected,
    )


@pytest.mark.parametrize(
    "filename, expected_status_code",
    [
        # fmt: off
        # Valid paths
        (r"hello.py", HTTPStatus.OK),
        (r"hello_world.py", HTTPStatus.OK),
        (r"hello_world/main.py", HTTPStatus.OK),
        (r"package/sub_package/module.py", HTTPStatus.OK),
        (r"a/b/c/d/e/f/g/h/i/j/k/l/m/n/o/p.py", HTTPStatus.OK),  # Many nested directories # noqa: B950 # fmt: skip
        (r"_underscore_start.py", HTTPStatus.OK),
        (r"underscore_end_.py", HTTPStatus.OK),
        (r"_underscore_start_end_.py", HTTPStatus.OK),
        (r"__dunder_start.py", HTTPStatus.OK),
        (r"dunder_end__.py", HTTPStatus.OK),
        (r"__dunder_start_end__.py", HTTPStatus.OK),

        # Invalid paths
        (r"hello world.py", HTTPStatus.BAD_REQUEST),        # Space in filename
        (r"3ight/hello.py", HTTPStatus.BAD_REQUEST),        # Directory starting with a number # noqa: B950
        (r"hello_world//main.py", HTTPStatus.BAD_REQUEST),  # Double slash
        (r"module.py.txt", HTTPStatus.BAD_REQUEST),         # Wrong extension
        (r"/absolute/path.py", HTTPStatus.BAD_REQUEST),     # Absolute path
        (r".py", HTTPStatus.BAD_REQUEST),                   # Just the extension
        (r"hello.py/", HTTPStatus.BAD_REQUEST),             # Ends with a slash
        (r"/hello.py", HTTPStatus.BAD_REQUEST),             # Starts with a slash
        (r"hello..py", HTTPStatus.BAD_REQUEST),             # Double dot in extension
        (r"hello.py.py", HTTPStatus.BAD_REQUEST),           # Double .py extension
        (r"_/hello.py", HTTPStatus.BAD_REQUEST),            # Single underscore directory name # noqa: B950
        (r"hello/_.py", HTTPStatus.BAD_REQUEST),            # Single underscore filename
        (r"hello/_file.py", HTTPStatus.BAD_REQUEST),        # Underscore start in nested file # noqa: B950
        (r"HELLO.PY", HTTPStatus.BAD_REQUEST),              # Uppercase extension (assuming case-sensitive) # noqa: B950
        (r"hello.pY", HTTPStatus.BAD_REQUEST),              # Mixed case extension
        (r"hello/world/.py", HTTPStatus.BAD_REQUEST),       # Hidden file in nested directory # noqa: B950
        (r"hello/.world/file.py", HTTPStatus.BAD_REQUEST),  # Hidden directory
        (r" hello.py", HTTPStatus.BAD_REQUEST),             # Leading space
        (r"hello.py ", HTTPStatus.BAD_REQUEST),             # Trailing space
        (r"\thello.py", HTTPStatus.BAD_REQUEST),            # Tab character
        (r"hello\world.py", HTTPStatus.BAD_REQUEST),        # Backslash instead of forward slash # noqa: B950
        (r"hello:world.py", HTTPStatus.BAD_REQUEST),        # Invalid character (colon)
        (r"hello@world.py", HTTPStatus.BAD_REQUEST),        # Invalid character (at sign) # noqa: B950
        (r"hello/world.py/extra", HTTPStatus.BAD_REQUEST),  # Extra content after .py
        (r"", HTTPStatus.BAD_REQUEST),                      # Empty string
        (r"hello/", HTTPStatus.BAD_REQUEST),                # Directory without file
        (r"hello.py/world.py", HTTPStatus.BAD_REQUEST),     # .py in middle of path
        (r"1/2/3/4.py", HTTPStatus.BAD_REQUEST),            # All numeric directory names # noqa: B950
        (r"../sample.py", HTTPStatus.BAD_REQUEST),          # No relative paths
        (r"..sample.py", HTTPStatus.BAD_REQUEST),
        # No prefix with dots
        # fmt: on
    ],
)
def test_plugin_file_filename_regex(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_plugins: dict[str, Any],
    filename: str,
    expected_status_code: HTTPStatus,
) -> None:
    """Test that the regular expression for validating plugin file filenames is able to
    handle a variety of malformed inputs.

    Given an authenticated user and a registered plugin, this test validates the
    following sequence of actions:

    - The user registers a plugin file with either a valid or invalid filename.
    - The response status code returns 200 (OK) if the filename is valid or 400
      (BAD REQUEST) if the filename is invalid.
    """
    registered_plugin = registered_plugins["plugin1"]
    response = dioptra_client.plugins.files.create(
        plugin_id=registered_plugin["id"],
        filename=filename,
        contents="# Empty file",
        function_tasks=[],
    )
    assert response.status_code == expected_status_code


def test_plugin_file_get_all(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
        dioptra_client,
        plugin_id=registered_plugin["id"],
        expected=plugin_file_expected_list,
    )


@pytest.mark.parametrize(
    "sort_by, descending , expected",
    [
        ("filename", True, ["plugin_file2", "plugin_file3", "plugin_file1"]),
        ("filename", False, ["plugin_file1", "plugin_file3", "plugin_file2"]),
        ("createdOn", True, ["plugin_file3", "plugin_file2", "plugin_file1"]),
        ("createdOn", False, ["plugin_file1", "plugin_file2", "plugin_file3"]),
    ],
)
def test_plugin_file_sort(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_plugin_with_files: dict[str, Any],
    sort_by: str,
    descending: bool,
    expected: list[str],
) -> None:
    """Test that plugin files can be sorted by column.

    Given an authenticated user and registered plugin files, this test validates the
    following sequence of actions:

    - A user registers three plugin files:
      "plugin_file_one.py",
      "plugin_file_two.py",
      "plugin_file_three.py".
    - The user is able to retrieve a list of all registered plugins files sorted by a
      column ascending/descending.
    - The returned list of plugin files matches the order in the parametrize lists
      above.
    """

    expected_plugin_files = [
        registered_plugin_with_files[expected_name] for expected_name in expected
    ]
    assert_retrieving_plugin_files_works(
        dioptra_client,
        expected=expected_plugin_files,
        plugin_id=registered_plugin_with_files["plugin"]["id"],
        sort_by=sort_by,
        descending=descending,
    )


def test_plugin_file_delete_all(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    dioptra_client.plugins.files.delete_all(plugin_id=registered_plugin["id"])
    assert_retrieving_plugin_files_works(
        dioptra_client,
        plugin_id=registered_plugin["id"],
        expected=plugin_file_expected_list,
    )


def test_cannot_register_existing_plugin_filename(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
        dioptra_client,
        plugin_id=registered_plugin["id"],
        existing_filename=existing_plugin_file["filename"],
        contents=existing_plugin_file["contents"],
        description=existing_plugin_file["description"],
    )


def test_rename_plugin_file(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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

    dioptra_client.plugins.files.modify_by_id(
        plugin_id=registered_plugin["id"],
        plugin_file_id=plugin_file_to_rename["id"],
        filename=updated_plugin_filename,
        contents=plugin_file_to_rename["contents"],
        function_tasks=[],
        description=plugin_file_to_rename["description"],
    )
    assert_plugin_filename_matches_expected_name(
        dioptra_client,
        plugin_id=registered_plugin["id"],
        plugin_file_id=plugin_file_to_rename["id"],
        expected_name=updated_plugin_filename,
    )
    assert_cannot_rename_plugin_file_with_existing_name(
        dioptra_client,
        plugin_id=registered_plugin["id"],
        plugin_file_id=plugin_file_to_rename["id"],
        existing_name=existing_plugin_file["filename"],
        existing_contents=existing_plugin_file["contents"],
        existing_description=plugin_file_to_rename["description"],
    )


def test_delete_plugin_file_by_id(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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

    dioptra_client.plugins.files.delete_by_id(
        plugin_id=registered_plugin["id"],
        plugin_file_id=plugin_file_to_delete["id"],
    )
    assert_plugin_file_is_not_found(
        dioptra_client,
        plugin_id=registered_plugin["id"],
        plugin_file_id=plugin_file_to_delete["id"],
    )


# -- Tests Plugin Drafts ---------------------------------------------------------------


def test_manage_existing_plugin_draft(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    # Requests data
    plugin = registered_plugins["plugin1"]
    description = "description"
    draft = {"name": "draft", "description": description}
    draft_mod = {"name": "draft2", "description": description}

    # Expected responses
    draft_expected = {
        "user_id": auth_account["id"],
        "group_id": plugin["group"]["id"],
        "resource_id": plugin["id"],
        "resource_snapshot_id": plugin["snapshot"],
        "num_other_drafts": 0,
        "payload": draft,
    }
    draft_mod_expected = {
        "user_id": auth_account["id"],
        "group_id": plugin["group"]["id"],
        "resource_id": plugin["id"],
        "resource_snapshot_id": plugin["snapshot"],
        "num_other_drafts": 0,
        "payload": draft_mod,
    }

    # Run routine: existing resource drafts tests
    routines.run_existing_resource_drafts_tests(
        dioptra_client.plugins,
        dioptra_client.plugins.modify_resource_drafts,
        dioptra_client.workflows,
        plugin["id"],
        draft=draft,
        draft_mod=draft_mod,
        draft_expected=draft_expected,
        draft_mod_expected=draft_mod_expected,
    )


def test_manage_new_plugin_drafts(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    # Requests data
    group_id = auth_account["groups"][0]["id"]
    drafts: dict[str, Any] = {
        "draft1": {"name": "plugin1", "description": "new plugin"},
        "draft2": {"name": "plugin2", "description": None},
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

    # Run routine: new resource drafts tests
    routines.run_new_resource_drafts_tests(
        dioptra_client.plugins,
        dioptra_client.plugins.new_resource_drafts,
        dioptra_client.workflows,
        drafts=drafts,
        draft1_mod=draft1_mod,
        draft1_expected=draft1_expected,
        draft2_expected=draft2_expected,
        draft1_mod_expected=draft1_mod_expected,
        group_id=group_id,
    )


def test_manage_existing_plugin_file_draft(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    # Requests data
    plugin_id = registered_plugin_with_files["plugin"]["id"]
    plugin_file = registered_plugin_with_files["plugin_file1"]
    description = "hello world plugin"
    contents = textwrap.dedent(
        """from dioptra import pyplugs

        @pyplugs.register
        def hello_world(name: str) -> str:
            return f"Hello, {name}!"
        """
    )
    draft = {
        "filename": "main.py",
        "description": description,
        "contents": contents,
        "tasks": [],
    }
    draft_mod = {
        "filename": "hello_world.py",
        "description": description,
        "contents": contents,
        "tasks": [],
    }

    # Expected responses
    draft_expected = {
        "user_id": auth_account["id"],
        "group_id": plugin_file["group"]["id"],
        "resource_id": plugin_file["id"],
        "resource_snapshot_id": plugin_file["snapshot"],
        "num_other_drafts": 0,
        "payload": draft,
    }
    draft_mod_expected = {
        "user_id": auth_account["id"],
        "group_id": plugin_file["group"]["id"],
        "resource_id": plugin_file["id"],
        "resource_snapshot_id": plugin_file["snapshot"],
        "num_other_drafts": 0,
        "payload": draft_mod,
    }

    # Run routine: existing resource drafts tests
    routines.run_existing_resource_drafts_tests(
        dioptra_client.plugins.files,
        dioptra_client.plugins.files.modify_resource_drafts,
        dioptra_client.workflows,
        plugin_id,
        plugin_file["id"],
        draft=draft,
        draft_mod=draft_mod,
        draft_expected=draft_expected,
        draft_mod_expected=draft_mod_expected,
    )


def test_manage_new_plugin_file_drafts(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    # Requests data
    plugin_id = registered_plugins["plugin1"]["id"]
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
            "tasks": [],
        },
        "draft2": {
            "filename": "plugin_file2.py",
            "description": None,
            "contents": contents,
            "tasks": [],
        },
    }
    draft1_mod = {
        "filename": "draft_plugin.py",
        "description": "new description",
        "contents": contents,
        "tasks": [],
    }

    # Expected responses
    group_id = auth_account["groups"][0]["id"]
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
        dioptra_client.plugins.files,
        dioptra_client.plugins.files.new_resource_drafts,
        dioptra_client.workflows,
        plugin_id,
        drafts=drafts,
        draft1_mod=draft1_mod,
        draft1_expected=draft1_expected,
        draft2_expected=draft2_expected,
        draft1_mod_expected=draft1_mod_expected,
    )


def test_manage_plugin_snapshots(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_plugins: dict[str, Any],
) -> None:
    """Test that different snapshots of a plugin can be retrieved by the user.

    Given an authenticated user and registered plugins, this test validates the
    following sequence of actions:

    - The user modifies a plugin
    - The user retrieves information about the original snapshot of the plugin and gets
      the expected response
    - The user retrieves information about the new snapshot of the plugin and gets the
      expected response
    - The user retrieves a list of all snapshots of the plugin and gets the expected
      response
    """
    plugin_to_rename = registered_plugins["plugin1"]
    modified_plugin = dioptra_client.plugins.modify_by_id(
        plugin_id=plugin_to_rename["id"],
        name=plugin_to_rename["name"] + "modified",
        description=plugin_to_rename["description"],
    ).json()

    # Run routine: resource snapshots tests
    routines.run_resource_snapshots_tests(
        dioptra_client.plugins.snapshots,
        resource_to_rename=plugin_to_rename.copy(),
        modified_resource=modified_plugin.copy(),
        drop_additional_fields=["files"],
    )


def test_manage_plugin_file_snapshots(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    plugin_file_to_rename = registered_plugin_with_files["plugin_file1"]
    contents = textwrap.dedent(
        """from dioptra import pyplugs

        @pyplugs.register
        def hello_world(name: str) -> str:
            return f"Hello, {name}!"
        """
    )

    modified_plugin_file = dioptra_client.plugins.files.modify_by_id(
        plugin_id=plugin_id,
        plugin_file_id=plugin_file_to_rename["id"],
        filename="modified_" + plugin_file_to_rename["filename"],
        contents=contents,
        function_tasks=[],
        description=plugin_file_to_rename["description"],
    ).json()

    # Run routine: resource snapshots tests
    routines.run_resource_snapshots_tests(
        dioptra_client.plugins.files.snapshots,
        plugin_id,
        resource_to_rename=plugin_file_to_rename.copy(),
        modified_resource=modified_plugin_file.copy(),
        drop_additional_fields=["plugin"],
    )


def test_tag_plugin(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_plugins: dict[str, Any],
    registered_tags: dict[str, Any],
) -> None:
    """Test that tags can applied to plugins.

    Given an authenticated user and registered plugins, this test validates the
    following sequence of actions:

    """
    plugin = registered_plugins["plugin1"]
    tag_ids = [tag["id"] for tag in registered_tags.values()]

    # Run routine: resource tag tests
    routines.run_resource_tag_tests(
        dioptra_client.plugins.tags,
        plugin["id"],
        tag_ids=tag_ids,
    )


def test_tag_plugin_file(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    tag_ids = [tag["id"] for tag in registered_tags.values()]

    # Run routine: resource tag tests
    routines.run_resource_tag_tests(
        dioptra_client.plugins.files.tags,
        plugin_id,
        plugin_file["id"],
        tag_ids=tag_ids,
    )
