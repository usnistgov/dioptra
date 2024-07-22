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
"""The server-side functions that perform job endpoint operations."""
from __future__ import annotations

from typing import Any, Final, cast

import structlog
from flask_login import current_user
from injector import inject
from sqlalchemy import func, select
from sqlalchemy.orm import aliased
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import db, models
from dioptra.restapi.errors import BackendDatabaseError
from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.entrypoints.service import EntrypointIdService
from dioptra.restapi.v1.experiments.service import ExperimentIdService
from dioptra.restapi.v1.groups.service import GroupIdService
from dioptra.restapi.v1.queues.service import QueueIdService
from dioptra.restapi.v1.shared.rq_service import RQServiceV1
from dioptra.restapi.v1.shared.search_parser import construct_sql_query_filters

from .errors import (
    EntryPointNotRegisteredToExperimentError,
    ExperimentJobDoesNotExistError,
    JobDoesNotExistError,
    JobInvalidParameterNameError,
    JobInvalidStatusTransitionError,
    JobMlflowRunAlreadySetError,
    QueueNotRegisteredToEntryPointError,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()

RESOURCE_TYPE: Final[str] = "job"
SEARCHABLE_FIELDS: Final[dict[str, Any]] = {
    "description": lambda x: models.Job.description.like(x),
    "status": lambda x: models.Job.status.like(x),
    "timeout": lambda x: models.Job.timeout.like(x),
    "tag": lambda x: models.Job.tags.any(models.Tag.name.like(x, escape="/")),
}
JOB_STATUS_TRANSITIONS: Final[dict[str, Any]] = {
    "queued": {"started", "deferred"},
    "started": {"finished", "failed"},
    "deferred": {"started"},
    "failed": {},
    "finished": {},
}


class JobService(object):
    """The service methods for registering and managing jobs by their unique id."""

    @inject
    def __init__(
        self,
        experiment_id_service: ExperimentIdService,
        queue_id_service: QueueIdService,
        entrypoint_id_service: EntrypointIdService,
        group_id_service: GroupIdService,
        rq_service: RQServiceV1,
    ) -> None:
        """Initialize the job service.

        All arguments are provided via dependency injection.

        Args:
            experiment_id_service: An ExperimentIdService object.
            queue_id_service: A QueueIdService object.
            entrypoint_id_service: An EntrypointIdService object.
            group_id_service: A GroupIdService object.
            rq_service: An RQServiceV1 object.
        """
        self._experiment_id_service = experiment_id_service
        self._queue_id_service = queue_id_service
        self._entrypoint_id_service = entrypoint_id_service
        self._group_id_service = group_id_service
        self._rq_service = rq_service

    def create(
        self,
        experiment_id: int,
        queue_id: int,
        entrypoint_id: int,
        values: dict[str, str],
        description: str,
        timeout: str,
        **kwargs,
    ) -> utils.JobDict:
        """Create a new job.

        Args:
            experiment_id: The unique id for the experiment this job is under.
            queue_id: The unique id for the queue this job will execute on.
            entrypoint_id: The unique id for the entrypoint defining the job.
            values: The parameter values passed to the entrypoint to configure the job.
            description: The description of the job.
            timeout: The length of time the job will run before timing out.
            group_id: The group that will own the job.

        Returns:
            The newly created job object.

        Raises:
            JobAlreadyExistsError: If a job with the given name already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        # Set the default status
        status = "queued"

        # Validate the provided experiment_id and fetch the ORM object
        experiment_dict = cast(
            utils.ExperimentDict,
            self._experiment_id_service.get(
                experiment_id, error_if_not_found=True, log=log
            ),
        )
        experiment = experiment_dict["experiment"]

        # Validate that the provided entrypoint_id is registered to the experiment
        parent_experiment = aliased(models.Experiment)
        experiment_entry_point_ids_stmt = (
            select(models.EntryPoint.resource_id)
            .join(
                models.resource_dependencies_table,
                models.EntryPoint.resource_id
                == models.resource_dependencies_table.c.child_resource_id,
            )
            .join(
                parent_experiment,
                parent_experiment.resource_id
                == models.resource_dependencies_table.c.parent_resource_id,
            )
            .where(parent_experiment.resource_id == experiment_id)
        )
        experiment_entry_point_ids = list(
            db.session.scalars(experiment_entry_point_ids_stmt).all()
        )

        if entrypoint_id not in set(experiment_entry_point_ids):
            log.debug(
                "Entry point not registered to experiment",
                entrypoint_id=entrypoint_id,
                experiment_id=experiment_id,
            )
            raise EntryPointNotRegisteredToExperimentError

        # Validate that the provided queue_id is registered to the entrypoint
        parent_entry_point = aliased(models.EntryPoint)
        entry_point_queue_ids_stmt = (
            select(models.Queue.resource_id)
            .join(
                models.resource_dependencies_table,
                models.Queue.resource_id
                == models.resource_dependencies_table.c.child_resource_id,
            )
            .join(
                parent_entry_point,
                parent_entry_point.resource_id
                == models.resource_dependencies_table.c.parent_resource_id,
            )
            .where(parent_entry_point.resource_id.in_(experiment_entry_point_ids))
        )
        entry_point_queue_ids = list(
            db.session.scalars(entry_point_queue_ids_stmt).all()
        )

        if queue_id not in set(entry_point_queue_ids):
            log.debug(
                "Queue not registered to entry point",
                queue_id=queue_id,
                entrypoint_id=entrypoint_id,
            )
            raise QueueNotRegisteredToEntryPointError

        # Fetch the validated queue
        queue_dict = cast(
            utils.QueueDict,
            self._queue_id_service.get(queue_id, error_if_not_found=True, log=log),
        )
        queue = queue_dict["queue"]

        # Fetch the validated entrypoint
        entrypoint_dict = cast(
            utils.EntrypointDict,
            self._entrypoint_id_service.get(
                entrypoint_id, error_if_not_found=True, log=log
            ),
        )
        entrypoint = entrypoint_dict["entry_point"]

        # Validate the keys in values against the registered entrypoint parameter names
        invalid_job_params = set(values.keys()) - set(
            param.name for param in entrypoint.parameters
        )
        if len(invalid_job_params) > 0:
            log.debug("Invalid parameter names", parameters=list(invalid_job_params))
            raise JobInvalidParameterNameError

        # Create the new Job resource and record the assigned entrypoint parameter
        # values
        job_resource = models.Resource(
            resource_type=RESOURCE_TYPE, owner=experiment.resource.owner
        )
        entrypoint_parameter_values = [
            models.EntryPointParameterValue(
                value=values.get(
                    entrypoint_parameter.name, entrypoint_parameter.default_value
                ),
                job_resource=job_resource,
                parameter=entrypoint_parameter,
            )
            for entrypoint_parameter in entrypoint.parameters
        ]

        new_job = models.Job(
            timeout=timeout,
            status=status,
            description=description,
            resource=job_resource,
            creator=current_user,
        )
        new_job.entry_point_job = models.EntryPointJob(
            job_resource=job_resource,
            entry_point=entrypoint,
            entry_point_parameter_values=entrypoint_parameter_values,
        )
        new_job.experiment_job = models.ExperimentJob(
            job_resource=job_resource,
            experiment=experiment,
        )
        new_job.queue_job = models.QueueJob(
            job_resource=job_resource,
            queue=queue,
        )
        db.session.add(new_job)
        db.session.commit()
        self._rq_service.submit(
            job_id=new_job.resource_id,
            experiment_id=experiment_id,
            queue=queue.name,
            timeout=timeout,
        )
        log.debug(
            "Job registration successful",
            job_id=new_job.resource_id,
        )
        return utils.JobDict(
            job=new_job,
            artifacts=[],
            has_draft=False,
        )

    def get(
        self,
        group_id: int | None,
        search_string: str,
        page_index: int,
        page_length: int,
        **kwargs,
    ) -> tuple[list[utils.JobDict], int]:
        """Fetch a list of jobs, optionally filtering by search string and paging
        parameters.

        Args:
            group_id: A group ID used to filter results.
            search_string: A search string used to filter results.
            page_index: The index of the first group to be returned.
            page_length: The maximum number of jobs to be returned.

        Returns:
            A tuple containing a list of jobs and the total number of jobs matching
            the query.

        Raises:
            BackendDatabaseError: If the database query returns a None when counting
                the number of jobs.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get full list of jobs")

        filters = list()

        if group_id is not None:
            filters.append(models.Resource.group_id == group_id)

        if search_string:
            filters.append(
                construct_sql_query_filters(search_string, SEARCHABLE_FIELDS)
            )

        stmt = (
            select(func.count(models.Job.resource_id))
            .join(models.Resource)
            .where(
                *filters,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id == models.Job.resource_snapshot_id,
            )
        )
        total_num_jobs = db.session.scalars(stmt).first()

        if total_num_jobs is None:
            log.error(
                "The database query returned a None when counting the number of "
                "groups when it should return a number.",
                sql=str(stmt),
            )
            raise BackendDatabaseError

        if total_num_jobs == 0:
            return [], total_num_jobs

        jobs_stmt = (
            select(models.Job)
            .join(models.Resource)
            .where(
                *filters,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id == models.Job.resource_snapshot_id,
            )
            .offset(page_index)
            .limit(page_length)
        )
        jobs = list(db.session.scalars(jobs_stmt).all())

        job_dicts: dict[int, utils.JobDict] = {
            job.resource_id: utils.JobDict(
                job=job,
                artifacts=[],
                has_draft=False,
            )
            for job in jobs
        }

        job_ids = [job.resource_id for job in jobs]
        artifacts_stmt = (
            select(models.Artifact)
            .join(models.Resource)
            .where(
                models.Artifact.job_id.in_(job_ids),
                models.Resource.is_deleted == False,  # noqa: E712
            )
        )
        for artifact in db.session.scalars(artifacts_stmt).all():
            job_dicts[artifact.job_id]["artifacts"].append(artifact)

        return list(job_dicts.values()), total_num_jobs


class JobIdService(object):
    """The service methods for registering and managing jobs by their unique id."""

    def get(
        self,
        job_id: int,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> utils.JobDict | None:
        """Fetch a job by its unique id.

        Args:
            job_id: The unique id of the job.
            error_if_not_found: If True, raise an error if the job is not found.
                Defaults to False.

        Returns:
            The job object if found, otherwise None.

        Raises:
            JobDoesNotExistError: If the job is not found and `error_if_not_found`
                is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get job by id", job_id=job_id)

        stmt = (
            select(models.Job)
            .join(models.Resource)
            .where(
                models.Job.resource_id == job_id,
                models.Job.resource_snapshot_id == models.Resource.latest_snapshot_id,
                models.Resource.is_deleted == False,  # noqa: E712
            )
        )
        job = db.session.scalars(stmt).first()

        if job is None:
            if error_if_not_found:
                log.debug("Job not found", job_id=job_id)
                raise JobDoesNotExistError

            return None

        artifacts_stmt = (
            select(models.Artifact)
            .join(models.Resource)
            .where(
                models.Artifact.job_id == job_id,
                models.Resource.is_deleted == False,  # noqa: E712
            )
        )
        artifacts = list(db.session.scalars(artifacts_stmt).all())

        return utils.JobDict(
            job=job,
            artifacts=artifacts,
            has_draft=False,
        )

    def delete(self, job_id: int, **kwargs) -> dict[str, Any]:
        """Delete a job.

        Args:
            job_id: The unique id of the job.

        Returns:
            A dictionary reporting the status of the request.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        stmt = select(models.Resource).filter_by(
            resource_id=job_id, resource_type=RESOURCE_TYPE, is_deleted=False
        )
        job_resource = db.session.scalars(stmt).first()

        if job_resource is None:
            raise JobDoesNotExistError

        deleted_resource_lock = models.ResourceLock(
            resource_lock_type="delete",
            resource=job_resource,
        )
        db.session.add(deleted_resource_lock)
        db.session.commit()
        log.debug("Job deleted", job_id=job_id)

        return {"status": "Success", "id": [job_id]}


class JobIdStatusService(object):
    """The service methods for retrieving the status of a job by unique id."""

    @inject
    def __init__(
        self,
        job_id_service: JobIdService,
    ) -> None:
        """Initialize the job status service.

        All arguments are provided via dependency injection.

        Args:
            job_id_service: A JobIdService object.
        """
        self._job_id_service = job_id_service

    def get(
        self,
        job_id: int,
        **kwargs,
    ) -> dict[str, Any]:
        """Fetch a job's status by its unique id.

        Args:
            job_id: The unique id of the job.

        Returns:
            The status message job object if found, otherwise an error message.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get job status by id", job_id=job_id)

        stmt = (
            select(models.Job)
            .join(models.Resource)
            .where(
                models.Job.resource_id == job_id,
                models.Job.resource_snapshot_id == models.Resource.latest_snapshot_id,
                models.Resource.is_deleted == False,  # noqa: E712
            )
        )
        job = db.session.scalars(stmt).first()

        if job is None:
            log.debug("Job not found", job_id=job_id)
            raise JobDoesNotExistError

        return {"status": job.status, "id": job.resource_id}


class ExperimentJobService(object):
    """The service methods for submitting and retrieving jobs within an experiment
    namespace."""

    @inject
    def __init__(
        self, experiment_id_service: ExperimentIdService, job_service: JobService
    ) -> None:
        """Initialize the ExperimentIdJob service.

        All arguments are provided via dependency injection.

        Args:
            experiment_id_service: An ExperimentIdService object.
            job_service: A JobService object.
        """
        self._experiment_id_service = experiment_id_service
        self._job_service = job_service

    def create(
        self,
        experiment_id: int,
        queue_id: int,
        entrypoint_id: int,
        values: dict[str, str],
        description: str,
        timeout: str,
        **kwargs,
    ) -> utils.JobDict:
        """Create a new job within an experiment.

        Args:
            experiment_id: The unique id for the experiment this job is under.
            queue_id: The unique id for the queue this job will execute on.
            entrypoint_id: The unique id for the entrypoint defining the job.
            values: The parameter values passed to the entrypoint to configure the job.
            description: The description of the job.
            timeout: The length of time the job will run before timing out.
            group_id: The group that will own the job.

        Returns:
            The newly created job object.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        return self._job_service.create(
            experiment_id=experiment_id,
            queue_id=queue_id,
            entrypoint_id=entrypoint_id,
            values=values,
            description=description,
            timeout=timeout,
            log=log,
        )

    def get(
        self,
        experiment_id: int,
        search_string: str,
        page_index: int,
        page_length: int,
        **kwargs,
    ) -> tuple[list[utils.JobDict], int]:
        """Fetch a list of jobs for a given experiment, optionally filtering by search
        string and paging parameters.

        Args:
            experiment_id: The unique id of the experiment.
            search_string: A search string used to filter results.
            page_index: The index of the first page to be returned.
            page_length: The maximum number of experiments to be returned.

        Returns:
            A tuple containing a list of jobs and the total number of jobs matching the
            query.

        Raises:
            ExperimentDoesNotExistError: If the experiment is not found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get full list of jobs for experiment", experiment_id=experiment_id)

        filters = []

        if search_string:
            filters.append(
                construct_sql_query_filters(search_string, SEARCHABLE_FIELDS)
            )

        cte_job_ids = (
            select(models.ExperimentJob.job_resource_id)
            .join(models.Resource)
            .where(
                models.ExperimentJob.experiment_id == experiment_id,
                models.Resource.is_deleted == False,  # noqa: E712
            )
            .cte()
        )
        stmt = (
            select(func.count(models.Job.resource_id))
            .join(models.Resource)
            .where(
                *filters,
                models.Job.resource_id.in_(select(cte_job_ids)),
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id == models.Job.resource_snapshot_id,
            )
        )
        total_num_jobs = db.session.scalars(stmt).first()

        if total_num_jobs is None:
            log.error(
                "The database query returned a None when counting the number of "
                "experiment jobs when it should return a number.",
                sql=str(stmt),
            )
            raise BackendDatabaseError

        if total_num_jobs == 0:
            return [], total_num_jobs

        jobs_stmt = (
            select(models.Job)
            .join(models.Resource)
            .where(
                *filters,
                models.Job.resource_id.in_(select(cte_job_ids)),
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id == models.Job.resource_snapshot_id,
            )
            .offset(page_index)
            .limit(page_length)
        )
        jobs = list(db.session.scalars(jobs_stmt).all())

        job_dicts: dict[int, utils.JobDict] = {
            job.resource_id: utils.JobDict(
                job=job,
                artifacts=[],
                has_draft=False,
            )
            for job in jobs
        }

        return list(job_dicts.values()), total_num_jobs


class ExperimentJobIdService(object):
    """The service methods for getting or deleting a specific job within an experiment
    namespace."""

    @inject
    def __init__(
        self, experiment_id_service: ExperimentIdService, job_id_service: JobIdService
    ) -> None:
        """Initialize the ExperimentIdJob service.

        All arguments are provided via dependency injection.

        Args:
            experiment_id_service: An ExperimentIdService object.
            job_service: A JobService object.
        """
        self._experiment_id_service = experiment_id_service
        self._job_id_service = job_id_service

    def get(self, experiment_id: int, job_id: int, **kwargs) -> utils.JobDict:
        """Fetch a job by its unique id under a given experiment namespace.

        Args:
            experiment_id: The unique id of the experiment.
            job_id: The unique id of the job.

        Returns:
            The job object if found, otherwise None.

        Raises:
            ExperimentJobDoesNotExistError: If the job associated with the experiment
                is not found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        experiment_job_stmt = select(models.ExperimentJob).where(
            models.ExperimentJob.experiment_id == experiment_id,
            models.ExperimentJob.job_resource_id == job_id,
        )
        experiment_job = db.session.scalar(experiment_job_stmt)

        if experiment_job is None:
            log.debug(
                "Experiment Job not found",
                job_id=job_id,
                experiment_id=experiment_id,
            )
            raise ExperimentJobDoesNotExistError

        return cast(
            utils.JobDict,
            self._job_id_service.get(
                job_id=job_id,
                error_if_not_found=True,
                log=log,
            ),
        )

    def delete(self, experiment_id: int, job_id: int, **kwargs) -> dict[str, Any]:
        """Delete a job.

        Args:
            experiment_id: The unique id of the experiment.
            job_id: The unique id of the job.

        Returns:
            A dictionary reporting the status of the request.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        experiment_job_stmt = select(models.ExperimentJob).where(
            models.ExperimentJob.experiment_id == experiment_id,
            models.ExperimentJob.job_resource_id == job_id,
        )
        experiment_job = db.session.scalar(experiment_job_stmt)

        if experiment_job is None:
            log.debug(
                "Job associated with experiment not found",
                job_id=job_id,
                experiment_id=experiment_id,
            )
            raise ExperimentJobDoesNotExistError

        return self._job_id_service.delete(
            job_id=job_id,
            log=log,
        )


class ExperimentJobIdStatusService(object):
    """The service methods for retrieving the status of a job by unique id."""

    @inject
    def __init__(
        self,
        experiment_job_id_service: ExperimentJobIdService,
    ) -> None:
        """Initialize the job status service.

        All arguments are provided via dependency injection.

        Args:
            experiment_job_id_service: An ExperimentJobIdService object.
        """
        self._experiment_job_id_service = experiment_job_id_service

    def get(
        self,
        experiment_id: int,
        job_id: int,
        **kwargs,
    ) -> dict[str, Any]:
        """Fetch a job's status by its unique id.

        Args:
            experiment_id: The unique id of the experiment.
            job_id: The unique id of the job.

        Returns:
            The status message job object if found, otherwise an error message.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get job status by id", job_id=job_id)

        job_dict = cast(
            utils.JobDict,
            self._experiment_job_id_service.get(
                experiment_id, job_id, error_if_not_found=True, log=log
            ),
        )
        job = job_dict["job"]

        return {"status": job.status, "id": job.resource_id}

    def modify(
        self,
        experiment_id: int,
        job_id: int,
        status: str,
        commit: bool = True,
        **kwargs,
    ) -> dict[str, Any] | None:
        """Modify a Job's status by unique id

        Args:
            experiment_id: The unique id of the experiment.
            job_id: The unique id of the job.
            status: The new status of the job.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The status message job object if found, otherwise an error message.
        """

        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Modify job status by id", job_id=job_id, status=status)

        job_dict = self._experiment_job_id_service.get(experiment_id, job_id, log=log)
        job = job_dict["job"]

        if status not in JOB_STATUS_TRANSITIONS.get(job.status, None):
            raise JobInvalidStatusTransitionError

        new_job = models.Job(
            timeout=job.timeout,
            status=status,
            description=job.description,
            resource=job.resource,
            creator=job.creator,
        )
        new_job.entry_point_job = job.entry_point_job
        new_job.experiment_job = job.experiment_job
        new_job.queue_job = job.queue_job

        db.session.add(new_job)

        if commit:
            db.session.commit()
            log.debug(
                "Job status modification successful",
                job_id=job_id,
                status=status,
            )

        return {"status": new_job.status, "id": job.resource_id}


class ExperimentJobIdMlflowrunService(object):
    """The service methods for managing the mlflow run id of a job by unique id."""

    @inject
    def __init__(
        self,
        experiment_job_id_service: ExperimentJobIdService,
    ) -> None:
        """Initialize the job status service.

        All arguments are provided via dependency injection.

        Args:
            experiment_job_id_service: An ExperimentJobIdService object.
        """
        self._experiment_job_id_service = experiment_job_id_service

    def get(
        self,
        experiment_id: int,
        job_id: int,
        **kwargs,
    ) -> dict[str, Any]:
        """Fetch a job's mlflow run id by its unique id.

        Args:
            experiment_id: The unique id of the experiment.
            job_id: The unique id of the job.

        Returns:
            The status message job object if found, otherwise an error message.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get job status by id", job_id=job_id)

        job_dict = cast(
            utils.JobDict,
            self._experiment_job_id_service.get(
                experiment_id, job_id, error_if_not_found=True, log=log
            ),
        )
        job = job_dict["job"]

        mlflow_run_id = (
            job.mlflow_run.mlflow_run_id if job.mlflow_run is not None else None
        )
        return {"mlflow_run_id": mlflow_run_id}

    def create(
        self,
        experiment_id: int,
        job_id: int,
        mlflow_run_id: str,
        commit: bool = True,
        **kwargs,
    ) -> dict[str, Any] | None:
        """Set a Job's mlflow run id by unique id

        Args:
            experiment_id: The unique id of the experiment.
            job_id: The unique id of the job.
            mlflow_run_id: The unique id of the mlflow run.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The status message job object if found, otherwise an error message.
        """

        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug(
            "Set the job's mlflow run id", job_id=job_id, mlflow_run_id=mlflow_run_id
        )

        job_dict = self._experiment_job_id_service.get(experiment_id, job_id, log=log)
        job = job_dict["job"]

        if job.mlflow_run is not None:
            raise JobMlflowRunAlreadySetError

        job.mlflow_run = models.JobMlflowRun(
            job_resource_id=job.resource_id,
            mlflow_run_id=mlflow_run_id,
        )

        if commit:
            db.session.commit()
            log.debug(
                "Setting Job mlflow run id successful",
                job_id=job_id,
                mlflow_run_id=mlflow_run_id,
            )

        return {"mlflow_run_id": job.mlflow_run.mlflow_run_id}


class JobIdMlflowrunService(object):
    """The service methods for managing the mlflow run id of a job by unique id."""

    @inject
    def __init__(
        self,
        job_id_service: JobIdService,
    ) -> None:
        """Initialize the job status service.

        All arguments are provided via dependency injection.

        Args:
            job_id_service: An JobIdService object.
        """
        self._job_id_service = job_id_service

    def get(
        self,
        job_id: int,
        **kwargs,
    ) -> dict[str, Any]:
        """Fetch a job's mlflow run id by its unique id.

        Args:
            job_id: The unique id of the job.

        Returns:
            The status message job object if found, otherwise an error message.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get job status by id", job_id=job_id)

        job_dict = cast(
            utils.JobDict,
            self._job_id_service.get(job_id, error_if_not_found=True, log=log),
        )
        job = job_dict["job"]

        mlflow_run_id = (
            job.mlflow_run.mlflow_run_id if job.mlflow_run is not None else None
        )
        return {"mlflow_run_id": mlflow_run_id}

    def create(
        self,
        job_id: int,
        mlflow_run_id: str,
        commit: bool = True,
        **kwargs,
    ) -> dict[str, Any] | None:
        """Set a Job's mlflow run id by unique id

        Args:
            job_id: The unique id of the job.
            mlflow_run_id: The unique id of the mlflow run.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The status message job object if found, otherwise an error message.
        """

        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug(
            "Set the job's mlflow run id", job_id=job_id, mlflow_run_id=mlflow_run_id
        )

        job_dict = cast(
            utils.JobDict,
            self._job_id_service.get(job_id, error_if_not_found=True, log=log),
        )
        job = job_dict["job"]

        if job.mlflow_run is not None:
            raise JobMlflowRunAlreadySetError

        job.mlflow_run = models.JobMlflowRun(
            job_resource_id=job.resource_id,
            mlflow_run_id=mlflow_run_id,
        )

        if commit:
            db.session.commit()
            log.debug(
                "Setting Job mlflow run id successful",
                job_id=job_id,
                mlflow_run_id=mlflow_run_id,
            )

        return {"mlflow_run_id": job.mlflow_run.mlflow_run_id}
