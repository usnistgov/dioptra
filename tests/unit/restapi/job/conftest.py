import datetime

import pytest

from mitre.securingai.restapi.models import Queue


@pytest.fixture(autouse=True)
def seed_queues(db):
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
    db.session.add(tf_cpu_queue)
    db.session.add(tf_gpu_queue)
    db.session.commit()
