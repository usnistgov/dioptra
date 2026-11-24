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
"""Allocate job runs and access artifacts through the configured MLflow store."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from urllib.parse import unquote, urlsplit

import mlflow.entities
import mlflow.exceptions
import mlflow.utils.uri
from marshmallow import ValidationError
from mlflow.store.artifact.artifact_repo import (
    ArtifactRepository as MlflowArtifactRepository,
)
from mlflow.store.artifact.artifact_repository_registry import (
    get_artifact_repository as get_mlflow_artifact_repository,
)
from mlflow.tracking import MlflowClient

from dioptra.restapi.errors import JobStoreError, MlflowRunNotFoundError
from dioptra.restapi.utils import validate_artifact_child_path, validate_artifact_path

DEFAULT_MLFLOW_EXPERIMENT_ID = "0"
RUN_PREFIX_REGEX = re.compile(
    rf"{DEFAULT_MLFLOW_EXPERIMENT_ID}/[0-9a-f]{{32}}/artifacts"
)


@dataclass
class ArtifactFile:
    """Metadata for a file or directory in an MLflow run.

    Attributes:
        relative_path: Path from the root of the requested lookup.
        file_size: Size in bytes for a file, or None for a directory.
        is_dir: Whether the entry is a directory.
    """

    relative_path: str
    file_size: int | None
    is_dir: bool


@dataclass
class UploadedArtifact(ArtifactFile):
    """A file or directory that Dioptra can register for a job.

    Attributes:
        storage_prefix: Path from the deployment storage root to the run directory.
    """

    storage_prefix: str


class JobRunStoreProtocol(Protocol):
    """Manage job runs and access artifacts identified by Dioptra locations."""

    def create_job_run(self) -> str:
        """Allocate a run for a Dioptra job.

        Returns:
            The hexadecimal ID of the new run in the Default MLflow experiment.
        """
        ...

    def delete_job_run(self, run_id: str) -> None:
        """Discard a run after its job transaction has rolled back.

        Args:
            run_id: Hexadecimal ID of the unbound MLflow run.
        """
        ...

    def download_artifacts(
        self,
        storage_prefix: str,
        artifact_path: str,
        path: str | None,
        destination: Path,
    ) -> Path:
        """Download an artifact or one entry within its registered directory.

        Args:
            storage_prefix: Run's artifact directory relative to the storage root.
            artifact_path: Canonical path of the registered file or directory.
            path: Optional child path relative to the registered directory.
            destination: Local directory for the downloaded entry.

        Returns:
            Local path of the downloaded file or directory.

        Raises:
            JobStoreError: If the location cannot be safely resolved or downloaded.
        """
        ...

    def get_artifact_file_list(
        self, storage_prefix: str, artifact_path: str
    ) -> list[ArtifactFile]:
        """Retrieve entries beneath a registered artifact directory.

        Args:
            storage_prefix: Run's artifact directory relative to the storage root.
            artifact_path: Canonical directory path within the run.

        Returns:
            File and empty-directory entries with paths relative to the artifact.

        Raises:
            JobStoreError: If the location cannot be safely resolved or listed.
        """
        ...

    def find_artifact(self, run_id: str, artifact_path: str) -> UploadedArtifact:
        """Find the uploaded entry that can be registered for this run.

        Args:
            run_id: Server-assigned MLflow run identifier.
            artifact_path: Canonical path within the producing run.

        Returns:
            The uploaded entry, including its verified run directory.

        Raises:
            MlflowRunNotFoundError: If the tracking service cannot find the run.
            JobStoreError: If the destination is invalid or the entry cannot be found.
        """
        ...


class MlFlowJobRunStore:
    """Use a configured tracking service for runs and their stored artifacts."""

    def __init__(
        self,
        client: MlflowClient,
        tracking_uri: str | None,
        artifact_base_uri: str | None,
    ):
        """Initialize the MlFlowJobRunStore object.

        Args:
            client: Client for the configured MLflow tracking service.
            tracking_uri: Tracking URI used with the MLflow artifact API.
            artifact_base_uri: Physical storage root, required for artifact operations.
        """
        self._mlflow_client = client
        self._tracking_uri = tracking_uri
        self._artifact_base_uri = artifact_base_uri

    def create_job_run(self) -> str:
        """Allocate a run for a Dioptra job.

        Returns:
            The hexadecimal ID of the new run in the Default MLflow experiment.
        """
        run = self._mlflow_client.create_run(DEFAULT_MLFLOW_EXPERIMENT_ID)
        run_id: str = run.info.run_id
        return run_id

    def delete_job_run(self, run_id: str) -> None:
        """Discard a run after its job transaction has rolled back.

        Args:
            run_id: Hexadecimal ID of the unbound MLflow run.
        """
        self._mlflow_client.delete_run(run_id)

    def download_artifacts(
        self,
        storage_prefix: str,
        artifact_path: str,
        path: str | None,
        destination: Path,
    ) -> Path:
        """Download an entry using the saved producing location.

        Args:
            storage_prefix: Run prefix associated with the artifact resource.
            artifact_path: Canonical path of the registered entry.
            path: Child path within a registered directory, if supplied.
            destination: Local directory for the downloaded entry.

        Returns:
            Local path of the downloaded entry.

        Raises:
            JobStoreError: If the location cannot be safely resolved or downloaded.
        """
        run_uri = self._get_run_uri(storage_prefix, artifact_path)
        target_path = artifact_path
        if path is not None:
            _validate_child_path(path, run_uri)
            target_path = f"{artifact_path}/{path}"

        repository = self._open_artifact_repository(run_uri)
        entry = _find_entry(repository, target_path)
        if entry.is_dir:
            return _download_directory(repository, target_path, destination)
        return _download_file(repository, target_path, destination)

    def get_artifact_file_list(
        self, storage_prefix: str, artifact_path: str
    ) -> list[ArtifactFile]:
        """List a registered directory using its saved producing location.

        Args:
            storage_prefix: Run prefix associated with the artifact resource.
            artifact_path: Canonical path to the directory within that run.

        Returns:
            Files and empty directories, with paths relative to the registered directory.

        Raises:
            JobStoreError: If the location cannot be safely resolved or listed.
        """
        run_uri = self._get_run_uri(storage_prefix, artifact_path)
        repository = self._open_artifact_repository(run_uri)
        return [
            ArtifactFile(
                entry.relative_path.removeprefix(artifact_path).removeprefix("/"),
                entry.file_size,
                entry.is_dir,
            )
            for entry in _list_artifact_files(repository, artifact_path)
        ]

    def _open_artifact_repository(self, run_uri: str) -> MlflowArtifactRepository:
        """Open a verified run root so child names stay separate from the URI."""
        try:
            return get_mlflow_artifact_repository(
                artifact_uri=run_uri, tracking_uri=self._tracking_uri
            )
        except mlflow.exceptions.MlflowException as error:
            raise JobStoreError(
                "Could not open the artifact storage location."
            ) from error

    def _get_run_uri(self, storage_prefix: str, artifact_path: str) -> str:
        """Revalidate both persisted components before assembling the run URI."""
        if not isinstance(storage_prefix, str) or not RUN_PREFIX_REGEX.fullmatch(
            storage_prefix
        ):
            raise JobStoreError("The recorded artifact storage prefix is invalid.")
        try:
            validate_artifact_path(artifact_path)
        except ValidationError as error:
            raise JobStoreError("The recorded artifact path is invalid.") from error
        return f"{self._get_artifact_root()}/{storage_prefix}"

    def _get_artifact_root(self) -> str:
        """Verify the Default experiment and select its configured access route."""
        base = self._artifact_base_uri
        if base is None:
            raise JobStoreError(
                "Set DIOPTRA_ARTIFACT_BASE_URI before accessing artifacts."
            )
        if not _is_supported_base(base):
            raise JobStoreError(
                "DIOPTRA_ARTIFACT_BASE_URI must be an absolute file or S3 URI."
            )
        base = base.rstrip("/")
        try:
            experiment = self._mlflow_client.get_experiment(
                DEFAULT_MLFLOW_EXPERIMENT_ID
            )
        except mlflow.exceptions.MlflowException as error:
            raise JobStoreError(
                "Could not verify the Default MLflow experiment."
            ) from error
        location = experiment.artifact_location

        # The proxy identifies the route only. Its physical base is supplied to
        # both services by deployment configuration.
        proxy_root = f"mlflow-artifacts:/{DEFAULT_MLFLOW_EXPERIMENT_ID}"
        if base.startswith("file:") and location == proxy_root:
            tracking = urlsplit(self._tracking_uri or "")
            if tracking.scheme not in {"http", "https"} or not tracking.netloc:
                raise JobStoreError(
                    "The MLflow artifact proxy requires an HTTP tracking URI."
                )
            return "mlflow-artifacts:"
        experiment_uri = f"{base}/{DEFAULT_MLFLOW_EXPERIMENT_ID}"
        if not _locations_match(experiment_uri, location):
            raise JobStoreError(
                "The Default MLflow experiment does not match DIOPTRA_ARTIFACT_BASE_URI."
            )
        return base

    def find_artifact(self, run_id: str, artifact_path: str) -> UploadedArtifact:
        """Match an uploaded entry to a canonical run-relative registration path.

        Args:
            run_id: Server-assigned ID of the producing run in the Default experiment.
            artifact_path: Canonical path within the run's artifact directory.

        Returns:
            The uploaded entry, including its verified run directory.

        Raises:
            MlflowRunNotFoundError: If the tracking service cannot find the run.
            JobStoreError: If the run location disagrees with deployment settings
                or the registered entry cannot be found there.
        """
        storage_prefix = f"{DEFAULT_MLFLOW_EXPERIMENT_ID}/{run_id}/artifacts"
        run_uri = self._get_run_uri(storage_prefix, artifact_path)
        try:
            run = self._mlflow_client.get_run(run_id)
        except mlflow.exceptions.MlflowException as error:
            raise MlflowRunNotFoundError(mlflow_run_id=run_id) from error

        if not _locations_match(run_uri, run.info.artifact_uri):
            raise JobStoreError(
                "The producing MLflow run has an unexpected artifact location."
            )

        repository = self._open_artifact_repository(run_uri)
        entry = _find_entry(repository, artifact_path)
        return UploadedArtifact(
            artifact_path, entry.file_size, entry.is_dir, storage_prefix
        )


def _list_directory(
    repository: MlflowArtifactRepository, path: str
) -> list[mlflow.entities.FileInfo]:
    """List a directory selected relative to the verified run root."""
    try:
        return repository.list_artifacts(path or None)
    except (mlflow.exceptions.MlflowException, ValueError) as error:
        raise JobStoreError("Could not list the artifact directory.") from error


def _find_entry(
    repository: MlflowArtifactRepository, path: str
) -> mlflow.entities.FileInfo:
    """Find an unambiguous, exact entry in the requested path's parent."""
    parent, _, _ = path.rpartition("/")
    matches = [
        entry for entry in _list_directory(repository, parent) if entry.path == path
    ]
    if len(matches) != 1:
        raise JobStoreError("The requested artifact was not found as a unique entry.")
    return matches[0]


