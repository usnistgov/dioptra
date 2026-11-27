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
"""Test suite for model operations.

This module contains a set of tests that validate the CRUD operations and additional
functionalities for the model entity. The tests ensure that the models can be
registered, renamed, deleted, and locked/unlocked as expected through the REST API.
"""

import tarfile
import tempfile
from http import HTTPStatus
from pathlib import Path
from typing import Any, cast
from urllib.parse import parse_qs, urlsplit
from uuid import UUID

import mlflow
import pytest
from pytest import MonkeyPatch
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from dioptra.client.base import DioptraResponseProtocol, StatusCodeError
from dioptra.client.client import DioptraClient
from dioptra.restapi.db import models
from dioptra.restapi.v1.shared import job_run_store

from ..lib import helpers, mock_mlflow
from ..test_utils import assert_retrieving_resource_works, assert_searchable_field_works

# -- Assertions ------------------------------------------------------------------------


def assert_artifact_response_contents_matches_expectations(
    response: dict[str, Any],
    expected_contents: dict[str, Any],
) -> None:
    """Assert that artifact response contents is valid.

    Args:
        response: The actual response from the API.
        expected_contents: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response or if the response contents is not
            valid.
    """
    expected_keys = {
        "id",
        "snapshot",
        "group",
        "user",
        "createdOn",
        "snapshotCreatedOn",
        "lastModifiedOn",
        "latestSnapshot",
        "hasDraft",
        "tags",
        "description",
        "task",
        "isDir",
        "fileSize",
        "fileUrl",
        "artifactPath",
        "job",
        "deleted",
    }
    assert set(response.keys()) == expected_keys

    # Validate the non-Ref fields
    assert isinstance(response["id"], int)
    assert isinstance(response["snapshot"], int)
    assert isinstance(response["createdOn"], str)
    assert isinstance(response["snapshotCreatedOn"], str)
    assert isinstance(response["lastModifiedOn"], str)
    assert isinstance(response["latestSnapshot"], bool)
    assert isinstance(response["hasDraft"], bool)
    assert isinstance(response["description"], str)
    assert isinstance(response["isDir"], bool)
    assert response["fileSize"] is None or isinstance(response["fileSize"], int)
    assert isinstance(response["fileUrl"], str)
    assert isinstance(response["artifactPath"], str)
    assert isinstance(response["job"], int)
    assert isinstance(response["deleted"], bool)

    assert response["artifactPath"] == expected_contents["artifactPath"]
    assert response["description"] == expected_contents["description"]
    assert response["isDir"] == expected_contents["isDir"]
    assert response["job"] == expected_contents["job"]

    assert helpers.is_iso_format(response["createdOn"])
    assert helpers.is_iso_format(response["snapshotCreatedOn"])
    assert helpers.is_iso_format(response["lastModifiedOn"])

    # Validate the UserRef structure
    assert isinstance(response["user"]["id"], int)
    assert isinstance(response["user"]["username"], str)
    assert isinstance(response["user"]["url"], str)
    assert response["user"]["id"] == expected_contents["user_id"]

    # Validate the GroupRef structure
    assert isinstance(response["group"]["id"], int)
    assert isinstance(response["group"]["name"], str)
    assert isinstance(response["group"]["url"], str)
    assert response["group"]["id"] == expected_contents["group_id"]

    # Validate the TagRef structure
    for tag in response["tags"]:
        assert isinstance(tag["id"], int)
        assert isinstance(tag["name"], str)
        assert isinstance(tag["url"], str)

    # validate the task structure
    for attribute, value in expected_contents["task"].items():
        assert attribute in response["task"]
        assert response["task"][attribute] == value


