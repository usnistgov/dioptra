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
"""Test suite for entrypoint validation."""

import textwrap
from http import HTTPStatus
from typing import Any

from flask_sqlalchemy import SQLAlchemy

from dioptra.client.base import DioptraResponseProtocol
from dioptra.client.client import DioptraClient

# -- Assertions ------------------------------------------------------------------------


def assert_entrypoint_inputs_are_valid(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    group_id: int,
    task_graph: str,
    plugin_snapshots: list[int],
    entrypoint_parameters: list[dict[str, Any]],
) -> None:
    """Asserts that the entrypoint workflow yaml is valid.

    Args:
        dioptra_client: The Dioptra client.
        group_id: The ID of the group validating the entrypoint resource.
        task_graph: The proposed task graph for the entrypoint resource.
        plugin_snapshots: A list of identifiers for the plugin snapshots that will be
            attached to the Entrypoint resource.
        entrypoint_parameters: The proposed list of parameters for the entrypoint
            resource.

    Raises:
        AssertionError: If the entrypoint workflow yaml is invalid.
    """
    response = dioptra_client.workflows.validate_entrypoint(
        group_id=group_id,
        task_graph=task_graph,
        plugin_snapshots=plugin_snapshots,
        entrypoint_parameters=entrypoint_parameters,
    )
    assert (
        response.status_code == HTTPStatus.OK
        and response.json()["schemaValid"]
        and not response.json()["schemaIssues"]
    )


def assert_entrypoint_inputs_are_invalid(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    group_id: int,
    task_graph: str,
    plugin_snapshots: list[int],
    entrypoint_parameters: list[dict[str, Any]],
) -> None:
    """Asserts that the entrypoint workflow yaml is invalid.

    Args:
        dioptra_client: The Dioptra client.
        group_id: The ID of the group validating the entrypoint resource.
        task_graph: The proposed task graph for the entrypoint resource.
        plugin_snapshots: A list of identifiers for the plugin snapshots that will be
            attached to the Entrypoint resource.
        entrypoint_parameters: The proposed list of parameters for the entrypoint
            resource.

    Raises:
        AssertionError: If the entrypoint workflow yaml is valid.
    """
    response = dioptra_client.workflows.validate_entrypoint(
        group_id=group_id,
        task_graph=task_graph,
        plugin_snapshots=plugin_snapshots,
        entrypoint_parameters=entrypoint_parameters,
    )
    assert (
        response.status_code == HTTPStatus.OK
        and not response.json()["schemaValid"]
        and response.json()["schemaIssues"]
    )


def assert_multiple_snapshots_for_plugin_raise_error(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    group_id: int,
    task_graph: str,
    plugin_snapshots: list[int],
    entrypoint_parameters: list[dict[str, Any]],
) -> None:
    """Asserts that passing multiple snapshots for the same plugin raises an error.

    Args:
        dioptra_client: The Dioptra client.
        group_id: The ID of the group validating the entrypoint resource.
        task_graph: The proposed task graph for the entrypoint resource.
        plugin_snapshots: A list of identifiers for the plugin snapshots that will be
            attached to the Entrypoint resource.
        entrypoint_parameters: The proposed list of parameters for the entrypoint
            resource.

    Raises:
        AssertionError: If the client does not return a 400 error.
    """
    response = dioptra_client.workflows.validate_entrypoint(
        group_id=group_id,
        task_graph=task_graph,
        plugin_snapshots=plugin_snapshots,
        entrypoint_parameters=entrypoint_parameters,
    )
    assert (
        response.status_code == HTTPStatus.BAD_REQUEST
        and "Only one snapshot ID per resource ID is allowed."
        in response.json()["message"]
    )


# -- Tests -----------------------------------------------------------------------------


def test_validate_entrypoint_workflow(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_plugin_parameter_types: dict[str, Any],
) -> None:
    """Test that correct entrypoint inputs pass validation.

    Given an authenticated user, this test validates the following sequence of actions:

    - A user creates the plugin "hello_world".
    - A user adds a plugin file with a single task "hello_world".
    - The user correctly sets up a proposed entrypoint input consisting of a task graph
      and global parameters.
    - The entrypoint input validates successfully.
    """
    # Create a plugin
    registered_plugin = dioptra_client.plugins.create(
        group_id=auth_account["default_group_id"],
        name="hello_world",
        description="The hello world plugin.",
    ).json()

    # Add a plugin file with a single task
    filename = "tasks.py"
    description = "The task plugin file for hello world."
    contents = textwrap.dedent(
        """"from dioptra import pyplugs

        @pyplugs.register
        def hello_world(name: str) -> str:
            return f'Hello, {name}!'"
        """
    )
    string_parameter_type = registered_plugin_parameter_types["string"]
    tasks = [
        {
            "name": "hello_world",
            "inputParams": [
                {
                    "name": "name",
                    "parameterType": string_parameter_type["id"],
                    "required": True,
                },
            ],
            "outputParams": [
                {
                    "name": "greeting",
                    "parameterType": string_parameter_type["id"],
                },
            ],
        },
    ]
    dioptra_client.plugins.files.create(
        plugin_id=registered_plugin["id"],
        filename=filename,
        description=description,
        contents=contents,
        function_tasks=tasks,
        artifact_tasks=None,
    )

    # Retrieve the latest plugin snapshot identifier (adding the plugin file creates a
    # new snapshot)
    plugin_snapshot_id = dioptra_client.plugins.get_by_id(
        registered_plugin["id"]
    ).json()["snapshot"]

    # Set up the entrypoint inputs
    task_graph = textwrap.dedent(
        """# my entrypoint graph
        hello_step:
          hello_world:
            name: $name
        """
    )
    plugin_snapshots = [plugin_snapshot_id]
    parameters = [
        {
            "name": "name",
            "defaultValue": "User",
            "parameterType": "string",
        },
    ]
    assert_entrypoint_inputs_are_valid(
        dioptra_client,
        group_id=auth_account["default_group_id"],
        task_graph=task_graph,
        plugin_snapshots=plugin_snapshots,
        entrypoint_parameters=parameters,
    )


