import datetime

import pytest
import structlog
from structlog._config import BoundLoggerLazyProxy

from mitre.securingai.restapi.models import Experiment, ExperimentRegistrationFormData

LOGGER: BoundLoggerLazyProxy = structlog.get_logger()


@pytest.fixture
def experiment() -> Experiment:
    return Experiment(
        experiment_id=1,
        created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        name="mnist",
    )


@pytest.fixture
def experiment_registration_form_data() -> ExperimentRegistrationFormData:
    return ExperimentRegistrationFormData(name="mnist")


def test_Experiment_create(experiment: Experiment) -> None:
    assert isinstance(experiment, Experiment)


def test_ExperimentRegistrationFormData_create(
    experiment_registration_form_data: ExperimentRegistrationFormData,
) -> None:
    assert isinstance(experiment_registration_form_data, dict)