def assert_retrieving_artifact_by_id_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    artifact_id: int,
    expected: dict[str, Any],
) -> None:
    """Assert that retrieving a artifact by id works.

    Args:
        client: The Flask test client.
        artifact_id: The id of the artifact to retrieve.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = dioptra_client.artifacts.get_by_id(artifact_id)
    response_data = response.json()
    assert response.status_code == HTTPStatus.OK and response_data == expected


def assert_retrieving_artifacts_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    expected: list[dict[str, Any]],
    group_id: int | None = None,
    sort_by: str | None = None,
    descending: bool | None = None,
    search: str | None = None,
    paging_info: dict[str, Any] | None = None,
) -> None:
    """Assert that retrieving all artifacts works.

    Args:
        client: The Flask test client.
        expected: The expected response from the API.
        group_id: The group ID used in query parameters.
        search: The search string used in query parameters.
        paging_info: The paging information used in query parameters.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """

    assert_retrieving_resource_works(
        dioptra_client=dioptra_client.artifacts,
        expected=expected,
        group_id=group_id,
        sort_by=sort_by,
        descending=descending,
        search=search,
        paging_info=paging_info,
    )


def assert_registering_existing_artifact_path_fails(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    artifact_path: str,
    group_id: int,
    job_id: int,
) -> None:
    """Assert that registering an artifact with an existing path fails.

    Args:
        client: The Flask test client.
        artifact_path: The artifact_path to assign to the new artifact.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = dioptra_client.artifacts.create(
        group_id=group_id, job_id=job_id, artifact_path=artifact_path, description=""
    )
    assert response.status_code == HTTPStatus.CONFLICT


def get_artifact_artifact_task_contents(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    registered_artifact_plugins: dict[str, Any],
    plugin_name: str | None,
    task_index: int | None,
) -> dict[str, Any]:
    if plugin_name is not None:
        plugin = registered_artifact_plugins[plugin_name]
        plugin_response = dioptra_client.plugins.get_by_id(plugin["plugin_id"]).json()
        return {
            **plugin["plugin_file"]["tasks"]["artifacts"][task_index],
            "pluginResourceId": plugin_response["id"],
            "pluginResourceSnapshotId": plugin_response["snapshot"],
            "pluginFileResourceId": plugin["plugin_file"]["id"],
            "pluginFileResourceSnapshotId": plugin["plugin_file"]["snapshot"],
        }
    else:
        return {}


# -- Tests -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    "job_name, artifact_name, plugin_name, task_index",
    [
        ("job1", "artifact1", None, None),
        ("job2", "artifact3", "artifact_plugin", 0),
    ],
)
def test_create_artifact(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_jobs: dict[str, Any],
    registered_artifact_plugins: dict[str, Any],
    mlflow_artifact_paths: dict[str, str],
    job_name: str,
    artifact_name: str,
    plugin_name: str | None,
    task_index: int | None,
) -> None:
    """Test that artifacts can be correctly registered and retrieved using the API.

    Given an authenticated user and an existing path that has been logged to mlflow
    for the given job, this test validates the following sequence of actions:

    - The user registers an artifact by its run-relative path.
    - The response is valid matches the expected values given the registration request.
    - The user is able to retrieve information about the artifact using the artifact id.
    """
    description = "The first artifact."
    job_id = registered_jobs[job_name]["id"]
    user_id = auth_account["id"]
    group_id = auth_account["groups"][0]["id"]
    artifact_path = mlflow_artifact_paths[artifact_name]
    task_contents = get_artifact_artifact_task_contents(
        dioptra_client, registered_artifact_plugins, plugin_name, task_index
    )
    artifact_response = dioptra_client.artifacts.create(
        group_id=group_id,
        job_id=job_id,
        artifact_path=artifact_path,
        plugin_snapshot_id=task_contents.get("pluginResourceSnapshotId", None),
        task_id=task_contents.get("id", None),
        description=description,
    )

    artifact_expected = artifact_response.json()

    assert_artifact_response_contents_matches_expectations(
        response=artifact_expected,
        expected_contents={
            "artifactPath": artifact_path,
            "description": description,
            "user_id": user_id,
            "group_id": group_id,
            "job": job_id,
            "isDir": False,
            "task": task_contents,
        },
    )
    assert_retrieving_artifact_by_id_works(
        dioptra_client, artifact_id=artifact_expected["id"], expected=artifact_expected
    )


