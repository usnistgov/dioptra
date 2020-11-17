import datetime
from typing import Optional

from typing_extensions import TypedDict


class JobInterface(TypedDict, total=False):
    job_id: str
    mlflow_run_id: Optional[str]
    experiment_id: int
    created_on: datetime.datetime
    last_modified: datetime.datetime
    queue: str
    timeout: Optional[str]
    workflow_uri: str
    entry_point: str
    entry_point_kwargs: Optional[str]
    depends_on: Optional[str]
    status: str


class JobUpdateInterface(TypedDict, total=False):
    status: str
