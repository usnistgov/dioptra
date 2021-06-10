# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
import datetime
from typing import BinaryIO

import pytest
import structlog
from structlog.stdlib import BoundLogger

from mitre.securingai.restapi.models import Job, JobFormData

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pytest.fixture
def job() -> Job:
    return Job(
        job_id="4520511d-678b-4966-953e-af2d0edcea32",
        mlflow_run_id=None,
        experiment_id=1,
        queue_id=1,
        created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        timeout="12h",
        workflow_uri="s3://workflow/workflows.tar.gz",
        entry_point="main",
        entry_point_kwargs="-P var1=testing",
        depends_on=None,
        status="queued",
    )


@pytest.fixture
def job_form_data(workflow_tar_gz: BinaryIO) -> JobFormData:
    return JobFormData(
        experiment_id=1,
        experiment_name="mnist",
        queue="tensorflow_cpu",
        timeout="12h",
        entry_point="main",
        entry_point_kwargs="-P var1=testing",
        depends_on="0c30644b-df51-4a8b-b745-9db07ce57f72",
        workflow=workflow_tar_gz,
    )


def test_Job_create(job: Job) -> None:
    assert isinstance(job, Job)


def test_JobFormData_create(job_form_data: JobFormData) -> None:
    assert isinstance(job_form_data, dict)