def test_register_artifact_with_missing_mlflow_run_returns_not_found(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_jobs: dict[str, Any],
    registered_mlflowrun: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify artifact registration reports an unavailable run as not found.

    The job has a persisted run association, but the tracking server cannot
    retrieve that run. The API reports the missing run without registering
    an artifact it cannot verify.
    """

    def missing_run(
        self: mock_mlflow.MockMlflowClient, run_id: str
    ) -> mock_mlflow.MockMlflowRun:
        """Raise the tracking error for a previously assigned run ID.

        Args:
            self: The test tracking client receiving the lookup.
            run_id: The run requested by the artifact service.

        Raises:
            MlflowException: The test scenario simulates a missing run.
        """
        raise mlflow.exceptions.MlflowException("Run not found")

    monkeypatch.setattr(mock_mlflow.MockMlflowClient, "get_run", missing_run)

    response = dioptra_client.artifacts.create(
        group_id=auth_account["groups"][0]["id"],
        job_id=registered_jobs["job1"]["id"],
        artifact_path="model v1.artifact",
        description="artifact with missing run",
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()["error"] == "MlflowRunNotFoundError"
    assert response.json()["detail"] == {}
    assert "Failed to locate mlflow run" in response.json()["message"]


def test_artifact_locations_keep_the_producing_run_after_reset(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db_session: Session,
    registered_artifacts: dict[str, Any],
    mockup_mlflow: mock_mlflow.MockMlflowClient,
) -> None:
    """A job can publish the same filename again after a development reset.

    Both artifacts should remain accessible, each from the run that produced it.
    Other files uploaded in the first run should share its storage directory.
    """
    first = registered_artifacts["artifact1"]
    second = registered_artifacts["artifact2"]
    first_location = db_session.get(models.ArtifactLocation, first["id"])
    second_location = db_session.get(models.ArtifactLocation, second["id"])
    assert first_location is not None and second_location is not None
    original_prefix = first_location.storage_prefix_id
    assert second_location.storage_prefix_id == original_prefix

    new_run = mockup_mlflow.create_run("0")
    binding = db_session.get(models.JobMlflowRun, first["job"])
    assert binding is not None
    binding.mlflow_run_id = UUID(new_run.info.run_id)
    db_session.commit()
    mlflow.start_run(new_run.info.run_id)
    mlflow.log_artifact(first["artifactPath"], artifact_path=None)
    mlflow.end_run()
    response = dioptra_client.artifacts.create(
        group_id=first["group"]["id"],
        job_id=first["job"],
        artifact_path=first["artifactPath"],
    )
    assert response.status_code == HTTPStatus.OK
    replacement = response.json()
    new_location = db_session.get(models.ArtifactLocation, replacement["id"])
    assert new_location is not None
    assert first_location.storage_prefix_id == original_prefix
    assert new_location.storage_prefix_id != original_prefix
    assert new_location.relative_path == first_location.relative_path

    snapshot = dioptra_client.artifacts.snapshots.get_by_id(
        first["id"], snapshot_id=first["snapshot"]
    )
    assert snapshot.status_code == HTTPStatus.OK
    assert snapshot.json()["artifactPath"] == first["artifactPath"]

    search = f'artifactPath:"{first["artifactPath"]}"'
    matches = dioptra_client.artifacts.get(search=search, sort_by="artifactPath").json()
    assert {artifact["id"] for artifact in matches["data"]} == {
        first["id"],
        registered_artifacts["artifact4"]["id"],
        replacement["id"],
    }


def test_failed_first_registration_preserves_no_storage_prefix(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db_session: Session,
    auth_account: dict[str, Any],
    registered_jobs: dict[str, Any],
    mlflow_artifact_paths: dict[str, str],
) -> None:
    """A task ID alone cannot identify the plugin that knows how to read a file.

    Rejecting that registration should leave no record of the file or its run
    directory, even though the upload to MLflow succeeded.
    """
    response = dioptra_client.artifacts.create(
        group_id=auth_account["groups"][0]["id"],
        job_id=registered_jobs["job1"]["id"],
        artifact_path=mlflow_artifact_paths["artifact1"],
        task_id=1,
    )
    assert response.status_code >= HTTPStatus.BAD_REQUEST
    assert (
        db_session.scalar(select(func.count()).select_from(models.ArtifactLocation))
        == 0
    )
    assert (
        db_session.scalar(
            select(func.count()).select_from(models.ArtifactStoragePrefix)
        )
        == 0
    )


def test_artifacts_get_all(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_artifacts: dict[str, Any],
) -> None:
    """Test that all artifacts can be retrieved.

    Given an authenticated user and registered artifacts, this test validates the
    following sequence of actions:

    - A user registers three artifacts with uris
        - "s3://bucket/model_v1.artifact"
        - "s3://bucket/cnn.artifact"
        - "s3://bucket/model.artifact"
        - "s3://bucket/model_v2.artifact"
    - The user is able to retrieve a list of all registered artifacts.
    - The returned list of artifacts matches the full list of registered artifacts.
    """
    artifacts_expected_list = list(registered_artifacts.values())
    assert_retrieving_artifacts_works(dioptra_client, expected=artifacts_expected_list)


def test_artifact_get_by_snapshot_id(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_artifacts: dict[str, Any],
) -> None:
    """Test that artifacts can be queried by snapshot id.

    Given an authenticated user and registered artifacts, this test validates the
    following sequence of actions:

    - The user is able to retrieve registered artifacts by their snapshot id.
    """
    for artifact in registered_artifacts.values():
        response = dioptra_client.artifacts.snapshots.get_by_id(
            artifact["id"], snapshot_id=artifact["snapshot"]
        ).json()
        assert response["id"] == artifact["id"]
        assert response["snapshot"] == artifact["snapshot"]


def test_artifact_snapshot_search_uses_the_requested_resource(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    registered_artifacts: dict[str, Any],
) -> None:
    """Searching one artifact’s history should match only its own file path.

    A path belonging to a different artifact should return an empty page.
    """
    artifact = registered_artifacts["artifact1"]
    other_path = registered_artifacts["artifact2"]["artifactPath"]
    for path, expected in (
        (artifact["artifactPath"], [artifact["snapshot"]]),
        (other_path, []),
    ):
        response = dioptra_client.artifacts.snapshots.get(
            artifact["id"], search=f'artifactPath:"{path}"'
        )
        assert response.status_code == HTTPStatus.OK
        page = response.json()
        assert page["totalNumResults"] == len(expected)
        assert [snapshot["snapshot"] for snapshot in page["data"]] == expected


@pytest.mark.parametrize(
    "field, value, expected_count",
    [
        ("artifactPath", None, 2),
        ("description", None, 1),
        ("tag", "Foo", 0),
    ],
)
def test_artifact_searchable_fields(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_artifacts: dict[str, Any],
    field: str,
    value: str | None,
    expected_count: int,
) -> None:
    artifact = registered_artifacts["artifact1"]
    search_value = artifact[field] if value is None else value
    assert_searchable_field_works(
        dioptra_client=dioptra_client.artifacts,
        term=field,
        value=search_value,
        expected_count=expected_count,
    )


@pytest.mark.parametrize(
    "sort_by, descending , expected",
    [
        ("id", True, ["artifact4", "artifact3", "artifact2", "artifact1"]),
        ("id", False, ["artifact1", "artifact2", "artifact3", "artifact4"]),
        ("description", True, ["artifact2", "artifact1", "artifact4", "artifact3"]),
        ("description", False, ["artifact3", "artifact4", "artifact1", "artifact2"]),
        ("createdOn", True, ["artifact4", "artifact3", "artifact2", "artifact1"]),
        ("createdOn", False, ["artifact1", "artifact2", "artifact3", "artifact4"]),
    ],
)
def test_artifact_sort(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    mockup_mlflow,
    auth_account: dict[str, Any],
    registered_artifacts: dict[str, Any],
    sort_by: str,
    descending: bool,
    expected: list[str],
) -> None:
    """Test that artifacts can be sorted by column.

    Given an authenticated user and registered artifacts, this test validates the
    following sequence of actions:

    - A user registers four artifacts with distinct descriptions and a repeated path:
        "Model artifact.",
        "Trained conv net model artifact.",
        "Another model",
        "Fine-tuned model.".
    - The user is able to retrieve a list of all registered artifacts sorted by a column
    - The returned list of artifacts matches the order in the parametrize lists above.
    """

    expected_queues = [
        registered_artifacts[expected_name] for expected_name in expected
    ]
    assert_retrieving_artifacts_works(
        dioptra_client, sort_by=sort_by, descending=descending, expected=expected_queues
    )


def test_artifact_search_query(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_artifacts: dict[str, Any],
) -> None:
    """Test that artifacts can be queried with a search term.

    Given an authenticated user and registered artifacts, this test validates the
    following sequence of actions:

    - The user is able to retrieve a list of all registered artifacts with 'artifact' in
        their description.
    - The returned list of artifacts matches the expected matches from the query.
    """
    artifacts_expected_list = list(registered_artifacts.values())[:2]
    assert_retrieving_artifacts_works(
        dioptra_client,
        expected=artifacts_expected_list,
        search="description:*artifact*",
    )


def test_artifact_group_query(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_artifacts: dict[str, Any],
) -> None:
    """Test that artifacts can retrieved using a group filter.

    Given an authenticated user and registered artifacts, this test validates the
    following sequence of actions:

    - The user is able to retrieve a list of all registered artifacts that are owned by
      the default group.
    - The returned list of artifacts matches the expected list owned by the default
      group.
    """
    artifacts_expected_list = list(registered_artifacts.values())
    assert_retrieving_artifacts_works(
        dioptra_client,
        expected=artifacts_expected_list,
        group_id=auth_account["groups"][0]["id"],
    )


def test_cannot_register_existing_artifact_path(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_artifacts: dict[str, Any],
) -> None:
    """Test that registering a artifact with an existing path fails.

    Given an authenticated user and registered artifacts, this test validates the
    following sequence of actions:

    - The user attempts to register a second artifact with the same path.
    - The request fails with an appropriate error message and response code.
    """
    existing_artifact = registered_artifacts["artifact1"]
    assert_registering_existing_artifact_path_fails(
        dioptra_client,
        artifact_path=existing_artifact["artifactPath"],
        group_id=existing_artifact["group"]["id"],
        job_id=existing_artifact["job"],
    )


def test_modify_artifact(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_artifacts: dict[str, Any],
    registered_artifact_plugins: dict[str, Any],
) -> None:
    """Test that an artifact can be modified.

    Given an authenticated user and registered artifact, this test validates the
    following sequence of actions:

    - The user issues a request to change the description, plugin_id and task_id of the
      artifact task for the artifact
    - The user retrieves information about the same artifact and it reflects
      the changes.
    """
    task_contents = get_artifact_artifact_task_contents(
        dioptra_client, registered_artifact_plugins, "artifact_plugin", 0
    )
    artifact_to_modify = registered_artifacts["artifact2"]
    response = dioptra_client.artifacts.modify_by_id(
        artifact_id=artifact_to_modify["id"],
        plugin_snapshot_id=task_contents["pluginResourceSnapshotId"],
        task_id=task_contents["id"],
        description="New Description",
    ).json()

    assert_artifact_response_contents_matches_expectations(
        response=response,
        expected_contents={
            "artifactPath": artifact_to_modify["artifactPath"],
            "description": "New Description",
            "user_id": artifact_to_modify["user"]["id"],
            "group_id": artifact_to_modify["group"]["id"],
            "job": artifact_to_modify["job"],
            "isDir": artifact_to_modify["isDir"],
            "task": task_contents,
        },
    )


def test_get_contents(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_artifacts: dict[str, Any],
) -> None:
    """A download must close the server's file before removing its temporary copy.

    Windows prevents deletion while the file is open. The client should receive
    the complete contents, and closing the response should leave no server files.
    """
    server_temp = tmp_path / "server"
    server_temp.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(server_temp))
    contents = dioptra_client.artifacts.get_contents(
        artifact_id=registered_artifacts["artifact1"]["id"], output_dir=tmp_path
    )
    assert contents.read_bytes() == b"test contents"
    assert not list(server_temp.iterdir())


def test_get_file_listing(
    tmp_path: Path,
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_jobs: dict[str, Any],
    registered_mlflowrun: dict[str, Any],
    mockup_mlflow: mock_mlflow.MockMlflowClient,
) -> None:
    """A user can list a directory and download a nested file by its original name.

    Spaces, Unicode letters, and a percent sign should survive both a snapshot
    download and a download of the complete directory as an archive.
    """
    name = "résumé 測試 50%.csv"
    relative_path = f"monthly/{name}"
    mlflow.start_run(registered_mlflowrun["job1"]["mlflowRunId"])
    mlflow.log_artifact(name, artifact_path="reports/monthly")
    mlflow.end_run()
    response = dioptra_client.artifacts.create(
        group_id=auth_account["groups"][0]["id"],
        job_id=registered_jobs["job1"]["id"],
        artifact_path="reports",
    )
    assert response.status_code == HTTPStatus.OK
    artifact = response.json()
    artifact_id = artifact["id"]
    contents = cast(
        list[dict[str, Any]],
        dioptra_client.artifacts.get_files(artifact_id=artifact_id).json(),
    )

    assert len(contents) == 1
    entry = contents[0]
    assert entry["relativePath"] == relative_path
    listing_url = urlsplit(entry["fileUrl"])
    assert listing_url.path == urlsplit(artifact["fileUrl"]).path
    assert parse_qs(listing_url.query)["path"] == [relative_path]
    child = dioptra_client.artifacts.get_contents(
        artifact_id, artifact_path=entry["relativePath"], output_dir=tmp_path
    )
    assert child.read_bytes() == b"test contents"
    snapshot = dioptra_client.artifacts.snapshots.get_contents(
        artifact_id,
        artifact["snapshot"],
        artifact_path=relative_path,
        output_dir=tmp_path,
    )
    assert snapshot.read_bytes() == b"test contents"
    with pytest.raises(StatusCodeError) as invalid:
        dioptra_client.artifacts.get_contents(
            artifact_id, artifact_path=".", output_dir=tmp_path
        )
    assert invalid.value.status_code == HTTPStatus.BAD_REQUEST

    archive = dioptra_client.artifacts.get_contents(artifact_id, output_dir=tmp_path)
    with tarfile.open(archive, mode="r:gz") as bundle:
        bundled_file = bundle.extractfile(f"reports/{relative_path}")
        assert bundled_file is not None
        assert bundled_file.read() == b"test contents"


@pytest.mark.parametrize("malformed_field", ["relative_path", "relative_prefix"])
def test_invalid_snapshot_location_is_rejected_before_storage_access(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    tmp_path: Path,
    registered_artifacts: dict[str, Any],
    db_session: Session,
    monkeypatch: MonkeyPatch,
    malformed_field: str,
) -> None:
    """An invalid location in the database should stop a snapshot download.

    For example, an incomplete conversion could leave an empty filename.
    The API should report the error before asking MLflow to look up the file.
    """
    artifact = registered_artifacts["artifact1"]
    location = db_session.get(models.ArtifactLocation, artifact["id"])
    assert location is not None
    if malformed_field == "relative_prefix":
        location.storage_prefix.relative_prefix = "invalid saved prefix"
    else:
        location.relative_path = ""
    db_session.commit()

    def unexpected_repository(*args, **kwargs):
        """Fail the test if the malformed location reaches repository selection."""
        pytest.fail("An invalid stored location reached artifact storage.")

    monkeypatch.setattr(
        job_run_store, "get_mlflow_artifact_repository", unexpected_repository
    )
    with pytest.raises(StatusCodeError) as invalid:
        dioptra_client.artifacts.snapshots.get_contents(
            artifact["id"], artifact["snapshot"], output_dir=tmp_path
        )
    assert invalid.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
