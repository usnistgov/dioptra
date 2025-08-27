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

from collections.abc import Iterable
from typing import Any, Final, cast

import structlog
from flask_login import current_user
from injector import inject
from sqlalchemy import delete, func, select, and_
from sqlalchemy.orm import aliased
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import db, models
from dioptra.restapi.errors import (
    BackendDatabaseError,
    DioptraError,
    EntityDoesNotExistError,
    EntityNotRegisteredError,
    JobArtifactParameterMissingError,
    JobInvalidParameterNameError,
    JobInvalidStatusTransitionError,
    JobMlflowRunAlreadySetError,
    JobMlflowRunNotSetError,
    SortParameterValidationError,
)
from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.artifacts.snapshot import ArtifactSnapshotIdService
from dioptra.restapi.v1.entrypoints.service import (
    RESOURCE_TYPE as ENTRYPOINT_RESOURCE_TYPE,
)
from dioptra.restapi.v1.entrypoints.service import (
    EntrypointIdService,
)
from dioptra.restapi.v1.experiments.service import (
    RESOURCE_TYPE as EXPERIMENT_RESOURCE_TYPE,
)
from dioptra.restapi.v1.experiments.service import (
    ExperimentIdService,
)
from dioptra.restapi.v1.groups.service import GroupIdService
from dioptra.restapi.v1.queues.service import RESOURCE_TYPE as QUEUE_RESOURCE_TYPE
from dioptra.restapi.v1.queues.service import QueueIdService
from dioptra.restapi.v1.shared.job_run_store import JobRunStoreProtocol
from dioptra.restapi.v1.shared.rq_service import RQServiceV1
from dioptra.restapi.v1.shared.search_parser import construct_sql_query_filters

from .schema import JobLogSeverity

LOGGER: BoundLogger = structlog.stdlib.get_logger()

