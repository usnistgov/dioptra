import datetime
from typing import Any, Dict

import pytest
import structlog
from _pytest.monkeypatch import MonkeyPatch
from flask import Flask
from freezegun import freeze_time
from structlog._config import BoundLoggerLazyProxy

from mitre.securingai.restapi.job.model import Job
from mitre.securingai.restapi.job.routes import BASE_ROUTE as JOB_BASE_ROUTE
from mitre.securingai.restapi.job.service import JobService
from mitre.securingai.restapi.shared.job_queue.model import JobQueue, JobStatus

LOGGER: BoundLoggerLazyProxy = structlog.get_logger()


@pytest.fixture
def job_submit_request() -> Dict[str, Any]:
    return {
        "queue": "tensorflow_cpu",
        "timeout": "12h",
        "workflowUri": "s3://workflow/workflows.tar.gz",
        "entryPoint": "main",
        "entryPointKwargs": "-P var1=testing",
    }


@freeze_time("2020-08-17T18:46:28.717559")
def test_job_resource_post(
    app: Flask,
    job_submit_request: Dict[str, Any],
    monkeypatch: MonkeyPatch,
) -> None:
    def mocksubmit(*args, **kwargs) -> Job:
        LOGGER.info("Mocking JobService.submit()")
        timestamp = datetime.datetime.now()
        return Job(
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

    monkeypatch.setattr(JobService, "submit", mocksubmit)

    with app.test_client() as client:
        response: Dict[str, Any] = client.post(
            f"/api/{JOB_BASE_ROUTE}/", json=job_submit_request
        ).get_json()

        expected: Dict[str, Any] = {
            "jobId": "4520511d-678b-4966-953e-af2d0edcea32",
            "createdOn": "2020-08-17T18:46:28.717559",
            "lastModified": "2020-08-17T18:46:28.717559",
            "queue": "tensorflow_cpu",
            "timeout": "12h",
            "workflowUri": "s3://workflow/workflows.tar.gz",
            "entryPoint": "main",
            "entryPointKwargs": "-P var1=testing",
            "dependsOn": None,
            "status": "queued",
        }

        assert response == expected


def test_job_id_resource_get(
    app: Flask,
    monkeypatch: MonkeyPatch,
) -> None:
    def mockgetbyid(self, jobId: str, *args, **kwargs) -> Job:
        LOGGER.info("Mocking JobService.get_by_id()")
        job: Job = Job(
            job_id=jobId,
            created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
            queue=JobQueue.tensorflow_cpu,
            timeout="12h",
            workflow_uri="s3://workflow/workflows.tar.gz",
            entry_point="main",
            depends_on=None,
            status=JobStatus.queued,
        )
        return job

    monkeypatch.setattr(JobService, "get_by_id", mockgetbyid)
    job_id: str = "4520511d-678b-4966-953e-af2d0edcea32"

    with app.test_client() as client:
        response: Dict[str, Any] = client.get(f"/api/{JOB_BASE_ROUTE}/{job_id}").get_json()

        expected: Dict[str, Any] = {
            "jobId": "4520511d-678b-4966-953e-af2d0edcea32",
            "createdOn": "2020-08-17T18:46:28.717559",
            "lastModified": "2020-08-17T18:46:28.717559",
            "queue": "tensorflow_cpu",
            "timeout": "12h",
            "workflowUri": "s3://workflow/workflows.tar.gz",
            "entryPoint": "main",
            "entryPointKwargs": None,
            "dependsOn": None,
            "status": "queued",
        }

        assert response == expected
