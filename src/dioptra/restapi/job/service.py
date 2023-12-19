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

from dioptra.restapi.db import db
from dioptra.restapi.experiment.errors import ExperimentDoesNotExistError
from dioptra.restapi.experiment.service import ExperimentNameService
from dioptra.restapi.models import Experiment, Queue
from dioptra.restapi.queue.service import QueueNameService
from dioptra.restapi.shared.rq.service import RQService
from dioptra.restapi.shared.s3.service import S3Service
from dioptra.task_engine.validation import is_valid

from .errors import (
    InvalidExperimentDescriptionError,
    JobWorkflowUploadError,
    JobDoesNotExistError,
    JobStatusIncorrectError,
)
from .model import Job

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class JobService(object):
    @inject
    def __init__(
        self,
        rq_service: RQService,
        s3_service: S3Service,
        experiment_name_service: ExperimentNameService,
        queue_name_service: QueueNameService,
    ) -> None:
        """Initialize the job service.

        All arguments are provided via dependency injection.

        Args:
            rq_service: The RQ service.
            s3_service: The S3 service.
            experiment_name_service: The experiment name service.
            queue_name_service: The queue name service.
        """
        self._rq_service = rq_service
        self._s3_service = s3_service
        self._experiment_name_service = experiment_name_service
        self._queue_name_service = queue_name_service

    def get_all(self, **kwargs) -> List[Job]:
        """Fetch the list of all jobs.

        Returns:
            A list of job objects.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841

        return Job.query.all()  # type: ignore

    def get(
        self, job_id: str, error_if_not_found: bool = False, **kwargs
    ) -> Job | None:
        """Fetch a job by its unique identifier.

        Args:
            job_id: The unique identifier of the job.
            error_if_not_found: If True, raise an error if the job is not found.
                Defaults to False.

        Returns:
            The job object if found, otherwise None.

        Raises:
            JobDoesNotExistError: If the job is not found and `error_if_not_found` is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841

        job = Job.query.filter_by(job_id=job_id).first()

        if job is None:
            if error_if_not_found:
                log.error("Job not found", job_id=job_id)
                raise JobDoesNotExistError
            return None

        return cast(Job, job)

    def create(
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
        """Create a new job.

        Args:
            queue_name: The name of the queue to which the job belongs.
            experiment_name: The name of the experiment associated with the job.
            timeout: The maximum execution time for the job.
            entry_point: The entry point for the job.
            entry_point_kwargs: The keyword arguments for the entry point.
            depends_on: A comma-separated string of job dependencies.
            workflow: The workflow file to be associated with the job.

        Returns:
            The newly created job object.

        Raises:
            ExperimentDoesNotExistError: If experiment is not found.
            QueueDoesNotExistError: If the queue is not found.
            JobWorkflowUploadError: If there is an error uploading the workflow to the backend storage.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        experiment: Experiment | None = self._experiment_name_service.get(
            experiment_name=experiment_name, error_if_not_found=True, log=log
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

        job_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now()

        new_job = Job(
            job_id=job_id,
            experiment_id=experiment.experiment_id,
            queue_id=queue.queue_id,
            created_on=timestamp,
            last_modified=timestamp,
            timeout=timeout,
            entry_point=entry_point,
            entry_point_kwargs=entry_point_kwargs,
            depends_on=depends_on,
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

    def change_status(self, job_id: str, status: str, **kwargs) -> Job:
        """Change the status of a job.

        Args:
            job_id: The unique identifier of the job.
            status: The new status for the job. Must be one of ["queued", "started", "deferred", "finished", "failed"].

        Returns:
            The updated job object.

        Raises:
            JobStatusIncorrectError: If the provided status is not valid.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        job = self.get(job_id=job_id, error_if_not_found=True)

        if status not in ["queued", "started", "deferred", "finished", "failed"]:
            raise JobStatusIncorrectError

        job.update({"status": status})

        db.session.commit()

        log.info("Job update successful", job_id=job.job_id, status=status)

        return job

    def submit_task_engine(
        self,
        queue_name: str,
        experiment_name: str,
        experiment_description: Mapping[str, Any],
        global_parameters: Mapping[str, Any] | None = None,
        timeout: str | None = None,
        depends_on: str | None = None,
    ) -> Job:
        """Submit a task engine job.

        Args:
            queue_name: The name of the queue to which the job belongs.
            experiment_name: The name of the experiment associated with the job.
            experiment_description: A mapping representing the experiment description.
            global_parameters: A mapping of global parameters for the job. Defaults to None.
            timeout: The maximum execution time for the job. Defaults to None.
            depends_on: A comma-separated string of job dependencies. Defaults to None.

        Returns:
            The newly created job object.

        Raises:
            ExperimentDoesNotExistError: If experiment is not found.
            QueueDoesNotExistError: If queue is not found.
            InvalidExperimentDescriptionError: If the experiment description is invalid.
        """
        from dioptra.restapi.models import Experiment, Queue

        log: BoundLogger = LOGGER.new()

        experiment = self._experiment_name_service.get(
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

    def _upload_workflow(self, workflow: FileStorage, **kwargs) -> str | None:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        upload_dir = Path(uuid.uuid4().hex)
        workflow_filename = upload_dir / secure_filename(workflow.filename or "")

        workflow_uri = self._s3_service.upload(
            fileobj=workflow,
            bucket="workflow",
            key=str(workflow_filename),
            log=log,
        )

        return workflow_uri
