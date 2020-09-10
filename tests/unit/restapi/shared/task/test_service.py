import datetime
import subprocess
from pathlib import Path

import rq
import pytest
import structlog
from _pytest.monkeypatch import MonkeyPatch
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from freezegun import freeze_time
from structlog._config import BoundLoggerLazyProxy

import mitre.securingai.restapi
import mitre.securingai.restapi.app
from mitre.securingai.restapi.job.model import Job
from mitre.securingai.restapi.shared.job_queue.model import JobQueue, JobStatus
from mitre.securingai.restapi.shared.task.service import run_mlflow_task


LOGGER: BoundLoggerLazyProxy = structlog.get_logger()


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


@pytest.fixture
@freeze_time("2020-08-17T18:46:28.717559")
def job(db: SQLAlchemy) -> Job:
    timestamp: datetime.datetime = datetime.datetime.now()

    job: Job = Job(
        job_id="4520511d-678b-4966-953e-af2d0edcea32",
        created_on=timestamp,
        last_modified=timestamp,
        queue=JobQueue.tensorflow_cpu,
        timeout="12h",
        workflow_uri="s3://workflow/workflows.tar.gz",
        entry_point="main",
        entry_point_kwargs="-P var1=testing",
        depends_on=None,
        status=JobStatus.queued,
    )

    db.session.add(job)
    db.session.commit()

    return job


@freeze_time("2020-08-17T19:46:28.717559")
def test_run_mlflow_task(
    job: Job,
    app: Flask,
    db: SQLAlchemy,
    monkeypatch: MonkeyPatch,
    tmp_path: Path,  # noqa
) -> None:
    def mockgetcurrentjob(*args, **kwargs) -> MockRQJob:
        LOGGER.info("Mocking rq.get_current_job() function", args=args, kwargs=kwargs)
        return MockRQJob()

    def mockrun(*args, **kwargs) -> MockCompletedProcess:
        LOGGER.info("Mocking subprocess.run() function", args=args, kwargs=kwargs)
        return MockCompletedProcess(*args, **kwargs)

    job_id: str = job.job_id
    job_initial_status: JobStatus = job.status
    d: Path = tmp_path / "run_mlflow_task"
    d.mkdir(parents=True)

    monkeypatch.setenv("AI_WORKDIR", str(d))
    monkeypatch.setattr(rq, "get_current_job", mockgetcurrentjob)

    with monkeypatch.context() as m:
        m.setattr(subprocess, "run", mockrun)
        p = run_mlflow_task(
            workflow_uri=job.workflow_uri,
            entry_point=job.entry_point,
            conda_env="base",
            entry_point_kwargs=job.entry_point_kwargs,
        )

    result: Job = Job.query.get(job_id)

    assert p.returncode == 0
    assert p.args == [
        "/usr/local/bin/run-mlflow-job.sh",
        "--s3-workflow",
        "s3://workflow/workflows.tar.gz",
        "--entry-point",
        "main",
        "--conda-env",
        "base",
        "-P",
        "var1=testing",
    ]
    assert Path(p.cwd).parent == d
    assert result.status == job_initial_status
