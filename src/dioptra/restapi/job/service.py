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
import json
import uuid
from pathlib import Path
from typing import Any, List, Mapping, Optional, cast

import structlog
from injector import inject
from structlog.stdlib import BoundLogger
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from dioptra.restapi.app import db
from dioptra.restapi.experiment.errors import ExperimentDoesNotExistError
from dioptra.restapi.experiment.service import ExperimentService
from dioptra.restapi.models import Experiment, Queue
from dioptra.restapi.queue.service import QueueNameService
from dioptra.restapi.shared.rq.service import RQService
from dioptra.restapi.shared.s3.service import S3Service
from dioptra.task_engine.validation import is_valid

from .errors import InvalidExperimentDescriptionError, JobWorkflowUploadError
from .model import Job

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class JobService(object):
    @inject
    def __init__(
        self,
        rq_service: RQService,
        s3_service: S3Service,
        experiment_service: ExperimentService,
        queue_name_service: QueueNameService,
    ) -> None:
        self._rq_service = rq_service
        self._s3_service = s3_service
        self._experiment_service = experiment_service
        self._queue_name_service = queue_name_service

    @staticmethod
    def create(
        experiment_id: int,
        queue_id: int,
        timeout: str,
        entry_point: str,
        entry_point_kwargs: str,
        depends_on: str,
        **kwargs,
    ) -> Job:
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841
        job_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now()

        return Job(
            job_id=job_id,
            experiment_id=experiment_id,
            queue_id=queue_id,
            created_on=timestamp,
            last_modified=timestamp,
            timeout=timeout,
            entry_point=entry_point,
            entry_point_kwargs=entry_point_kwargs,
            depends_on=depends_on,
        )

    @staticmethod
    def get_all(**kwargs) -> List[Job]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841

        return Job.query.all()  # type: ignore

    @staticmethod
    def get_by_id(job_id: str, **kwargs) -> Job:
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841

        return Job.query.get(job_id)  # type: ignore

    def submit(
        self,
        queue_name: str,
        experiment_name: str,
        timeout: str,
        entry_point: str,
        entry_point_kwargs: str,
        depends_on: str,
        workflow: FileStorage,
        **kwargs,
    ) -> Job:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        experiment: Optional[Experiment] = self._experiment_service.get_by_name(
            experiment_name=experiment_name, log=log
        )

        if experiment is None:
            raise ExperimentDoesNotExistError

        queue = cast(
            Queue,
            self._queue_name_service.get(
                queue_name=queue_name,
                unlocked_only=True,
                error_if_not_found=True,
                log=log,
            ),
        )

        workflow_uri: Optional[str] = self._upload_workflow(workflow=workflow, log=log)

        if workflow_uri is None:
            log.error(
                "Failed to upload workflow to backend storage",
                workflow_filename=secure_filename(workflow.filename or ""),
            )
            raise JobWorkflowUploadError

        new_job: Job = self.create(
            queue_id=queue.queue_id,
            experiment_id=experiment.experiment_id,
            timeout=timeout,
            entry_point=entry_point,
            entry_point_kwargs=entry_point_kwargs,
            depends_on=depends_on,
            log=log,
        )

        new_job.workflow_uri = workflow_uri

        db.session.add(new_job)
        db.session.commit()

        self._rq_service.submit_mlflow_job(
            job_id=new_job.job_id,
            queue=queue_name,
            workflow_uri=new_job.workflow_uri,
            experiment_id=new_job.experiment_id,
            entry_point=new_job.entry_point,
            entry_point_kwargs=new_job.entry_point_kwargs,
            depends_on=new_job.depends_on,
            timeout=new_job.timeout,
            log=log,
        )

        log.info("Job submission successful", job_id=new_job.job_id)

        return new_job

    def submit_task_engine(
        self,
        queue_name: str,
        experiment_name: str,
        experiment_description: Mapping[str, Any],
        global_parameters: Optional[Mapping[str, Any]] = None,
        timeout: Optional[str] = None,
        depends_on: Optional[str] = None,
    ) -> Job:
        from dioptra.restapi.models import Experiment, Queue

        log: BoundLogger = LOGGER.new()

        experiment: Optional[Experiment] = self._experiment_service.get_by_name(
            experiment_name=experiment_name, log=log
        )

        if experiment is None:
            raise ExperimentDoesNotExistError

        queue = cast(
            Queue,
            self._queue_name_service.get(
                queue_name, unlocked_only=True, error_if_not_found=True, log=log
            ),
        )

        if not is_valid(experiment_description):
            raise InvalidExperimentDescriptionError

        job_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now()

        new_job = Job(
            job_id=job_id,
            experiment_id=experiment.experiment_id,
            queue_id=queue.queue_id,
            created_on=timestamp,
            last_modified=timestamp,
            timeout=timeout,
            depends_on=depends_on,
        )

        if global_parameters is not None:
            new_job.entry_point_kwargs = json.dumps(global_parameters)

        db.session.add(new_job)
        db.session.commit()

        self._rq_service.submit_task_engine_job(
            job_id=job_id,
            queue=queue_name,
            experiment_id=experiment.experiment_id,
            experiment_description=experiment_description,
            global_parameters=global_parameters,
            depends_on=depends_on,
            timeout=timeout,
        )

        log.info("Job submission successful", job_id=job_id)

        return new_job

    def _upload_workflow(self, workflow: FileStorage, **kwargs) -> Optional[str]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        upload_dir = Path(uuid.uuid4().hex)
        workflow_filename = upload_dir / secure_filename(workflow.filename or "")

        workflow_uri: Optional[str] = self._s3_service.upload(
            fileobj=workflow,
            bucket="workflow",
            key=str(workflow_filename),
            log=log,
        )

        return workflow_uri
