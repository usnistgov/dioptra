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
from __future__ import annotations

import datetime

import pytest
import structlog
from structlog.stdlib import BoundLogger

from dioptra.restapi.models import Experiment, ExperimentRegistrationFormData

LOGGER: BoundLogger = structlog.stdlib.get_logger()


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
