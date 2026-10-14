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

import json
import os
import textwrap
from http import HTTPStatus
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from unittest.mock import Mock

import pytest
from freezegun import freeze_time

from dioptra.client import DioptraClient, DioptraFile
from dioptra.client.base import DioptraResponseProtocol
from dioptra.client.utils import select_files_in_directory, select_one_or_more_files
from dioptra.restapi.v1.shared import io_file_service as file_io
from dioptra.restapi.v1.workflows import service as workflow_service

# -- Assertions ------------------------------------------------------------------------


def assert_imported_resources_match_expected(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    expected: dict[str, Any],
):
    response = dioptra_client.plugins.get()
    response_plugins = {plugin["name"] for plugin in response.json()["data"]}
    expected_plugins = {Path(plugin["path"]).stem for plugin in expected["plugins"]}
    assert (
        response.status_code == HTTPStatus.OK and response_plugins == expected_plugins
    )

    response = dioptra_client.plugin_parameter_types.get()
    response_types = {param["name"] for param in response.json()["data"]}
    expected_types = {param["name"] for param in expected["plugin_param_types"]}
    assert (
        response.status_code == HTTPStatus.OK
        and response_types & expected_types == expected_types
    )

    response = dioptra_client.entrypoints.get()
    response_entrypoints = {ep["name"] for ep in response.json()["data"]}
    expected_entrypoints = {ep["name"] for ep in expected["entrypoints"]}
    assert (
        response.status_code == HTTPStatus.OK
        and response_entrypoints == expected_entrypoints
    )


def assert_resource_import_fails_due_to_name_clash(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    group_id: int,
    archive_file: DioptraFile,
):
    response = dioptra_client.workflows.import_resources(
        group_id=group_id,
        source=archive_file,
        resolve_name_conflicts_strategy="fail",
    )

    assert response.status_code == HTTPStatus.CONFLICT


def assert_resource_import_fails_due_to_duplicate_names(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    group_id: int,
    files: list[DioptraFile],
):
    response = dioptra_client.workflows.import_resources(
        group_id, source=files, config_path="dioptra.toml"
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "duplicate" in response.text


def assert_resource_import_update_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    group_id: int,
    archive_file: DioptraFile,
    description: str,
):
    response = dioptra_client.workflows.import_resources(
        group_id=group_id,
        source=archive_file,
        resolve_name_conflicts_strategy="update",
    )
    resource_ids = response.json()["resources"]
    plugin_response = dioptra_client.plugins.get_by_id(
        resource_ids["plugins"]["hello_world"]
    )
    entrypoint_response = dioptra_client.entrypoints.get_by_id(
        resource_ids["entrypoints"]["Hello World"]
    )
    param_type_response = dioptra_client.plugin_parameter_types.get_by_id(
        resource_ids["plugin_param_types"]["message"]
    )

    assert response.status_code == HTTPStatus.OK
    assert (
        plugin_response.status_code == HTTPStatus.OK
        and plugin_response.json()["description"] != description
    )
    assert (
        entrypoint_response.status_code == HTTPStatus.OK
        and entrypoint_response.json()["description"] != description
    )
    assert (
        param_type_response.status_code == HTTPStatus.OK
        and param_type_response.json()["description"] != description
    )


def assert_resource_import_overwrite_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    group_id: int,
    archive_file: DioptraFile,
):
    response = dioptra_client.workflows.import_resources(
        group_id=group_id,
        source=archive_file,
        resolve_name_conflicts_strategy="overwrite",
    )

    assert response.status_code == HTTPStatus.OK


