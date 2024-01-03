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
"""The module defining the job endpoints."""
from __future__ import annotations

import uuid
from typing import List, Optional

import flask
import structlog
from flask import request
from flask_accepts import accepts, responds
from flask_login import login_required
from flask_restx import Namespace, Resource
from injector import inject
from structlog.stdlib import BoundLogger

from dioptra.restapi.utils import as_api_parser, as_parameters_schema_list

from .errors import JobDoesNotExistError
from .model import Job
from .schema import JobSchema, TaskEngineSubmission
from .service import JobService

LOGGER: BoundLogger = structlog.stdlib.get_logger()

api: Namespace = Namespace(
    "Job",
    description="Job submission and management operations",
)


@api.route("/")
class JobResource(Resource):
    """Shows a list of all jobs, and lets you POST to create new jobs."""

    @inject
    def __init__(
        self,
        *args,
        job_service: JobService,
        **kwargs,
    ) -> None:
        self._job_service = job_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=JobSchema(many=True), api=api)
    def get(self) -> List[Job]:
        """Gets a list of all submitted jobs."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="job", request_type="GET"
        )  # noqa: F841
        log.info("Request received")
        return self._job_service.get_all(log=log)

    @login_required
    @api.expect(
        as_api_parser(
            api,
            as_parameters_schema_list(JobSchema, operation="load", location="form"),
        )
    )
    @accepts(form_schema=JobSchema, api=api)
    @responds(schema=JobSchema, api=api)
    def post(self) -> Job:
        """Creates a new job via a job submission form with an attached file."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="job", request_type="POST"
        )  # noqa: F841
        parsed_obj = request.parsed_form  # type: ignore
        log.info("Request received")
        return self._job_service.submit(
            queue_name=parsed_obj["queue"],
            experiment_name=parsed_obj["experiment_name"],
            timeout=parsed_obj["timeout"],
            entry_point=parsed_obj["entry_point"],
            entry_point_kwargs=parsed_obj["entry_point_kwargs"],
            depends_on=parsed_obj["depends_on"],
            workflow=request.files["workflow"],
            log=log,
        )


@api.route("/<string:jobId>")
@api.param("jobId", "A string specifying a job's UUID.")
class JobIdResource(Resource):
    """Shows a single job."""

    @inject
    def __init__(self, *args, job_service: JobService, **kwargs) -> None:
        self._job_service = job_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=JobSchema, api=api)
    def get(self, jobId: str) -> Job:
        """Gets a job by its unique identifier."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="jobId", request_type="GET"
        )  # noqa: F841
        log.info("Request received", job_id=jobId)
        job: Optional[Job] = self._job_service.get_by_id(jobId, log=log)

        if job is None:
            log.error("Job not found", job_id=jobId)
            raise JobDoesNotExistError

        return job


@api.route("/newTaskEngine")
class TaskEngineResource(Resource):
    @inject
    def __init__(self, job_service: JobService, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._job_service = job_service

    @accepts(schema=TaskEngineSubmission, api=api)
    @responds(schema=JobSchema, api=api)
    def post(self) -> Job:
        post_obj = flask.request.parsed_obj  # type: ignore

        new_job = self._job_service.submit_task_engine(
            queue_name=post_obj["queue"],
            experiment_name=post_obj["experimentName"],
            experiment_description=post_obj["experimentDescription"],
            global_parameters=post_obj.get("globalParameters"),
            timeout=post_obj.get("timeout"),
            depends_on=post_obj.get("dependsOn"),
        )

        return new_job
