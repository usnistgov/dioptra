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
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urlparse

import mlflow.artifacts
import mlflow.entities
import mlflow.exceptions
import structlog
from mlflow.tracking import MlflowClient
from structlog.stdlib import BoundLogger
from upath import UPath

from dioptra.restapi.errors import EntityDoesNotExistError, JobStoreError

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@dataclass
class ArtifactFile:
    relative_path: str
    file_size: int | None
    is_dir: bool


class JobRunStoreProtocol(Protocol):
    def get_metrics(self, run_id: str | None) -> list[dict[str, Any]]:
        """Retrieve the metrics for a particular run using its id.

        Args:
            run_id: the run id to for which metrics should be retrieved, an empty list
                is returned if None is provided

        Returns:
            A list of metrics for the job.

        Raises:
            EntityDoesNotExistError if a provided run id does not exist
        """
        ...

    def get_metric_history(
        self, run_id: str, name: str, page_index: int, page_length: int
    ) -> tuple[list[dict[str, Any]], int]:
        """Retrieve the metrics for a particular run using its id.

        Args:
            run_id: the run id to for which metrics should be retrieved
            name: the name of the metric to retrieve the history of
            page_index: the index of the page to retrieve
            page_length: the length of each page, will be the maximum size of the list
                returned

        Returns:
            A tuple with the first element the historical values for the metric at the
            requested page, and the second element the total number of historical values
            for the given metric
        """
        ...

    def log_metric(
        self, run_id: str, name: str, value: float, step: int | None
    ) -> None:
        """Log the metrics for a particular run using its id.

        Args:
            run_id: the run id for which to log the metric
            name: the name of the metric to log
            value: the metric value to log
            step: the job step if provided

        Raises:
            EntityDoesNotExistError if the provided run id does not exist
        """
        ...

    def download_artifacts(
        self, artifact_uri: str, path: str | None, destination: Path
    ) -> Path:
        """Retrieve an logged artifact by URI.

        Args:
            artifact_uri: the uri
            path: A valid path for the artifact if it is a directory. The file or
            directory indicated by the path will returned instead of all of the files
            pointed to by the artifact. If None, all files are returned for the
            artifact.
            destination: the path to where the files should be stored
        """
        ...

    def get_artifact_file_list(
        self, base_uri: str, subfolder_path: str
    ) -> list[ArtifactFile]:
        """
        Retrieve the list of files contained within an artifact.

        Args:
            base_uri: the base URI under which to list artifacts
            subfolder_path: the local path to the artifact file

        Returns:
            a list of ArtifactFiles.

        Raises:
            JobStoreError: If the artifact is not found in the JobStore.
        """
        ...

    def find_artifact(self, run_id: str, uri: str) -> ArtifactFile:
        """Find an artifact within the provided run.

        Args:
            run_id: the run id to search
            uri: uri of the artifact to search for

        Returns:
            Information about the file or directory indicated by the uri

        Raises:
            EntityDoesNotExistError if the provided run id does not exist
            JobStoreError if an error occurs while searching
        """
        ...


