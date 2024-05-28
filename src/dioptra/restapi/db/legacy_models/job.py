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
import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dioptra.restapi.db.db import (
    bigintnovariant,
    db,
    optionalstr36,
    str36,
    str255,
    text_,
)

if TYPE_CHECKING:
    from .experiment import LegacyExperiment
    from .queues import LegacyQueue


legacy_job_statuses = db.Table(
    "legacy_job_statuses",
    Column("status", String(255), primary_key=True),
)


class LegacyJob(db.Model):  # type: ignore[name-defined]
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

    __tablename__ = "legacy_jobs"

    job_id: Mapped[str36] = mapped_column(
        primary_key=True, doc="A UUID that identifies the job."
    )
    mlflow_run_id: Mapped[optionalstr36] = mapped_column(init=False, index=True)
    experiment_id: Mapped[bigintnovariant] = mapped_column(
        ForeignKey("legacy_experiments.experiment_id"), nullable=True, index=True
    )
    queue_id: Mapped[bigintnovariant] = mapped_column(
        ForeignKey("legacy_queues.queue_id"), nullable=True, index=True
    )
    created_on: Mapped[datetime.datetime] = mapped_column(nullable=True)
    last_modified: Mapped[datetime.datetime] = mapped_column(nullable=True)
    timeout: Mapped[text_] = mapped_column(nullable=True)
    workflow_uri: Mapped[text_] = mapped_column(nullable=True)
    entry_point: Mapped[text_] = mapped_column(nullable=True)
    entry_point_kwargs: Mapped[text_] = mapped_column(nullable=True)
    status: Mapped[str255] = mapped_column(
        ForeignKey("legacy_job_statuses.status"), init=False, nullable=True, index=True
    )
    depends_on: Mapped[optionalstr36] = mapped_column(nullable=True)

    experiment: Mapped["LegacyExperiment"] = relationship(
        init=False, back_populates="jobs"
    )
    queue: Mapped["LegacyQueue"] = relationship(init=False, back_populates="jobs")

    def __post_init__(self) -> None:
        self.mlflow_run_id = None
        self.status = "queued"

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
