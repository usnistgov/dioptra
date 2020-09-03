from __future__ import annotations

import datetime
import uuid
from typing import Any, Dict, Optional, Union

import rq
import pytest
import structlog
from _pytest.monkeypatch import MonkeyPatch
from freezegun import freeze_time
from structlog._config import BoundLoggerLazyProxy

from mitre.securingai.restapi.job.model import Job
from mitre.securingai.restapi.shared.job_queue.model import JobQueue, JobStatus
from mitre.securingai.restapi.shared.job_queue.service import RQService


LOGGER: BoundLoggerLazyProxy = structlog.get_logger()


class MockRQJob(object):
    def __init__(
        self,
        id: str = "4520511d-678b-4966-953e-af2d0edcea32",
        queue: Optional[str] = None,
        timeout: Optional[str] = None,
        cmd_kwargs: Optional[Dict[str, Any]] = None,
        depends_on: Optional[Union[str, MockRQJob]] = None,
    ) -> None:
        LOGGER.info("Mocking rq.job.Job instance", id=id, queue=queue, timeout=timeout, cmd_kwargs=cmd_kwargs, depends_on=depends_on)
        self.queue = queue
        self.timeout = timeout
        self.cmd_kwargs = cmd_kwargs
        self._id = id
        self._dependency_ids = None

        if depends_on is not None:
            self._dependency_ids = [depends_on.id if isinstance(depends_on, MockRQJob) else depends_on]

    @classmethod
    def fetch(cls, id: str, *args, **kwargs) -> MockRQJob:
        LOGGER.info("Mocking rq.job.Job.fetch() function", id=id, args=args, kwargs=kwargs)
        return cls(id=id)

    def get_id(self) -> str:
        LOGGER.info("Mocking rq.job.Job.get_id() function")
        return self._id

    def get_status(self) -> str:
        LOGGER.info("Mocking rq.job.Job.get_status() function")
        return "started"

    @property
    def id(self) -> str:
        LOGGER.info("Mocking rq.job.Job.id getter")
        return self._id

    @id.setter
    def id(self, value: str) -> None:
        LOGGER.info("Mocking rq.job.Job.id setter", value=value)
        self._id = value

    @property
    def dependency(self) -> Optional[MockRQJob]:
        LOGGER.info("Mocking rq.job.Job.dependency getter")
        if not self._dependency_ids:
            return None

        return self.fetch(self._dependency_ids[0])


class MockRQQueue(object):
    def __init__(self, *args, **kwargs):
        LOGGER.info("Mocking rq.Queue instance", args=args, kwargs=kwargs)
        self.name = kwargs.get("name") or args[0]
        self.default_timeout = kwargs.get("default_timeout")

    def enqueue(self, *args, **kwargs) -> MockRQJob:
        LOGGER.info("Mocking rq.Queue.enqueue() function", args=args, kwargs=kwargs)
        cmd_kwargs = kwargs.get("kwargs")
        depends_on = kwargs.get("depends_on")
        timeout = kwargs.get("timeout")
        return MockRQJob(queue=self.name, timeout=timeout, cmd_kwargs=cmd_kwargs, depends_on=depends_on)


@pytest.fixture
def rq_service(dependency_injector, monkeypatch: MonkeyPatch) -> RQService:
    monkeypatch.setattr(rq.job, "Job", MockRQJob)
    monkeypatch.setattr(rq, "Queue", MockRQQueue)
    monkeypatch.setattr(rq.queue, "Queue", MockRQQueue)
    return dependency_injector.get(RQService)


@freeze_time("2020-08-17T18:46:28.717559")
def test_get_rq_job(rq_service: RQService):  # noqa
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
        status=JobStatus.started,
    )

    rq_job = rq_service.get_rq_job(job=job)

    assert rq_job.get_id() == "4520511d-678b-4966-953e-af2d0edcea32"
    assert rq_job.get_status() == "started"


@freeze_time("2020-08-17T18:46:28.717559")
def test_submit_mlflow_job(rq_service: RQService):  # noqa
    rq_job = rq_service.submit_mlflow_job(
        queue=JobQueue.tensorflow_cpu,
        timeout="12h",
        workflow_uri="s3://workflow/workflows.tar.gz",
        entry_point="main",
        entry_point_kwargs="-P var1=test",
        depends_on=None,
    )

    assert rq_job.queue == JobQueue.tensorflow_cpu.name
    assert rq_job.timeout == "12h"
    assert rq_job.cmd_kwargs == {
        "workflow_uri": "s3://workflow/workflows.tar.gz",
        "entry_point": "main",
        "entry_point_kwargs": "-P var1=test",
    }

@freeze_time("2020-08-17T18:46:28.717559")
def test_submit_dependent_mlflow_jobs(rq_service: RQService):  # noqa
    train_job_id: str = str(uuid.uuid4())
    fgm_job_id: str = str(uuid.uuid4())

    rq_train_job = rq_service.submit_mlflow_job(
        queue=JobQueue.tensorflow_cpu,
        timeout="2d",
        workflow_uri="s3://workflow/workflows.tar.gz",
        entry_point="train",
        entry_point_kwargs=None,
        depends_on=None,
    )
    rq_train_job.id = train_job_id

    rq_fgm_job = rq_service.submit_mlflow_job(
        queue=JobQueue.tensorflow_cpu,
        timeout="12h",
        workflow_uri="s3://workflow/workflows.tar.gz",
        entry_point="fgm",
        entry_point_kwargs=None,
        depends_on=rq_train_job.get_id(),
    )
    rq_fgm_job.id = fgm_job_id

    assert rq_train_job.get_id() == train_job_id
    assert rq_train_job.timeout == "2d"
    assert rq_train_job.cmd_kwargs == {
        "workflow_uri": "s3://workflow/workflows.tar.gz",
        "entry_point": "train",
    }
    assert rq_train_job.dependency is None

    assert rq_fgm_job.get_id() == fgm_job_id
    assert rq_fgm_job.timeout == "12h"
    assert rq_fgm_job.cmd_kwargs == {
        "workflow_uri": "s3://workflow/workflows.tar.gz",
        "entry_point": "fgm",
    }
    assert isinstance(rq_fgm_job.dependency, MockRQJob)
    assert rq_fgm_job.dependency.get_id() == train_job_id
