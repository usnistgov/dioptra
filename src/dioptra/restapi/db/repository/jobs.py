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
"""
The queue repository: data operations related to queues
"""

import datetime
from collections.abc import Iterable, Sequence
from typing import Any, Final, overload

import sqlalchemy as sa
from sqlalchemy import func, select
from sqlalchemy.orm import aliased

import dioptra.restapi.db.repository.utils as utils
from dioptra.restapi.db.models import (
    EntryPoint,
    Experiment,
    ExperimentJob,
    Group,
    Job,
    Queue,
    Resource,
    Tag,
    resource_dependencies_table,
)
from dioptra.restapi.db.models.jobs import JobLog, JobMetric
from dioptra.restapi.db.repository.utils.common import DeletionPolicy
from dioptra.restapi.errors import (
    EntityNotRegisteredError,
    SortParameterValidationError,
)
from dioptra.restapi.v1.jobs.schema import JobLogSeverity


class JobRepository:
    SEARCHABLE_FIELDS: Final[dict[str, Any]] = {
        "description": lambda x: Job.description.like(x),
        "status": lambda x: Job.status.like(x),
        "timeout": lambda x: Job.timeout.like(x),
        "tag": lambda x: Job.tags.any(Tag.name.like(x, escape="/")),
    }
    SORTABLE_FIELDS: Final[dict[str, Any]] = {
        "id": Resource.resource_id,
        "description": Job.description,
        "createdOn": Job.created_on,
        "lastModifiedOn": Resource.last_modified_on,
        "status": Job.status,
        "experiment": Experiment.name,
        "entrypoint": EntryPoint.name,
        "queue": Queue.name,
    }
    SEARCHABLE_LOG_FIELDS: Final[dict[str, Any]] = {
        "severity": lambda x: JobLog.severity.like(x),
        "message": lambda x: JobLog.message.like(x),
        "logger_name": lambda x: JobLog.logger_name.like(x),
    }
    SORTABLE_LOG_FIELDS: Final[dict[str, Any]] = {
        "severity": JobLog.severity,
        "logger_name": JobLog.logger_name,
        "created_on": JobLog.created_on,
    }
    JOB_STATUS_TRANSITIONS: Final[dict[str, Any]] = {
        "queued": {"started", "deferred", "reset"},
        "started": {"finished", "failed", "reset"},
        "deferred": {"started", "reset"},
        "failed": {"reset"},
        "finished": {"reset"},
    }

    def __init__(self, session: utils.CompatibleSession[utils.S]):
        self.session = session

    def create(self, job: Job) -> None:
        """
        Create a new job resource.  This creates both the resource and the
        initial snapshot.

        Args:
            job: The job to create

        Raises:
            EntityExistsError: if the job resource or snapshot already
                exists, or the job name collides with another job in the
                same group
            EntityDoesNotExistError: if the group owner or user creator does
                not exist
            EntityDeletedError: if the job, its creator, or its group owner
                is deleted
            UserNotInGroupError: if the user creator is not a member of the
                group who will own the resource
            MismatchedResourceTypeError: if the snapshot or resource's type is
                not "job"
        """

        # Consistency rules:
        # - Job snapshots must be of job resources
        # - For now, the snapshot creator must be a member of the group who
        #   owns the resource.  I think this will become more complicated when
        #   we implement shares and permissions.

        utils.assert_can_create_resource(self.session, job, "job")

        self.session.add(job)

    def create_snapshot(self, job: Job) -> None:
        """
        Create a new job snapshot.

        Args:
            job: A Job object with the desired snapshot settings

        Raises:
            EntityDoesNotExistError: if the job resource or snapshot creator
                user does not exist
            EntityExistsError: if the snapshot already exists
            EntityDeletedError: if the job or snapshot creator user are
                deleted
            UserNotInGroupError: if the snapshot creator user is not a member
                of the group who owns the job
            MismatchedResourceTypeError: if the snapshot or resource's type is
                not "job"
        """
        # Consistency rules:
        # - Job snapshots must be of job resources
        # - Snapshot timestamps must be monotonically increasing(?)
        # - For now, the snapshot creator must be a member of the group who
        #   owns the resource.  I think this will become more complicated when
        #   we implement shares and permissions.

        utils.assert_can_create_snapshot(self.session, job, "job")

        # Assume that the new snapshot's created_on timestamp is later than the
        # current latest timestamp?

        self.session.add(job)

    def delete(self, job: Job | int) -> None:
        """
        Delete a job.  No-op if the job is already deleted.

        Args:
            job: A Job object or resource_id primary key value identifying
                a job resource

        Raises:
            EntityDoesNotExistError: if the job does not exist
        """

        utils.delete_resource(self.session, job)

    @overload
    def get(
        self,
        resource_ids: int,
        deletion_policy: utils.DeletionPolicy,
    ) -> Job | None: ...

    @overload
    def get(
        self,
        resource_ids: Iterable[int],
        deletion_policy: utils.DeletionPolicy,
    ) -> Sequence[Job]: ...

    def get(
        self,
        resource_ids: int | Iterable[int],
        deletion_policy: utils.DeletionPolicy = utils.DeletionPolicy.NOT_DELETED,
    ) -> Job | Sequence[Job] | None:
        """
        Get the latest snapshot of the given job resource.

        Args:
            resource_ids: A single or iterable of job resource IDs
            deletion_policy: Whether to look at deleted jobs, non-deleted
                jobs, or all jobs

        Returns:
            A Job/list of Job objects, or None/empty list if none were
            found with the given ID(s)
        """
        return utils.get_latest_snapshots(
            self.session, Job, resource_ids, deletion_policy
        )

    def get_one(
        self,
        resource_id: int,
        deletion_policy: utils.DeletionPolicy,
    ) -> Job:
        """
        Get the latest snapshot of the given job resource; require that
        exactly one is found, or raise an exception.

        Args:
            resource_id: A resource ID
            deletion_policy: Whether to look at deleted jobs, non-deleted
                jobs, or all jobs

        Returns:
            A Job object

        Raises:
            EntityDoesNotExistError: if the job does not exist in the
                database (deleted or not)
            EntityExistsError: if the job exists and is not deleted, but
                policy was to find a deleted job
            EntityDeletedError: if the job is deleted, but policy was to find
                a non-deleted job
        """
        return utils.get_one_latest_snapshot(
            self.session, Job, resource_id, deletion_policy
        )

    def get_by_filters_paged(
        self,
        group: Group | int | None,
        experiment: Experiment | int | None,
        filters: list[dict],
        page_start: int,
        page_length: int,
        sort_by: str | None,
        descending: bool,
        deletion_policy: utils.DeletionPolicy = utils.DeletionPolicy.NOT_DELETED,
    ) -> tuple[Sequence[Job], int]:
        """
        Get some jobs according to search criteria.

        Args:
            group: Limit jobs to those owned by this group; None to not limit
                the search
            filters: Search criteria, see parse_search_text()
            page_start: Zero-based row index where the page should start
            page_length: Maximum number of rows in the page; use <= 0 for
                unlimited length
            sort_by: Sort criterion; must be a key of SORTABLE_FIELDS.  None
                to sort in an implementation-dependent way.
            descending: Whether to sort in descending order; only applicable
                if sort_by is given
            deletion_policy: Whether to look at deleted jobs, non-deleted
                jobs, or all jobs

        Returns:
            A 2-tuple including the page of jobs and total count of matching
            jobs which exist

        Raises:
            SearchParseError: if filters includes a non-searchable field
            SortParameterValidationError: if sort_by is a non-sortable field
            EntityDoesNotExistError: if the given group does not exist
            EntityDeletedError: if the given group is deleted
        """

        experiment_id = (
            None if experiment is None else utils.get_resource_id(experiment)
        )

        additional_query_terms = []
        if experiment_id is not None:
            additional_query_terms.append(
                lambda stmt: apply_experiment_filter(stmt, experiment_id)
            )

        return utils.get_by_filters_paged(
            self.session,
            Job,
            self.SORTABLE_FIELDS,
            self.SEARCHABLE_FIELDS,
            group,
            filters,
            page_start,
            page_length,
            sort_by,
            descending,
            deletion_policy,
            additional_query_terms,
        )

    def assert_resources_registered(
        self, entrypoint_id: int, experiment_id: int, queue_id: int
    ):
        # Validate that the provided entrypoint_id is registered to the experiment
        parent_experiment = aliased(Experiment)
        experiment_entry_point_ids_stmt = (
            select(EntryPoint.resource_id)
            .join(
                resource_dependencies_table,
                EntryPoint.resource_id
                == resource_dependencies_table.c.child_resource_id,
            )
            .join(
                parent_experiment,
                parent_experiment.resource_id
                == resource_dependencies_table.c.parent_resource_id,
            )
            .where(parent_experiment.resource_id == experiment_id)
        )
        experiment_entry_point_ids = list(
            self.session.scalars(experiment_entry_point_ids_stmt).all()
        )

        if entrypoint_id not in set(experiment_entry_point_ids):
            raise EntityNotRegisteredError(
                "experiment",
                experiment_id,
                "entry_point",
                entrypoint_id,
            )

        # Validate that the provided queue_id is registered to the entrypoint
        parent_entry_point = aliased(EntryPoint)
        entry_point_queue_ids_stmt = (
            select(Queue.resource_id)
            .join(
                resource_dependencies_table,
                Queue.resource_id == resource_dependencies_table.c.child_resource_id,
            )
            .join(
                parent_entry_point,
                parent_entry_point.resource_id
                == resource_dependencies_table.c.parent_resource_id,
            )
            .where(parent_entry_point.resource_id.in_(experiment_entry_point_ids))
        )
        entry_point_queue_ids = list(
            self.session.scalars(entry_point_queue_ids_stmt).all()
        )

        if queue_id not in set(entry_point_queue_ids):
            raise EntityNotRegisteredError(
                "entry_point", entrypoint_id, "eueue", queue_id
            )

    def get_latest_metrics(self, job_id: int):
        """
        TODO: docstrings
        """
        utils.assert_resource_exists(self.session, job_id, DeletionPolicy.NOT_DELETED)

        stmt = select(JobMetric).where(
            JobMetric.is_latest, JobMetric.job_resource_id == job_id
        )

        return self.session.scalars(stmt).all()

    def get_metric_step(
        self, job_id: int, metric_name: str, metric_step: int
    ) -> JobMetric | None:
        """
        TODO: docstrings
        """
        utils.assert_resource_exists(self.session, job_id, DeletionPolicy.NOT_DELETED)

        stmt = select(JobMetric).where(
            JobMetric.job_resource_id == job_id,
            JobMetric.name == metric_name,
            JobMetric.step == metric_step,
        )

        return self.session.scalar(stmt)

    def get_metric_history(self, job_id: int, metric_name: str) -> Sequence[JobMetric]:
        """
        TODO: docstrings
        """
        utils.assert_resource_exists(self.session, job_id, DeletionPolicy.NOT_DELETED)

        stmt = select(JobMetric).where(
            JobMetric.job_resource_id == job_id,
            JobMetric.name == metric_name,
        )

        return self.session.scalars(stmt).unique().all()

    def add_metric(self, metric: JobMetric) -> None:
        """
        TODO: docstrings
        """
        self.session.add(metric)

    def add_logs(
        self,
        job_id: int,
        records: Iterable[dict[str, Any]],
    ) -> Sequence[JobLog]:
        """
        Add the given log records to the database.

        Args:
            job_resource_id: The resource ID of a job
            records: An iterable of dicts, where each dict complies with the
                JobLogRecordSchema marshmallow schema (after loading).
        """
        job = self.get_one(job_id, DeletionPolicy.NOT_DELETED)

        job_logs: list[JobLog] = []

        for record in records:
            job_log = JobLog(
                severity=record["severity"].name,
                logger_name=record["logger_name"],
                message=record["message"],
                job_resource=job.resource,
            )
            self.session.add(job_log)
            job_logs.append(job_log)

        return job_logs

    def get_logs(
        self,
        job_id: int,
        filters: list,
        page_start: int,
        page_length: int,
        sort_by: str,
        descending: bool,
        severity: list[str] | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        Get log records from the database, for the given job.

        Args:
            job_id: The resource ID of a job
            filters: list,
            page_start: Zero-based index of the first log record to return
            page_length: The number of records to return
            sort_by: The name of the column to sort.
            descending: Boolean indicating whether to sort by descending or not.
            severity: list of severities to filter by

        Returns:
            A 2-tuple including (1) The list of records comprising this page,
            each complying with JobLogRecordSchema, and (2) the total number of
            records across all pages.
        """
        utils.assert_resource_exists(self.session, job_id, DeletionPolicy.NOT_DELETED)

        count_stmt = (
            select(func.count())
            .select_from(JobLog)
            .where(*filters, JobLog.job_resource_id == job_id)
        )
        if severity:
            count_stmt = count_stmt.where(JobLog.severity.in_(severity))
        total_count = self.session.scalar(count_stmt)
        # "select count(*) ..." can't produce None
        assert total_count is not None

        page_stmt = (
            select(JobLog)
            .where(*filters, JobLog.job_resource_id == job_id)
            .offset(page_start)
            .limit(page_length)
        )

        if severity:
            page_stmt = page_stmt.where(JobLog.severity.in_(severity))

        if sort_by and sort_by in JobRepository.SORTABLE_LOG_FIELDS:
            sort_column = JobRepository.SORTABLE_LOG_FIELDS[sort_by]
            sort_column = sort_column.desc() if descending else sort_column.asc()
            # primary: user sort, secondary: id
            page_stmt = page_stmt.order_by(sort_column, JobLog.id)
        elif sort_by:
            raise SortParameterValidationError("job", sort_by)
        else:
            # default: just by id
            page_stmt = page_stmt.order_by(JobLog.id)

        log_objs = self.session.scalars(page_stmt)

        records = []
        for log_obj in log_objs:
            record = {
                "severity": JobLogSeverity[log_obj.severity],
                "logger_name": log_obj.logger_name,
                "message": log_obj.message,
                "created_on": log_obj.created_on,
            }
            records.append(record)

        return records, total_count


def apply_experiment_filter(stmt: sa.Select, experiment_id: int) -> sa.Select:
    cte_job_ids = (
        select(ExperimentJob.job_resource_id)
        .join(Resource)
        .where(
            ExperimentJob.experiment_id == experiment_id,
            Resource.is_deleted == False,  # noqa: E712
        )
        .cte()
    )
    return stmt.where(Job.resource_id.in_(select(cte_job_ids)))


def apply_severity_filter(stmt: sa.Select, severity: list[str]):
    return stmt.select(JobLog).where(JobLog.severity.in_(severity))
