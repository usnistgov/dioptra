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

import pytest

from http import HTTPStatus
from pathlib import Path
from typing import Any

from flask.testing import FlaskClient
from freezegun import freeze_time

from dioptra.client.base import DioptraResponseProtocol
from dioptra.client.client import DioptraClient

from ...lib import actions, mock_mlflow, mock_rq

swap_plugins = {
    "plugin1": {
        "filename": "plugin1.py",
        "tasks": {
            "task1" : ["arg1"]
        }
    },
    "plugin9": {
        "filename": "plugin9.py",
        "tasks": {
            "task2" : ["arg2", "arg3"],
            "task4" : ["arg5"],
        }
    },
    "plugin13": {
        "filename": "plugin13.py",
        "tasks": {
            "task10" : ["arg3", "arg4"],
        }
    }
}

swap_entrypoints = {
    "swap_test.yml" : {
        "name": "swap_test",
        "params": ["global1", "global3", "global6", "global9", "global12"]
    },
    "no_swap_test.yml": {
        "name": "no_swap_test",
        "params": ["global1", "global6", "global12"]
    }
}

test_cases_for_file = {}

test_cases_for_file["no_swap_test"] = [
    {
        "swaps": {},
        "globals": [
            "global1", "global6", "global12"
        ],
        "sort_order": [
            ["step1", "step3", "step4", "step2"],
        ],
        "active_plugins": [
            "plugin1", "plugin9", "plugin13"
        ],
    },
]

test_cases_for_file["swap_test"] = [
    {
        "swaps": {
            "step2_choice": "task2",
            "step3_choice": "task1"
        },        
        "globals": [
            "global1", "global3", "global6", "global9"
        ],
        "sort_order": [ # it can be any of these three orders
            ["step1", "step2", "step3", "step4"],
            ["step1", "step3", "step2", "step4"],
            ["step1", "step3", "step4", "step2"],
        ], 
        "active_plugins": [
            "plugin1", "plugin9"
        ]
    },
    {
        "swaps": {
            "step2_choice": "task2",
            "step3_choice": "task2"
        }, 
        "globals": [
            "global1", "global3", "global6", "global12"
        ],                
        "sort_order": [[
            "step1", "step2", "step3", "step4"
        ]],
        "active_plugins": [
            "plugin1", "plugin9"
        ]
    },
    {
        "swaps": {
            "step2_choice": "task10",
            "step3_choice": "task1"
        },
        "globals": [
            "global1", "global6", "global9"
        ],
        "sort_order": [[
            "step1", "step3", "step4", "step2"
        ]],
        "active_plugins": [
            "plugin1", "plugin9", "plugin13"
        ]
    },
    {
        "swaps": {
            "step2_choice": "task10",
            "step3_choice": "task2"
        },
        "globals": [
            "global1", "global6", "global12"
        ],
        "sort_order": [[
            "step1", "step3", "step4", "step2"
        ]],
        "active_plugins": [
            "plugin1", "plugin9", "plugin13"
        ]
    }
]
@pytest.fixture
@freeze_time("Apr 1st, 2025 11:00am", auto_tick_seconds=1)
def registered_swap_plugins(
    client: FlaskClient,
    auth_account: dict[str, Any],
    registered_plugin_parameter_types: dict[str, Any]
) -> dict[str, Any]:

    output = {}

    string_type_response = registered_plugin_parameter_types["string"]

    for plugin_name in swap_plugins:
        plugin_response = actions.register_plugin(
            client,
            name=plugin_name,
            description=f"{plugin_name} description",
            group_id=auth_account["groups"][0]["id"],
        ).get_json()
    
        plugin_tasks = swap_plugins[plugin_name]['tasks']

        tasks = [
            {
                "name": t,
                "inputParams": [
                    {
                        "name": arg, 
                        "parameterType": string_type_response["id"]
                    }
                    for arg in plugin_tasks[t]
                ],
                "outputParams": [
                    {
                        "name": "out",
                        "parameterType": string_type_response["id"]
                    }
                ]
            }
            for t in plugin_tasks
        ]

        plugin_filename = swap_plugins[plugin_name]['filename']

        plugin_file_contents = ""

        plugin_file_response = actions.register_plugin_file(
            client,
            plugin_id=plugin_response["id"],
            description="The plugin file with tasks.",
            filename=plugin_filename,
            contents=plugin_file_contents,
            function_tasks=tasks,
        ).get_json()

        output[plugin_name] = plugin_response 
    return output

