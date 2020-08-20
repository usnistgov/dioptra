import datetime
from typing import Optional

from typing_extensions import TypedDict

from mitre.securingai.restapi.shared.job_queue.model import JobQueue, JobStatus


class JobInterface(TypedDict, total=False):
    job_id: str
    created_on: datetime.datetime
    last_modified: datetime.datetime
    queue: JobQueue
    workflow_uri: str
    entry_point: str
    entry_point_kwargs: Optional[str]
    status: JobStatus


class JobSubmitInterface(TypedDict, total=False):
    queue: JobQueue
    workflow_uri: str
    entry_point: str
    entry_point_kwargs: Optional[str]


class JobUpdateInterface(TypedDict, total=False):
    status: JobStatus