def _list_artifact_files(
    repository: MlflowArtifactRepository, directory: str
) -> list[ArtifactFile]:
    """Verify each immediate child before following it beneath the directory."""
    entries = _list_directory(repository, directory)
    if not entries:
        return [ArtifactFile(directory, None, True)]

    contents: list[ArtifactFile] = []
    seen_paths: set[str] = set()
    for entry in entries:
        parent, _, name = entry.path.rpartition("/")
        if parent != directory or entry.path in seen_paths:
            raise JobStoreError("MLflow returned an unexpected artifact listing path.")
        seen_paths.add(entry.path)
        _validate_child_path(name, repository.artifact_uri)
        if entry.is_dir:
            contents.extend(_list_artifact_files(repository, entry.path))
        else:
            contents.append(ArtifactFile(entry.path, entry.file_size, False))
    return contents


def _download_directory(
    repository: MlflowArtifactRepository, path: str, destination: Path
) -> Path:
    """Download verified descendants while retaining the artifact's directory layout."""
    # Review entry paths before selecting any content downloads. MLflow's generic
    # directory download follows its backend's listing without this directory check.
    for entry in _list_artifact_files(repository, path):
        if entry.is_dir:
            (destination / entry.relative_path).mkdir(parents=True, exist_ok=True)
        else:
            _download_file(repository, entry.relative_path, destination)
    return destination / path


