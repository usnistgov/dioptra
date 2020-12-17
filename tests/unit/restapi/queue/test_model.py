import datetime

import pytest
import structlog
from structlog._config import BoundLoggerLazyProxy

from mitre.securingai.restapi.models import Queue, QueueLock, QueueRegistrationFormData

LOGGER: BoundLoggerLazyProxy = structlog.get_logger()


@pytest.fixture
def queue_lock() -> QueueLock:
    return QueueLock(
        queue_id=1,
        created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
    )


@pytest.fixture
def queue() -> Queue:
    return Queue(
        queue_id=1,
        created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        name="tensorflow_cpu",
    )


@pytest.fixture
def queue_registration_form_data() -> QueueRegistrationFormData:
    return QueueRegistrationFormData(name="tensorflow_cpu")


def test_QueueLock_create(queue_lock: QueueLock) -> None:
    assert isinstance(queue_lock, QueueLock)


def test_Queue_create(queue: Queue) -> None:
    assert isinstance(queue, Queue)


def test_QueueRegistrationFormData_create(
    queue_registration_form_data: QueueRegistrationFormData,
) -> None:
    assert isinstance(queue_registration_form_data, dict)