@pytest.fixture
@freeze_time("Apr 1st, 2025 11:00am", auto_tick_seconds=1)
def registered_swap_entrypoints(
    client: FlaskClient,
    auth_account: dict[str, Any],
    registered_queues: dict[str, Any],
    registered_swap_plugins: dict[str, Any],
) -> dict[str, Any]:
    output = {}

    for fname in swap_entrypoints:

        entrypoint = swap_entrypoints[fname]

        with (Path(__file__).absolute().parent / 'entrypoint_swaps' / fname).open('r') as f:
            task_graph = f.read()
            parameters = [
                {
                    "name": p,
                    "defaultValue": "default",
                    "parameterType": "string"
                }
                for p in entrypoint['params']
            ]
        
        plugin_ids = [plugin["id"] for plugin in list(registered_swap_plugins.values())]
        queue_ids = [queue["id"] for queue in list(registered_queues.values())]
        
        entrypoint_response = actions.register_entrypoint(
            client,
            name=entrypoint['name'],
            description="The first entrypoint.",
            group_id=auth_account["groups"][0]["id"],
            task_graph=task_graph,
            parameters=parameters,
            plugin_ids=plugin_ids,
            queue_ids=queue_ids,
        ).get_json()

        output[entrypoint['name']] = entrypoint_response
    return output

def test_entrypoint_swaps_endpoint(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_swap_entrypoints: dict[str, Any],
) -> None:
    """
        Test that the entrypoint swaps produces the expected output.
    Args:
        dioptra_client: The Flask test client.
    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """

    for file in test_cases_for_file:
        test_cases = test_cases_for_file[file]
        for case in test_cases:
            swaps = case["swaps"]
            
            expected_globals = case["globals"]
            expected_sort_order = case["sort_order"]
            expected_active_plugins = case["active_plugins"]

            evaluated = dioptra_client.workflows.task_graph_global_params(
                entrypoint_id=registered_swap_entrypoints[file]["id"],
                entrypoint_snapshot_id=registered_swap_entrypoints[file]["snapshot"],
                swaps=swaps
            ).json()

            assert set(expected_globals) == set(evaluated["entrypointParams"])
            assert evaluated["topologicalSort"] in expected_sort_order
            assert len(expected_active_plugins) == len(evaluated["activePlugins"])
            for plugin in evaluated["activePlugins"]:
                assert plugin['name'] in expected_active_plugins

            if swaps != {}:
                # this test is N/A if the entrypoint has no swaps
                forgot_swaps = dioptra_client.workflows.task_graph_global_params(
                    entrypoint_id=registered_swap_entrypoints[file]["id"],
                    entrypoint_snapshot_id=registered_swap_entrypoints[file]["snapshot"],
                    swaps={}
                )
                assert forgot_swaps.status_code == HTTPStatus.BAD_REQUEST

            too_many = swaps
            too_many['extra'] = 'task10'

            too_many_swaps = dioptra_client.workflows.task_graph_global_params(
                entrypoint_id=registered_swap_entrypoints[file]["id"],
                entrypoint_snapshot_id=registered_swap_entrypoints[file]["snapshot"],
                swaps=swaps
            )

            assert too_many_swaps.status_code == HTTPStatus.BAD_REQUEST

            imaginary = swaps
            imaginary['step3_choice'] = "doesnt_exist2"

            imaginary_tasks = dioptra_client.workflows.task_graph_global_params(
                entrypoint_id=registered_swap_entrypoints[file]["id"],
                entrypoint_snapshot_id=registered_swap_entrypoints[file]["snapshot"],
                swaps=swaps
            )

            assert imaginary_tasks.status_code == HTTPStatus.BAD_REQUEST