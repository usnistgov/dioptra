import datetime
from typing import List, Optional

import structlog
from injector import inject
from mlflow.exceptions import RestException
from structlog.stdlib import BoundLogger

from mitre.securingai.restapi.app import db
from mitre.securingai.restapi.shared.mlflow_tracking.service import (
    MLFlowTrackingService,
)

from .errors import (
    ExperimentAlreadyExistsError,
    ExperimentMLFlowTrackingAlreadyExistsError,
    ExperimentMLFlowTrackingDoesNotExistError,
    ExperimentMLFlowTrackingRegistrationError,
)
from .model import (
    Experiment,
    ExperimentRegistrationForm,
    ExperimentRegistrationFormData,
)
from .schema import ExperimentRegistrationFormSchema

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class ExperimentService(object):
    @inject
    def __init__(
        self,
        experiment_registration_form_schema: ExperimentRegistrationFormSchema,
        mlflow_tracking_service: MLFlowTrackingService,
    ) -> None:
        self._experiment_registration_form_schema = experiment_registration_form_schema
        self._mlflow_tracking_service = mlflow_tracking_service

    def create(
        self,
        experiment_registration_form_data: ExperimentRegistrationFormData,
        **kwargs,
    ) -> Experiment:
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        experiment_name: str = experiment_registration_form_data["name"]

        if self.get_by_name(experiment_name, log=log) is not None:
            raise ExperimentAlreadyExistsError

        timestamp = datetime.datetime.now()
        experiment_id: int = self.create_mlflow_experiment(experiment_name)
        new_experiment: Experiment = Experiment(
            experiment_id=experiment_id,
            name=experiment_name,
            created_on=timestamp,
            last_modified=timestamp,
        )
        db.session.add(new_experiment)
        db.session.commit()

        log.info(
            "Experiment registration successful",
            experiment_id=new_experiment.experiment_id,
        )

        return new_experiment

    def create_mlflow_experiment(self, experiment_name: str) -> int:
        try:
            experiment_id: Optional[
                str
            ] = self._mlflow_tracking_service.create_experiment(experiment_name)

        except RestException:
            raise ExperimentMLFlowTrackingRegistrationError

        if experiment_id is None:
            raise ExperimentMLFlowTrackingAlreadyExistsError

        return int(experiment_id)

    def delete_experiment(self, experiment_id: int, **kwargs) -> List[int]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841
        experiment: Optional[Experiment] = self.get_by_id(experiment_id=experiment_id)

        if experiment is None:
            return []

        reply: Optional[bool] = self._mlflow_tracking_service.delete_experiment(
            experiment_id=experiment_id
        )

        if reply is None:
            raise ExperimentMLFlowTrackingDoesNotExistError

        experiment.update(changes={"is_deleted": True})
        db.session.commit()

        return [experiment_id]

    def rename_experiment(
        self, experiment: Experiment, new_name: str, **kwargs
    ) -> Experiment:
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841
        reply: Optional[bool] = self._mlflow_tracking_service.rename_experiment(
            experiment_id=experiment.experiment_id, new_name=new_name
        )

        if reply is None:
            raise ExperimentMLFlowTrackingDoesNotExistError

        experiment.update(changes={"name": new_name})
        db.session.commit()

        return experiment

    @staticmethod
    def get_all(**kwargs) -> List[Experiment]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841

        return Experiment.query.filter_by(is_deleted=False).all()  # type: ignore

    @staticmethod
    def get_by_id(experiment_id: int, **kwargs) -> Optional[Experiment]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841

        return Experiment.query.filter_by(  # type: ignore
            experiment_id=experiment_id, is_deleted=False
        ).first()

    @staticmethod
    def get_by_name(experiment_name: str, **kwargs) -> Optional[Experiment]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.info("Lookup experiment by unique name", experiment_name=experiment_name)

        return Experiment.query.filter_by(  # type: ignore
            name=experiment_name, is_deleted=False
        ).first()

    def extract_data_from_form(
        self, experiment_registration_form: ExperimentRegistrationForm, **kwargs
    ) -> ExperimentRegistrationFormData:
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841

        data: ExperimentRegistrationFormData = (
            self._experiment_registration_form_schema.dump(experiment_registration_form)
        )

        return data
