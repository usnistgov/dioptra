import datetime

import pytest

from mitre.securingai.restapi.models import Queue, QueueLock


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
