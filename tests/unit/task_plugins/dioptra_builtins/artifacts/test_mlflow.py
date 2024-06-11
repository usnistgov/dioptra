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
from __future__ import annotations

import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import pytest
from _pytest.monkeypatch import MonkeyPatch
from mlflow.entities import Run, RunData, RunInfo, RunStatus, RunTag
from mlflow.entities.lifecycle_stage import LifecycleStage
from mlflow.tracking.fluent import ActiveRun
from mlflow.utils.mlflow_tags import (
    MLFLOW_PARENT_RUN_ID,
    MLFLOW_RUN_NAME,
    MLFLOW_RUN_NOTE,
    MLFLOW_USER,
)


def _get_run_name_from_tags(tags):
    for tag in tags:
        if tag.key == MLFLOW_RUN_NAME:
            return tag.value


class MockMLFlowClient(object):
    def __init__(
        self, tracking_uri: Optional[str] = None, registry_uri: Optional[str] = None
    ):
        pass

    def download_artifacts(
        self, run_id: str, path: str, dst_path: Optional[str] = None
    ) -> str:
        if dst_path is None:
            dst_path = "tmp_unit_test"
        dst_path = str(Path(dst_path).absolute())
        dst_local_path = dst_path
        return dst_local_path

    def log_artifact(self, run_id: str, local_path: str, artifact_path=None) -> None:
        print("REACHED")
        return None

    def create_run(self, experiment_id, start_time=56020, tags=None, run_name=None):
        tags = tags if tags else {}
        user_id = tags.get(MLFLOW_USER, "unknown")
        experiment_id = 1 if experiment_id is None else experiment_id
        tags = tags or []
        run_name_tag = _get_run_name_from_tags(tags)
        if run_name and run_name_tag and run_name != run_name_tag:
            raise Exception(
                "Both 'run_name' argument and 'mlflow.runName' tag",
                "are specified, but with ",
                f"different values (run_name='{run_name}',",
                f"mlflow.runName='{run_name_tag}').",
            )
        run_name = run_name or run_name_tag or "experiment12345"
        if not run_name_tag:
            tags.append(RunTag(key=MLFLOW_RUN_NAME, value=run_name))
        run_uuid = uuid.uuid4().hex
        artifact_uri = Path("/path/to/artifacts/") / run_uuid / "artifacts"

        run_info = RunInfo(
            run_uuid=run_uuid,
            run_id=run_uuid,
            run_name=run_name,
            experiment_id=experiment_id,
            artifact_uri=artifact_uri,
            user_id=user_id,
            status=RunStatus.to_string(RunStatus.RUNNING),
            start_time=start_time,
            end_time=None,
            lifecycle_stage=LifecycleStage.ACTIVE,
        )
        return Run(run_info, RunData(None, None, tags))


def mock_start_run(
    run_id: str = None,
    experiment_id: Optional[str] = None,
    run_name: Optional[str] = None,
    nested: bool = False,
    tags: Optional[Dict[str, Any]] = None,
    description: Optional[str] = None,
) -> ActiveRun:
    client = MockMLFlowClient()
    parent_run_id = None

    exp_id_for_run = experiment_id if experiment_id is not None else "experiment12345"
    user_specified_tags = deepcopy(tags) or {}
    if description:
        if MLFLOW_RUN_NOTE in user_specified_tags:
            raise Exception(
                f"Description is already set via the tag {MLFLOW_RUN_NOTE} in tags."
                f"Remove the key {MLFLOW_RUN_NOTE} from the tags or omit",
                "the description.",
            )
        user_specified_tags[MLFLOW_RUN_NOTE] = description
    if parent_run_id is not None:
        user_specified_tags[MLFLOW_PARENT_RUN_ID] = parent_run_id
    if run_name:
        user_specified_tags[MLFLOW_RUN_NAME] = run_name

    resolved_tags = user_specified_tags

    active_run_obj = client.create_run(
        experiment_id=exp_id_for_run, tags=resolved_tags, run_name=run_name
    )
    return ActiveRun(active_run_obj)


def mock_log_artifact(local_path: str, artifact_path: Optional[str] = None) -> None:
    run_id = "ex123456"
    MockMLFlowClient().log_artifact(run_id, local_path, artifact_path)


