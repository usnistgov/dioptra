import datetime
import uuid
from pathlib import Path
from typing import List, Optional

import rq
import structlog
from injector import inject
from structlog import BoundLogger
from structlog._config import BoundLoggerLazyProxy
from werkzeug.utils import secure_filename

from mitre.securingai.restapi.app import db
from mitre.securingai.restapi.shared.job_queue.model import JobStatus
from mitre.securingai.restapi.shared.job_queue.service import RQService
from mitre.securingai.restapi.shared.s3.service import S3Service

from .model import Job, JobFormData


LOGGER: BoundLoggerLazyProxy = structlog.get_logger()


class JobService(object):
    @inject
    def __init__(self, rq_service: RQService, s3_service: S3Service) -> None:
        self._rq_service = rq_service
        self._s3_service = s3_service

    @staticmethod
    def create(job_form_data: JobFormData, **kwargs) -> Job:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        return Job(
            queue=job_form_data["queue"],
            timeout=job_form_data.get("timeout"),
            entry_point=job_form_data["entry_point"],
            entry_point_kwargs=job_form_data.get("entry_point_kwargs"),
            depends_on=job_form_data.get("depends_on"),
        )

    @staticmethod
    def get_all(**kwargs) -> List[Job]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        return Job.query.all()

    @staticmethod
    def get_by_id(job_id: str, **kwargs) -> Job:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        return Job.query.get(job_id)

    def submit(self, job_form_data: JobFormData, **kwargs) -> Job:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        timestamp = datetime.datetime.now()

        workflow_uri: Optional[str] = self._upload_workflow(job_form_data, log=log)

        new_job: Job = self.create(job_form_data, log=log)
        new_job.created_on = timestamp
        new_job.last_modified = timestamp

        if workflow_uri is None:
            new_job.status = JobStatus.failed
            log.warning("Job submission failed")
            return new_job

        new_job.workflow_uri = workflow_uri

        rq_job: rq.job.Job = self._rq_service.submit_mlflow_job(
            queue=new_job.queue,
            workflow_uri=new_job.workflow_uri,
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
            job_form_data["workflow"].filename
        )

        return self._s3_service.upload(
            fileobj=job_form_data["workflow"],
            bucket="workflow",
            key=str(workflow_filename),
            log=log,
        )
