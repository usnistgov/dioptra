# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
import datetime

import pytest
import structlog
from structlog.stdlib import BoundLogger

from mitre.securingai.restapi.models import Queue, QueueLock
from mitre.securingai.restapi.queue.interface import (
    QueueInterface,
    QueueLockInterface,
    QueueUpdateInterface,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pytest.fixture
def queue_interface() -> QueueInterface:
    return QueueInterface(
        queue_id=1,
        created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        name="tensorflow_cpu",
    )


@pytest.fixture
def queue_lock_interface() -> QueueLockInterface:
    return QueueLockInterface(
        queue_id=1, created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559)
    )


@pytest.fixture
def queue_update_interface() -> QueueUpdateInterface:
    return QueueUpdateInterface(name="tensorflow_cpu_dev")


def test_QueueInterface_create(queue_interface: QueueInterface) -> None:
    assert isinstance(queue_interface, dict)


def test_QueueLockInterface_create(queue_lock_interface: QueueLockInterface) -> None:
    assert isinstance(queue_lock_interface, dict)


def test_QueueUpdateInterface_create(
    queue_update_interface: QueueUpdateInterface,
) -> None:
    assert isinstance(queue_update_interface, dict)


def test_QueueInterface_works(queue_interface: QueueInterface) -> None:
    queue: Queue = Queue(**queue_interface)
    assert isinstance(queue, Queue)


def test_QueueLockInterface_works(queue_lock_interface: QueueLockInterface) -> None:
    queue_lock: QueueLock = QueueLock(**queue_lock_interface)
    assert isinstance(queue_lock, QueueLock)


def test_QueueUpdateInterface_works(
    queue_update_interface: QueueUpdateInterface,
) -> None:
    queue: Queue = Queue(**queue_update_interface)
    assert isinstance(queue, Queue)
