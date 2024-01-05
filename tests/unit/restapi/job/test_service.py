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
from dataclasses import dataclass
from typing import Any, BinaryIO, List, Optional

import pytest
import structlog
from _pytest.monkeypatch import MonkeyPatch
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from freezegun import freeze_time
from structlog.stdlib import BoundLogger
from werkzeug.datastructures import FileStorage

from dioptra.restapi.job.service import JobService
from dioptra.restapi.models import Experiment, Job
from dioptra.restapi.shared.rq.service import RQService
from dioptra.restapi.shared.s3.service import S3Service

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@dataclass
class MockRQJob(object):
    id: str

    def get_id(self) -> str:
        return self.id


@pytest.fixture
@freeze_time("2020-08-17T18:46:28.717559")
def new_experiment(db: SQLAlchemy) -> Experiment:
    timestamp: datetime.datetime = datetime.datetime.now()
    new_experiment: Experiment = Experiment(
        experiment_id=1,
        name="mnist",
        created_on=timestamp,
        last_modified=timestamp,
    )
    db.session.add(new_experiment)
    db.session.commit()
    return new_experiment


@pytest.fixture
def new_job() -> Job:
    return Job(
        experiment_id=1,
        queue_id=1,
        timeout="12h",
        workflow_uri="s3://workflow/workflows.tar.gz",
        entry_point="main",
        entry_point_kwargs="-P var1=testing",
        depends_on=None,
    )


@pytest.fixture
def job_submission_data(app: Flask, workflow_tar_gz: BinaryIO) -> dict[str, Any]:
    return {
        "experiment_name": "mnist",
        "queue_name": "tensorflow_cpu",
        "timeout": "12h",
        "entry_point": "main",
        "entry_point_kwargs": "-P var1=testing",
        "depends_on": None,
        "workflow": FileStorage(
            stream=workflow_tar_gz, filename="workflows.tar.gz", name="workflow"
        ),
    }


@pytest.fixture
def job_service(dependency_injector) -> JobService:
    return dependency_injector.get(JobService)


@freeze_time("2020-08-17T18:46:28.717559")
def test_get_all(db: SQLAlchemy, job_service: JobService):
    timestamp: datetime.datetime = datetime.datetime.now()

    new_job1 = Job(
        job_id="4520511d-678b-4966-953e-af2d0edcea32",
        mlflow_run_id=None,
        experiment_id=1,
        queue_id=1,
        created_on=timestamp,
        last_modified=timestamp,
        timeout="2d",
        workflow_uri="s3://workflow/workflows.tar.gz",
        entry_point="main",
        entry_point_kwargs="-P var1=testing",
        depends_on=None,
    )

    new_job2 = Job(
        job_id="0c30644b-df51-4a8b-b745-9db07ce57f72",
        mlflow_run_id=None,
        experiment_id=1,
        queue_id=2,
        created_on=timestamp,
        last_modified=timestamp,
        timeout="12h",
        workflow_uri="s3://workflow/workflows.tar.gz",
        entry_point="second",
        depends_on="4520511d-678b-4966-953e-af2d0edcea32",
    )

    db.session.add(new_job1)
    db.session.add(new_job2)
    db.session.commit()

    results: List[Job] = job_service.get_all()

    assert len(results) == 2
    assert new_job1 in results and new_job2 in results


@freeze_time("2020-08-17T18:46:28.717559")
def test_submit(
    db: SQLAlchemy,
    new_experiment: Experiment,
    job_service: JobService,
    job_submission_data: dict[str, Any],
    monkeypatch: MonkeyPatch,
) -> None:
    def mocksubmit(*args, **kwargs) -> MockRQJob:
        LOGGER.info("Mocking RQService.submit_mlflow_job()")

    def mockupload(
        self, fileobj: BinaryIO, bucket: str, key: str, *args, **kwargs
    ) -> Optional[str]:
        LOGGER.info(
            "Mocking S3Service.upload() function",
            fileobj=fileobj,
            bucket=bucket,
            key=key,
        )
        return "s3://workflow/3db4050001b145a4ae1864e7d1bc7e9a/workflows.tar.gz"

    monkeypatch.setattr(RQService, "submit_mlflow_job", mocksubmit)
    monkeypatch.setattr(S3Service, "upload", mockupload)

    job_service.create(**job_submission_data)
    results: List[Job] = Job.query.all()

    assert len(results) == 1
    assert results[0].queue_id == 1
    assert results[0].mlflow_run_id is None
    assert results[0].experiment_id == 1
    assert results[0].created_on == datetime.datetime(2020, 8, 17, 18, 46, 28, 717559)
    assert results[0].last_modified == datetime.datetime(
        2020, 8, 17, 18, 46, 28, 717559
    )
    assert results[0].timeout == "12h"
    assert (
        results[0].workflow_uri
        == "s3://workflow/3db4050001b145a4ae1864e7d1bc7e9a/workflows.tar.gz"
    )
    assert results[0].entry_point == "main"
    assert results[0].entry_point_kwargs == "-P var1=testing"
    assert results[0].depends_on is None
    assert results[0].status == "queued"
