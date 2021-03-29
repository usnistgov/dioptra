"""The interfaces for creating and updating |Job| objects.

.. |Job| replace:: :py:class:`~.model.Job`
"""

import datetime
from typing import Optional

from typing_extensions import TypedDict


class JobInterface(TypedDict, total=False):
    """The interface for constructing a new |Job| object.

    Attributes:
        job_id: A UUID that identifies the job.
        mlflow_run_id: A UUID that identifies the MLFlow run associated with the job.
        experiment_id: An integer identifying a registered experiment.
        queue_id: An integer identifying a registered queue.
        created_on: The date and time the job was created.
        last_modified: The date and time the job was last modified.
        timeout: The maximum alloted time for a job before it times out and is stopped.
        workflow_uri: The URI pointing to the tarball archive or zip file uploaded with
            the job.
        entry_point: The name of the entry point in the MLproject file to run.
        entry_point_kwargs: A string listing parameter values to pass to the entry point
            for the job. The list of parameters is specified using the following format:
            `-P param1=value1 -P param2=value2`.
        status: The current status of the job. The allowed values are: `queued`,
            `started`, `deferred`, `finished`, `failed`.
        depends_on: A UUID for a previously submitted job to set as a dependency for the
            current job.
    """

    job_id: str
    mlflow_run_id: Optional[str]
    experiment_id: int
    queue_id: int
    created_on: datetime.datetime
    last_modified: datetime.datetime
    timeout: Optional[str]
    workflow_uri: str
    entry_point: str
    entry_point_kwargs: Optional[str]
    status: str
    depends_on: Optional[str]


class JobUpdateInterface(TypedDict, total=False):
    """The interface for updating a |Job| object.

    Attributes:
        status: The current status of the job. The allowed values are: `queued`,
            `started`, `deferred`, `finished`, `failed`.
    """

    status: str