@pytest.fixture
def mlflow_client(monkeypatch: MonkeyPatch):
    import mlflow

    monkeypatch.setattr(mlflow.tracking, "MlflowClient", MockMLFlowClient)
    monkeypatch.setattr(mlflow.tracking.fluent, "start_run", mock_start_run)
    monkeypatch.setattr(mlflow, "log_artifact", mock_log_artifact)


@pytest.mark.parametrize(
    "run_id",
    ["ex123", "ex456", "ex621"],
)
@pytest.mark.parametrize(
    "artifact_path",
    ["path/to/file", "path/to/other_file"],
)
@pytest.mark.parametrize(
    "destination_path",
    ["path/to/file", "path/to/other/file"],
)
def test_download_all_artifacts_in_run(
    mlflow_client, run_id, artifact_path, destination_path
) -> None:
    from dioptra_builtins.artifacts.mlflow import download_all_artifacts_in_run

    dst_path = download_all_artifacts_in_run(run_id, artifact_path, destination_path)
    assert isinstance(dst_path, str)
    assert Path(destination_path) == Path(dst_path).relative_to(Path.cwd())


@pytest.mark.parametrize(
    "data_frame",
    [
        pd.DataFrame(
            [
                ["dollars", -10],
                ["books", 20],
                ["bottles", 0],
                ["frogs", -3],
                ["flies", 9],
                ["snakes", 60],
            ],
            columns=["things", "counts"],
        )
    ],
)
@pytest.mark.parametrize(
    ("file_name", "file_format", "output"),
    [
        ("pddf.csv", "csv.gz", "csv.gz"),
        ("pddf.csv", "csv", "csv"),
        ("pddf.csv", "csv.bz2", "csv.bz2"),
        ("pddf.csv", "csv.xz", "csv.xz"),
        ("pddf.json", "json", "json"),
        ("pddf.feather", "feather", "feather"),
        ("pddf.pkl", "pickle", "pkl"),
    ],
)
def test_upload_data_frame_artifact(
    mlflow_client, data_frame, file_name, file_format, output, tmp_path
) -> None:
    from dioptra_builtins.artifacts.mlflow import upload_data_frame_artifact

    upload_data_frame_artifact(data_frame, file_name, file_format, None, tmp_path)

    pwd = Path("." if tmp_path is None else tmp_path).absolute()
    assert (pwd / Path(file_name).with_suffix(f".{output}")).is_file()


@pytest.mark.parametrize(
    "source_dir",
    ["./tmp"],
)
@pytest.mark.parametrize(
    "tarball_filename",
    ["workflow.tar.gz"],
)
@pytest.mark.parametrize(
    "tarball_write_mode",
    ["w:gz"],
)
@pytest.mark.parametrize(
    "working_dir",
    [None],
)
def test_upload_directory_as_tarball_artifact(
    mlflow_client, source_dir, tarball_filename, tarball_write_mode, working_dir
) -> None:
    from dioptra_builtins.artifacts.mlflow import upload_directory_as_tarball_artifact

    Path(source_dir).mkdir(parents=True, exist_ok=True)
    fp = open(Path(source_dir) / "myfile.py", "w+")
    fp.close()
    Path(source_dir).mkdir(parents=True, exist_ok=True)
    fp = open(Path(source_dir) / "myfile2.py", "w+")
    fp.close()
    upload_directory_as_tarball_artifact(
        source_dir, tarball_filename, tarball_write_mode, working_dir
    )
    pwd = Path("." if working_dir is None else working_dir).absolute()
    assert (pwd / tarball_filename).is_file()


@pytest.mark.parametrize(
    ("working_dir", "file"),
    [
        ("./tmp_unit_test", "this.py"),
        ("./tmp_unit_tests", "test2.tar.gz"),
        ("./tmp_unit_test", "MLProject"),
    ],
)
def test_upload_file_as_artifact(mlflow_client, working_dir, file) -> None:
    from dioptra_builtins.artifacts.mlflow import upload_file_as_artifact

    Path(working_dir).mkdir(parents=True, exist_ok=True)
    fp = open(Path(working_dir) / file, "w+")
    fp.close()
    upload_file_as_artifact(Path(working_dir) / file)