RESOURCE_TYPE: Final[str] = "job"
SEARCHABLE_FIELDS: Final[dict[str, Any]] = {
    "description": lambda x: models.Job.description.like(x),
    "status": lambda x: models.Job.status.like(x),
    "timeout": lambda x: models.Job.timeout.like(x),
    "tag": lambda x: models.Job.tags.any(models.Tag.name.like(x, escape="/")),
}
SORTABLE_FIELDS: Final[dict[str, Any]] = {
    "id": models.Resource.resource_id,
    "description": models.Job.description,
    "createdOn": models.Job.created_on,
    "lastModifiedOn": models.Resource.last_modified_on,
    "status": models.Job.status,
    "experiment": models.Experiment.name,
    "entrypoint": models.EntryPoint.name,
    "queue": models.Queue.name,
}
JOB_STATUS_TRANSITIONS: Final[dict[str, Any]] = {
    "queued": {"started", "deferred", "reset"},
    "started": {"finished", "failed", "reset"},
    "deferred": {"started", "reset"},
    "failed": {"reset"},
    "finished": {"reset"},
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
        artifact_snapshot_id_service: ArtifactSnapshotIdService,
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
        self._artifact_snapshot_id_service = artifact_snapshot_id_service
        self._group_id_service = group_id_service
        self._rq_service = rq_service

    def create(
        self,
        experiment_id: int,
        queue_id: int,
        entrypoint_id: int,
        values: dict[str, str],
        artifact_value_ids: dict[str, dict[str, int]],
        description: str,
        timeout: str,
        entrypoint_snapshot_id: int | None = None,
        **kwargs,
    ) -> utils.JobDict:
        """Create a new job.

        Args:
            experiment_id: The unique id for the experiment this job is under.
            queue_id: The unique id for the queue this job will execute on.
            entrypoint_id: The unique id for the entrypoint defining the job.
            values: The parameter values passed to the entrypoint to configure the job.
            artifact_value_ids: The artifact values passed to the entrypoint to
                configure the job.
            description: The description of the job.
            timeout: The length of time the job will run before timing out.
            group_id: The group that will own the job.

        Returns:
            The newly created job object.

        Raises:
            EntityExistsError: If a job with the given name already exists.
            EntityDoesNotExistError: if any of the values in artifact_value_ids does not
                correspond with an Artifact
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
            raise EntityNotRegisteredError(
                EXPERIMENT_RESOURCE_TYPE,
                experiment_id,
                ENTRYPOINT_RESOURCE_TYPE,
                entrypoint_id,
            )

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
            raise EntityNotRegisteredError(
                ENTRYPOINT_RESOURCE_TYPE, entrypoint_id, QUEUE_RESOURCE_TYPE, queue_id
            )

        # Fetch the validated queue
        queue_dict = cast(
            utils.QueueDict,
            self._queue_id_service.get(queue_id, error_if_not_found=True, log=log),
        )
        queue = queue_dict["queue"]

        # Fetch the validated entrypoint
        entrypoint_dict = self._entrypoint_id_service.get(
            entrypoint_id, entrypoint_snapshot_id=entrypoint_snapshot_id, log=log
        )
        entrypoint = entrypoint_dict["entry_point"]

        # Validate the keys in values against the registered entrypoint parameter names
        invalid_job_params = list(
            set(values.keys()) - {param.name for param in entrypoint.parameters}
        )
        if len(invalid_job_params) > 0:
            log.debug("Invalid parameter names", parameters=invalid_job_params)
            raise JobInvalidParameterNameError(invalid_job_params)

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

        entrypoint_artifact_values = self._create_entrypoint_artifact_values(
            artifact_value_ids=artifact_value_ids,
            entrypoint=entrypoint,
            job_resource=job_resource,
            log=log,
        )

        new_job = models.Job(
            timeout=timeout,
            status=status,
            description=description,
            resource=job_resource,
            creator=current_user,
        )
        db.session.add(new_job)
        new_job.entry_point_job = models.EntryPointJob(
            job_resource=job_resource,
            entry_point=entrypoint,
            entry_point_parameter_values=entrypoint_parameter_values,
            entry_point_artifact_parameter_values=entrypoint_artifact_values,
        )
        new_job.experiment_job = models.ExperimentJob(
            job_resource=job_resource,
            experiment=experiment,
        )
        new_job.queue_job = models.QueueJob(
            job_resource=job_resource,
            queue=queue,
        )
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

    def _create_entrypoint_artifact_values(
        self,
        artifact_value_ids: dict[str, dict[str, int]],
        entrypoint: models.EntryPoint,
        job_resource: models.Resource,
        log: BoundLogger,
    ) -> list[models.EntryPointArtifactParameterValue]:
        # Validate the keys in artifact_values against the registered entrypoint
        # artifact names, retrieve the artifacts, verify that there are no extra
        invalid_artifact_params = set(artifact_value_ids.keys())
        missing_artifact_params: list[str] = []
        entrypoint_artifact_values: list[models.EntryPointArtifactParameterValue] = []
        for artifact_parameter in entrypoint.artifact_parameters:
            try:
                invalid_artifact_params.remove(artifact_parameter.name)

                value = artifact_value_ids[artifact_parameter.name]
                # if no artifact found, will raise EntityDoesNotExist
                artifact = self._artifact_snapshot_id_service.get(
                    artifact_id=value["id"], artifact_snapshot_id=value["snapshot_id"]
                )

                # test that types match -- including the order
                len_task_params = len(artifact.task.output_parameters)
                len_artifact_params = len(artifact_parameter.output_parameters)
                if len_task_params != len_artifact_params:
                    message = (
                        "Output parameter types do not match. Different number of "
                        "types: expected {len_artifact_params} and received "
                        f"{len_task_params} types for parameter "
                        f"{artifact_parameter.name}"
                    )
                    log.error(message)
                    raise DioptraError(message)

                if [
                    param.parameter_type.resource_snapshot_id
                    for param in sorted(
                        artifact_parameter.output_parameters,
                        key=lambda x: x.parameter_number,
                    )
                ] != [
                    param.parameter_type.resource_snapshot_id
                    for param in sorted(
                        artifact_parameter.output_parameters,
                        key=lambda x: x.parameter_number,
                    )
                ]:
                    raise DioptraError(
                        "Output parameter types do not match for "
                        f"parameter {artifact_parameter.name}."
                    )

                entrypoint_artifact_values.append(
                    models.EntryPointArtifactParameterValue(
                        artifact=artifact,
                        job_resource=job_resource,
                        artifact_parameter=artifact_parameter,
                    )
                )
            except KeyError:
                # an artifact parameter was not provided
                missing_artifact_params.append(artifact_parameter.name)

        # anything left-over was not a valid artifact parameter
        if len(invalid_artifact_params) > 0:
            raise JobInvalidParameterNameError(
                list(invalid_artifact_params), artifact=True
            )
        if len(missing_artifact_params) > 0:
            raise JobArtifactParameterMissingError(list(invalid_artifact_params))

        return entrypoint_artifact_values

    def get(
        self,
        group_id: int | None,
        search_string: str,
        page_index: int,
        page_length: int,
        sort_by_string: str,
        descending: bool,
        **kwargs,
    ) -> tuple[list[utils.JobDict], int]:
        """Fetch a list of jobs, optionally filtering by search string and paging
        parameters.

        Args:
            group_id: A group ID used to filter results.
            search_string: A search string used to filter results.
            page_index: The index of the first group to be returned.
            page_length: The maximum number of jobs to be returned.
            sort_by_string: The name of the column to sort.
            descending: Boolean indicating whether to sort by descending or not.

        Returns:
            A tuple containing a list of jobs and the total number of jobs matching
            the query.

        Raises:
            BackendDatabaseError: If the database query returns a None when counting
                the number of jobs.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get full list of jobs")

        filters = []

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
            .join(models.Job.experiment_job)
            .join(models.ExperimentJob.experiment)
            .join(models.Job.entry_point_job)
            .join(models.EntryPointJob.entry_point)
            .join(models.Job.queue_job)
            .join(models.QueueJob.queue)
            .where(
                *filters,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id == models.Job.resource_snapshot_id,
            )
            .offset(page_index)
            .limit(page_length)
        )

        if sort_by_string and sort_by_string in SORTABLE_FIELDS:
            sort_column = SORTABLE_FIELDS[sort_by_string]
            if descending:
                sort_column = sort_column.desc()
            else:
                sort_column = sort_column.asc()
            jobs_stmt = jobs_stmt.order_by(sort_column)
        elif sort_by_string and sort_by_string not in SORTABLE_FIELDS:
            raise SortParameterValidationError(RESOURCE_TYPE, sort_by_string)

        jobs = list(db.session.scalars(jobs_stmt).all())
        return _build_job_dict(jobs), total_num_jobs


