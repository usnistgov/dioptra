# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
import datetime
from typing import Any, BinaryIO, Dict

import pytest
import structlog
from flask import Flask
from structlog.stdlib import BoundLogger
from werkzeug.datastructures import FileStorage

from mitre.securingai.restapi.job.schema import JobFormSchema, JobSchema
from mitre.securingai.restapi.models import Job, JobForm

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pytest.fixture
def job_form(app: Flask, workflow_tar_gz: BinaryIO) -> JobForm:
    with app.test_request_context():
        form = JobForm(
            data={
                "experiment_name": "mnist",
                "queue": "tensorflow_gpu",
                "timeout": "12h",
                "entry_point": "main",
                "entry_point_kwargs": "-P var1=testing",
                "depends_on": "0c30644b-df51-4a8b-b745-9db07ce57f72",
                "workflow": FileStorage(
                    stream=workflow_tar_gz, filename="workflows.tar.gz", name="workflow"
                ),
            }
        )

    return form


@pytest.fixture
def job_schema() -> JobSchema:
    return JobSchema()


@pytest.fixture
def job_form_schema() -> JobFormSchema:
    return JobFormSchema()


def test_JobSchema_create(
    job_schema: JobSchema,
) -> None:
    assert isinstance(job_schema, JobSchema)


def test_JobFormSchema(
    job_form_schema: JobFormSchema,
) -> None:
    assert isinstance(job_form_schema, JobFormSchema)


def test_JobSchema_load_works(
    job_schema: JobSchema,
) -> None:
    job: Job = job_schema.load(
        {
            "jobId": "4520511d-678b-4966-953e-af2d0edcea32",
            "mlflowRunId": "a82982a795824afb926e646277eda152",
            "experimentId": 1,
            "queueId": 2,
            "createdOn": "2020-08-17T18:46:28.717559",
            "lastModified": "2020-08-17T18:46:28.717559",
            "timeout": "12h",
            "workflowUri": "s3://workflow/workflows.tar.gz",
            "entryPoint": "main",
            "entryPointKwargs": "-P var1=testing",
            "dependsOn": None,
            "status": "finished",
        }
    )

    assert job.job_id == "4520511d-678b-4966-953e-af2d0edcea32"
    assert job.mlflow_run_id == "a82982a795824afb926e646277eda152"
    assert job.experiment_id == 1
    assert job.queue_id == 2
    assert job.created_on == datetime.datetime(2020, 8, 17, 18, 46, 28, 717559)
    assert job.last_modified == datetime.datetime(2020, 8, 17, 18, 46, 28, 717559)
    assert job.timeout == "12h"
    assert job.workflow_uri == "s3://workflow/workflows.tar.gz"
    assert job.entry_point == "main"
    assert job.entry_point_kwargs == "-P var1=testing"
    assert job.depends_on is None
    assert job.status == "finished"


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


def test_JobFormSchema_dump_works(
    job_form: JobForm,
    job_form_schema: JobFormSchema,
    workflow_tar_gz: BinaryIO,
) -> None:
    job_serialized: Dict[str, Any] = job_form_schema.dump(job_form)

    assert job_serialized["experiment_name"] == "mnist"
    assert job_serialized["queue"] == "tensorflow_gpu"
    assert job_serialized["timeout"] == "12h"
    assert job_serialized["entry_point"] == "main"
    assert job_serialized["entry_point_kwargs"] == "-P var1=testing"
    assert job_serialized["depends_on"] == "0c30644b-df51-4a8b-b745-9db07ce57f72"
    assert job_serialized["workflow"].stream == workflow_tar_gz
    assert job_serialized["workflow"].filename == "workflows.tar.gz"
