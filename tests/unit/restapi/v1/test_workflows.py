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
    entrypoint_parameters: dict[str, str],
) -> TestResponse:
    """"""
    payload: dict[str, Any] = {
        "taskGraph" : task_graph,
        "pluginIds": plugin_ids,
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
    entrypoint_parameters: dict[str, str],
 ) -> None:
    response = validate_entrypoint_workflow(
        client,
        task_graph=task_graph,
        plugin_ids=plugin_ids,
        entrypoint_parameters=entrypoint_parameters,
    )
    assert response.status_code == 200 and response.valid == True


# -- Tests -----------------------------------------------------------------------------


def test_entrypoint_workflow_validation(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
) -> None:
    """"""
    task_graph = ""
    plugin_ids = []
    entrypoint_parameters = []
    assert_entrypoint_workflow_is_valid(
        client,
        task_graph=task_graph,
        plugin_ids=plugin_ids,
        entrypoint_parameters=entrypoint_parameters,
    )
