import datetime
from typing import Optional

from typing_extensions import TypedDict

from mitre.securingai.restapi.shared.job_queue.model import JobQueue, JobStatus


class JobInterface(TypedDict, total=False):
    job_id: str
    created_on: datetime.datetime
    last_modified: datetime.datetime
    queue: JobQueue
    timeout: Optional[str]
    workflow_uri: str
    entry_point: str
    entry_point_kwargs: Optional[str]
    depends_on: Optional[str]
    status: JobStatus


class JobUpdateInterface(TypedDict, total=False):
    status: JobStatus
