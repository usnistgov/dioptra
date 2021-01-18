import datetime
from dataclasses import dataclass
from typing import BinaryIO, List, Optional

import pytest
import structlog
from _pytest.monkeypatch import MonkeyPatch
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from freezegun import freeze_time
from structlog.stdlib import BoundLogger
from werkzeug.datastructures import FileStorage

from mitre.securingai.restapi.job.service import JobService
from mitre.securingai.restapi.models import Job, JobFormData
from mitre.securingai.restapi.shared.rq.service import RQService
from mitre.securingai.restapi.shared.s3.service import S3Service

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@dataclass
class MockRQJob(object):
    id: str

    def get_id(self) -> str:
        return self.id


@pytest.fixture
def new_job() -> Job:
    return Job(
        experiment_id=1,
        queue_id=1,
        timeout="12h",
        workflow_uri="s3://workflow/workflows.tar.gz",
        entry_point="main",
        entry_point_kwargs="-P var1=testing",
        depends_on=None,
    )


@pytest.fixture
def job_form_data(app: Flask, workflow_tar_gz: BinaryIO) -> JobFormData:
    return JobFormData(
        experiment_name="mnist",
        experiment_id=1,
        queue_id=1,
        queue="tensorflow_cpu",
        timeout="12h",
        entry_point="main",
        entry_point_kwargs="-P var1=testing",
        depends_on=None,
        workflow=FileStorage(
            stream=workflow_tar_gz, filename="workflows.tar.gz", name="workflow"
        ),
    )


@pytest.fixture
def job_service(dependency_injector) -> JobService:
    return dependency_injector.get(JobService)


def test_create(job_service: JobService, job_form_data: JobFormData):
    job: Job = job_service.create(job_form_data=job_form_data)

    assert job.experiment_id == 1
    assert job.queue_id == 1
    assert job.timeout == "12h"
    assert job.entry_point == "main"
    assert job.entry_point_kwargs == "-P var1=testing"
    assert job.depends_on is None


@freeze_time("2020-08-17T18:46:28.717559")
def test_get_all(db: SQLAlchemy, job_service: JobService):
    timestamp: datetime.datetime = datetime.datetime.now()

    new_job1 = Job(
        job_id="4520511d-678b-4966-953e-af2d0edcea32",
        mlflow_run_id=None,
        experiment_id=1,
        queue_id=1,
        created_on=timestamp,
        last_modified=timestamp,
        timeout="2d",
        workflow_uri="s3://workflow/workflows.tar.gz",
        entry_point="main",
        entry_point_kwargs="-P var1=testing",
        depends_on=None,
    )

    new_job2 = Job(
        job_id="0c30644b-df51-4a8b-b745-9db07ce57f72",
        mlflow_run_id=None,
        experiment_id=1,
        queue_id=2,
        created_on=timestamp,
        last_modified=timestamp,
        timeout="12h",
        workflow_uri="s3://workflow/workflows.tar.gz",
        entry_point="second",
        depends_on="4520511d-678b-4966-953e-af2d0edcea32",
    )

    db.session.add(new_job1)
    db.session.add(new_job2)
    db.session.commit()

    results: List[Job] = job_service.get_all()

    assert len(results) == 2
    assert new_job1 in results and new_job2 in results


@freeze_time("2020-08-17T18:46:28.717559")
def test_submit(
    db: SQLAlchemy,
    job_service: JobService,
    job_form_data: JobFormData,
    monkeypatch: MonkeyPatch,
) -> None:
    def mocksubmit(*args, **kwargs) -> MockRQJob:
        LOGGER.info("Mocking RQService.submit_mlflow_job()")
        return MockRQJob(id="4520511d-678b-4966-953e-af2d0edcea32")

    def mockupload(
        self, fileobj: BinaryIO, bucket: str, key: str, *args, **kwargs
    ) -> Optional[str]:
        LOGGER.info(
            "Mocking S3Service.upload() function",
            fileobj=fileobj,
            bucket=bucket,
            key=key,
        )
        return "s3://workflow/3db4050001b145a4ae1864e7d1bc7e9a/workflows.tar.gz"

    monkeypatch.setattr(RQService, "submit_mlflow_job", mocksubmit)
    monkeypatch.setattr(S3Service, "upload", mockupload)

    job_service.submit(job_form_data=job_form_data)
    results: List[Job] = Job.query.all()

    assert len(results) == 1
    assert results[0].job_id == "4520511d-678b-4966-953e-af2d0edcea32"
    assert results[0].queue_id == 1
    assert results[0].mlflow_run_id is None
    assert results[0].experiment_id == 1
    assert results[0].created_on == datetime.datetime(2020, 8, 17, 18, 46, 28, 717559)
    assert results[0].last_modified == datetime.datetime(
        2020, 8, 17, 18, 46, 28, 717559
    )
    assert results[0].timeout == "12h"
    assert (
        results[0].workflow_uri
        == "s3://workflow/3db4050001b145a4ae1864e7d1bc7e9a/workflows.tar.gz"
    )
    assert results[0].entry_point == "main"
    assert results[0].entry_point_kwargs == "-P var1=testing"
    assert results[0].depends_on is None
    assert results[0].status == "queued"
