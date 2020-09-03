from enum import Enum

import structlog
from structlog._config import BoundLoggerLazyProxy

from mitre.securingai.restapi.shared.job_queue.model import JobQueue, JobStatus

LOGGER: BoundLoggerLazyProxy = structlog.get_logger()


def test_JobQueue_works() -> None:
    assert issubclass(JobQueue, Enum)
    assert JobQueue["tensorflow_cpu"].name == "tensorflow_cpu"
    assert JobQueue["tensorflow_gpu"].name == "tensorflow_gpu"


def test_JobStatus_works() -> None:
    assert issubclass(JobStatus, Enum)
    assert JobStatus["queued"].name == "queued"
    assert JobStatus["started"].name == "started"
    assert JobStatus["deferred"].name == "deferred"
    assert JobStatus["failed"].name == "failed"
    assert JobStatus["finished"].name == "finished"
