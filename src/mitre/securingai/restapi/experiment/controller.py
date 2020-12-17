import uuid
from typing import List, Optional

import structlog
from flask import jsonify, request
from flask.wrappers import Response
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource
from injector import inject
from structlog import BoundLogger
from structlog._config import BoundLoggerLazyProxy

from .errors import ExperimentDoesNotExistError, ExperimentRegistrationError
from .interface import ExperimentUpdateInterface
from .model import (
    Experiment,
    ExperimentRegistrationForm,
    ExperimentRegistrationFormData,
)
from .schema import (
    ExperimentRegistrationSchema,
    ExperimentSchema,
    ExperimentUpdateSchema,
)
from .service import ExperimentService

LOGGER: BoundLoggerLazyProxy = structlog.get_logger()

api: Namespace = Namespace(
    "Experiment",
    description="Endpoint for registering experiments.",
)


@api.route("/")
class ExperimentResource(Resource):
    @inject
    def __init__(self, *args, experiment_service: ExperimentService, **kwargs) -> None:
        self._experiment_service = experiment_service
        super().__init__(*args, **kwargs)

    @responds(schema=ExperimentSchema(many=True), api=api)
    def get(self) -> List[Experiment]:
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="experiment", request_type="GET"
        )  # noqa: F841
        log.info("Request received")
        return self._experiment_service.get_all(log=log)

    @accepts(ExperimentRegistrationSchema, api=api)
    @responds(schema=ExperimentSchema, api=api)
    def post(self) -> Experiment:
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="experiment", request_type="POST"
        )  # noqa: F841
        experiment_registration_form: ExperimentRegistrationForm = (
            ExperimentRegistrationForm()
        )

        log.info("Request received")

        if not experiment_registration_form.validate_on_submit():
            log.error("Form validation failed")
            raise ExperimentRegistrationError

        log.info("Form validation successful")
        experiment_registration_form_data: ExperimentRegistrationFormData = (
            self._experiment_service.extract_data_from_form(
                experiment_registration_form=experiment_registration_form, log=log
            )
        )
        return self._experiment_service.create(
            experiment_registration_form_data=experiment_registration_form_data, log=log
        )


@api.route("/<int:experimentId>")
@api.param("experimentId", "Unique experiment identifier")
class ExperimentIdResource(Resource):
    @inject
    def __init__(self, *args, experiment_service: ExperimentService, **kwargs) -> None:
        self._experiment_service = experiment_service
        super().__init__(*args, **kwargs)

    @responds(schema=ExperimentSchema, api=api)
    def get(self, experimentId: int) -> Experiment:
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

    def delete(self, experimentId: int) -> Response:
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="experimentId", request_type="DELETE"
        )  # noqa: F841
        log.info("Request received", experiment_id=experimentId)
        id: List[int] = self._experiment_service.delete_experiment(
            experiment_id=experimentId
        )

        return jsonify(dict(status="Success", id=id))  # type: ignore

    @accepts(schema=ExperimentUpdateSchema, api=api)
    @responds(schema=ExperimentSchema, api=api)
    def put(self, experimentId: int) -> Experiment:
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="experimentId", request_type="PUT"
        )  # noqa: F841
        changes: ExperimentUpdateInterface = request.parsed_obj  # type: ignore
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
@api.param("experimentName", "Unique experiment name")
class ExperimentNameResource(Resource):
    @inject
    def __init__(self, *args, experiment_service: ExperimentService, **kwargs) -> None:
        self._experiment_service = experiment_service
        super().__init__(*args, **kwargs)

    @responds(schema=ExperimentSchema, api=api)
    def get(self, experimentName: str) -> Experiment:
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

    def delete(self, experimentName: str) -> Response:
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
            return jsonify(dict(status="Success", id=[]))  # type: ignore

        id: List[int] = self._experiment_service.delete_experiment(
            experiment_id=experiment.experiment_id
        )

        return jsonify(dict(status="Success", id=id))  # type: ignore

    @accepts(schema=ExperimentUpdateSchema, api=api)
    @responds(schema=ExperimentSchema, api=api)
    def put(self, experimentName: str) -> Experiment:
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="experimentName", request_type="PUT"
        )  # noqa: F841
        changes: ExperimentUpdateInterface = request.parsed_obj  # type: ignore
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
