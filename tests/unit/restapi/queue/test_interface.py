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
