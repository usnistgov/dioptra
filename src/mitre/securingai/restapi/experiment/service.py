import datetime
from typing import List, Optional

import structlog
from injector import inject
from structlog import BoundLogger
from structlog._config import BoundLoggerLazyProxy

from mitre.securingai.restapi.app import db

from .errors import ExperimentAlreadyExistsError
from .model import (
    Experiment,
    ExperimentRegistrationForm,
    ExperimentRegistrationFormData,
)
from .schema import ExperimentRegistrationFormSchema


LOGGER: BoundLoggerLazyProxy = structlog.get_logger()


class ExperimentService(object):
    @inject
    def __init__(
        self, experiment_registration_form_schema: ExperimentRegistrationFormSchema,
    ) -> None:
        self._experiment_registration_form_schema = experiment_registration_form_schema

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
        new_experiment: Experiment = Experiment(
            name=experiment_registration_form_data["name"],
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

    @staticmethod
    def get_all(**kwargs) -> List[Experiment]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        return Experiment.query.all()

    @staticmethod
    def get_by_id(experiment_id: int, **kwargs) -> Optional[Experiment]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        return Experiment.query.get(experiment_id)

    @staticmethod
    def get_by_name(experiment_name: str, **kwargs) -> Optional[Experiment]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        return Experiment.query.filter_by(name=experiment_name).first()

    def extract_data_from_form(
        self, experiment_registration_form: ExperimentRegistrationForm, **kwargs
    ) -> ExperimentRegistrationFormData:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        return self._experiment_registration_form_schema.dump(
            experiment_registration_form
        )
