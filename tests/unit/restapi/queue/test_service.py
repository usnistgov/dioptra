import datetime
from typing import List, Optional, Set

import pytest
import structlog
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from freezegun import freeze_time
from structlog.stdlib import BoundLogger

from mitre.securingai.restapi.models import (
    Queue,
    QueueRegistrationForm,
    QueueRegistrationFormData,
)
from mitre.securingai.restapi.queue.errors import QueueAlreadyExistsError
from mitre.securingai.restapi.queue.service import QueueService

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pytest.fixture
def queue_registration_form(app: Flask) -> QueueRegistrationForm:
    with app.test_request_context():
        form = QueueRegistrationForm(data={"name": "tensorflow_cpu"})

    return form


@pytest.fixture
def queue_registration_form_data() -> QueueRegistrationFormData:
    return QueueRegistrationFormData(name="tensorflow_cpu")


@pytest.fixture
def queue_registration_form_data2() -> QueueRegistrationFormData:
    return QueueRegistrationFormData(name="tensorflow_gpu")


@pytest.fixture
def queue_service(dependency_injector) -> QueueService:
    return dependency_injector.get(QueueService)


@freeze_time("2020-08-17T18:46:28.717559")
def test_create(
    db: SQLAlchemy,
    queue_service: QueueService,
    queue_registration_form_data: QueueRegistrationFormData,
    queue_registration_form_data2: QueueRegistrationFormData,
):
    queue: Queue = queue_service.create(
        queue_registration_form_data=queue_registration_form_data
    )
    queue2: Queue = queue_service.create(
        queue_registration_form_data=queue_registration_form_data2
    )

    assert queue.queue_id == 1
    assert queue.name == "tensorflow_cpu"
    assert queue.created_on == datetime.datetime(2020, 8, 17, 18, 46, 28, 717559)
    assert queue.last_modified == datetime.datetime(2020, 8, 17, 18, 46, 28, 717559)

    assert queue2.queue_id == 2
    assert queue2.name == "tensorflow_gpu"
    assert queue2.created_on == datetime.datetime(2020, 8, 17, 18, 46, 28, 717559)
    assert queue2.last_modified == datetime.datetime(2020, 8, 17, 18, 46, 28, 717559)

    with pytest.raises(QueueAlreadyExistsError):
        queue_service.create(queue_registration_form_data=queue_registration_form_data)


def test_delete_queue(
    db: SQLAlchemy,
    queue_service: QueueService,
    default_queues,
):
    tf_cpu_queue_id: List[int] = queue_service.delete_queue(1)
    assert tf_cpu_queue_id[0] == 1

    tf_cpu_queue: Queue = Queue.query.filter_by(queue_id=1).first()
    assert tf_cpu_queue.is_deleted


def test_rename_queue(
    db: SQLAlchemy,
    queue_service: QueueService,
    default_queues,
):
    tf_cpu_queue: Queue = Queue.query.filter_by(queue_id=1, is_deleted=False).first()
    assert tf_cpu_queue.name == "tensorflow_cpu"

    tf_cpu_queue = queue_service.rename_queue(tf_cpu_queue, new_name="tf_cpu")
    tf_cpu_queue_updated_query: Queue = Queue.query.filter_by(
        queue_id=1, is_deleted=False
    ).first()

    assert tf_cpu_queue.name == tf_cpu_queue_updated_query.name
    assert tf_cpu_queue_updated_query.name == "tf_cpu"


@freeze_time("2020-08-17T18:46:28.717559")
def test_lock_queue(db: SQLAlchemy, queue_service: QueueService, default_queues):
    tf_cpu_dev_queue: Queue = Queue.query.filter_by(
        queue_id=3, is_deleted=False
    ).first()
    assert not tf_cpu_dev_queue.lock

    tf_cpu_dev_queue_id: int = tf_cpu_dev_queue.queue_id
    response: List[int] = queue_service.lock_queue(queue=tf_cpu_dev_queue)

    assert Queue.query.filter_by(queue_id=3, is_deleted=False).first().lock
    assert response[0] == tf_cpu_dev_queue_id


@freeze_time("2020-08-17T18:46:28.717559")
def test_unlock_queue(
    db: SQLAlchemy, queue_service: QueueService, default_queues_with_locks
):
    tf_gpu_dev_queue: Queue = Queue.query.filter_by(
        queue_id=4, is_deleted=False
    ).first()
    assert tf_gpu_dev_queue.lock

    tf_gpu_dev_queue_id: int = tf_gpu_dev_queue.queue_id
    response: List[int] = queue_service.unlock_queue(queue=tf_gpu_dev_queue)

    assert not Queue.query.filter_by(queue_id=4, is_deleted=False).first().lock
    assert response[0] == tf_gpu_dev_queue_id


