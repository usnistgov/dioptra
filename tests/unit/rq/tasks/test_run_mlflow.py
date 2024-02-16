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
import subprocess
from pathlib import Path

import rq
import structlog
from _pytest.monkeypatch import MonkeyPatch
from botocore.client import BaseClient
from freezegun import freeze_time
from structlog.stdlib import BoundLogger

from dioptra.rq.tasks import run_mlflow_task

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class MockRQJob(object):
    def get_id(self) -> str:
        LOGGER.info("Mocking rq.job.Job.get_id() function")
        return "4520511d-678b-4966-953e-af2d0edcea32"


class MockCompletedProcess(object):
    def __init__(self, *args, **kwargs) -> None:
        LOGGER.info(
            "Mocking subprocess.CompletedProcess instance", args=args, kwargs=kwargs
        )
        self.args = kwargs.get("args")
        self.cwd = kwargs.get("cwd")

    @property
    def returncode(self) -> int:
        LOGGER.info("Mocking CompletedProcess.returncode attribute")
        return 0


@freeze_time("2020-08-17T19:46:28.717559")
def test_run_mlflow_task(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    s3_stubbed_workflow_plugins: tuple[BaseClient, dict[str, dict[str, bytes]]],
) -> None:
    s3, bucket_info = s3_stubbed_workflow_plugins

    def mockgetcurrentjob(*args, **kwargs) -> MockRQJob:
        LOGGER.info("Mocking rq.get_current_job() function", args=args, kwargs=kwargs)
        return MockRQJob()

    def mockrun(*args, **kwargs) -> MockCompletedProcess:
        LOGGER.info("Mocking subprocess.run() function", args=args, kwargs=kwargs)
        return MockCompletedProcess(*args, **kwargs)

    d: Path = tmp_path / "run_mlflow_task"
    d.mkdir(parents=True)

    # S3 downloader ought to create this directory automatically
    tmp_plugins_dir = tmp_path / "plugins"

    monkeypatch.setenv("DIOPTRA_WORKDIR", str(d))
    monkeypatch.setenv("DIOPTRA_PLUGIN_DIR", str(tmp_plugins_dir))
    monkeypatch.setenv("DIOPTRA_PLUGINS_S3_URI", "s3://plugins/dioptra_builtins")
    monkeypatch.setenv("DIOPTRA_CUSTOM_PLUGINS_S3_URI", "s3://plugins/dioptra_custom")
    monkeypatch.setenv("MLFLOW_S3_ENDPOINT_URL", "http://example.org/")
    monkeypatch.setattr(rq, "get_current_job", mockgetcurrentjob)

    workflow_key = next(iter(bucket_info["workflow"]))
    workflow_s3_uri = f"s3://workflow/{workflow_key}"

    with monkeypatch.context() as m:
        m.setattr(subprocess, "run", mockrun)
        p = run_mlflow_task(
            workflow_uri=workflow_s3_uri,
            entry_point="main",
            experiment_id="0",
            conda_env="base",
            entry_point_kwargs="-P var1=testing",
            s3=s3,
        )

    assert p.returncode == 0
    assert p.args == [
        "/usr/local/bin/run-mlflow-job.sh",
        "--s3-workflow",
        workflow_s3_uri,
        "--entry-point",
        "main",
        "--conda-env",
        "base",
        "--experiment-id",
        "0",
        "-P",
        "var1=testing",
    ]
    assert Path(p.cwd).parent == d

    # Can't test the downloaded workflow tarball... it is downloaded to a temp
    # directory which is deleted after use.  So it has already disappeared.

    for key, value in bucket_info["plugins"].items():
        local_file = tmp_plugins_dir / key

        assert local_file.exists()
        assert local_file.read_bytes() == value
