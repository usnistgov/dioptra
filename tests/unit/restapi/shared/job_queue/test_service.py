import datetime
from typing import Any, Dict, Optional

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
        self, queue: Optional[str] = None, cmd_kwargs: Optional[Dict[str, Any]] = None
    ):
        LOGGER.info("Mocking rq.job.Job instance", queue=queue, cmd_kwargs=cmd_kwargs)
        self.queue = queue
        self.cmd_kwargs = cmd_kwargs

    @classmethod
    def fetch(cls, *args, **kwargs):
        LOGGER.info("Mocking rq.job.Job.fetch() function", args=args, kwargs=kwargs)
        return cls()

    def get_id(self) -> str:
        LOGGER.info("Mocking rq.job.Job.get_id() function")
        return "4520511d-678b-4966-953e-af2d0edcea32"

    def get_status(self) -> str:
        LOGGER.info("Mocking rq.job.Job.get_status() function")
        return "started"


class MockRQQueue(object):
    def __init__(self, *args, **kwargs):
        LOGGER.info("Mocking rq.Queue instance", args=args, kwargs=kwargs)
        self.name = kwargs.get("name") or args[0]

    def enqueue(self, *args, **kwargs) -> MockRQJob:
        LOGGER.info("Mocking rq.Queue.enqueue() function", args=args, kwargs=kwargs)
        cmd_kwargs = kwargs.get("kwargs")
        return MockRQJob(queue=self.name, cmd_kwargs=cmd_kwargs)


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
        workflow_uri="s3://workflow/workflows.tar.gz",
        entry_point="main",
        entry_point_kwargs="-P var1=testing",
        status=JobStatus.started,
    )

    rq_job = rq_service.get_rq_job(job=job)

    assert rq_job.get_id() == "4520511d-678b-4966-953e-af2d0edcea32"
    assert rq_job.get_status() == "started"


@freeze_time("2020-08-17T18:46:28.717559")
def test_submit_mlflow_job(rq_service: RQService):  # noqa
    rq_job = rq_service.submit_mlflow_job(
        queue=JobQueue.tensorflow_cpu,
        workflow_uri="s3://workflow/workflows.tar.gz",
        entry_point="main",
        entry_point_kwargs="-P var1=test",
    )

    assert rq_job.queue == JobQueue.tensorflow_cpu.name
    assert rq_job.cmd_kwargs == {
        "workflow_uri": "s3://workflow/workflows.tar.gz",
        "entry_point": "main",
        "entry_point_kwargs": "-P var1=test",
    }
