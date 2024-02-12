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
"""The module defining the experiment endpoints."""
from __future__ import annotations

import uuid
from typing import List, Optional

import structlog
from flask import jsonify, request
from flask.wrappers import Response
from flask_accepts import accepts, responds
from flask_login import login_required
from flask_restx import Namespace, Resource
from injector import inject
from structlog.stdlib import BoundLogger

from dioptra.restapi.utils import slugify

from ..page import Page
from .errors import ExperimentDoesNotExistError
from .model import Experiment
from .schema import ExperimentPageSchema, ExperimentSchema
from .service import ExperimentService

LOGGER: BoundLogger = structlog.stdlib.get_logger()

api: Namespace = Namespace(
    "Experiment",
    description="Experiment registration operations",
)


@api.route("/")
class ExperimentResource(Resource):
    """Shows a list of all experiments, and lets you POST to register new ones."""

    @inject
    def __init__(self, *args, experiment_service: ExperimentService, **kwargs) -> None:
        self._experiment_service = experiment_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=ExperimentPageSchema, api=api)
    def get(self) -> Page:
        """Gets a page of registered experiments."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="experiment", request_type="GET"
        )  # noqa: F841
        log.info("Request received")

        index = request.args.get("index", 0, type=int)
        page_length = request.args.get("page_length", 20, type=int)

        data = self._experiment_service.get_page(
            index=index, page_length=page_length, log=log
        )

        is_complete = True if Experiment.query.count() <= index + page_length else False

        return Page(
            data=data,
            index=index,
            is_complete=is_complete,
            endpoint="experiment",
            page_length=page_length,
        )

    @login_required
    @accepts(schema=ExperimentSchema, api=api)
    @responds(schema=ExperimentSchema, api=api)
    def post(self) -> Experiment:
        """Creates a new experiment via an experiment registration form."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="experiment", request_type="POST"
        )  # noqa: F841

        log.info("Request received")

        parsed_obj = request.parsed_obj  # type: ignore

        name = slugify(str(parsed_obj["name"]))
        return self._experiment_service.create(experiment_name=name, log=log)


@api.route("/<int:experimentId>")
@api.param("experimentId", "An integer identifying a registered experiment.")
class ExperimentIdResource(Resource):
    """Shows a single experiment (id reference) and lets you modify and delete it."""

    @inject
    def __init__(self, *args, experiment_service: ExperimentService, **kwargs) -> None:
        self._experiment_service = experiment_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=ExperimentSchema, api=api)
    def get(self, experimentId: int) -> Experiment:
        """Gets an experiment by its unique identifier."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="experimentId", request_type="GET"
        )  # noqa: F841
        log.info("Request received", experiment_id=experimentId)
        experiment: Optional[Experiment] = self._experiment_service.get_by_id(
            experiment_id=experimentId, log=log
        )

        if experiment is None:
            log.error("Experiment not found", experiment_id=experimentId)
            raise ExperimentDoesNotExistError

        return experiment

    @login_required
    def delete(self, experimentId: int) -> Response:
        """Deletes an experiment by its unique identifier."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="experimentId", request_type="DELETE"
        )  # noqa: F841
        log.info("Request received", experiment_id=experimentId)
        id: List[int] = self._experiment_service.delete_experiment(
            experiment_id=experimentId
        )

        return jsonify(dict(status="Success", id=id))

    @login_required
    @accepts(schema=ExperimentSchema, api=api)
    @responds(schema=ExperimentSchema, api=api)
    def put(self, experimentId: int) -> Experiment:
        """Modifies an experiment by its unique identifier."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="experimentId", request_type="PUT"
        )  # noqa: F841
        changes: dict = request.parsed_obj  # type: ignore
        experiment: Optional[Experiment] = self._experiment_service.get_by_id(
            experimentId, log=log
        )

        if experiment is None:
            log.error("Experiment not found", experiment_id=experimentId)
            raise ExperimentDoesNotExistError

        experiment = self._experiment_service.rename_experiment(
            experiment=experiment, new_name=changes["name"], log=log
        )

        return experiment


@api.route("/name/<string:experimentName>")
@api.param("experimentName", "The name of the experiment.")
class ExperimentNameResource(Resource):
    """Shows a single experiment (name reference) and lets you modify and delete it."""

    @inject
    def __init__(self, *args, experiment_service: ExperimentService, **kwargs) -> None:
        self._experiment_service = experiment_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=ExperimentSchema, api=api)
    def get(self, experimentName: str) -> Experiment:
        """Gets an experiment by its unique name."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="experimentName", request_type="GET"
        )  # noqa: F841
        log.info("Request received", experiment_name=experimentName)
        experiment: Optional[Experiment] = self._experiment_service.get_by_name(
            experiment_name=experimentName, log=log
        )

        if experiment is None:
            log.error("Experiment not found", experiment_name=experimentName)
            raise ExperimentDoesNotExistError

        return experiment

    @login_required
    def delete(self, experimentName: str) -> Response:
        """Deletes an experiment by its unique name."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="experimentName",
            experiment_name=experimentName,
            request_type="DELETE",
        )  # noqa: F841
        log.info("Request received")
        experiment: Optional[Experiment] = self._experiment_service.get_by_name(
            experiment_name=experimentName, log=log
        )

        if experiment is None:
            return jsonify(dict(status="Success", id=[]))

        id: List[int] = self._experiment_service.delete_experiment(
            experiment_id=experiment.experiment_id
        )

        return jsonify(dict(status="Success", id=id))

    @login_required
    @accepts(schema=ExperimentSchema, api=api)
    @responds(schema=ExperimentSchema, api=api)
    def put(self, experimentName: str) -> Experiment:
        """Modifies an experiment by its unique name."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="experimentName", request_type="PUT"
        )  # noqa: F841
        changes: dict = request.parsed_obj  # type: ignore
        experiment: Optional[Experiment] = self._experiment_service.get_by_name(
            experiment_name=experimentName, log=log
        )

        if experiment is None:
            log.error("Experiment not found", experiment_name=experimentName)
            raise ExperimentDoesNotExistError

        experiment = self._experiment_service.rename_experiment(
            experiment=experiment, new_name=changes["name"], log=log
        )

        return experiment
