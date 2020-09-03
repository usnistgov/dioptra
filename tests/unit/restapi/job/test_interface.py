import datetime

import pytest
import structlog
from structlog._config import BoundLoggerLazyProxy

from mitre.securingai.restapi.job.interface import (
    JobInterface,
    JobSubmitInterface,
    JobUpdateInterface,
)
from mitre.securingai.restapi.job.model import Job
from mitre.securingai.restapi.shared.job_queue.model import JobQueue, JobStatus

LOGGER: BoundLoggerLazyProxy = structlog.get_logger()


@pytest.fixture
def job_interface() -> JobInterface:
    return JobInterface(
        job_id="4520511d-678b-4966-953e-af2d0edcea32",
        created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        queue=JobQueue.tensorflow_cpu,
        timeout="12h",
        workflow_uri="s3://workflow/workflows.tar.gz",
        entry_point="main",
        entry_point_kwargs="-P var1=testing",
        depends_on=None,
    )


@pytest.fixture
def job_create_interface() -> JobSubmitInterface:
    return JobSubmitInterface(
        queue=JobQueue.tensorflow_cpu,
        timeout="12h",
        workflow_uri="s3://workflow/workflows.tar.gz",
        entry_point="main",
        entry_point_kwargs="-P var1=testing",
        depends_on="0c30644b-df51-4a8b-b745-9db07ce57f72",
    )


@pytest.fixture
def job_update_interface() -> JobUpdateInterface:
    return JobUpdateInterface(status=JobStatus.started)


def test_JobInterface_create(job_interface: JobInterface) -> None:
    assert isinstance(job_interface, dict)


def test_JobCreateInterface_create(job_create_interface: JobSubmitInterface) -> None:
    assert isinstance(job_create_interface, dict)


def test_JobUpdateInterface_create(job_update_interface: JobUpdateInterface) -> None:
    assert isinstance(job_update_interface, dict)


def test_JobInterface_works(job_interface: JobInterface) -> None:
    job: Job = Job(**job_interface)
    assert isinstance(job, Job)


def test_JobCreateInterface_works(job_create_interface: JobSubmitInterface) -> None:
    job: Job = Job(**job_create_interface)
    assert isinstance(job, Job)


def test_JobUpdateInterface_works(job_update_interface: JobUpdateInterface) -> None:
    job: Job = Job(**job_update_interface)
    assert isinstance(job, Job)
