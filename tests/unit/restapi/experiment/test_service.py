import datetime
from typing import List

import pytest
import structlog
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from freezegun import freeze_time
from structlog._config import BoundLoggerLazyProxy

from mitre.securingai.restapi.models import (
    Experiment,
    ExperimentRegistrationForm,
    ExperimentRegistrationFormData,
)
from mitre.securingai.restapi.experiment.errors import ExperimentAlreadyExistsError
from mitre.securingai.restapi.experiment.service import ExperimentService


LOGGER: BoundLoggerLazyProxy = structlog.get_logger()


@pytest.fixture
def experiment_registration_form(app: Flask) -> ExperimentRegistrationForm:
    with app.test_request_context():
        form = ExperimentRegistrationForm(data={"name": "mnist"})

    return form


@pytest.fixture
def experiment_registration_form_data(app: Flask) -> ExperimentRegistrationFormData:
    return ExperimentRegistrationFormData(name="mnist")


@pytest.fixture
def experiment_service(dependency_injector) -> ExperimentService:
    return dependency_injector.get(ExperimentService)


@freeze_time("2020-08-17T18:46:28.717559")
def test_create(
    db: SQLAlchemy,
    experiment_service: ExperimentService,
    experiment_registration_form_data: ExperimentRegistrationFormData,
    monkeypatch,
):  # noqa
    def mockcreatemlflowexperiment(self, experiment_name: str, *args, **kwargs) -> int:
        LOGGER.info(
            "Mocking ExperimentService.create_mlflow_experiment()",
            experiment_name=experiment_name,
            args=args,
            kwargs=kwargs,
        )
        return 1

    monkeypatch.setattr(
        ExperimentService, "create_mlflow_experiment", mockcreatemlflowexperiment
    )
    experiment: Experiment = experiment_service.create(
        experiment_registration_form_data=experiment_registration_form_data
    )

    assert experiment.experiment_id == 1
    assert experiment.name == "mnist"
    assert experiment.created_on == datetime.datetime(2020, 8, 17, 18, 46, 28, 717559)
    assert experiment.last_modified == datetime.datetime(
        2020, 8, 17, 18, 46, 28, 717559
    )

    with pytest.raises(ExperimentAlreadyExistsError):
        experiment_service.create(
            experiment_registration_form_data=experiment_registration_form_data
        )


@freeze_time("2020-08-17T18:46:28.717559")
def test_get_by_id(db: SQLAlchemy, experiment_service: ExperimentService):  # noqa
    timestamp: datetime.datetime = datetime.datetime.now()

    new_experiment: Experiment = Experiment(
        name="mnist", created_on=timestamp, last_modified=timestamp
    )

    db.session.add(new_experiment)
    db.session.commit()

    experiment: Experiment = experiment_service.get_by_id(1)

    assert experiment == new_experiment


@freeze_time("2020-08-17T18:46:28.717559")
def test_get_by_name(db: SQLAlchemy, experiment_service: ExperimentService):  # noqa
    timestamp: datetime.datetime = datetime.datetime.now()

    new_experiment: Experiment = Experiment(
        name="mnist", created_on=timestamp, last_modified=timestamp
    )

    db.session.add(new_experiment)
    db.session.commit()

    experiment: Experiment = experiment_service.get_by_name("mnist")

    assert experiment == new_experiment


@freeze_time("2020-08-17T18:46:28.717559")
def test_get_all(db: SQLAlchemy, experiment_service: ExperimentService):  # noqa
    timestamp: datetime.datetime = datetime.datetime.now()

    new_experiment1: Experiment = Experiment(
        name="mnist", created_on=timestamp, last_modified=timestamp
    )
    new_experiment2: Experiment = Experiment(
        name="imagenet", created_on=timestamp, last_modified=timestamp
    )

    db.session.add(new_experiment1)
    db.session.add(new_experiment2)
    db.session.commit()

    results: List[Experiment] = experiment_service.get_all()

    assert len(results) == 2
    assert new_experiment1 in results and new_experiment2 in results
    assert new_experiment1.experiment_id == 1
    assert new_experiment2.experiment_id == 2


def test_extract_data_from_form(
    experiment_service: ExperimentService,
    experiment_registration_form: ExperimentRegistrationForm,
):  # noqa
    experiment_registration_form_data: ExperimentRegistrationFormData = experiment_service.extract_data_from_form(
        experiment_registration_form=experiment_registration_form
    )

    assert experiment_registration_form_data["name"] == "mnist"
