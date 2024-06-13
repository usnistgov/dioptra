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
from dioptra.restapi.v1.jobs.schema import JobSchema
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
        """Initialize the experiment resource.

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
            request_id=str(uuid.uuid4()), resource="Experiment", request_type="GET"
        )
        parsed_query_params = request.parsed_query_params  # noqa: F841

        print(parsed_query_params)  # TEST
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
            query=search_string,
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
            request_id=str(uuid.uuid4()), resource="Experiment", request_type="POST"
        )
        parsed_obj = request.parsed_obj  # noqa: F841
        log.debug(f"parsed_obj: {parsed_obj}")  # TEST
        experiment = self._experiment_service.create(
            name=str(parsed_obj["name"]),
            description=str(parsed_obj["description"]),
            group_id=int(parsed_obj["group_id"]),
            entrypoint_ids=list[int](parsed_obj["entrypoint_ids"]),
            # tags=list[int](parsed_obj["tag_ids"]),
            log=log,
        )
        return utils.build_experiment(experiment)


@api.route("/<int:id>")
@api.param("id", "An integer identifying a registered experiment.")
class ExperimentIdEndpoint(Resource):
    @inject
    def __init__(
        self, experiment_id_service: ExperimentIdService, *args, **kwargs
    ) -> None:
        """Initialize the experiment resource.

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
            resource="Experiment",
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
            resource="Experiment",
            request_type="DELETE",
            id=id,
        )
        return self._experiment_id_service.delete(experiment_id=id, log=log)

    @login_required
    @accepts(schema=ExperimentMutableFieldsSchema, api=api)
    @responds(schema=ExperimentSchema, api=api)
    def put(self, id: int):
        """Modifies an experiment by its unique identifier."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="Experiment",
            request_type="PUT",
            id=id,
        )
        parsed_obj = request.parsed_obj  # type: ignore
        experiment = cast(
            models.Experiment,
            self._experiment_id_service.modify(
                id,
                name=parsed_obj["name"],
                description=parsed_obj["description"],
                # entrypoints=parsed_obj["entrypoints"], #TODO add entrypoints
                # jobs=parsed_obj["jobs"], #TODO add jobs
                error_if_notfound=True,
                log=log,
            ),
        )
        return utils.build_experiment(experiment)


@api.route("/<int:id>/jobs")
@api.param("id", "An integer identifying a registered experiment.")
class ExperimentIdJobEndpoint(Resource):

    @login_required
    @accepts(query_params_schema=ExperimentGetQueryParameters, api=api)
    @responds(schema=JobSchema(many=True), api=api)
    def get(self, id: int):
        """Returns a list of jobs for a specified experiment."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="id", request_type="GET", id=id
        )  # noqa: F841
        log.info("Request received")
        # return self._experiment_service.get_jobs(id, error_if_not_found=True, log=log)
