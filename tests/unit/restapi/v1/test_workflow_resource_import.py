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

from typing import Any
from pathlib import Path
from tempfile import NamedTemporaryFile
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from werkzeug.test import TestResponse

from dioptra.restapi.routes import V1_ROOT, V1_WORKFLOWS_ROUTE


# -- Actions ---------------------------------------------------------------------------


def resource_import(
    client: FlaskClient,
    resources_tar_file: NamedTemporaryFile,
    group_id: int,
    read_only: bool,
    resolve_name_conflict_strategy: str,
) -> TestResponse:
    """Import resources into Dioptra

    Args:
        client: The Flask test client.
        group_id: The id of the group to import resources into.

    Returns:
        The response from the API.
    """

    payload = {
        "groupId": group_id,
        "sourceType": "upload",
        "archiveFile": (resources_tar_file, "upload.tar.gz"),
        "configPath": "dioptra.toml",
        "readOnly": read_only,
        "resolveNameConflictsStrategy": resolve_name_conflict_strategy,
    }

    return client.post(
        f"/{V1_ROOT}/{V1_WORKFLOWS_ROUTE}/resourceImport",
        data=payload,
        content_type="multipart/form-data",
        follow_redirects=True,
    )


# -- Assertions ------------------------------------------------------------------------


def assert_imported_resources_match_expected(
    client: FlaskClient,
    expected: dict[str, Any],
):
    response = client.get(f"/{V1_ROOT}/plugins", follow_redirects=True)
    response_plugins = set(plugin["name"] for plugin in response.get_json()["data"])
    expected_plugins = set(Path(plugin["path"]).stem for plugin in expected["plugins"])
    assert response.status_code == 200 and response_plugins == expected_plugins

    response = client.get(f"/{V1_ROOT}/pluginParameterTypes", follow_redirects=True)
    response_types = set(param["name"] for param in response.get_json()["data"])
    expected_types = set(param["name"] for param in expected["plugin_param_types"])
    assert (
        response.status_code == 200
        and response_types & expected_types == expected_types
    )

    response = client.get(f"/{V1_ROOT}/entrypoints", follow_redirects=True)
    response_entrypoints = set(ep["name"] for ep in response.get_json()["data"])
    expected_entrypoints = set(ep["name"] for ep in expected["entrypoints"])
    assert response.status_code == 200 and response_entrypoints == expected_entrypoints


def assert_resource_import_fails_due_to_name_clash(
    client: FlaskClient,
    group_id: int,
    resources_tar_file: NamedTemporaryFile,
):
    payload = {"name": "hello_world", "group": group_id}
    client.post(f"/{V1_ROOT}/plugins", json=payload, follow_redirects=True)

    response = resource_import(
        client,
        resources_tar_file,
        group_id,
        read_only=True,
        resolve_name_conflict_strategy="fail",
    )
    assert response.status_code == 409


def assert_resource_import_overwrite_works(
    client: FlaskClient,
    group_id: int,
    resources_tar_file: NamedTemporaryFile,
):
    payload = {"name": "hello_world", "group": group_id}
    client.post(f"/{V1_ROOT}/plugins", json=payload, follow_redirects=True)

    response = resource_import(
        client,
        resources_tar_file,
        group_id,
        read_only=True,
        resolve_name_conflict_strategy="overwrite",
    )
    assert response.status_code == 200


# -- Tests -----------------------------------------------------------------------------


def test_resource_import(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    resources_tar_file: NamedTemporaryFile,
    resources_import_config: dict[str, Any],
):
    group_id = auth_account["groups"][0]["id"]
    resource_import(
        client,
        resources_tar_file,
        group_id,
        read_only=True,
        resolve_name_conflict_strategy="fail",
    )

    assert_imported_resources_match_expected(client, resources_import_config)


def test_resource_import_fails_from_name_clash(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    resources_tar_file: NamedTemporaryFile,
):
    group_id = auth_account["groups"][0]["id"]
    assert_resource_import_fails_due_to_name_clash(client, group_id, resources_tar_file)


def test_resource_import_overwrite(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    resources_tar_file: NamedTemporaryFile,
):
    group_id = auth_account["groups"][0]["id"]
    assert_resource_import_overwrite_works(client, group_id, resources_tar_file)
