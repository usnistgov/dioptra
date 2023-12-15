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
"""The data models for the job endpoint objects."""
from __future__ import annotations

import datetime
from typing import Any

from dioptra.restapi.app import db

job_statuses = db.Table(
    "job_statuses", db.Column("status", db.String(255), primary_key=True)
)


class Job(db.Model):
    """The jobs table.

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

    __tablename__ = "jobs"

    job_id = db.Column(db.String(36), primary_key=True)
    """A UUID that identifies the job."""

    mlflow_run_id = db.Column(db.String(36), index=True)
    experiment_id = db.Column(
        db.BigInteger(), db.ForeignKey("experiments.experiment_id"), index=True
    )
    queue_id = db.Column(db.BigInteger(), db.ForeignKey("queues.queue_id"), index=True)
    created_on = db.Column(db.DateTime())
    last_modified = db.Column(db.DateTime())
    timeout = db.Column(db.Text())
    workflow_uri = db.Column(db.Text())
    entry_point = db.Column(db.Text())
    entry_point_kwargs = db.Column(db.Text())
    status = db.Column(
        db.String(255),
        db.ForeignKey("job_statuses.status"),
        default="queued",
        index=True,
    )
    depends_on = db.Column(db.String(36))

    experiment = db.relationship("Experiment", back_populates="jobs")
    queue = db.relationship("Queue", back_populates="jobs")

    def update(self, changes: dict[str, Any]):
        """Updates the record.

        Args:
            changes: A :py:class:`~.interface.JobUpdateInterface` dictionary containing
                record updates.
        """
        self.last_modified = datetime.datetime.now()

        for key, val in changes.items():
            setattr(self, key, val)

        return self