# -- Tests -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("strategy", "existing"),
    [("fail", False), ("overwrite", False), ("update", False), ("update", True)],
)
def test_resource_import_rejects_missing_global(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    tmp_path: Path,
    strategy: str,
    existing: bool,
):
    """Reject undeclared global references during import creation and updates.

    Verify that imports run full save-time validation even though entry-point
    services defer committing the transaction to the batch import service.
    """
    group_id = auth_account["groups"][0]["id"]
    config = tmp_path / "dioptra.toml"
    plugin = tmp_path / "tasks" / "tasks.py"
    plugin.parent.mkdir()
    entrypoint = tmp_path / "entrypoint.yaml"
    config.write_text(
        textwrap.dedent("""\
        [[plugins]]
        path = "tasks"
        [[plugins.tasks.functions]]
        filename = "tasks.py"
        name = "alpha"
        input_params = [{ name = "value", type = "string", required = true }]
        output_params = [{ name = "result", type = "string" }]

        [[entrypoints]]
        name = "Imported entrypoint"
        path = "entrypoint.yaml"
        plugins = ["tasks"]
    """)
    )
    plugin.write_text("def alpha(value):\n    return value\n")

    def import_resources():
        files = select_one_or_more_files(
            [str(config), str(plugin), str(entrypoint)],
            renames={
                str(path): path.relative_to(tmp_path).as_posix()
                for path in (config, plugin, entrypoint)
            },
        )
        return dioptra_client.workflows.import_resources(
            group_id,
            source=files,
            resolve_name_conflicts_strategy=strategy,
        )

    if existing:
        entrypoint.write_text(
            textwrap.dedent("""\
                graph:
                  selected:
                    alpha:
                      value: valid
            """)
        )
        response = import_resources()
        assert response.status_code == HTTPStatus.OK, response.text

    entrypoint.write_text(
        textwrap.dedent("""\
            graph:
              selected:
                alpha:
                  value: $missing_global
        """)
    )
    response = import_resources()

    assert response.status_code == HTTPStatus.BAD_REQUEST, response.text
    reason = response.json()["detail"]["reason"]
    assert "missing_global" in reason["missing_global_params"]
    assert any(
        "missing_global" in error for error in reason["rendered_validation_errors"]
    )


@pytest.mark.parametrize(
    ("resource_import_source", "config_path"),
    [
        ("files", "dioptra.toml"),
        ("tar.gz", "dioptra.toml"),
        ("github", "dioptra.toml"),
        ("gitlab", "dioptra.toml"),
        ("files", "configs/dioptra.toml"),
    ],
    indirect=["resource_import_source"],
)
def test_resource_import_sources_use_same_pipeline(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    resources_import_config: dict[str, Any],
    resource_import_source,
    config_path: str,
    monkeypatch: pytest.MonkeyPatch,
):
    root = Path(__file__).parent / "resource_import_files"
    contents = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    config = contents.pop("dioptra.toml")
    if config_path != "dioptra.toml":
        config = config.replace(b'path = "plugins/', b'path = "../plugins/').replace(
            b'path = "entrypoints/', b'path = "../entrypoints/'
        )
    contents[config_path] = config
    source, expected_hash = resource_import_source(contents)
    cwd = Path.cwd()
    chdir = Mock(side_effect=AssertionError("Resource imports must not change cwd"))
    monkeypatch.setattr(os, "chdir", chdir)
    group_id = auth_account["groups"][0]["id"]
    response = dioptra_client.workflows.import_resources(
        group_id, source=source, config_path=config_path
    )
    assert response.status_code == HTTPStatus.OK, response.text
    assert response.json()["hash"] == expected_hash
    assert Path.cwd() == cwd
    chdir.assert_not_called()
    assert_imported_resources_match_expected(dioptra_client, resources_import_config)


