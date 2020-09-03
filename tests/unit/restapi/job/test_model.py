import datetime

import pytest
import structlog
from structlog._config import BoundLoggerLazyProxy

from mitre.securingai.restapi.job.model import Job
from mitre.securingai.restapi.shared.job_queue.model import JobQueue, JobStatus

LOGGER: BoundLoggerLazyProxy = structlog.get_logger()


@pytest.fixture
def job() -> Job:
    return Job(
        job_id="4520511d-678b-4966-953e-af2d0edcea32",
        created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        queue=JobQueue.tensorflow_cpu,
        timeout="12h",
        workflow_uri="s3://workflow/workflows.tar.gz",
        entry_point="main",
        entry_point_kwargs="-P var1=testing",
        depends_on=None,
        status=JobStatus.queued,
    )


def test_Job_create(job: Job) -> None:
    assert isinstance(job, Job)
