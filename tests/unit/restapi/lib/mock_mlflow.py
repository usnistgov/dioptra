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

import contextlib
import dataclasses
import time
import uuid
from pathlib import Path
from typing import Any, Optional, Tuple
from urllib.parse import urlparse

import mlflow.entities
import structlog
from structlog.stdlib import BoundLogger

LOGGER: BoundLogger = structlog.stdlib.get_logger()


PREFIX: str = "s3://dioptra-fixtures/outputs"


class MockMlflowException(Exception):
    def __init__(
        self,
        text: str,
    ) -> None:
        LOGGER.info("Mocking mlflow.exceptions.MlflowException class")
        super().__init__(text)


class MockMlflowMetric(object):
    def __init__(
        self,
        key: str,
        value: float,
        step: int,
        timestamp: int,
    ) -> None:
        LOGGER.info("Mocking mlflow.entities.Metric class")
        self._key = key
        self._value = value
        self._step = step
        self._timestamp = timestamp

    @property
    def key(self) -> str:
        LOGGER.info("Mocking mlflow.entities.Metric.key getter")
        return self._key

    @key.setter
    def key(self, value: str) -> None:
        LOGGER.info("Mocking mlflow.entities.Metric.key setter", value=value)
        self._key = value

    @property
    def value(self) -> float:
        LOGGER.info("Mocking mlflow.entities.Metric.value getter")
        return self._value

    @value.setter
    def value(self, value: float) -> None:
        LOGGER.info("Mocking mlflow.entities.Metric.value setter", value=value)
        self._value = value

    @property
    def step(self) -> int:
        LOGGER.info("Mocking mlflow.entities.Metric.step getter")
        return self._step

    @step.setter
    def step(self, value: int) -> None:
        LOGGER.info("Mocking mlflow.entities.Metric.step setter", value=value)
        self._step = value

    @property
    def timestamp(self) -> int:
        LOGGER.info("Mocking mlflow.entities.Metric.timestamp getter")
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value: int) -> None:
        LOGGER.info("Mocking mlflow.entities.Metric.timestamp setter", value=value)
        self._timestamp = value


class MockMlflowRunData(object):
    def __init__(
        self,
    ) -> None:
        LOGGER.info("Mocking mlflow.entities.RunData class")
        self._metrics: dict[str, Any] = {}
        self._metric_history: dict[str, list[MockMlflowMetric]] = {}

    @property
    def metrics(self) -> dict[str, Any]:
        LOGGER.info("Mocking mlflow.entities.RunData.metrics getter")
        return self._metrics

    def _add_metric(self, metric: MockMlflowMetric) -> None:
        self._metrics[metric.key] = metric.value
        if metric.key in self._metric_history:
            self._metric_history[metric.key].append(metric)
        else:
            self._metric_history[metric.key] = [metric]


class MockMlflowRunInfo(object):
    def __init__(
        self, run_uuid: uuid.UUID | None, run_id: str | None, experiment_id: int
    ) -> None:
        LOGGER.info("Mocking mlflow.entities.RunInfo class")
        if run_uuid:
            run_id = run_uuid.hex
        elif run_id is None:
            raise Exception("run_id and run_uuid cannot both be None")
        self._run_id: str = run_id
        self._experiment_id = experiment_id

    @property
    def run_id(self) -> str:
        LOGGER.info("Mocking mlflow.entities.RunInfo.run_id getter")
        return self._run_id

    @property
    def artifact_uri(self) -> str:
        """Return the artifact directory owned by this test run."""
        return f"{PREFIX}/{self._experiment_id}/{self._run_id}/artifacts"


@dataclasses.dataclass
class MockArtifact:
    info: mlflow.entities.FileInfo
    children: dict[str, "MockArtifact"] = dataclasses.field(default_factory=lambda: {})


