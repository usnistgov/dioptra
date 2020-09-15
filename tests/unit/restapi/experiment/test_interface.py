import datetime

import pytest
import structlog
from structlog._config import BoundLoggerLazyProxy

from mitre.securingai.restapi.experiment.interface import (
    ExperimentInterface,
    ExperimentUpdateInterface,
)
from mitre.securingai.restapi.models import Experiment

LOGGER: BoundLoggerLazyProxy = structlog.get_logger()


@pytest.fixture
def experiment_interface() -> ExperimentInterface:
    return ExperimentInterface(
        experiment_id=1,
        created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        name="mnist",
    )


@pytest.fixture
def experiment_update_interface() -> ExperimentUpdateInterface:
    return ExperimentUpdateInterface(name="group-mnist")


def test_ExperimentInterface_create(experiment_interface: ExperimentInterface) -> None:
    assert isinstance(experiment_interface, dict)


def test_ExperimentUpdateInterface_create(
    experiment_update_interface: ExperimentUpdateInterface,
) -> None:
    assert isinstance(experiment_update_interface, dict)


def test_ExperimentInterface_works(experiment_interface: ExperimentInterface) -> None:
    experiment: Experiment = Experiment(**experiment_interface)
    assert isinstance(experiment, Experiment)


def test_ExperimentUpdateInterface_works(
    experiment_update_interface: ExperimentUpdateInterface,
) -> None:
    experiment: Experiment = Experiment(**experiment_update_interface)
    assert isinstance(experiment, Experiment)
