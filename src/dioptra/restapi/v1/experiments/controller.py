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
import uuid
from typing import cast

import structlog
from flask import request
from flask_accepts import accepts, responds
from flask_login import login_required
from flask_restx import Namespace, Resource
from injector import inject
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import models
from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.jobs.schema import JobSchema, JobStatusSchema
from dioptra.restapi.v1.schemas import IdStatusResponseSchema

from .schema import (
    ExperimentGetQueryParameters,
    ExperimentMutableFieldsSchema,
    ExperimentPageSchema,
    ExperimentSchema,
)
from .service import ExperimentIdService, ExperimentService

LOGGER: BoundLogger = structlog.stdlib.get_logger()

api: Namespace = Namespace("Experiments", description="Experiments endpoint")


@api.route("/")
class ExperimentEndpoint(Resource):
    @inject
    def __init__(self, experiment_service: ExperimentService, *args, **kwargs) -> None:
        """Initialize the ExperimentEndpoint resource.

        All arguments are provided via dependency injection.

        Args:
            experiment_service: An ExperimentService object.
        """
        self._experiment_service = experiment_service
        super().__init__(*args, **kwargs)

    @login_required
    @accepts(query_params_schema=ExperimentGetQueryParameters, api=api)
    @responds(schema=ExperimentPageSchema, api=api)
    def get(self):
        """Gets a page of Experiment resources matching the filter parameters."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="ExperimentEndpoint",
            request_type="GET",
        )
        parsed_query_params = request.parsed_query_params  # noqa: F841

        group_id = parsed_query_params["group_id"]
        search_string = parsed_query_params["search"]
        page_index = parsed_query_params["index"]
        page_length = parsed_query_params["page_length"]

        experiments, total_num_experiments = self._experiment_service.get(
            group_id=group_id,
            search_string=search_string,
            page_index=page_index,
            page_length=page_length,
            log=log,
        )
        return utils.build_paging_envelope(
            "experiments",
            build_fn=utils.build_experiment,
            data=experiments,
            group_id=group_id,
            query=search_string,
            draft_type=None,
            index=page_index,
            length=page_length,
            total_num_elements=total_num_experiments,
        )

    @login_required
    @accepts(schema=ExperimentSchema, api=api)
    @responds(schema=ExperimentSchema, api=api)
    def post(self):
        """Creates an Experiment resource with a provided name."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="ExperimentEndpoint",
            request_type="POST",
        )
        parsed_obj = request.parsed_obj  # noqa: F841
        experiment = self._experiment_service.create(
            name=parsed_obj["name"],
            description=parsed_obj["description"],
            entrypoint_ids=parsed_obj["entrypoint_ids"],
            tag_ids=parsed_obj["tag_ids"],
            group_id=parsed_obj["group_id"],
            log=log,
        )
        return utils.build_experiment(experiment)


@api.route("/<int:id>")
@api.param("id", "ID for the Experiment resource.")
class ExperimentIdEndpoint(Resource):
    @inject
    def __init__(
        self, experiment_id_service: ExperimentIdService, *args, **kwargs
    ) -> None:
        """Initialize the ExperimentIdEndpoint resource.

        All arguments are provided via dependency injection.

        Args:
            experiment_id_service: An ExperimentIdService object.
        """
        self._experiment_id_service = experiment_id_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=ExperimentSchema, api=api)
    def get(self, id: int):
        """Gets an experiment by its unique identifier."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="ExperimentIdEndpoint",
            request_type="GET",
            id=id,
        )
        experiment = cast(
            models.Experiment,
            self._experiment_id_service.get(id, error_if_not_found=True, log=log),
        )
        return utils.build_experiment(experiment)

    @login_required
    @responds(schema=IdStatusResponseSchema, api=api)
    def delete(self, id: int):
        """Deletes an experiment by its unique identifier."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="ExperimentIdEndpoint",
            request_type="DELETE",
            id=id,
        )
        return self._experiment_id_service.delete(id, log=log)

    @login_required
    @accepts(schema=ExperimentMutableFieldsSchema, api=api)
    @responds(schema=ExperimentSchema, api=api)
    def put(self, id: int):
        """Modifies an experiment by its unique identifier."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="ExperimentIdEndpoint",
            request_type="PUT",
            id=id,
        )
        parsed_obj = request.parsed_obj  # type: ignore
        experiment = cast(
            utils.ExperimentDict,
            self._experiment_id_service.modify(
                id,
                name=parsed_obj["name"],
                description=parsed_obj["description"],
                entrypoint_ids=parsed_obj["entrypoint_ids"],
                error_if_not_found=True,
                log=log,
            ),
        )
        return utils.build_experiment(experiment)


@api.route("/<int:id>/jobs")
@api.param("id", "ID for the Experiment resource.")
class ExperimentIdJobEndpoint(Resource):

    @login_required
    @accepts(query_params_schema=ExperimentGetQueryParameters, api=api)
    @responds(schema=JobSchema(many=True), api=api)
    def get(self, id: int):
        """Returns a list of jobs for a specified Experiment."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="ExperimentIdJobEndpoint",
            request_type="GET",
            id=id,
        )  # noqa: F841
        log.debug("Request received")
        parsed_query_params = request.parsed_query_params  # type: ignore # noqa: F841

    @login_required
    @accepts(schema=JobSchema, api=api)
    @responds(schema=JobSchema, api=api)
    def post(self):
        """Creates a Job resource under the specified Experiment."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="ExperimentIdJobEndpoint",
            request_type="POST",
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
            request_id=str(uuid.uuid4()),
            resource="ExperimentIdJobIdEndpoint",
            request_type="GET",
            id=id,
            job_id=jobId,
        )
        log.debug("Request received")

    @login_required
    @responds(schema=IdStatusResponseSchema, api=api)
    def delete(self, id: int, jobId: int):
        """Deletes a Job resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="ExperimentIdJobIdEndpoint",
            request_type="DELETE",
            id=id,
            job_id=jobId,
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
            resource="ExperimentIdJobIdStatusEndpoint",
            request_type="GET",
            id=id,
            job_id=jobId,
        )
        log.debug("Request received")
