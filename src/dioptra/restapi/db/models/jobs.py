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
from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, ForeignKeyConstraint, Index, Text, select
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from dioptra.restapi.db.db import bigint, db, guid, intpk, text_

from .entry_points import EntryPoint
from .experiments import Experiment
from .queues import Queue
from .resources import ResourceSnapshot

if TYPE_CHECKING:
    from .entry_points import EntryPointParameterValue
    from .resources import Resource

# -- Tables (no ORM) -------------------------------------------------------------------

job_status_types_table = db.Table(
    "job_status_types",
    Column("status", Text(), primary_key=True),
)

# -- ORM Classes -----------------------------------------------------------------------


class EntryPointJob(db.Model):  # type: ignore[name-defined]
    __tablename__ = "entry_point_jobs"

    # Database fields
    entry_point_resource_snapshot_id: Mapped[intpk] = mapped_column(
        ForeignKey("entry_points.resource_snapshot_id"), init=False
    )
    job_resource_id: Mapped[intpk] = mapped_column(
        ForeignKey("resources.resource_id"), init=False
    )

    # Derived fields (read-only)
    entry_point_id: Mapped[bigint] = column_property(
        select(EntryPoint.resource_id)
        .where(EntryPoint.resource_snapshot_id == entry_point_resource_snapshot_id)
        .correlate_except(EntryPoint)
        .scalar_subquery()
    )

    # Relationships
    job_resource: Mapped["Resource"] = relationship()
    entry_point: Mapped["EntryPoint"] = relationship(
        back_populates="entry_point_jobs", lazy="joined"
    )
    jobs: Mapped[list["Job"]] = relationship(
        init=False, back_populates="entry_point_job"
    )
    entry_point_parameter_values: Mapped[list["EntryPointParameterValue"]] = (
        relationship(
            back_populates="entry_point_job", overlaps="job_resource,parameter,values"
        )
    )

    # Additional settings
    __table_args__ = (Index(None, "job_resource_id", unique=True),)


class ExperimentJob(db.Model):  # type: ignore[name-defined]
    __tablename__ = "experiment_jobs"

    # Database fields
    experiment_resource_snapshot_id: Mapped[intpk] = mapped_column(
        ForeignKey("experiments.resource_snapshot_id"), init=False
    )
    job_resource_id: Mapped[intpk] = mapped_column(
        ForeignKey("resources.resource_id"), init=False
    )

    # Derived fields (read-only)
    experiment_id: Mapped[bigint] = column_property(
        select(Experiment.resource_id)
        .where(Experiment.resource_snapshot_id == experiment_resource_snapshot_id)
        .correlate_except(Experiment)
        .scalar_subquery()
    )

    # Relationships
    job_resource: Mapped["Resource"] = relationship()
    experiment: Mapped["Experiment"] = relationship(
        back_populates="experiment_jobs", lazy="joined"
    )
    jobs: Mapped[list["Job"]] = relationship(
        init=False, back_populates="experiment_job", overlaps="jobs"
    )

    # Additional settings
    __table_args__ = (Index(None, "job_resource_id", unique=True),)


class QueueJob(db.Model):  # type: ignore[name-defined]
    __tablename__ = "queue_jobs"

    # Database fields
    queue_resource_snapshot_id: Mapped[intpk] = mapped_column(
        ForeignKey("queues.resource_snapshot_id"), init=False
    )
    job_resource_id: Mapped[intpk] = mapped_column(
        ForeignKey("resources.resource_id"), init=False
    )

    # Derived fields (read-only)
    queue_id: Mapped[bigint] = column_property(
        select(Queue.resource_id)
        .where(Queue.resource_snapshot_id == queue_resource_snapshot_id)
        .correlate_except(Queue)
        .scalar_subquery()
    )

    # Relationships
    job_resource: Mapped["Resource"] = relationship()
    queue: Mapped["Queue"] = relationship(back_populates="queue_jobs", lazy="joined")
    jobs: Mapped[list["Job"]] = relationship(
        init=False, back_populates="queue_job", overlaps="jobs"
    )

    # Additional settings
    __table_args__ = (Index(None, "job_resource_id", unique=True),)


class JobMlflowRun(db.Model):  # type: ignore[name-defined]
    __tablename__ = "job_mlflow_runs"

    # Database fields
    job_resource_id: Mapped[intpk] = mapped_column(ForeignKey("resources.resource_id"))
    mlflow_run_id: Mapped[guid] = mapped_column(nullable=False)

    # Relationships
    job_resource: Mapped["Resource"] = relationship(init=False)
    jobs: Mapped[list["Job"]] = relationship(
        init=False,
        back_populates="mlflow_run",
        primaryjoin="JobMlflowRun.job_resource_id == foreign(Job.resource_id)",
        overlaps="jobs",
    )

    # Additional settings
    __table_args__ = (Index(None, "mlflow_run_id", unique=True),)


class Job(ResourceSnapshot):
    __tablename__ = "jobs"

    # Database fields
    resource_snapshot_id: Mapped[intpk] = mapped_column(init=False)
    resource_id: Mapped[bigint] = mapped_column(
        ForeignKey("entry_point_jobs.job_resource_id"),
        ForeignKey("experiment_jobs.job_resource_id"),
        ForeignKey("queue_jobs.job_resource_id"),
        init=False,
        nullable=False,
        index=True,
    )
    timeout: Mapped[text_] = mapped_column(nullable=False)
    status: Mapped[text_] = mapped_column(
        ForeignKey("job_status_types.status"), nullable=False, index=True
    )

    # Relationships
    entry_point_job: Mapped["EntryPointJob"] = relationship(
        init=False, back_populates="jobs", overlaps="jobs"
    )
    experiment_job: Mapped["ExperimentJob"] = relationship(
        init=False, back_populates="jobs", overlaps="entry_point_job,jobs"
    )
    mlflow_run: Mapped["JobMlflowRun"] = relationship(
        init=False,
        back_populates="jobs",
        primaryjoin="JobMlflowRun.job_resource_id == foreign(Job.resource_id)",
        overlaps="entry_point_job,experiment_job,jobs",
    )
    queue_job: Mapped["QueueJob"] = relationship(
        init=False,
        back_populates="jobs",
        overlaps="entry_point_job,experiment_job,mlflow_run,jobs",
    )

    # Additional settings
    __table_args__ = (  # type: ignore[assignment]
        Index(None, "resource_snapshot_id", "resource_id", unique=True),
        ForeignKeyConstraint(
            ["resource_snapshot_id", "resource_id"],
            [
                "resource_snapshots.resource_snapshot_id",
                "resource_snapshots.resource_id",
            ],
        ),
    )
    __mapper_args__ = {
        "polymorphic_identity": "job",
    }