class JobIdService(object):
    """The service methods for registering and managing jobs by their unique id."""

    def get(
        self,
        job_id: int,
        **kwargs,
    ) -> utils.JobDict:
        """Fetch a job by its unique id.

        Args:
            job_id: The unique id of the job.

        Returns:
            The job object if found, otherwise None.

        Raises:
            EntityDoesNotExistError: If the job is not found
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
            raise EntityDoesNotExistError(RESOURCE_TYPE, job_id=job_id)

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
            raise EntityDoesNotExistError(RESOURCE_TYPE, job_id=job_id)

        deleted_resource_lock = models.ResourceLock(
            resource_lock_type="delete",
            resource=job_resource,
        )
        db.session.add(deleted_resource_lock)
        db.session.commit()
        log.debug("Job deleted", job_id=job_id)

        return {"status": "Success", "id": [job_id]}

    def get_parameter_values(
        self, job_id: int, **kwargs
    ) -> list[models.EntryPointParameterValue]:
        """Run a query to get the parameter values for the job.

        Args:
            job_id: The ID of the job to get the parameter values for.
            logger: A structlog logger object to use for logging. A new logger will be
                created if None.

        Returns:
            The parameter values for the job.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841

        entry_point_param_values_stmt = select(models.EntryPointParameterValue).where(
            models.EntryPointParameterValue.job_resource_id == job_id,
        )
        return list(db.session.scalars(entry_point_param_values_stmt).unique().all())

    def get_artifact_values(
        self, job_id: int, **kwargs
    ) -> list[models.EntryPointArtifactParameterValue]:
        """Run a query to get the artfiact values for the job.

        Args:
            job_id: The ID of the job to get the artifact values for.
            logger: A structlog logger object to use for logging. A new logger will be
                created if None.

        Returns:
            The parameter values for the job.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841

        entry_point_artifact_values_stmt = select(
            models.EntryPointArtifactParameterValue
        ).where(
            models.EntryPointArtifactParameterValue.job_resource_id == job_id,
        )
        return list(db.session.scalars(entry_point_artifact_values_stmt).unique().all())


class JobIdStatusService(object):
    """The service methods for retrieving the status of a job by unique id."""

    @inject
    def __init__(
        self,
    ) -> None:
        """Initialize the job status service.

        All arguments are provided via dependency injection.
        """
        pass

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
            raise EntityDoesNotExistError(RESOURCE_TYPE, job_id=job_id)

        return {"status": job.status, "id": job.resource_id}


class JobIdMetricsService(object):
    """The service methods for retrieving the metrics of a job by unique id."""

    @inject
    def __init__(
        self,
        job_id_service: JobIdService
    ) -> None:
        """Initialize the job metrics service.

        All arguments are provided via dependency injection.

        """
        self._job_id_service = job_id_service

    def get(
        self,
        job_id: int,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Fetch a job's metrics by its unique id.

        Args:
            job_id: The unique id of the job.

        Returns:
            The metrics for the requested job if found, otherwise an error message.
        """

        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get job metrics by id", job_id=job_id)

        job_metrics_max_step_sub_query = select(
            models.JobMetric.name, func.max(models.JobMetric.step).label("mstep")
        ).where(
            models.JobMetric.job_resource_id == job_id
        ).group_by(
            models.JobMetric.name
        ).subquery()
        
        job_metrics_stmt = select(
            models.JobMetric
        ).where(
            models.JobMetric.job_resource_id == job_id
        ).join_from(
            models.JobMetric,
            job_metrics_max_step_sub_query,
            and_(models.JobMetric.name == job_metrics_max_step_sub_query.c.name, models.JobMetric.step == job_metrics_max_step_sub_query.c.mstep)
        )

        #select metrics with the highest step value
        job_metrics = list(db.session.scalars(job_metrics_stmt).unique().all())

        job_metrics_dict = {}

        # select metrics with the biggest timestamp for each metric name + step
        for job_metric in job_metrics:
            kept = job_metrics_dict.get(job_metric.name, None)

            if kept is None or kept.timestamp < job_metric.timestamp:
                job_metrics_dict[job_metric.name] = job_metric
    
        
        return list(job_metrics_dict.values())

    def update(
        self,
        job_id: int,
        metric_name: str,
        metric_value: float | None,
        metric_step: int | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Update a job's metrics by its unique id.

        Args:
            job_id: The unique id of the job.
            metric_name: The name of the metric to create or update.
            metric_value: The value of the metric being updated.
        Returns:
            The metric dictionary passed in if successful, otherwise an error message.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Update job metrics by id", job_id=job_id)

        job_dict = self._job_id_service.get(job_id, error_if_not_found=True)
        # can't be None since error_if_not_found is True: the .get() call would
        # error instead of returning None.
        assert job_dict is not None
        job = job_dict["job"]

        new_metric = models.JobMetric(name=metric_name, value=metric_value, step=metric_step, job_resource=job.resource)

        db.session.add(new_metric)
        db.session.commit()

        return {"name": metric_name, "value": metric_value}


class JobIdMetricsSnapshotsService(object):
    """The service methods for retrieving the historical metrics of a
    job by unique id and metric name."""

    @inject
    def __init__(
        self,
        job_id_mlflowrun_service: "JobIdMlflowrunService",
        job_run_store: JobRunStoreProtocol,
    ) -> None:
        """Initialize the job metrics snapshots service.

        All arguments are provided via dependency injection.
        """
        self._job_id_mlflowrun_service = job_id_mlflowrun_service
        self._job_run_store = job_run_store

    def get(
        self,
        job_id: int,
        metric_name: str,
        page_index: int,
        page_length: int,
        **kwargs,
    ) -> tuple[list[dict[str, Any]], int]:
        """Fetch a job's metrics by its unique id and metric name.

        Args:
            job_id: The unique id of the job.
            metric_name: The name of the metric.
            page_index: The index of the first page to be returned.
            page_length: The maximum number of experiments to be returned.
        Returns:
            The metric history for the requested job and metric if found,
            otherwise an error message.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug(
            "Get job metric history by id and name",
            job_id=job_id,
            metric_name=metric_name,
        )

        job_metrics_stmt = select(
            models.JobMetric
        ).where(
            models.JobMetric.job_resource_id == job_id,
            models.JobMetric.name == metric_name
        )
        
        history =  list(db.session.scalars(job_metrics_stmt).unique().all())

        metrics_page = [
            {
                "name": metric.name,
                "value": metric.value,
                "step": metric.step,
                "timestamp": metric.timestamp,
            }
            for metric in history[
                page_index * page_length : (page_index + 1) * page_length
            ]
        ]
        return metrics_page, len(history)


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
        artifact_values: dict[str, dict[str, int]],
        description: str,
        timeout: str,
        entrypoint_snapshot_id: int | None = None,
        **kwargs,
    ) -> utils.JobDict:
        """Create a new job within an experiment.

        Args:
            experiment_id: The unique id for the experiment this job is under.
            queue_id: The unique id for the queue this job will execute on.
            entrypoint_id: The unique id for the entrypoint defining the job.
            values: The parameter values passed to the entrypoint to configure the job.
            artifact_values: The artifact values passed to the entrypoint to configure
                the job.
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
            artifact_value_ids=artifact_values,
            description=description,
            timeout=timeout,
            entrypoint_snapshot_id=entrypoint_snapshot_id,
            log=log,
        )

    def get(
        self,
        experiment_id: int,
        search_string: str,
        page_index: int,
        page_length: int,
        sort_by_string: str,
        descending: bool,
        **kwargs,
    ) -> tuple[list[utils.JobDict], int]:
        """Fetch a list of jobs for a given experiment, optionally filtering by search
        string and paging parameters.

        Args:
            experiment_id: The unique id of the experiment.
            search_string: A search string used to filter results.
            page_index: The index of the first page to be returned.
            page_length: The maximum number of experiments to be returned.
            sort_by_string: The name of the column to sort.
            descending: Boolean indicating whether to sort by descending or not.

        Returns:
            A tuple containing a list of jobs and the total number of jobs matching the
            query.

        Raises:
            EntityDoesNotExistError: If the experiment is not found.
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
            .join(models.Job.entry_point_job)
            .join(models.EntryPointJob.entry_point)
            .join(models.Job.queue_job)
            .join(models.QueueJob.queue)
            .where(
                *filters,
                models.Job.resource_id.in_(select(cte_job_ids)),
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id == models.Job.resource_snapshot_id,
            )
            .offset(page_index)
            .limit(page_length)
        )

        if sort_by_string and sort_by_string in SORTABLE_FIELDS:
            sort_column = SORTABLE_FIELDS[sort_by_string]
            if descending:
                sort_column = sort_column.desc()
            else:
                sort_column = sort_column.asc()
            jobs_stmt = jobs_stmt.order_by(sort_column)
        elif sort_by_string and sort_by_string not in SORTABLE_FIELDS:
            raise SortParameterValidationError(RESOURCE_TYPE, sort_by_string)

        jobs = list(db.session.scalars(jobs_stmt).all())
        return _build_job_dict(jobs), total_num_jobs


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
            EntityDoesNotExistError: If the job associated with the experiment
                is not found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        experiment_job_stmt = select(models.ExperimentJob).where(
            models.ExperimentJob.experiment_id == experiment_id,
            models.ExperimentJob.job_resource_id == job_id,
        )
        experiment_job = db.session.scalar(experiment_job_stmt)

        if experiment_job is None:
            raise EntityDoesNotExistError(
                RESOURCE_TYPE, job_id=job_id, experiment_id=experiment_id
            )

        return self._job_id_service.get(job_id=job_id, log=log)

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
            raise EntityDoesNotExistError(
                RESOURCE_TYPE, job_id=job_id, experiment_id=experiment_id
            )

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

        job_dict = self._experiment_job_id_service.get(
            experiment_id, job_id, error_if_not_found=True, log=log
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

        if status not in JOB_STATUS_TRANSITIONS.get(job.status, set()):
            raise JobInvalidStatusTransitionError
        if status == "reset":
            db.session.execute(
                delete(models.JobMlflowRun).where(
                    models.JobMlflowRun.job_resource_id == job_id
                )
            )
            status = "queued"

        new_job = models.Job(
            timeout=job.timeout,
            status=status,
            description=job.description,
            resource=job.resource,
            creator=job.creator,
        )
        db.session.add(new_job)
        new_job.entry_point_job = job.entry_point_job
        new_job.experiment_job = job.experiment_job
        new_job.queue_job = job.queue_job

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

        job_dict = self._experiment_job_id_service.get(
            experiment_id, job_id, error_if_not_found=True, log=log
        )
        job = job_dict["job"]

        mlflow_run_id = (
            job.mlflow_run.mlflow_run_id.hex if job.mlflow_run is not None else None
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

        return {"mlflow_run_id": job.mlflow_run.mlflow_run_id.hex}


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
    ) -> str | None:
        """Fetch a job's mlflow run id by its unique id.

        Args:
            job_id: The unique id of the job.

        Returns:
            The MlflowRun id of the job object, otherwise None if the job exists but
            does not yet have an mlflow run ID.

        Raises:
            EntityDoesNotExistError: If the job is not found
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get job status by id", job_id=job_id)

        job_dict = self._job_id_service.get(job_id, log=log)
        job = job_dict["job"]

        return job.mlflow_run.mlflow_run_id.hex if job.mlflow_run is not None else None

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

        job_dict = self._job_id_service.get(job_id, log=log)
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

        return {"mlflow_run_id": job.mlflow_run.mlflow_run_id.hex}