class MlFlowJobRunStore:
    def __init__(self, client: MlflowClient):
        self._client = client

    def get_metrics(self, run_id: str | None) -> list[dict[str, Any]]:
        metrics = []
        if run_id is not None:
            try:
                run = self._client.get_run(run_id)
                metrics = [
                    {"name": metric, "value": run.data.metrics[metric]}
                    for metric in run.data.metrics.keys()
                ]
            except mlflow.exceptions.MlflowException as e:
                raise EntityDoesNotExistError("MLFLowRun", run_id=run_id) from e
        return metrics

    def log_metric(
        self, run_id: str, name: str, value: float, step: int | None
    ) -> None:
        # this is here just to raise an error if the run does not exist
        try:
            self._client.get_run(run_id)  # noqa: F841
        except mlflow.exceptions.MlflowException as e:
            raise EntityDoesNotExistError("MlFlowRun", run_id=run_id) from e

        try:
            self._client.log_metric(
                run_id,
                key=name,
                value=value,
                step=step,
            )
        except mlflow.exceptions.MlflowException as e:
            raise JobStoreError(e.message) from e

    def get_metric_history(
        self, run_id: str, name: str, page_index: int, page_length: int
    ) -> tuple[list[dict[str, Any]], int]:
        try:
            history = self._client.get_metric_history(run_id=run_id, key=name)
        except mlflow.exceptions.MlflowException as e:
            raise JobStoreError(e.message) from e

        if history == []:
            raise EntityDoesNotExistError("Metric", name=name)

        metrics_page = [
            {
                "name": metric.key,
                "value": metric.value,
                "step": metric.step,
                "timestamp": metric.timestamp,
            }
            for metric in history[
                page_index * page_length : (page_index + 1) * page_length
            ]
        ]
        return metrics_page, len(history)

    def download_artifacts(
        self, artifact_uri: str, path: str | None, destination: Path
    ) -> Path:
        log: BoundLogger = LOGGER.new()
        log.debug("downloading artifacts", artifact_uri=artifact_uri, path=path)
        if path:
            root_path = (UPath(artifact_uri) / path).as_posix()
        else:
            root_path = artifact_uri

        result = mlflow.artifacts.download_artifacts(
            artifact_uri=root_path, dst_path=str(destination)
        )
        return Path(result)

    def get_artifact_file_list(
        self, base_uri: str, subfolder_path: str
    ) -> list[ArtifactFile]:
        """
        A function for retrieving the list of files contained within an artifact.

        Args:
            base_uri: the base URI under which to list artifacts
            subfolder_path: the local path to the artifact file

        Returns:
            a list of ArtifactFiles.

        Raises:
            JobStoreError: If the artifact is not found in MLFlow.
        """
        contents: list[ArtifactFile] = []

        artifact_list = mlflow.artifacts.list_artifacts(artifact_uri=base_uri)
        if artifact_list is None:
            raise JobStoreError(
                f'An artifact file with path "{base_uri}" does not exist in MLFlow.'
            )
        # If it is empty, it means it is a directory with no contents
        if len(artifact_list) == 0:
            contents.append(
                ArtifactFile(relative_path=subfolder_path, file_size=None, is_dir=True)
            )

        for artifact in artifact_list:
            base_name = Path(artifact.path).name
            if artifact.is_dir:
                # Recurse into the subdirectory
                contents.extend(
                    self.get_artifact_file_list(
                        base_uri=Path(base_uri, base_name).as_posix(),
                        subfolder_path=Path(subfolder_path, base_name).as_posix(),
                    )
                )
            else:
                # Else it is a file
                contents.append(
                    ArtifactFile(
                        relative_path=Path(subfolder_path, base_name).as_posix(),
                        file_size=artifact.file_size,
                        is_dir=False,
                    )
                )
        return contents

    def _mflow_run_artifacts(
        self, mlflow_run_id: str, base_path: str | None, log: BoundLogger
    ) -> list[mlflow.entities.FileInfo]:
        try:
            artifact_list = self._client.list_artifacts(
                run_id=mlflow_run_id, path=base_path
            )
            if artifact_list is None:
                raise JobStoreError(
                    f"No artifacts are associated with the provided MLFlow run "
                    f"id: {mlflow_run_id}"
                )
            return artifact_list
        except (
            mlflow.exceptions.RestException,
            mlflow.exceptions.MlflowException,
        ) as e:
            log.error(f"{e}")
            raise JobStoreError(f"{e}") from e

    def find_artifact(self, run_id: str, uri: str) -> ArtifactFile:
        log: BoundLogger = LOGGER.new()
        # raise an error if the run does not exist
        try:
            self._client.get_run(run_id)
        except mlflow.exceptions.MlflowException as e:
            raise EntityDoesNotExistError("MlFlowRun", run_id=run_id) from e

        # mflow run id should be an element in the uri path
        # depending on the uri format is likely not stable
        parsed_uri = urlparse(uri)
        elements = parsed_uri.path.split("/")

        try:
            index = elements.index(run_id)
        except ValueError:
            raise JobStoreError(
                f"The specified artifact uri {uri} is not part of MLFlow run "
                f"id: {run_id}"
            ) from None

        if len(elements) < (index + 2) or elements[index + 1] != "artifacts":
            raise JobStoreError(
                f"The specified artifact uri {uri} is formatted unexpectedly."
            )
        uri_path = "/".join(elements[index + 2 :])
        base_path = None
        if index + 2 < (len(elements) - 1):
            base_path = "/".join(elements[index + 2 : -1])

        artifact_list = self._mflow_run_artifacts(
            mlflow_run_id=run_id, base_path=base_path, log=log
        )
        artifact: mlflow.entities.FileInfo
        for artifact in artifact_list:
            if artifact.path == uri_path:
                return ArtifactFile(
                    relative_path=artifact.path,
                    file_size=artifact.file_size,
                    is_dir=artifact.is_dir,
                )
        else:
            raise JobStoreError(
                f"The specified artifact uri {uri} is not part of MLFlow run "
                f"id: {run_id}"
            )