@freeze_time("2020-08-17T18:46:28.717559")
def test_get_by_id(db: SQLAlchemy, queue_service: QueueService):
    timestamp: datetime.datetime = datetime.datetime.now()

    new_queue: Queue = Queue(
        queue_id=1, name="tensorflow_cpu", created_on=timestamp, last_modified=timestamp
    )

    db.session.add(new_queue)
    db.session.commit()

    queue: Queue = queue_service.get_by_id(1)

    assert queue == new_queue


@freeze_time("2020-08-17T18:46:28.717559")
def test_get_by_name(db: SQLAlchemy, queue_service: QueueService):
    timestamp: datetime.datetime = datetime.datetime.now()

    new_queue: Queue = Queue(
        name="tensorflow_cpu", created_on=timestamp, last_modified=timestamp
    )

    db.session.add(new_queue)
    db.session.commit()

    queue: Queue = queue_service.get_by_name("tensorflow_cpu")

    assert queue == new_queue


@freeze_time("2020-08-17T18:46:28.717559")
def test_get_unlocked_by_id(
    db: SQLAlchemy, queue_service: QueueService, default_queues_with_locks
):
    tf_cpu_dev_queue: Optional[Queue] = queue_service.get_unlocked_by_id(3)
    tf_gpu_dev_queue: Optional[Queue] = queue_service.get_unlocked_by_id(4)

    assert tf_cpu_dev_queue
    assert tf_cpu_dev_queue.queue_id == 3
    assert tf_cpu_dev_queue.name == "tensorflow_cpu_dev"
    assert tf_gpu_dev_queue is None


@freeze_time("2020-08-17T18:46:28.717559")
def test_get_unlocked_by_name(
    db: SQLAlchemy, queue_service: QueueService, default_queues_with_locks
):
    tf_cpu_dev_queue: Optional[Queue] = queue_service.get_unlocked_by_name(
        "tensorflow_cpu_dev"
    )
    tf_gpu_dev_queue: Optional[Queue] = queue_service.get_unlocked_by_name(
        "tensorflow_gpu_dev"
    )

    assert tf_cpu_dev_queue
    assert tf_cpu_dev_queue.queue_id == 3
    assert tf_cpu_dev_queue.name == "tensorflow_cpu_dev"
    assert tf_gpu_dev_queue is None


@freeze_time("2020-08-17T18:46:28.717559")
def test_get_all(db: SQLAlchemy, queue_service: QueueService):
    timestamp: datetime.datetime = datetime.datetime.now()

    new_queue1: Queue = Queue(
        queue_id=1, name="tensorflow_cpu", created_on=timestamp, last_modified=timestamp
    )
    new_queue2: Queue = Queue(
        queue_id=2, name="tensorflow_gpu", created_on=timestamp, last_modified=timestamp
    )

    db.session.add(new_queue1)
    db.session.add(new_queue2)
    db.session.commit()

    results: List[Queue] = queue_service.get_all()

    assert len(results) == 2
    assert new_queue1 in results and new_queue2 in results
    assert new_queue1.queue_id == 1
    assert new_queue2.queue_id == 2


def test_get_all_unlocked(
    db: SQLAlchemy, queue_service: QueueService, default_queues_with_locks
):
    results: List[Queue] = queue_service.get_all_unlocked()
    queue_names: Set[str] = {queue.name for queue in results}
    queue_name_diff: Set[str] = queue_names.difference(
        {"tensorflow_cpu", "tensorflow_gpu", "tensorflow_cpu_dev"}
    )

    assert len(results) == 3
    assert len(queue_name_diff) == 0


def test_get_all_locked(
    db: SQLAlchemy, queue_service: QueueService, default_queues_with_locks
):
    results: List[Queue] = queue_service.get_all_locked()
    queue_names: Set[str] = {queue.name for queue in results}
    queue_name_diff: Set[str] = queue_names.difference({"tensorflow_gpu_dev"})

    assert len(results) == 1
    assert len(queue_name_diff) == 0


def test_extract_data_from_form(
    queue_service: QueueService,
    queue_registration_form: QueueRegistrationForm,
):
    queue_registration_form_data: QueueRegistrationFormData = (
        queue_service.extract_data_from_form(
            queue_registration_form=queue_registration_form
        )
    )

    assert queue_registration_form_data["name"] == "tensorflow_cpu"
