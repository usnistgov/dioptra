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
"""Test suite for the resource import workflow

This module contains a set of tests that validate the CRUD operations and additional
functionalities for the queue entity. The tests ensure that the queues can be
registered, renamed, deleted, and locked/unlocked as expected through the REST API.
"""

import shutil
from http import HTTPStatus
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import pytest
from flask_sqlalchemy import SQLAlchemy

from dioptra.client import DioptraClient, DioptraFile
from dioptra.client.base import DioptraResponseProtocol

# -- Assertions ------------------------------------------------------------------------


def assert_imported_resources_match_expected(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    expected: dict[str, Any],
):
    response = dioptra_client.plugins.get()
    response_plugins = set(plugin["name"] for plugin in response.json()["data"])
    expected_plugins = set(Path(plugin["path"]).stem for plugin in expected["plugins"])
    assert (
        response.status_code == HTTPStatus.OK and response_plugins == expected_plugins
    )

    response = dioptra_client.plugin_parameter_types.get()
    response_types = set(param["name"] for param in response.json()["data"])
    expected_types = set(param["name"] for param in expected["plugin_param_types"])
    assert (
        response.status_code == HTTPStatus.OK
        and response_types & expected_types == expected_types
    )

    response = dioptra_client.entrypoints.get()
    response_entrypoints = set(ep["name"] for ep in response.json()["data"])
    expected_entrypoints = set(ep["name"] for ep in expected["entrypoints"])
    assert (
        response.status_code == HTTPStatus.OK
        and response_entrypoints == expected_entrypoints
    )


def assert_resource_import_fails_due_to_name_clash(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    group_id: int,
    archive_file: DioptraFile,
):
    dioptra_client.plugins.create(group_id=group_id, name="hello_world")
    response = dioptra_client.workflows.import_resources(
        group_id=group_id,
        source=archive_file,
        resolve_name_conflicts_strategy="fail",
    )

    assert response.status_code == HTTPStatus.CONFLICT


def assert_resource_import_overwrite_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    group_id: int,
    archive_file: DioptraFile,
):
    dioptra_client.entrypoints.create(
        group_id=group_id, name="Hello World", task_graph=""
    )
    dioptra_client.plugins.create(group_id=group_id, name="hello_world")
    dioptra_client.plugin_parameter_types.create(group_id=group_id, name="message")
    response = dioptra_client.workflows.import_resources(
        group_id=group_id,
        source=archive_file,
        resolve_name_conflicts_strategy="overwrite",
    )

    assert response.status_code == HTTPStatus.OK


# -- Tests -----------------------------------------------------------------------------


def test_resource_import_from_archive_file(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    resources_tar_file: DioptraFile,
    resources_import_config: dict[str, Any],
):
    group_id = auth_account["groups"][0]["id"]
    dioptra_client.workflows.import_resources(group_id, source=resources_tar_file)

    assert_imported_resources_match_expected(dioptra_client, resources_import_config)


def test_resource_import_from_files(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    resources_files: list[DioptraFile],
    resources_import_config: dict[str, Any],
):
    group_id = auth_account["groups"][0]["id"]
    dioptra_client.workflows.import_resources(group_id, source=resources_files)

    assert_imported_resources_match_expected(dioptra_client, resources_import_config)


@pytest.mark.skipif(shutil.which("git") is None, reason="git was not found.")
def test_resource_import_from_repo(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    resources_repo: str,
    resources_import_config: dict[str, Any],
):
    group_id = auth_account["groups"][0]["id"]
    dioptra_client.workflows.import_resources(group_id, source=resources_repo)

    assert_imported_resources_match_expected(dioptra_client, resources_import_config)


def test_resource_import_fails_from_name_clash(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    resources_tar_file: NamedTemporaryFile,
):
    group_id = auth_account["groups"][0]["id"]

    assert_resource_import_fails_due_to_name_clash(
        dioptra_client, group_id=group_id, archive_file=resources_tar_file
    )


def test_resource_import_overwrite(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    resources_tar_file: NamedTemporaryFile,
):
    group_id = auth_account["groups"][0]["id"]

    assert_resource_import_overwrite_works(
        dioptra_client, group_id=group_id, archive_file=resources_tar_file
    )
