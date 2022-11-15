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
from typing import Any, Dict

import pytest
import structlog
from flask import Flask
from structlog.stdlib import BoundLogger

from dioptra.restapi.models import Queue, QueueRegistrationForm
from dioptra.restapi.queue.interface import (
    QueueInterface,
    QueueLockInterface,
    QueueUpdateInterface,
)
from dioptra.restapi.queue.model import QueueLock
from dioptra.restapi.queue.schema import (
    QueueLockSchema,
    QueueNameUpdateSchema,
    QueueRegistrationFormSchema,
    QueueSchema,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pytest.fixture
def queue_registration_form(app: Flask) -> QueueRegistrationForm:
    with app.test_request_context():
        form = QueueRegistrationForm(data={"name": "tensorflow_cpu"})

    return form


@pytest.fixture
def queue_lock_schema() -> QueueLockSchema:
    return QueueLockSchema()


@pytest.fixture
def queue_schema() -> QueueSchema:
    return QueueSchema()


@pytest.fixture
def queue_name_update_schema() -> QueueNameUpdateSchema:
    return QueueNameUpdateSchema()


@pytest.fixture
def queue_registration_form_schema() -> QueueRegistrationFormSchema:
    return QueueRegistrationFormSchema()


def test_QueueLockSchema_create(queue_lock_schema: QueueLockSchema) -> None:
    assert isinstance(queue_lock_schema, QueueLockSchema)


def test_QueueNameUpdateSchema_create(
    queue_name_update_schema: QueueNameUpdateSchema,
) -> None:
    assert isinstance(queue_name_update_schema, QueueNameUpdateSchema)


def test_QueueSchema_create(queue_schema: QueueSchema) -> None:
    assert isinstance(queue_schema, QueueSchema)


def test_QueueRegistrationFormSchema_create(
    queue_registration_form_schema: QueueRegistrationFormSchema,
) -> None:
    assert isinstance(queue_registration_form_schema, QueueRegistrationFormSchema)


def test_QueueSchema_load_works(queue_schema: QueueSchema) -> None:
    queue: QueueInterface = queue_schema.load(
        {
            "queueId": 1,
            "createdOn": "2020-08-17T18:46:28.717559",
            "lastModified": "2020-08-17T18:46:28.717559",
            "name": "tensorflow_cpu",
        }
    )

    assert queue["queue_id"] == 1
    assert queue["created_on"] == datetime.datetime(2020, 8, 17, 18, 46, 28, 717559)
    assert queue["last_modified"] == datetime.datetime(2020, 8, 17, 18, 46, 28, 717559)
    assert queue["name"] == "tensorflow_cpu"


def test_QueueLockSchema_load_works(queue_lock_schema: QueueLockSchema) -> None:
    queue_lock: QueueLockInterface = queue_lock_schema.load(
        {"queueId": 1, "createdOn": "2020-08-17T18:46:28.717559"}
    )

    assert queue_lock["queue_id"] == 1
    assert queue_lock["created_on"] == datetime.datetime(
        2020, 8, 17, 18, 46, 28, 717559
    )


def test_QueueNameUpdateSchema_load_works(
    queue_name_update_schema: QueueNameUpdateSchema,
) -> None:
    queue: QueueUpdateInterface = queue_name_update_schema.load(
        {"name": "tensorflow_cpu"}
    )

    assert queue["name"] == "tensorflow_cpu"


def test_QueueSchema_dump_works(queue_schema: QueueSchema) -> None:
    queue: Queue = Queue(
        queue_id=1,
        created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        name="tensorflow_cpu",
    )
    queue_serialized: Dict[str, Any] = queue_schema.dump(queue)

    assert queue_serialized["queueId"] == 1
    assert queue_serialized["createdOn"] == "2020-08-17T18:46:28.717559"
    assert queue_serialized["lastModified"] == "2020-08-17T18:46:28.717559"
    assert queue_serialized["name"] == "tensorflow_cpu"


def test_QueueLockSchema_dump_works(queue_lock_schema: QueueLockSchema) -> None:
    queue_lock: QueueLock = QueueLock(
        queue_id=1,
        created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
    )
    queue_lock_serialized: Dict[str, Any] = queue_lock_schema.dump(queue_lock)

    assert queue_lock_serialized["queueId"] == 1
    assert queue_lock_serialized["createdOn"] == "2020-08-17T18:46:28.717559"


def test_QueueNameUpdateSchema_dump_works(
    queue_name_update_schema: QueueNameUpdateSchema,
) -> None:
    queue: Queue = Queue(name="tensorflow_cpu")
    queue_name_updated_serialized: Dict[str, Any] = queue_name_update_schema.dump(queue)

    assert queue_name_updated_serialized["name"] == "tensorflow_cpu"


def test_QueueRegistrationFormSchema_dump_works(
    queue_registration_form: QueueRegistrationForm,
    queue_registration_form_schema: QueueRegistrationFormSchema,
) -> None:
    queue_serialized: Dict[str, Any] = queue_registration_form_schema.dump(
        queue_registration_form
    )

    assert queue_serialized["name"] == "tensorflow_cpu"