def test_validate_entrypoint_workflow_with_error(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_plugin_parameter_types: dict[str, Any],
) -> None:
    """Test that an incorrect entrypoint input fails validation.

    Given an authenticated user, this test validates the following sequence of actions:

    - A user creates the plugin "hello_world".
    - A user adds a plugin file with a single task "hello_world".
    - The user incorrectly sets up a proposed entrypoint input consisting of a task
      graph and global parameters. The task graph misspells the task "hello_world" as
      "hello_wrld".
    - The entrypoint input fails validation.
    """
    # Create a plugin
    registered_plugin = dioptra_client.plugins.create(
        group_id=auth_account["default_group_id"],
        name="hello_world",
        description="The hello world plugin.",
    ).json()

    # Add a plugin file with a single task
    filename = "tasks.py"
    description = "The task plugin file for hello world."
    contents = textwrap.dedent(
        """"from dioptra import pyplugs

        @pyplugs.register
        def hello_world(name: str) -> str:
            return f'Hello, {name}!'"
        """
    )
    string_parameter_type = registered_plugin_parameter_types["string"]
    tasks = [
        {
            "name": "hello_world",
            "inputParams": [
                {
                    "name": "name",
                    "parameterType": string_parameter_type["id"],
                    "required": True,
                },
            ],
            "outputParams": [
                {
                    "name": "greeting",
                    "parameterType": string_parameter_type["id"],
                },
            ],
        },
    ]
    dioptra_client.plugins.files.create(
        plugin_id=registered_plugin["id"],
        filename=filename,
        description=description,
        contents=contents,
        function_tasks=tasks,
        artifact_tasks=None,
    )

    # Retrieve the latest plugin snapshot identifier (adding the plugin file creates a
    # new snapshot)
    plugin_snapshot_id = dioptra_client.plugins.get_by_id(
        registered_plugin["id"]
    ).json()["snapshot"]

    # Set up the entrypoint inputs
    #
    # NOTE: The task graph misspells the task "hello_world" as "hello_wrld".
    task_graph = textwrap.dedent(
        """# my entrypoint graph
        hello_step:
          hello_wrld:
            name: $name
        """
    )
    plugin_snapshots = [plugin_snapshot_id]
    parameters = [
        {
            "name": "name",
            "defaultValue": "User",
            "parameterType": "string",
        },
    ]
    assert_entrypoint_inputs_are_invalid(
        dioptra_client,
        group_id=auth_account["default_group_id"],
        task_graph=task_graph,
        plugin_snapshots=plugin_snapshots,
        entrypoint_parameters=parameters,
    )


def test_validation_rejects_multi_snapshots_for_same_plugin_resource(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_plugin_parameter_types: dict[str, Any],
) -> None:
    """Test that passing multiple snapshots for the same plugin raises an error.

    Given an authenticated user, this test validates the following sequence of actions:

    - A user creates the plugin "hello_world".
    - A user adds a plugin file with a single task "hello_world".
    - The user incorrectly sets up a proposed entrypoint input consisting of a task
      graph and global parameters by passing a list of two plugin snapshots that point
      at the same plugin resource.
    - The client returns a 400 status code.
    """
    # Create a plugin
    registered_plugin = dioptra_client.plugins.create(
        group_id=auth_account["default_group_id"],
        name="hello_world",
        description="The hello world plugin.",
    ).json()

    # Add a plugin file with a single task
    filename = "tasks.py"
    description = "The task plugin file for hello world."
    contents = textwrap.dedent(
        """"from dioptra import pyplugs

        @pyplugs.register
        def hello_world(name: str) -> str:
            return f'Hello, {name}!'"
        """
    )
    string_parameter_type = registered_plugin_parameter_types["string"]
    tasks = [
        {
            "name": "hello_world",
            "inputParams": [
                {
                    "name": "name",
                    "parameterType": string_parameter_type["id"],
                    "required": True,
                },
            ],
            "outputParams": [
                {
                    "name": "greeting",
                    "parameterType": string_parameter_type["id"],
                },
            ],
        },
    ]
    dioptra_client.plugins.files.create(
        plugin_id=registered_plugin["id"],
        filename=filename,
        description=description,
        contents=contents,
        function_tasks=tasks,
        artifact_tasks=None,
    )

    # Retrieve the latest plugin snapshot identifier (adding the plugin file creates a
    # new snapshot)
    plugin_snapshot_id = dioptra_client.plugins.get_by_id(
        registered_plugin["id"]
    ).json()["snapshot"]

    # Set up the entrypoint inputs
    task_graph = textwrap.dedent(
        """# my entrypoint graph
        hello_step:
          hello_world:
            name: $name
        """
    )
    plugin_snapshots = [registered_plugin["snapshot"], plugin_snapshot_id]
    parameters = [
        {
            "name": "name",
            "defaultValue": "User",
            "parameterType": "string",
        },
    ]
    assert_multiple_snapshots_for_plugin_raise_error(
        dioptra_client,
        group_id=auth_account["default_group_id"],
        task_graph=task_graph,
        plugin_snapshots=plugin_snapshots,
        entrypoint_parameters=parameters,
    )
