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
"""The server-side functions that perform job endpoint operations."""
from __future__ import annotations

import datetime
import uuid
from pathlib import Path
from typing import List, Optional, cast

import structlog
from injector import inject
from rq.job import Job as RQJob
from structlog.stdlib import BoundLogger
from werkzeug.utils import secure_filename

from dioptra.restapi.app import db
from dioptra.restapi.experiment.errors import ExperimentDoesNotExistError
from dioptra.restapi.experiment.service import ExperimentService
from dioptra.restapi.queue.service import QueueNameService
from dioptra.restapi.shared.rq.service import RQService
from dioptra.restapi.shared.s3.service import S3Service

from .errors import JobWorkflowUploadError
from .model import Job, JobForm, JobFormData
from .schema import JobFormSchema

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class JobService(object):
    @inject
    def __init__(
        self,
        job_form_schema: JobFormSchema,
        rq_service: RQService,
        s3_service: S3Service,
        experiment_service: ExperimentService,
        queue_name_service: QueueNameService,
    ) -> None:
        self._job_form_schema = job_form_schema
        self._rq_service = rq_service
        self._s3_service = s3_service
        self._experiment_service = experiment_service
        self._queue_name_service = queue_name_service

    @staticmethod
    def create(job_form_data: JobFormData, **kwargs) -> Job:
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841
        timestamp = datetime.datetime.now()

        return Job(
            experiment_id=job_form_data["experiment_id"],
            queue_id=job_form_data["queue_id"],
            created_on=timestamp,
            last_modified=timestamp,
            timeout=job_form_data.get("timeout"),
            entry_point=job_form_data["entry_point"],
            entry_point_kwargs=job_form_data.get("entry_point_kwargs"),
            depends_on=job_form_data.get("depends_on"),
        )

    @staticmethod
    def get_all(**kwargs) -> List[Job]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841

        return Job.query.all()  # type: ignore

    @staticmethod
    def get_by_id(job_id: str, **kwargs) -> Job:
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841

        return Job.query.get(job_id)  # type: ignore

    def extract_data_from_form(self, job_form: JobForm, **kwargs) -> JobFormData:
        from dioptra.restapi.models import Experiment, Queue

        log: BoundLogger = kwargs.get("log", LOGGER.new())

        job_form_data: JobFormData = self._job_form_schema.dump(job_form)

        experiment: Optional[Experiment] = self._experiment_service.get_by_name(
            job_form_data["experiment_name"], log=log
        )

        if experiment is None:
            raise ExperimentDoesNotExistError

        queue = cast(
            Queue,
            self._queue_name_service.get(
                job_form_data["queue"],
                unlocked_only=True,
                error_if_not_found=True,
                log=log,
            ),
        )

        job_form_data["experiment_id"] = experiment.experiment_id
        job_form_data["queue_id"] = queue.queue_id

        return job_form_data

    def submit(self, job_form_data: JobFormData, **kwargs) -> Job:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        workflow_uri: Optional[str] = self._upload_workflow(job_form_data, log=log)

        if workflow_uri is None:
            log.error(
                "Failed to upload workflow to backend storage",
                workflow_filename=secure_filename(
                    job_form_data["workflow"].filename or ""
                ),
            )
            raise JobWorkflowUploadError

        new_job: Job = self.create(job_form_data, log=log)
        new_job.workflow_uri = workflow_uri

        rq_job: RQJob = self._rq_service.submit_mlflow_job(
            queue=job_form_data["queue"],
            workflow_uri=new_job.workflow_uri,
            experiment_id=new_job.experiment_id,
            entry_point=new_job.entry_point,
            entry_point_kwargs=new_job.entry_point_kwargs,
            depends_on=new_job.depends_on,
            timeout=new_job.timeout,
            log=log,
        )

        new_job.job_id = rq_job.get_id()

        db.session.add(new_job)
        db.session.commit()

        log.info("Job submission successful", job_id=new_job.job_id)

        return new_job

    def _upload_workflow(self, job_form_data: JobFormData, **kwargs) -> Optional[str]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        upload_dir = Path(uuid.uuid4().hex)
        workflow_filename = upload_dir / secure_filename(
            job_form_data["workflow"].filename or ""
        )

        workflow_uri: Optional[str] = self._s3_service.upload(
            fileobj=job_form_data["workflow"],
            bucket="workflow",
            key=str(workflow_filename),
            log=log,
        )

        return workflow_uri
