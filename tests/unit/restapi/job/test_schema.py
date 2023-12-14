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
from typing import Any, BinaryIO, Dict

import pytest
import structlog
from structlog.stdlib import BoundLogger
from werkzeug.datastructures import FileStorage

from dioptra.restapi.job.schema import JobSchema
from dioptra.restapi.models import Job

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pytest.fixture
def job_schema() -> JobSchema:
    return JobSchema()


def test_JobSchema_create(
    job_schema: JobSchema,
) -> None:
    assert isinstance(job_schema, JobSchema)


def test_JobSchema_load_works(
    job_schema: JobSchema,
    workflow_tar_gz: BinaryIO,
) -> None:
    job = job_schema.load(
        {
            "experimentName": "mnist",
            "queue": "tensorflow_cpu",
            "timeout": "12h",
            "workflow": FileStorage(
                stream=workflow_tar_gz, filename="workflows.tar.gz", name="workflow"
            ),
            "entryPoint": "main",
            "entryPointKwargs": "-P var1=testing",
            "dependsOn": None,
        }
    )

    assert job["experiment_name"] == "mnist"
    assert job["queue"] == "tensorflow_cpu"
    assert job["timeout"] == "12h"
    assert job["workflow"].filename == "workflows.tar.gz"
    assert job["workflow"].name == "workflow"
    assert job["entry_point"] == "main"
    assert job["entry_point_kwargs"] == "-P var1=testing"
    assert job["depends_on"] is None


def test_JobSchema_dump_works(
    job_schema: JobSchema,
) -> None:
    job: Job = Job(
        job_id="4520511d-678b-4966-953e-af2d0edcea32",
        mlflow_run_id="a82982a795824afb926e646277eda152",
        experiment_id=1,
        queue_id=2,
        created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        timeout="12h",
        workflow_uri="s3://workflow/workflows.tar.gz",
        entry_point="main",
        entry_point_kwargs="-P var1=testing",
        depends_on="0c30644b-df51-4a8b-b745-9db07ce57f72",
        status="finished",
    )
    job_serialized: Dict[str, Any] = job_schema.dump(job)

    assert job_serialized["jobId"] == "4520511d-678b-4966-953e-af2d0edcea32"
    assert job_serialized["mlflowRunId"] == "a82982a795824afb926e646277eda152"
    assert job_serialized["experimentId"] == 1
    assert job_serialized["queueId"] == 2
    assert job_serialized["createdOn"] == "2020-08-17T18:46:28.717559"
    assert job_serialized["lastModified"] == "2020-08-17T18:46:28.717559"
    assert job_serialized["timeout"] == "12h"
    assert job_serialized["workflowUri"] == "s3://workflow/workflows.tar.gz"
    assert job_serialized["entryPoint"] == "main"
    assert job_serialized["entryPointKwargs"] == "-P var1=testing"
    assert job_serialized["dependsOn"] == "0c30644b-df51-4a8b-b745-9db07ce57f72"
    assert job_serialized["status"] == "finished"
