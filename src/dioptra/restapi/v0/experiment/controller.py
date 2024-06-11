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
from typing import Any, cast

import structlog
from flask import request
from flask_accepts import accepts, responds
from flask_login import login_required
from flask_restx import Namespace, Resource
from injector import inject
from structlog.stdlib import BoundLogger

from dioptra.restapi.db.legacy_models import LegacyExperiment

from .schema import ExperimentSchema, IdStatusResponseSchema, NameStatusResponseSchema
from .service import ExperimentNameService, ExperimentService

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
    @responds(schema=ExperimentSchema(many=True), api=api)
    def get(self) -> list[LegacyExperiment]:
        """Gets a list of all registered experiments."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="experiment", request_type="GET"
        )  # noqa: F841
        log.info("Request received")
        return self._experiment_service.get_all(log=log)

    @login_required
    @accepts(schema=ExperimentSchema, api=api)
    @responds(schema=ExperimentSchema, api=api)
    def post(self) -> LegacyExperiment:
        """Creates a new experiment via an experiment registration form."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="experiment", request_type="POST"
        )  # noqa: F841
        log.info("Request received")
        parsed_obj = request.parsed_obj  # type: ignore
        return self._experiment_service.create(parsed_obj["name"], log=log)


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
    def get(self, experimentId: int) -> LegacyExperiment:
        """Gets an experiment by its unique identifier."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="experimentId", request_type="GET"
        )  # noqa: F841
        log.info("Request received", experiment_id=experimentId)
        return cast(
            LegacyExperiment,
            self._experiment_service.get(
                experimentId, error_if_not_found=True, log=log
            ),
        )

    @login_required
    @responds(schema=IdStatusResponseSchema)
    def delete(self, experimentId: int) -> dict[str, Any]:
        """Deletes an experiment by its unique identifier."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="experimentId", request_type="DELETE"
        )  # noqa: F841
        log.info("Request received", experiment_id=experimentId)
        return self._experiment_service.delete(experimentId)

    @login_required
    @accepts(schema=ExperimentSchema, api=api)
    @responds(schema=ExperimentSchema, api=api)
    def put(self, experimentId: int) -> LegacyExperiment:
        """Modifies an experiment by its unique identifier."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="experimentId", request_type="PUT"
        )  # noqa: F841
        parsed_obj = request.parsed_obj  # type: ignore
        return self._experiment_service.rename(
            experimentId, new_name=parsed_obj["name"], log=log
        )


@api.route("/name/<string:experimentName>")
@api.param("experimentName", "The name of the experiment.")
class ExperimentNameResource(Resource):
    """Shows a single experiment (name reference) and delete it."""

    @inject
    def __init__(
        self, *args, experiment_name_service: ExperimentNameService, **kwargs
    ) -> None:
        self._experiment_name_service = experiment_name_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=ExperimentSchema, api=api)
    def get(self, experimentName: str) -> LegacyExperiment:
        """Gets an experiment by its unique name."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="experimentName", request_type="GET"
        )  # noqa: F841
        log.info("Request received", experiment_name=experimentName)
        return cast(
            LegacyExperiment,
            self._experiment_name_service.get(
                experimentName, error_if_not_found=True, log=log
            ),
        )

    @login_required
    @responds(schema=NameStatusResponseSchema)
    def delete(self, experimentName: str) -> dict[str, Any]:
        """Deletes an experiment by its unique name."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="experimentName",
            experiment_name=experimentName,
            request_type="DELETE",
        )  # noqa: F841
        log.info("Request received")
        return self._experiment_name_service.delete(experimentName, log=log)
