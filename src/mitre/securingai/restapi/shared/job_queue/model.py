from enum import Enum, auto


class JobStatus(Enum):
    queued = auto()
    started = auto()
    deferred = auto()
    finished = auto()
    failed = auto()


class JobQueue(Enum):
    tensorflow_cpu = auto()
    tensorflow_gpu = auto()