class ExperimentMetricsService(object):
    """The service methods for retrieving metrics attached to jobs in the experiment."""

    @inject
    def __init__(
        self,
        experiment_jobs_service: ExperimentJobService,
        job_id_metrics_service: JobIdMetricsService,
    ) -> None:
        """Initialize the experiment service.

        All arguments are provided via dependency injection.
        """
        self._job_id_metrics_service = job_id_metrics_service
        self._experiment_jobs_service = experiment_jobs_service

    def get(
        self,
        experiment_id: int,
        search_string: str,
        page_index: int,
        page_length: int,
        sort_by_string: str,
        descending: bool,
        **kwargs,
    ):
        """Get a list of jobs and the latest metrics associated with each.

        Args:
            experiment_id: The unique id of the experiment.
            error_if_not_found: If True, raise an error if the experiment is not found.
                Defaults to False.

        Returns:
            The list of jobs and the metrics associated with them.

        Raises:
            EntityDoesNotExistError: If the experiment is not found and
                `error_if_not_found` is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug(
            "Get metrics for all jobs for an experiment by resource id",
            resource_id=experiment_id,
        )

        jobs, num_jobs = self._experiment_jobs_service.get(
            experiment_id,
            search_string=search_string,
            page_index=page_index,
            page_length=page_length,
            sort_by_string=sort_by_string,
            descending=descending,
            **kwargs,
        )

        job_ids = [job["job"].resource_id for job in jobs]

        metrics_for_jobs = [
            {"id": job_id, "metrics": self._job_id_metrics_service.get(job_id)}
            for job_id in job_ids
        ]
        return metrics_for_jobs, num_jobs


class JobLogService(object):
    @inject
    def __init__(self, job_id_service: JobIdService):
        self._job_id_service = job_id_service

    def add_logs(
        self, job_resource_id: int, records: Iterable[dict[str, Any]], **kwargs
    ) -> list[dict[str, Any]]:
        """
        Add the given log records to the database.

        Args:
            job_resource_id: The resource ID of a job
            records: An iterable of dicts, where each dict complies with the
                JobLogRecordSchema marshmallow schema (after loading).
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Add job logs", job_id=job_resource_id)
        job_dict = self._job_id_service.get(job_resource_id, error_if_not_found=True)
        # can't be None since error_if_not_found is True: the .get() call would
        # error instead of returning None.
        assert job_dict is not None

        job = job_dict["job"]
        job_logs: list[models.JobLog] = []

        for record in records:
            job_log = models.JobLog(
                severity=record["severity"].name,
                logger_name=record["logger_name"],
                message=record["message"],
                job_resource=job.resource,
            )
            db.session.add(job_log)
            job_logs.append(job_log)

        db.session.commit()
        response = [
            {
                "severity": JobLogSeverity[log.severity],
                "logger_name": log.logger_name,
                "message": log.message,
                "created_on": log.created_on,
            }
            for log in job_logs
        ]
        return response

    def get_logs(
        self,
        job_resource_id: int,
        index: int,
        page_length: int,
        **kwargs,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        Get log records from the database, for the given job.

        Args:
            job_resource_id: The resource ID of a job
            index: Zero-based index of the first log record to return
            page_length: The number of records to return

        Returns:
            A 2-tuple including (1) The list of records comprising this page,
            each complying with JobLogRecordSchema, and (2) the total number of
            records across all pages.
        """

        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get job logs", job_id=job_resource_id)
        count_stmt = (
            select(func.count())
            .select_from(models.JobLog)
            .where(models.JobLog.job_resource_id == job_resource_id)
        )
        total_count = db.session.scalar(count_stmt)
        # "select count(*) ..." can't produce None
        assert total_count is not None

        page_stmt = (
            select(models.JobLog)
            .where(models.JobLog.job_resource_id == job_resource_id)
            .order_by(models.JobLog.id)
            .offset(index)
            .limit(page_length)
        )

        log_objs = db.session.scalars(page_stmt)

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


def _build_job_dict(jobs: list[models.Job]) -> list[utils.JobDict]:
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

    return list(job_dicts.values())
