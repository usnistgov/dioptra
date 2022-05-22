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

from dioptra.restapi.models import Queue, QueueLock


@pytest.fixture
def default_queues(db):
    tf_cpu_queue: Queue = Queue(
        queue_id=1,
        created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        name="tensorflow_cpu",
    )
    tf_gpu_queue: Queue = Queue(
        queue_id=2,
        created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        name="tensorflow_gpu",
    )
    tf_cpu_dev_queue: Queue = Queue(
        queue_id=3,
        created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        name="tensorflow_cpu_dev",
    )
    tf_gpu_dev_queue: Queue = Queue(
        queue_id=4,
        created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        last_modified=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
        name="tensorflow_gpu_dev",
    )
    db.session.add(tf_cpu_queue)
    db.session.add(tf_gpu_queue)
    db.session.add(tf_cpu_dev_queue)
    db.session.add(tf_gpu_dev_queue)
    db.session.commit()


@pytest.fixture
def default_queues_with_locks(db, default_queues):
    queue_lock: QueueLock = QueueLock(
        queue_id=4,
        created_on=datetime.datetime(2020, 8, 17, 18, 46, 28, 717559),
    )
    db.session.add(queue_lock)
    db.session.commit()
