# This Software (Dioptra) is being made available as a public service by the
# National Institute of Standards and Technology (NIST), an Agency of the United
# States Department of Commerce. This software was developed in part by employees of
# NIST and in part by NIST contractors. Copyright in portions of this software that
# were developed by NIST contractors has been licensed or assigned to NIST. Pursuant
# to Title 17 United States Code Section 105, works of NIST employees are not
# subject to copyright protection in the United States. However, NIST may hold
# international copyright in software created by its employees and domestic
# copyright (or licensing rights) in portions of software that were assigned or
# licensed to NIST.
#
# ACCESS THE FULL CC BY 4.0 LICENSE HERE:
# https://creativecommons.org/licenses/by/4.0/legalcode


import textwrap
from http import HTTPStatus
from typing import Any

from dioptra.client.base import DioptraResponseProtocol
from dioptra.client.client import DioptraClient


def _create_multi_task_plugin(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_plugin_parameter_types: dict[str, Any],
):

    registered_plugin = dioptra_client.plugins.create(
        group_id=auth_account["default_group_id"],
        name="swap_test_plugin",
        description="A plugin exposing four tasks.",
    ).json()

    filename = "tasks.py"
    description = "The task plugin file exposing four tasks."
    contents = textwrap.dedent(
        """from dioptra import pyplugs

        @pyplugs.register
        def task_one(name: str) -> str:
            return f'Task One says hello to {name}!'

        @pyplugs.register
        def task_two(name: str) -> str:
            return f'Task Two greets {name}!'

        @pyplugs.register
        def task_three(name: str) -> str:
            return f'Task Three welcomes {name}!'

        @pyplugs.register
        def task_int(name: str) -> int:
            return len(name)
        """
    )

    string_parameter_type = registered_plugin_parameter_types["string"]
    integer_parameter_type = registered_plugin_parameter_types["integer"]

    tasks = [
        {
            "name": "task_one",
            "inputParams": [
                {
                    "name": "name",
                    "parameterType": string_parameter_type["id"],
                    "required": True,
                }
            ],
            "outputParams": [
                {
                    "name": "greeting",
                    "parameterType": string_parameter_type["id"],
                }
            ],
        },
        {
            "name": "task_two",
            "inputParams": [
                {
                    "name": "name",
                    "parameterType": string_parameter_type["id"],
                    "required": True,
                }
            ],
            "outputParams": [
                {
                    "name": "greeting",
                    "parameterType": string_parameter_type["id"],
                }
            ],
        },
        {
            "name": "task_three",
            "inputParams": [
                {
                    "name": "name",
                    "parameterType": string_parameter_type["id"],
                    "required": True,
                }
            ],
            "outputParams": [
                {
                    "name": "greeting",
                    "parameterType": string_parameter_type["id"],
                }
            ],
        },
        {
            "name": "task_int",
            "inputParams": [
                {
                    "name": "name",
                    "parameterType": string_parameter_type["id"],
                    "required": True,
                }
            ],
            "outputParams": [
                {
                    "name": "value",
                    "parameterType": integer_parameter_type["id"],
                }
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

    plugin_snapshot_id = dioptra_client.plugins.get_by_id(
        registered_plugin["id"]
    ).json()["snapshot"]
    return plugin_snapshot_id


def test_validate_swaps_graph_success(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_plugin_parameter_types: dict[str, Any],
) -> None:
    """Test a valid swaps graph.
    """
    plugin_snapshot_id = _create_multi_task_plugin(
        dioptra_client, auth_account, registered_plugin_parameter_types
    )

    swaps_graph = textwrap.dedent(
        """
        step1:
          ?swap1:
            alias1:
              task_one: arthur
            alias2:
              task: task_two
              args: [lancelot]
            alias3:
              task: task_three
              kwargs:
                name: galahad
        measure:
          task_int: $step1

        """
    )

    response = dioptra_client.workflows.validate_swaps_graph(
        swaps_graph=swaps_graph,
        plugin_snapshots=[plugin_snapshot_id],
    )
    assert (
        response.status_code == HTTPStatus.OK
        and response.json()["schemaValid"]
        and len(response.json()["swapErrors"]) == 0
    )


def test_validate_swaps_graph_invalid_task(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_plugin_parameter_types: dict[str, Any],
) -> None:
    """Test that use of nonexistent tasks in a swap returns an error.
    """

    plugin_snapshot_id = _create_multi_task_plugin(
        dioptra_client, auth_account, registered_plugin_parameter_types
    )

    swaps_graph = textwrap.dedent(
        """
        step1:
          ?swap1:
            alias1:
              task: nonexistent_task
        """
    )

    response = dioptra_client.workflows.validate_swaps_graph(
        swaps_graph=swaps_graph,
        plugin_snapshots=[plugin_snapshot_id],
    )
    assert (
        response.status_code == HTTPStatus.OK
        and response.json()["schemaValid"]
        and len(response.json()["swapErrors"]) > 0
    )


def test_validate_swaps_graph_mixed_output_error(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_plugin_parameter_types: dict[str, Any],
) -> None:
    """Test that it errors for different types within a single swap.
    """
    plugin_snapshot_id = _create_multi_task_plugin(
        dioptra_client, auth_account, registered_plugin_parameter_types
    )

    swaps_graph = textwrap.dedent(
        """
        step1:
          ?swap1:
            alias_str:
              task: task_one
            alias_int:
              task: task_int
        """
    )

    response = dioptra_client.workflows.validate_swaps_graph(
        swaps_graph=swaps_graph,
        plugin_snapshots=[plugin_snapshot_id],
    )
    assert (
        response.status_code == HTTPStatus.OK
        and response.json()["schemaValid"]
        and len(response.json()["swapErrors"]) > 0
    )
