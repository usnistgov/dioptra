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
"""The module defining the endpoints for Experiment resources."""
from __future__ import annotations

import uuid

import structlog
from flask import request
from flask_accepts import accepts, responds
from flask_login import login_required
from flask_restx import Namespace, Resource
from structlog.stdlib import BoundLogger

from dioptra.restapi.v1.jobs.schema import JobSchema, JobStatusSchema
from dioptra.restapi.v1.schemas import IdStatusResponseSchema

from .schema import (
    ExperimentGetQueryParameters,
    ExperimentMutableFieldsSchema,
    ExperimentPageSchema,
    ExperimentSchema,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()

api: Namespace = Namespace("Experiments", description="Experiments endpoint")


@api.route("/")
class ExperimentEndpoint(Resource):

    @login_required
    @accepts(query_params_schema=ExperimentGetQueryParameters, api=api)
    @responds(schema=ExperimentPageSchema, api=api)
    def get(self):
        """Gets a page of Experiment resources matching the filter parameters."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Experiment", request_type="GET"
        )
        log.debug("Request received")
        """
        index = request.args.get("index", 0, type=int)
        page_length = request.args.get("pageLength", 20, type=int)

        data = self._experiment_service.get_page(
            index=index, page_length=page_length, log=log
        )

        is_complete = True if Experiment.query.count() <= index + page_length else False

        return Page(
            data=data,
            index=index,
            is_complete=is_complete,
            endpoint="v0/experiment",
            page_length=page_length,
        )"""

    @login_required
    @accepts(schema=ExperimentSchema, api=api)
    @responds(schema=ExperimentSchema, api=api)
    def post(self):
        """Creates an Experiment resource with a provided name."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Experiment", request_type="POST"
        )
        log.debug("Request received")
        parsed_obj = request.parsed_obj  # noqa: F841
        # return self._experiment_service.create(parsed_obj["name"], log=log)


@api.route("/<int:id>")
@api.param("id", "ID for the Experiment resource.")
class ExperimentIdEndpoint(Resource):

    @login_required
    @responds(schema=ExperimentSchema, api=api)
    def get(self, id: int):
        """Gets an experiment by its unique identifier."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="id", request_type="GET", id=id
        )  # noqa: F841
        log.info("Request received")
        # return self._experiment_service.get(id, error_if_not_found=True, log=log)

    @login_required
    @responds(schema=IdStatusResponseSchema)
    def delete(self, id: int):
        """Deletes an experiment by its unique identifier."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="id", request_type="DELETE", id=id
        )  # noqa: F841
        log.info("Request received")
        # return self._experiment_service.delete(id)

    @login_required
    @accepts(schema=ExperimentMutableFieldsSchema, api=api)
    @responds(schema=ExperimentSchema, api=api)
    def put(self, id: int):
        """Modifies an experiment by its unique identifier."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="id", request_type="PUT", id=id
        )  # noqa: F841
        log.debug("Request received")
        # parsed_obj = request.parsed_obj  # type: ignore
        # return self._experiment_service.rename(id,new_name=parsed_obj["name"],log=log)


@api.route("/<int:id>/jobs")
@api.param("id", "ID for the Experiment resource.")
class ExperimentIdJobEndpoint(Resource):

    @login_required
    @accepts(query_params_schema=ExperimentGetQueryParameters, api=api)
    @responds(schema=JobSchema(many=True), api=api)
    def get(self, id: int):
        """Returns a list of jobs for a specified Experiment."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="id", request_type="GET", id=id
        )  # noqa: F841
        log.info("Request received")
        # return self._experiment_service.get_jobs(id, error_if_not_found=True, log=log)

    @login_required
    @accepts(schema=JobSchema, api=api)
    @responds(schema=JobSchema, api=api)
    def post(self):
        """Creates a Job resource under the specified Experiment."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Job", request_type="POST"
        )
        log.debug("Request received")
        parsed_obj = request.parsed_obj  # noqa: F841


@api.route("/<int:id>/jobs/<int:jobId>")
@api.param("id", "ID for the Experiment resource.")
@api.param("jobId", "ID for the Job resource.")
class ExperimentIdJobIdEndpoint(Resource):
    @login_required
    @responds(schema=JobSchema, api=api)
    def get(self, id: int, jobId: int):
        """Gets a Job resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Job", request_type="GET", id=id
        )
        log.debug("Request received")

    @login_required
    @responds(schema=IdStatusResponseSchema, api=api)
    def delete(self, id: int, jobId: int):
        """Deletes a Job resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="Job",
            request_type="DELETE",
            id=id,
        )
        log.debug("Request received")


@api.route("/<int:id>/jobs/<int:jobId>/status")
@api.param("id", "ID for the Experiment resource.")
@api.param("jobId", "ID for the Job resource.")
class ExperimentIdJobIdStatusEndpoint(Resource):
    @login_required
    @responds(schema=JobStatusSchema, api=api)
    def get(self, id: int, jobId: int):
        """Gets a Job resource's status."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="Job",
            request_type="GET",
            id=id,
        )
        log.debug("Request received")
