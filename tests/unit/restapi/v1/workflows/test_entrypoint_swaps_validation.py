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

def test_validate_swaps_graph_success(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_multi_task_plugin: int,
) -> None:
    """Test a valid swaps graph.
    """
    plugin_snapshot_id = registered_multi_task_plugin

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

    response = dioptra_client.workflows.validate_entrypoint(
        swaps_graph=swaps_graph,
        plugin_snapshots=[plugin_snapshot_id],
        entrypoint_parameters=[]

    )
    assert (
        response.status_code == HTTPStatus.OK
        and response.json()["schemaValid"]
        and len(response.json()["swapIssues"]) == 0
    )

def test_validate_swaps_graph_invalid_task(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_multi_task_plugin: int,
) -> None:
    """Test that use of nonexistent tasks in a swap returns an error.
    """

    plugin_snapshot_id = registered_multi_task_plugin

    swaps_graph = textwrap.dedent(
        """
        step1:
          ?swap1:
            alias1:
              task: nonexistent_task
        """
    )

    parameters = [
    ]

    response = dioptra_client.workflows.validate_swaps_graph(
        swaps_graph=swaps_graph,
        plugin_snapshots=[plugin_snapshot_id],
        entrypoint_parameters=[]
    )
    assert (
        response.status_code == HTTPStatus.OK
        and response.json()["schemaValid"]
        and len(response.json()["swapIssues"]) > 0
    )

def test_validate_swaps_graph_mixed_output_error(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_multi_task_plugin: int,
) -> None:
    """Test that it errors for different types within a single swap.
    """
    plugin_snapshot_id = registered_multi_task_plugin

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
        entrypoint_parameters=[]
    )
    assert (
        response.status_code == HTTPStatus.OK
        and response.json()["schemaValid"]
        and len(response.json()["swapIssues"]) > 0
    )