# This Software (Dioptra) is being made available as a public service by the
# National Institute of Standards and Technology (NIST), an Agency of the United
# States Department of Commerce. This software was developed in part by employees of
# NIST and in part by NIST contractors. Copyright in portions of this software that
# were developed by NIST contractors has been licensed or assigned to NIST. Pursuant
# to Title 17 United States Code Section 105, works of NIST employees are not
# subject to copyright protection in the United States. However, NIST may hold
# international copyright in software created by its employees and domestic
# copyright (or licensing rights) in portions of software that were assigned or
# licensed to NIST. To the extent that NIST holds copyright in this software, it is
# being made available under the Creative Commons Attribution 4.0 International
# license (CC BY 4.0). The disclaimers of the CC BY 4.0 license apply to all parts
# of the software developed or licensed by NIST.
#
# ACCESS THE FULL CC BY 4.0 LICENSE HERE:
# https://creativecommons.org/licenses/by/4.0/legalcode
from __future__ import annotations

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