def _download_file(
    repository: MlflowArtifactRepository, path: str, destination: Path
) -> Path:
    """Ask MLflow to materialize a selected file in the response directory."""
    try:
        downloaded = repository.download_artifacts(  # type: ignore[no-untyped-call]
            path, str(destination)
        )
        result = Path(downloaded).resolve()
    except (mlflow.exceptions.MlflowException, ValueError) as error:
        raise JobStoreError("Could not download the registered artifact.") from error
    if not result.is_relative_to(destination.resolve()):
        raise JobStoreError("MLflow returned a path outside the response directory.")
    if not result.is_file():
        raise JobStoreError("MLflow did not return the selected artifact file.")
    return result


def _is_supported_base(base: str) -> bool:
    """Identify a usable configured file or S3 base without contacting storage."""
    try:
        parsed = urlsplit(base)
    except ValueError:
        return False
    if parsed.query or parsed.fragment or any(c in base for c in "\r\n\t"):
        return False
    if parsed.scheme == "file":
        return not parsed.netloc and parsed.path.startswith("/")
    if parsed.scheme == "s3":
        return bool(re.fullmatch(r"[a-z0-9.-]+", parsed.netloc))
    return False


def _locations_match(expected: str, actual: str) -> bool:
    """Compare MLflow metadata without using it as an artifact request address."""
    if expected.startswith("file:"):
        expected_path = unquote(urlsplit(expected).path)
        try:
            parsed = urlsplit(actual)
        except ValueError:
            return False
        # Local tracking stores may publish an absolute path or a file URI.
        if parsed.netloc or parsed.query or parsed.fragment:
            return False
        if parsed.scheme == "file":
            return unquote(parsed.path) == expected_path
        return actual == expected_path
    return expected == actual


def _validate_child_path(path: str, repository_uri: str) -> None:
    """Keep child names literal on the selected storage route.

    S3 uses the path as an object key. MLflow decodes file and proxy paths,
    and proxy file downloads place the path in the HTTP request URL.
    """
    try:
        validate_artifact_child_path(path)
        if repository_uri.startswith("s3:"):
            return
        decoded_path = mlflow.utils.uri.validate_path_is_safe(path)  # type: ignore[no-untyped-call]
        if decoded_path != path:
            raise ValueError("MLflow would change the child path.")
        if (
            repository_uri.startswith(("mlflow-artifacts:", "http:", "https:"))
            and "?" in path
        ):
            raise ValueError("The child path would change the proxy URL query.")
    except (ValueError, mlflow.exceptions.MlflowException) as error:
        raise JobStoreError(
            "The artifact child path is invalid for its storage route."
        ) from error
