import datetime
from typing import Any, Dict

import pytest
import structlog
from structlog._config import BoundLoggerLazyProxy

from mitre.securingai.restapi.job.model import Job
from mitre.securingai.restapi.job.schema import (
    JobSchema,
    JobSubmitSchema,
)
from mitre.securingai.restapi.shared.job_queue.model import JobQueue, JobStatus

LOGGER: BoundLoggerLazyProxy = structlog.get_logger()


@pytest.fixture
def job_schema() -> JobSchema:
    return JobSchema()


@pytest.fixture
def job_submit_schema() -> JobSubmitSchema:
    return JobSubmitSchema()


def test_JobSchema_create(
    job_schema: JobSchema,
) -> None:
    assert isinstance(job_schema, JobSchema)


def test_JobSubmitSchema_create(
    job_submit_schema: JobSubmitSchema,
) -> None:
    assert isinstance(job_submit_schema, JobSubmitSchema)


def test_JobSchema_load_works(
    job_schema: JobSchema,
) -> None:
    job: Job = job_schema.load({
        "jobId": "4520511d-678b-4966-953e-af2d0edcea32",
        "createdOn": "2020-08-17T18:46:28.717559",
        "lastModified": "2020-08-17T18:46:28.717559",
        "queue": "tensorflow_cpu",
        "workflowUri": "s3://workflow/workflows.tar.gz",
        "entryPoint": "main",
        "entryPointKwargs": "-P var1=testing",
        "status": "finished",
    })

    assert job.job_id == "4520511d-678b-4966-953e-af2d0edcea32"
    assert job.created_on == datetime.datetime(2020, 8, 17, 18, 46, 28, 717559)
    assert job.last_modified == datetime.datetime(2020, 8, 17, 18, 46, 28, 717559)
    assert job.queue == JobQueue.tensorflow_cpu
    assert job.workflow_uri == "s3://workflow/workflows.tar.gz"
    assert job.entry_point == "main"
    assert job.entry_point_kwargs == "-P var1=testing"
    assert job.status == JobStatus.finished


def test_JobSubmitSchema_load_works(
    job_submit_schema: JobSubmitSchema,
) -> None:
    job: Job = job_submit_schema.load({
        "queue": "tensorflow_gpu",
        "workflowUri": "s3://workflow/workflows.tar.gz",
        "entryPoint": "main",
        "entryPointKwargs": "-P var1=testing",
    })

    assert job.queue == JobQueue.tensorflow_gpu
    assert job.workflow_uri == "s3://workflow/workflows.tar.gz"
    assert job.entry_point == "main"
    assert job.entry_point_kwargs == "-P var1=testing"


def test_JobSchema_dump_works(
    job_schema: JobSchema,
) -> None:
    job: Job = Job(
        job_id="4520511d-678b-4966-953e-af2d0edcea32",
        created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        queue=JobQueue.tensorflow_cpu,
        workflow_uri="s3://workflow/workflows.tar.gz",
        entry_point="main",
        entry_point_kwargs="-P var1=testing",
        status=JobStatus.finished,
    )
    job_serialized: Dict[str, Any] = job_schema.dump(job)

    assert job_serialized["jobId"] == "4520511d-678b-4966-953e-af2d0edcea32"
    assert job_serialized["createdOn"] == "2020-08-17T18:46:28.717559"
    assert job_serialized["lastModified"] == "2020-08-17T18:46:28.717559"
    assert job_serialized["queue"] == "tensorflow_cpu"
    assert job_serialized["workflowUri"] == "s3://workflow/workflows.tar.gz"
    assert job_serialized["entryPoint"] == "main"
    assert job_serialized["entryPointKwargs"] == "-P var1=testing"


def test_JobSubmitSchema_dump_works(
    job_submit_schema: JobSubmitSchema,
) -> None:
    job: Job = Job(
        queue=JobQueue.tensorflow_cpu,
        workflow_uri="s3://workflow/workflows.tar.gz",
        entry_point="main",
        entry_point_kwargs="-P var1=testing",
    )
    job_serialized: Dict[str, Any] = job_submit_schema.dump(job)

    assert job_serialized["queue"] == "tensorflow_cpu"
    assert job_serialized["workflowUri"] == "s3://workflow/workflows.tar.gz"
    assert job_serialized["entryPoint"] == "main"
    assert job_serialized["entryPointKwargs"] == "-P var1=testing"
