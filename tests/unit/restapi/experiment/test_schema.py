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
import datetime
from typing import Any, Dict

import pytest
import structlog
from flask import Flask
from structlog.stdlib import BoundLogger

from mitre.securingai.restapi.experiment.schema import (
    ExperimentRegistrationFormSchema,
    ExperimentSchema,
)
from mitre.securingai.restapi.models import Experiment, ExperimentRegistrationForm

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pytest.fixture
def experiment_registration_form(app: Flask) -> ExperimentRegistrationForm:
    with app.test_request_context():
        form = ExperimentRegistrationForm(data={"name": "mnist"})

    return form


@pytest.fixture
def experiment_schema() -> ExperimentSchema:
    return ExperimentSchema()


@pytest.fixture
def experiment_registration_form_schema() -> ExperimentRegistrationFormSchema:
    return ExperimentRegistrationFormSchema()


def test_ExperimentSchema_create(experiment_schema: ExperimentSchema) -> None:
    assert isinstance(experiment_schema, ExperimentSchema)


def test_ExperimentRegistrationFormSchema_create(
    experiment_registration_form_schema: ExperimentRegistrationFormSchema,
) -> None:
    assert isinstance(
        experiment_registration_form_schema, ExperimentRegistrationFormSchema
    )


def test_ExperimentSchema_load_works(experiment_schema: ExperimentSchema) -> None:
    experiment: Experiment = experiment_schema.load(
        {
            "experimentId": 1,
            "createdOn": "2020-08-17T18:46:28.717559",
            "lastModified": "2020-08-17T18:46:28.717559",
            "name": "mnist",
        }
    )

    assert experiment["experiment_id"] == 1
    assert experiment["created_on"] == datetime.datetime(
        2020, 8, 17, 18, 46, 28, 717559
    )
    assert experiment["last_modified"] == datetime.datetime(
        2020, 8, 17, 18, 46, 28, 717559
    )
    assert experiment["name"] == "mnist"


def test_ExperimentSchema_dump_works(experiment_schema: ExperimentSchema) -> None:
    experiment: Experiment = Experiment(
        experiment_id=1,
        created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        name="mnist",
    )
    experiment_serialized: Dict[str, Any] = experiment_schema.dump(experiment)

    assert experiment_serialized["experimentId"] == 1
    assert experiment_serialized["createdOn"] == "2020-08-17T18:46:28.717559"
    assert experiment_serialized["lastModified"] == "2020-08-17T18:46:28.717559"
    assert experiment_serialized["name"] == "mnist"


def test_ExperimentRegistrationFormSchema_dump_works(
    experiment_registration_form: ExperimentRegistrationForm,
    experiment_registration_form_schema: ExperimentRegistrationFormSchema,
) -> None:
    experiment_serialized: Dict[str, Any] = experiment_registration_form_schema.dump(
        experiment_registration_form
    )

    assert experiment_serialized["name"] == "mnist"
