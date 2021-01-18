import datetime
import uuid
from pathlib import Path
from typing import List, Optional

import structlog
from injector import inject
from rq.job import Job as RQJob
from structlog.stdlib import BoundLogger
from werkzeug.utils import secure_filename

from mitre.securingai.restapi.app import db
from mitre.securingai.restapi.experiment.service import ExperimentService
from mitre.securingai.restapi.queue.service import QueueService
from mitre.securingai.restapi.shared.rq.service import RQService
from mitre.securingai.restapi.shared.s3.service import S3Service

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
        queue_service: QueueService,
    ) -> None:
        self._job_form_schema = job_form_schema
        self._rq_service = rq_service
        self._s3_service = s3_service
        self._experiment_service = experiment_service
        self._queue_service = queue_service

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
        from mitre.securingai.restapi.models import Experiment, Queue

        log: BoundLogger = kwargs.get("log", LOGGER.new())

        job_form_data: JobFormData = self._job_form_schema.dump(job_form)

        experiment: Experiment = self._experiment_service.get_by_name(
            job_form_data["experiment_name"], log=log
        )
        queue: Queue = self._queue_service.get_unlocked_by_name(
            job_form_data["queue"], log=log
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