class MockMlflowArtifactStore(object):
    def __init__(
        self,
        info: MockMlflowRunInfo,
    ) -> None:
        LOGGER.info("Mocking mlflow.artifacts")
        self._store: dict[str, MockArtifact] = {}
        self._info = info

    def add_artifact(self, local_path: str, artifact_path: str | None) -> None:
        # grab name from local_path and build up the uri
        path = Path(local_path)
        if artifact_path:
            file_path = f"{artifact_path}/{path.name}"
        else:
            file_path = path.name

        file_info = mlflow.entities.FileInfo(
            path=file_path, is_dir=False, file_size=100
        )
        if path.exists():
            if path.is_dir():
                file_info._is_dir = True
            else:
                file_info._bytes = path.stat().st_size

        if artifact_path:
            parent = self._get_entry(artifact_path)
            parent.children[path.name] = MockArtifact(file_info)
        else:
            self._store[path.name] = MockArtifact(file_info)

    def _get_entry(self, artifact_path: str) -> MockArtifact:
        result = None
        store = self._store
        elements = artifact_path.split("/")
        for i, e in enumerate(elements):
            if e not in store:
                store[e] = MockArtifact(
                    mlflow.entities.FileInfo(
                        path="/".join(elements[: i + 1]),
                        is_dir=True,
                        file_size=None,
                    )
                )
            result = store[e]
            store = result.children
        if result is None:
            raise Exception(f"artifact_path has invalid value: {artifact_path}")
        return result

    def get_artifact_uri(self, artifact_path: str) -> str:
        return _build_artifact_uri(
            path_prefix=PREFIX,
            experiment_id=self._info._experiment_id,
            run_id=self._info.run_id,
            artifact_path=artifact_path,
            name=None,
        )

    @property
    def artifact_uri(self) -> str:
        """Return the configured URI of the test run's repository."""
        return self.get_artifact_uri("")

    def list_artifacts(self, path: str | None = None) -> list[mlflow.entities.FileInfo]:
        """Return immediate entries of a test directory, matching MLflow listings.

        Args:
            path: Directory to list, or None for the run's artifact root.

        Returns:
            Files and subdirectories immediately below the requested directory.
        """
        children = self._store
        if path:
            for component in path.split("/"):
                entry = children.get(component)
                if entry is None or not entry.info.is_dir:
                    return []
                children = entry.children
        return [entry.info for entry in children.values()]

    def download_artifacts(self, artifact_path: str, dst_path: str) -> str:
        """Materialize one test file under its run-relative path.

        Args:
            artifact_path: Run-relative path of the selected file.
            dst_path: Local root for the materialized file.

        Returns:
            Path of the downloaded file.
        """
        output = Path(dst_path, artifact_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("test contents", encoding="UTF-8", newline="")
        return str(output)


class MockMlflowRun(contextlib.AbstractContextManager):
    def __init__(
        self, run_uuid: uuid.UUID | None, run_id: str | None, experiment_id: int | None
    ) -> None:
        LOGGER.info("Mocking mlflow.entities.Run class")
        self._data = MockMlflowRunData()
        self._info = MockMlflowRunInfo(
            run_uuid=run_uuid,
            run_id=run_id,
            experiment_id=0 if experiment_id is None else experiment_id,
        )
        self.artifacts = MockMlflowArtifactStore(self._info)

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        pass

    @property
    def id(self) -> str:
        return self._info.run_id

    @property
    def data(self) -> MockMlflowRunData:
        LOGGER.info("Mocking mlflow.entities.Run.data getter")
        return self._data

    @property
    def info(self) -> MockMlflowRunInfo:
        LOGGER.info("Mocking mlflow.entities.Run.info getter")
        return self._info


class MockState:
    registered_runs: dict[str, MockMlflowRun] = {}
    active_run: MockMlflowRun | None = None
    experiments: list[str] = []


class MockMlflowClient(object):
    def __init__(self) -> None:
        LOGGER.info(
            "Mocking mlflow.tracking.MlflowClient instance",
        )

    def create_run(self, experiment_id: str) -> MockMlflowRun:
        """Allocate a run in the test tracking store.

        Args:
            experiment_id: Numeric ID of the selected tracking experiment.

        Returns:
            The new run. Later lookups in the test store use its generated ID.
        """
        return _create_run(run_uuid=uuid.uuid4(), experiment_id=int(experiment_id))

    def delete_run(self, run_id: str) -> None:
        """Remove a run from the test tracking store.

        Args:
            run_id: ID of the run to remove.
        """
        MockState.registered_runs.pop(run_id, None)

    def get_experiment(self, experiment_id: str) -> mlflow.entities.Experiment:
        """Return the experiment rooted under the configured test bucket.

        Args:
            experiment_id: ID whose directory the tracking client should describe.

        Returns:
            Tracking metadata with the corresponding artifact root.
        """
        return mlflow.entities.Experiment(
            experiment_id, "Default", f"{PREFIX}/{experiment_id}", "active"
        )

    def get_run(self, run_id: str) -> MockMlflowRun:
        # Note: In Mlflow, this function would usually throw an MlflowException
        # if the run id is not found. For simplicity this is left out in favor of
        # assuming the run should exist in this mock instance.
        LOGGER.info("Mocking MlflowClient.get_run() function")
        if run_id in MockState.registered_runs:
            return MockState.registered_runs[run_id]
        # this is likely a problem
        LOGGER.warning(f"creating run with id {run_id}")
        return _create_run(run_id=run_id)

    def list_artifacts(
        self, run_id: str, path: str | None = None
    ) -> list[mlflow.entities.FileInfo]:
        return self.get_run(run_id).artifacts.list_artifacts(path=path)


def _create_run(
    run_uuid: uuid.UUID | None = None,
    run_id: str | None = None,
    experiment_id: int | None = None,
) -> MockMlflowRun:
    run = MockMlflowRun(run_uuid=run_uuid, run_id=run_id, experiment_id=experiment_id)
    MockState.registered_runs[run.info.run_id] = run
    return run


# mock for mlflow.create_experiment
def create_experiment(name: str) -> int:
    LOGGER.info("Mocking mlflow.create_experiment function")
    try:
        return MockState.experiments.index(name)
    except ValueError:
        MockState.experiments.append(name)
        return len(MockState.experiments)


# mock for mlflow.set_tag
def set_tag(key: str, value: Any):
    LOGGER.info("Mocking mlflow.set_tag function")
    # nothing to do at the moment -- this information is not directly used
    pass


# mock for mlflow.log_dict
def log_dict(dictionary: dict[str, Any], artifact_file: str) -> None:
    LOGGER.info("Mocking mlflow.log_dict function")
    # nothing to do at the moment -- this information is not directly used
    pass


# mock for mlflow.log_params
def log_params(params: dict[str, Any]) -> None:
    LOGGER.info("Mocking mlflow.log_params function")
    # nothing to do at the moment -- this information is not directly used
    pass


# mock for mlflow.start_run
def start_run(
    run_id: str | None = None, experiment_id: int | None = None
) -> MockMlflowRun:
    if run_id is not None:
        client = MockMlflowClient()
        run = client.get_run(run_id)
    else:
        run = _create_run(run_uuid=uuid.uuid4(), experiment_id=experiment_id)
    MockState.active_run = run
    return MockState.active_run


# mock for mlflow.end_run
def end_run(status: str | None = "FINISHED"):
    MockState.active_run = None


# mock for mlflow.log_artifact
def log_artifact(local_path: str, artifact_path: str | None) -> None:
    if MockState.active_run is None:
        raise MockMlflowException("No Active Run")
    MockState.active_run.artifacts.add_artifact(local_path, artifact_path)


# mock for mlflow.get_artifact_uri
def get_artifact_uri(artifact_path: str) -> str:
    if MockState.active_run is None:
        raise MockMlflowException("No Active Run")
    return MockState.active_run.artifacts.get_artifact_uri(artifact_path)


# the assumed uri format for MLFlow is something like:
# scheme:{path prefix}/<experiment id>/<run id>/artifacts/<artifact_path>/<name>
def _build_artifact_uri(
    path_prefix: str,
    experiment_id: int,
    run_id: str,
    artifact_path: str | None,
    name: str | None,
) -> str:
    result = f"{path_prefix}/{experiment_id}/{run_id}/artifacts"
    if artifact_path:
        result += "/" + artifact_path
    if name:
        result += "/" + name
    return result


def _parse_artifact_uri(uri: str) -> Tuple[str, str]:
    """
    Parse the Artifact URI
    Arguments:
        uri: the uri to parse

    Returns:
        a tuple with the first element is the run id and the secomde element is path
        within the artifacts directory of the artifact
    """
    parsed_uri = urlparse(uri)
    elements = parsed_uri.path.split("/")
    # raises value error if uri is not formatted as expected
    index = len(urlparse(PREFIX).path.split("/"))
    return (elements[index + 1], "/".join(elements[index + 3 :]))


def get_artifact_repository(
    artifact_uri: str, tracking_uri: str | None = None
) -> MockMlflowArtifactStore:
    """Select the test repository associated with the configured run URI.

    Args:
        artifact_uri: Configured root of the selected run.
        tracking_uri: Tracking selection supplied by the API.

    Returns:
        Test repository listing run-relative entries.
    """
    run_id, _ = _parse_artifact_uri(artifact_uri)
    return MockState.registered_runs[run_id].artifacts
