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
from typing import Any

from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from werkzeug.test import TestResponse

from dioptra.restapi.routes import V1_WORKFLOWS_ROUTE, V1_ROOT

from ..lib import actions, asserts, helpers


# -- Actions ---------------------------------------------------------------------------


def validate_entrypoint_workflow(
    client: FlaskClient,
    task_graph: str,
    plugin_ids: list[int],
    entrypoint_parameters: list[dict[str, Any]],
) -> TestResponse:
    """"""
    payload: dict[str, Any] = {
        "taskGraph" : task_graph,
        "plugins": plugin_ids,
        "parameters": entrypoint_parameters,
    }

    return client.post(
        f"/{V1_ROOT}/{V1_WORKFLOWS_ROUTE}/entrypointValidate",
        json=payload,
        follow_redirects=True,
    )


# -- Assertions ------------------------------------------------------------------------


def assert_entrypoint_workflow_is_valid(
    client: FlaskClient,
    task_graph: str,
    plugin_ids: list[int],
    entrypoint_parameters: list[dict[str, Any]],
 ) -> None:
    response = validate_entrypoint_workflow(
        client,
        task_graph=task_graph,
        plugin_ids=plugin_ids,
        entrypoint_parameters=entrypoint_parameters,
    )
    assert response.status_code == 200 and response.get_json()['valid'] == True


def assert_entrypoint_workflow_has_errors(
    client: FlaskClient,
    task_graph: str,
    plugin_ids: list[int],
    entrypoint_parameters: list[dict[str, Any]],
    expected_message: str,
) -> None:
    response = validate_entrypoint_workflow(
        client,
        task_graph=task_graph,
        plugin_ids=plugin_ids,
        entrypoint_parameters=entrypoint_parameters,
    )
    assert response.status_code == 422 and response.get_json()['message'] == expected_message


# -- Tests -----------------------------------------------------------------------------


def test_entrypoint_workflow_validation(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
) -> None:
    """"""
    plugin_response = actions.register_plugin(
        client,
        name="hello_world",
        description="The hello world plugin.",
        group_id=auth_account["default_group_id"],
    ).get_json()
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
    plugin_file_response = actions.register_plugin_file(
        client,
        plugin_id=plugin_response["id"],
        filename="tasks.py",
        description="The task plugin file for hello world.",
        contents=plugin_file_contents,
        tasks = plugin_file_tasks,
    ).get_json()
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
        client,
        task_graph=task_graph,
        plugin_ids=plugin_ids,
        entrypoint_parameters=entrypoint_parameters,
    )


def test_entrypoint_workflow_validation_has_error(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
) -> None:
    """"""
    plugin_response = actions.register_plugin(
        client,
        name="hello_world",
        description="The hello world plugin.",
        group_id=auth_account["default_group_id"],
    ).get_json()
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
    plugin_file_response = actions.register_plugin_file(
        client,
        plugin_id=plugin_response["id"],
        filename="tasks.py",
        description="The task plugin file for hello world.",
        contents=plugin_file_contents,
        tasks = plugin_file_tasks,
    ).get_json()
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
    expected_message = "[ValidationIssue(IssueType.SEMANTIC, IssueSeverity.ERROR, 'In step \"hello_step\": unrecognized task plugin: hello_wrld')]"
    assert_entrypoint_workflow_has_errors(
        client,
        task_graph=task_graph,
        plugin_ids=plugin_ids,
        entrypoint_parameters=entrypoint_parameters,
        expected_message=expected_message,
    )