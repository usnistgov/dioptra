import datetime
from dataclasses import dataclass
from typing import List

import pytest
import structlog
from _pytest.monkeypatch import MonkeyPatch
from flask_sqlalchemy import SQLAlchemy
from freezegun import freeze_time
from structlog._config import BoundLoggerLazyProxy

from mitre.securingai.restapi.job.model import Job
from mitre.securingai.restapi.job.service import JobService
from mitre.securingai.restapi.shared.job_queue.model import JobQueue, JobStatus
from mitre.securingai.restapi.shared.job_queue.service import RQService


LOGGER: BoundLoggerLazyProxy = structlog.get_logger()


@dataclass
class MockRQJob(object):
    id: str

    def get_id(self) -> str:
        return self.id


@pytest.fixture
def new_job() -> Job:
    return Job(
        queue=JobQueue.tensorflow_cpu,
        timeout="12h",
        workflow_uri="s3://workflow/workflows.tar.gz",
        entry_point="main",
        entry_point_kwargs="-P var1=testing",
        depends_on=None,
    )


@pytest.fixture
def job_service(dependency_injector) -> JobService:
    return dependency_injector.get(JobService)


@freeze_time("2020-08-17T18:46:28.717559")
def test_get_all(db: SQLAlchemy, job_service: JobService):  # noqa
    timestamp: datetime.datetime = datetime.datetime.now()

    new_job1 = Job(
        job_id="4520511d-678b-4966-953e-af2d0edcea32",
        created_on=timestamp,
        last_modified=timestamp,
        queue=JobQueue.tensorflow_cpu,
        timeout="2d",
        workflow_uri="s3://workflow/workflows.tar.gz",
        entry_point="main",
        entry_point_kwargs="-P var1=testing",
        depends_on=None,
    )

    new_job2 = Job(
        job_id="0c30644b-df51-4a8b-b745-9db07ce57f72",
        created_on=timestamp,
        last_modified=timestamp,
        queue=JobQueue.tensorflow_gpu,
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
    db: SQLAlchemy,  # noqa
    new_job: Job,
    job_service: JobService,
    monkeypatch: MonkeyPatch,
) -> None:
   def mocksubmit(*args, **kwargs) -> MockRQJob:
      LOGGER.info("Mocking RQService.submit_mlflow_job()")
      return MockRQJob(id="4520511d-678b-4966-953e-af2d0edcea32")

   monkeypatch.setattr(RQService, "submit_mlflow_job", mocksubmit)

   job_service.submit(new_job=new_job)
   results: List[Job] = Job.query.all()

   assert len(results) == 1
   assert results[0].job_id == "4520511d-678b-4966-953e-af2d0edcea32"
   assert results[0].created_on == datetime.datetime(2020, 8, 17, 18, 46, 28, 717559)
   assert results[0].last_modified == datetime.datetime(2020, 8, 17, 18, 46, 28, 717559)
   assert results[0].queue == JobQueue.tensorflow_cpu
   assert results[0].timeout == "12h"
   assert results[0].workflow_uri == "s3://workflow/workflows.tar.gz"
   assert results[0].entry_point == "main"
   assert results[0].entry_point_kwargs == "-P var1=testing"
   assert results[0].depends_on is None
   assert results[0].status == JobStatus.queued
