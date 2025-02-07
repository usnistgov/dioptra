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
"""Test suite for entrypoint operations.

This module contains a set of tests that validate the CRUD operations and additional
functionalities for the entrypoint entity. The tests ensure that the entrypoints can be
registered, renamed, deleted, and locked/unlocked as expected through the REST API.
"""
import textwrap
from http import HTTPStatus
from typing import Any

from flask_sqlalchemy import SQLAlchemy

from dioptra.client.base import DioptraResponseProtocol
from dioptra.client.client import DioptraClient
from dioptra.restapi.routes import V1_ROOT, V1_WORKFLOWS_ROUTE

# -- Actions ---------------------------------------------------------------------------


def validate_entrypoint_workflow(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    task_graph: str,
    plugin_ids: list[int],
    entrypoint_parameters: list[dict[str, Any]],
) -> DioptraResponseProtocol:
    """POST method for the validate entrypoint workflow yaml.

    Args:
        dioptra_client (DioptraClient): The Dioptra client.
        task_graph (str): The task graph of the entrypoint yaml.
        plugin_ids (list[int]): The ids of plugins defined in the task graph.
        entrypoint_parameters (list[dict[str, Any]]): The parmeters defined in the task graph.

    Returns:
        TestResponse: The response from the api.
    """

    return dioptra_client.workflows.validate_entrypoint(
        task_graph=task_graph,
        plugins=plugin_ids,
        entrypoint_parameters=entrypoint_parameters
    )


# -- Assertions ------------------------------------------------------------------------


def assert_entrypoint_workflow_is_valid(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    task_graph: str,
    plugin_ids: list[int],
    entrypoint_parameters: list[dict[str, Any]],
 ) -> None:
    """Asserts that the entrypoint workflow yaml is valid.

    Args:
        dioptra_client (DioptraClient): The Dioptra client.
        task_graph (str): The task graph of the entrypoint yaml.
        plugin_ids (list[int]): The ids of plugins defined in the task graph.
        entrypoint_parameters (list[dict[str, Any]]): The parmeters defined in the task graph.
    """
    response = validate_entrypoint_workflow(
        dioptra_client,
        task_graph=task_graph,
        plugin_ids=plugin_ids,
        entrypoint_parameters=entrypoint_parameters,
    )
    assert response.status_code == HTTPStatus.OK and response.json()['valid'] == True


def assert_entrypoint_workflow_has_errors(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    task_graph: str,
    plugin_ids: list[int],
    entrypoint_parameters: list[dict[str, Any]],
) -> None:
    """Asserts that the entrypoint workflow yaml is invalid.

    Args:
        dioptra_client (DioptraClient): The Dioptra client.
        task_graph (str): The task graph of the entrypoint yaml.
        plugin_ids (list[int]): The ids of plugins defined in the task graph.
        entrypoint_parameters (list[dict[str, Any]]): The parmeters defined in the task graph.
    """
    response = validate_entrypoint_workflow(
        dioptra_client,
        task_graph=task_graph,
        plugin_ids=plugin_ids,
        entrypoint_parameters=entrypoint_parameters,
    )
    assert response.status_code == 422


# -- Tests -----------------------------------------------------------------------------


def test_entrypoint_workflow_validation(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
) -> None:
    """Verifies that a validation entrypoint workflow yaml endpoint works with a valid yaml.

    Args:
        dioptra_client (DioptraClient): The Dioptra client.
        db (SQLAlchemy): The entity database. 
        auth_account (dict[str, Any]): The default authorized user account.
    """
    plugin_response = dioptra_client.plugins.create(
        group_id=auth_account["default_group_id"],
        name="hello_world",
        description="The hello world plugin.",
    ).json()

    plugin_file_contents = textwrap.dedent(
        """"from dioptra import pyplugs
        
        @pyplugs.register
        def hello_world(name: str) -> str:
            return f'Hello, {name}!'"
        """
    )

    plugin_file_tasks = [
        {
            "name": "hello_world",
            "inputParams": [
                {
                    "name": "name",
                    "parameterType": 2,
                    "required": True,
                },
            ],
            "outputParams": [
                {
                    "name": "greeting",
                    "parameterType": 2,
                },
            ],
        },
    ]

    plugin_file_response = dioptra_client.plugins.files.create(
        plugin_id=plugin_response["id"],
        filename="tasks.py",
        description="The task plugin file for hello world.",
        contents=plugin_file_contents,
        tasks = plugin_file_tasks,
    ).json()

    task_graph = textwrap.dedent(
        """# my entrypoint graph
        hello_step:
          hello_world:
            name: $name
        """
    )

    plugin_ids = [plugin_response["id"]]
    entrypoint_parameters = [
        {
            "name" : "name",
            "defaultValue": "User",
            "parameterType": "string",
        },
    ]
    assert_entrypoint_workflow_is_valid(
        dioptra_client,
        task_graph=task_graph,
        plugin_ids=plugin_ids,
        entrypoint_parameters=entrypoint_parameters,
    )


def test_entrypoint_workflow_validation_has_error(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
) -> None:
    """Verifies that a validation entrypoint workflow yaml endpoint works with a invalid yaml.

    Args:
        dioptra_client (DioptraClient): The Dioptra client.
        db (SQLAlchemy): The entity database. 
        auth_account (dict[str, Any]): The default authorized user account.
    """
    plugin_response = dioptra_client.plugins.create(
        name="hello_world",
        description="The hello world plugin.",
        group_id=auth_account["default_group_id"],
    ).json()

    plugin_file_contents = textwrap.dedent(
        """"from dioptra import pyplugs
        
        @pyplugs.register
        def hello_world(name: str) -> str:
            return f'Hello, {name}!'"
        """
    )

    plugin_file_tasks = [
        {
            "name": "hello_world",
            "inputParams": [
                {
                    "name": "name",
                    "parameterType": 2,
                    "required": True,
                },
            ],
            "outputParams": [
                {
                    "name": "greeting",
                    "parameterType": 2,
                },
            ],
        },
    ]

    plugin_file_response = dioptra_client.plugins.files.create(
        plugin_id=plugin_response["id"],
        filename="tasks.py",
        description="The task plugin file for hello world.",
        contents=plugin_file_contents,
        tasks = plugin_file_tasks,
    ).json()

    task_graph = textwrap.dedent(
        """# my entrypoint graph
        hello_step:
          hello_wrld:
            name: $name
        """
    ) # task graph is wrong, hello_wrld is not the task plugin

    plugin_ids = [plugin_response["id"]]
    
    entrypoint_parameters = [
        {
            "name" : "name",
            "defaultValue": "User",
            "parameterType": "string",
        },
    ]
    assert_entrypoint_workflow_has_errors(
        dioptra_client,
        task_graph=task_graph,
        plugin_ids=plugin_ids,
        entrypoint_parameters=entrypoint_parameters,
    )