@pytest.mark.parametrize("resource_import_source", ["files"], indirect=True)
@pytest.mark.parametrize(
    ("field", "path"),
    [
        ("config", "../dioptra.toml"),
        ("config", "/outside/dioptra.toml"),
        ("plugin", "../outside"),
        ("plugin", "/outside"),
        ("entrypoint", "../outside.yml"),
        ("entrypoint", "/outside.yml"),
    ],
)
def test_resource_import_confines_reads_and_rolls_back(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    resource_import_source,
    field: str,
    path: str,
):
    group_id = auth_account["groups"][0]["id"]
    original = dioptra_client.plugins.create(group_id=group_id, name="inside").json()
    config = '[[plugins]]\npath = "inside"\n'
    if field == "plugin":
        config += f"[[plugins]]\npath = {json.dumps(path)}\n"
    elif field == "entrypoint":
        config += f'[[entrypoints]]\nname = "outside"\npath = {json.dumps(path)}\n'
    source, _ = resource_import_source(
        {"dioptra.toml": config.encode(), "inside/tasks.py": b"def task(): pass\n"}
    )
    response = dioptra_client.workflows.import_resources(
        group_id,
        source=source,
        config_path=path if field == "config" else "dioptra.toml",
        resolve_name_conflicts_strategy="overwrite",
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST, response.text
    assert response.json()["error"] == "ImportFailedError"
    assert "path" in response.json()["detail"]["reason"].lower()
    plugins = dioptra_client.plugins.get().json()["data"]
    assert [(plugin["id"], plugin["name"]) for plugin in plugins] == [
        (original["id"], "inside")
    ]


def test_resource_import_rejects_oversized_uploaded_archive(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    resources_tar_file: DioptraFile,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(workflow_service, "MAX_ARCHIVE_BYTES", 4)
    response = dioptra_client.workflows.import_resources(
        auth_account["groups"][0]["id"], source=resources_tar_file
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "download/upload size limit" in response.json()["detail"]["reason"]
    assert dioptra_client.plugins.get().json()["data"] == []


@pytest.mark.parametrize(
    ("setting", "limit", "message"),
    [("MAX_ENTRIES", 1, "too many entries"), ("MAX_TOTAL_BYTES", 5, "total content")],
)
def test_resource_import_limits_multipart_uploads(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    setting: str,
    limit: int,
    message: str,
):
    monkeypatch.setattr(workflow_service, setting, limit)
    with BytesIO(b"123") as first, BytesIO(b"456") as second:
        response = dioptra_client.workflows.import_resources(
            auth_account["groups"][0]["id"],
            source=[DioptraFile("a", first, None), DioptraFile("b", second, None)],
        )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert message in response.json()["detail"]["reason"]
    assert dioptra_client.plugins.get().json()["data"] == []


@pytest.mark.parametrize("resource_import_source", ["github"], indirect=True)
def test_repository_import_gets_fresh_extraction_budget_after_slow_download(
    dioptra_client, auth_account, resource_import_source, repository_http, monkeypatch
):
    source, expected_hash = resource_import_source({"dioptra.toml": b""})
    get_response = repository_http.get.side_effect
    with freeze_time("2025-01-01") as clock:

        def slow_response(url, **kwargs):
            response = get_response(url, **kwargs)
            chunks = response.iter_content

            def slow_chunks(chunk_size):
                clock.tick(180)
                yield from chunks(chunk_size)

            monkeypatch.setattr(response, "iter_content", slow_chunks)
            return response

        repository_http.get.side_effect = slow_response
        response = dioptra_client.workflows.import_resources(
            auth_account["groups"][0]["id"], source=source
        )

    assert response.status_code == HTTPStatus.OK, response.text
    assert response.json()["hash"] == expected_hash


@pytest.mark.parametrize("resource_import_source", ["tar.gz", "github"], indirect=True)
def test_archive_extraction_timeout_is_handled(
    dioptra_client, auth_account, resource_import_source, monkeypatch
):
    source, _ = resource_import_source({"dioptra.toml": b"", "extra.txt": b""})
    now = [1000.0]
    monkeypatch.setattr(file_io, "monotonic", lambda: now[0])
    write_file = file_io.IOFileService.write_file

    def slow_write(*args, **kwargs):
        now[0] += 61
        return write_file(*args, **kwargs)

    # Two individually short writes must share one 120-second extraction budget.
    monkeypatch.setattr(file_io.IOFileService, "write_file", staticmethod(slow_write))
    response = dioptra_client.workflows.import_resources(
        auth_account["groups"][0]["id"], source=source
    )
    expected_status = (
        HTTPStatus.INTERNAL_SERVER_ERROR
        if isinstance(source, str)
        else HTTPStatus.BAD_REQUEST
    )
    assert response.status_code == expected_status, response.text
    assert "Import archive extraction timed out." in response.text
    assert dioptra_client.plugins.get().json()["data"] == []


@pytest.mark.parametrize("rollback_fails", [False, True])
def test_unexpected_import_error_is_handled(
    dioptra_client, auth_account, resources_tar_file, monkeypatch, rollback_fails
):
    monkeypatch.setattr(
        workflow_service,
        "TemporaryDirectory",
        Mock(side_effect=OSError("internal setup detail")),
    )
    with monkeypatch.context() as patch:
        rollback = Mock(wraps=workflow_service.db.session.rollback)
        if rollback_fails:
            rollback.side_effect = RuntimeError("internal rollback detail")
        patch.setattr(workflow_service.db.session, "rollback", rollback)
        response = dioptra_client.workflows.import_resources(
            auth_account["groups"][0]["id"], source=resources_tar_file
        )
        rollback.assert_called_once()

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json()["error"] == "UnexpectedImportError"
    assert "Resource import failed unexpectedly." in response.json()["message"]
    assert "internal setup detail" not in response.text
    assert "internal rollback detail" not in response.text


def test_resource_import_handles_repository_download_failure(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    repository_http,
    repository_response,
):
    repository_http.get.return_value = repository_response(status=404)
    group_id = auth_account["groups"][0]["id"]
    response = dioptra_client.workflows.import_resources(
        group_id, source="https://github.com/owner/missing"
    )

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json()["error"] == "GitError"
    assert "HTTP 404" in response.json()["message"]
    assert dioptra_client.plugins.get().json()["data"] == []


def test_resource_import_fails_from_name_clash(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    resources_tar_file: NamedTemporaryFile,
):
    group_id = auth_account["groups"][0]["id"]

    dioptra_client.plugins.create(group_id=group_id, name="hello_world")
    assert_resource_import_fails_due_to_name_clash(
        dioptra_client, group_id=group_id, archive_file=resources_tar_file
    )


def test_resource_import_update(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    resources_tar_file: NamedTemporaryFile,
    registered_plugin_with_files: dict[str, Any],
):
    group_id = auth_account["groups"][0]["id"]
    description_to_replace = "original description"
    plugin_ids = [registered_plugin_with_files["plugin"]["id"]]

    task_graph = textwrap.dedent(
        """
        message:
          hello_world: $name
        """
    )
    dioptra_client.plugin_parameter_types.create(
        group_id=group_id, name="message", description=description_to_replace
    )

    dioptra_client.entrypoints.create(
        group_id=group_id,
        name="Hello World",
        task_graph=task_graph,
        parameters=[
            {
                "name": "name",
                "defaultValue": "test",
                "parameterType": "string",
            }
        ],
        description=description_to_replace,
        plugins=plugin_ids,
    )
    dioptra_client.plugins.create(
        group_id=group_id, name="hello_world", description=description_to_replace
    )
    assert_resource_import_update_works(
        dioptra_client,
        group_id=group_id,
        archive_file=resources_tar_file,
        description=description_to_replace,
    )


def test_resource_import_update_deleted_queue(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    resources_tar_file: NamedTemporaryFile,
    registered_plugin_with_files: dict[str, Any],
):
    group_id = auth_account["groups"][0]["id"]
    description_to_replace = "original description"
    plugin_ids = [registered_plugin_with_files["plugin"]["id"]]

    task_graph = textwrap.dedent(
        """
        message:
          hello_world: $name
        """
    )

    dioptra_client.plugin_parameter_types.create(
        group_id=group_id, name="message", description=description_to_replace
    )

    entrypoint_response = dioptra_client.entrypoints.create(
        group_id=group_id,
        name="Hello World",
        task_graph=task_graph,
        parameters=[
            {
                "name": "name",
                "defaultValue": "test",
                "parameterType": "string",
            }
        ],
        description=description_to_replace,
        plugins=plugin_ids,
    )
    dioptra_client.plugins.create(
        group_id=group_id, name="hello_world", description=description_to_replace
    )
    queue_response = dioptra_client.queues.create(group_id=group_id, name="queue")
    dioptra_client.entrypoints.queues.create(
        entrypoint_response.json()["id"], [queue_response.json()["id"]]
    )
    dioptra_client.queues.delete_by_id(queue_response.json()["id"])
    assert_resource_import_update_works(
        dioptra_client,
        group_id=group_id,
        archive_file=resources_tar_file,
        description=description_to_replace,
    )


def test_resource_import_update_dioptra_optic(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
):
    group_id = auth_account["groups"][0]["id"]
    extra_path = Path(__file__).parents[5] / "extra"
    response = dioptra_client.workflows.import_resources(
        group_id=group_id,
        source=select_files_in_directory(extra_path, recursive=True),
        config_path="dioptra_optic.toml",
        resolve_name_conflicts_strategy="update",
    )
    assert response.status_code == HTTPStatus.OK

    response = dioptra_client.workflows.import_resources(
        group_id=group_id,
        source=select_files_in_directory(extra_path, recursive=True),
        config_path="dioptra_optic.toml",
        resolve_name_conflicts_strategy="update",
    )
    assert response.status_code == HTTPStatus.OK


def test_resource_import_overwrite(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_plugin_parameter_types: dict[str, Any],
    resources_tar_file: NamedTemporaryFile,
):
    group_id = auth_account["groups"][0]["id"]

    task_graph = textwrap.dedent(
        """
        message:
          shout: $name
        """
    )

    dioptra_client.entrypoints.create(
        group_id=group_id,
        name="Hello World",
        task_graph=task_graph,
        parameters=[
            {
                "name": "name",
                "defaultValue": "test",
                "parameterType": "string",
            }
        ],
    )

    dioptra_client.plugin_parameter_types.create(group_id=group_id, name="message")

    dioptra_client.plugins.create(group_id=group_id, name="hello_world")

    assert_resource_import_overwrite_works(
        dioptra_client, group_id=group_id, archive_file=resources_tar_file
    )


@pytest.mark.parametrize(
    "resources_import_config",
    [
        # test duplicate entrypoints
        "entrypoints = [ { name = 'duplicate' }, { name = 'duplicate' } ]",
        # test duplicate plugins
        "plugins = [ { path = 'duplicate' }, { path = 'duplicate' } ]",
        # test duplicate plugin tasks
        "plugins = [ { path = 'tasks.py', tasks = { functions = [ { name='duplicate' }, { name = 'duplicate' } ] } } ]",
        # test duplicate entrypoint parameters
        "entrypoints = [ { name = 'ep1', params = [ { name = 'duplicate', type = 'str'}, { name = 'duplicate', type = 'str'} ] } ]",
        # test duplicate plugin parameters
        "plugins = [ { path = 'tasks.py', tasks = { functions = [ { name = 'duplicate', input_params = [ { name = 'duplicate', type = 'str' }, { name = 'duplicate', type = 'str' } ] } ] } } ]",
        # test duplicate plugin output parameters
        "plugins = [ { path = 'tasks.py', tasks = { functions = [ { name = 'duplicate', output_params = [ { name = 'duplicate', type = 'str' }, { name = 'duplicate', type = 'str' } ] } ] } } ]",
        # test duplicate artifact parameters
        "entrypoints = [ { name = 'ep2', artifact_params = [ { name = 'duplicate', type = 'str'}, { name = 'duplicate', type = 'str'} ] } ]",
        # test duplicate artifact output parameters
        "plugins = [ { path = 'tasks.py', tasks = { artifacts = [ { name = 'duplicate' }, { name = 'duplicate' } ] } } ]",
    ],
)
def test_resource_import_duplicate_names_fail(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    resources_import_config: str,
):
    group_id = auth_account["groups"][0]["id"]
    with NamedTemporaryFile(suffix=".toml", delete=False) as f:
        f.write(resources_import_config.encode("utf-8"))
        f.seek(0)
        files = select_one_or_more_files([f.name], renames={f.name: "dioptra.toml"})
        assert_resource_import_fails_due_to_duplicate_names(
            dioptra_client, group_id, files
        )
