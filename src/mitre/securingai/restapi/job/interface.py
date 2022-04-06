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
"""The interfaces for creating and updating |Job| objects.

.. |Job| replace:: :py:class:`~.model.Job`
"""
from __future__ import annotations

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
