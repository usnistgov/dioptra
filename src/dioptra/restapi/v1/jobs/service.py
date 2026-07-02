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

import datetime
import math
from collections.abc import Iterable
from typing import Any

import structlog
from flask_login import current_user
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import models
from dioptra.restapi.db.repository.utils.common import DeletionPolicy
from dioptra.restapi.errors import (
    DioptraError,
    JobArtifactParameterMissingError,
    JobInvalidParameterNameError,
    JobMlflowRunAlreadySetError,
    JobParameterMissingError,
)
from dioptra.restapi.service_context import ServiceContext, ServiceContextService
from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.entity_types import EntityType
from dioptra.restapi.v1.shared.search_parser import parse_search_text
from dioptra.restapi.v1.shared.task_engine_yaml.service import (
    check_artifact_param_type_mismatch,
    coerce_entrypoint_param_types,
)

from .schema import JobLogSeverity

LOGGER: BoundLogger = structlog.stdlib.get_logger()


def _create_job(
    context: ServiceContext,
    experiment_id: int,
    queue_id: int,
    entrypoint_id: int,
    values: dict[str, str],
    artifact_value_ids: dict[str, dict[str, int]],
    description: str,
    timeout: str,
    entrypoint_snapshot_id: int | None,
    log: BoundLogger,
) -> utils.JobDict:
    uow = context.uow

    status = "queued"

    uow.job_repo.assert_resources_registered(entrypoint_id, experiment_id, queue_id)

    experiment = uow.experiment_repo.get_one(experiment_id, DeletionPolicy.NOT_DELETED)
    queue = uow.queue_repo.get_one(queue_id, DeletionPolicy.NOT_DELETED)

    if entrypoint_snapshot_id is None:
        entrypoint = uow.entrypoint_repo.get_one(
            entrypoint_id, DeletionPolicy.NOT_DELETED
        )
    else:
        entrypoint = uow.entrypoint_repo.get_one_snapshot(
            entrypoint_id, entrypoint_snapshot_id, DeletionPolicy.NOT_DELETED
        )

    invalid_job_params = list(
        set(values.keys()) - {param.name for param in entrypoint.parameters}
    )
    if len(invalid_job_params) > 0:
        log.debug("Invalid parameter names", parameters=invalid_job_params)
        raise JobInvalidParameterNameError(invalid_job_params)

    job_resource = models.Resource(
        EntityType.JOB.db_table_name, experiment.resource.owner
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

    missing_parameter_values = [
        param.parameter.name
        for param in entrypoint_parameter_values
        if param.value is None
    ]
    if len(missing_parameter_values) > 0:
        raise JobParameterMissingError(missing_parameter_values)

    coerce_entrypoint_param_types(entrypoint_parameter_values)

    entrypoint_artifact_values = _create_entrypoint_artifact_values(
        context=context,
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
    new_job.queue_job = models.QueueJob(job_resource=job_resource, queue=queue)

    with uow():
        uow.job_repo.create(new_job)

    context.job_queue.submit(
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
    context: ServiceContext,
    artifact_value_ids: dict[str, dict[str, int]],
    entrypoint: models.EntryPoint,
    job_resource: models.Resource,
    log: BoundLogger,
) -> list[models.EntryPointArtifactParameterValue]:
    uow = context.uow
    invalid_artifact_params = set(artifact_value_ids.keys())
    missing_artifact_params: list[str] = []
    entrypoint_artifact_values: list[models.EntryPointArtifactParameterValue] = []
    for artifact_parameter in entrypoint.artifact_parameters:
        try:
            invalid_artifact_params.remove(artifact_parameter.name)

            value = artifact_value_ids[artifact_parameter.name]
            artifact = uow.artifact_repo.get_one_snapshot(
                value["id"], value["snapshot_id"], DeletionPolicy.NOT_DELETED
            )

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

            check_artifact_param_type_mismatch(
                artifact_parameter.output_parameters,
                artifact.task.output_parameters,
            )

            entrypoint_artifact_values.append(
                models.EntryPointArtifactParameterValue(
                    artifact=artifact,
                    job_resource=job_resource,
                    artifact_parameter=artifact_parameter,
                )
            )
        except KeyError:
            missing_artifact_params.append(artifact_parameter.name)

    if len(invalid_artifact_params) > 0:
        raise JobInvalidParameterNameError(list(invalid_artifact_params), artifact=True)
    if len(missing_artifact_params) > 0:
        raise JobArtifactParameterMissingError(missing_artifact_params)

    return entrypoint_artifact_values


class JobService(ServiceContextService):
    """The service methods for registering and managing jobs by their unique id."""

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

        return _create_job(
            context=self._context,
            experiment_id=experiment_id,
            queue_id=queue_id,
            entrypoint_id=entrypoint_id,
            values=values,
            artifact_value_ids=artifact_value_ids,
            description=description,
            timeout=timeout,
            entrypoint_snapshot_id=entrypoint_snapshot_id,
            log=log,
        )

    def get(
        self,
        group_id: int | None,
        search_string: str,
        page_index: int,
        page_length: int,
        sort_by_string: str,
        descending: bool,
        show_deleted: bool = False,
        **kwargs,
    ) -> tuple[list[utils.JobDict], int]:
        """Fetch a list of jobs, optionally filtering by search string and paging
        parameters.

        Args:
            group_id: A group ID used to filter results.
            search_string: A search string used to filter results.
            page_index: The index of the first page to be returned.
            page_length: The maximum number of jobs to be returned.
            sort_by_string: The name of the column to sort.
            descending: Boolean indicating whether to sort by descending or not.
            show_deleted: Boolean indicating whether to include deleted jobs.

        Returns:
            A tuple containing a list of jobs and the total number of jobs matching
            the query.

        Raises:
            BackendDatabaseError: If the database query returns a None when counting
                the number of jobs.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get full list of jobs")

        search_struct = parse_search_text(search_string)

        deletion_policy = (
            DeletionPolicy.ANY if show_deleted else DeletionPolicy.NOT_DELETED
        )

        jobs, total_num_jobs = self._uow.job_repo.get_by_filters_paged(
            group_id,
            None,
            search_struct,
            page_index,
            page_length,
            sort_by_string,
            descending,
            deletion_policy,
        )

        artifacts = self._uow.artifact_repo.get_by_job(
            *[job.resource_id for job in jobs],
            deletion_policy=deletion_policy,
        )

        return _build_job_dicts(list(jobs), list(artifacts)), total_num_jobs


class JobIdService(ServiceContextService):
    """The service methods for registering and managing jobs by their unique id."""

    def get(self, job_id: int, **kwargs) -> utils.JobDict:
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

        job = self._uow.job_repo.get_one(job_id, DeletionPolicy.ANY)

        artifacts = self._uow.artifact_repo.get_by_job(
            job_id, deletion_policy=DeletionPolicy.ANY
        )

        return utils.JobDict(job=job, artifacts=list(artifacts), has_draft=False)

    def delete(self, job_id: int, **kwargs) -> dict[str, Any]:
        """Delete a job.

        Args:
            job_id: The unique id of the job.

        Returns:
            A dictionary reporting the status of the request.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        with self._uow():
            # No-op if already deleted
            self._uow.job_repo.delete(job_id)

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

        job = self._uow.job_repo.get_one(job_id, DeletionPolicy.NOT_DELETED)

        log.debug("Retrieved entrypoint parameter values", job_id=job_id)

        return job.entry_point_job.entry_point_parameter_values

    def get_artifact_values(
        self, job_id: int, **kwargs
    ) -> list[models.EntryPointArtifactParameterValue]:
        """Run a query to get the artifact values for the job.

        Args:
            job_id: The ID of the job to get the artifact values for.
            logger: A structlog logger object to use for logging. A new logger will be
                created if None.

        Returns:
            The artifact values for the job.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841

        job = self._uow.job_repo.get_one(job_id, DeletionPolicy.NOT_DELETED)

        log.debug("Retrieved entrypoint artifact parameter values", job_id=job_id)

        return job.entry_point_job.entry_point_artifact_parameter_values


class JobIdStatusService(ServiceContextService):
    """The service methods for retrieving the status of a job by unique id."""

    def get(self, job_id: int, **kwargs) -> dict[str, Any]:
        """Fetch a job's status by its unique id.

        Args:
            job_id: The unique id of the job.

        Returns:
            The status message job object if found, otherwise an error message.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get job status by id", job_id=job_id)

        job = self._uow.job_repo.get_one(job_id, DeletionPolicy.NOT_DELETED)

        return {"status": job.status, "id": job.resource_id}


class JobIdMetricsService(ServiceContextService):
    """The service methods for retrieving the metrics of a job by unique id."""

    def get(self, job_id: int, **kwargs) -> list[dict[str, Any]]:
        """Fetch a job's metrics by its unique id.

        Args:
            job_id: The unique id of the job.

        Returns:
            The metrics for the requested job if found, otherwise an error message.
        """

        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get job metrics by id", job_id=job_id)

        job_metrics = self._uow.job_repo.get_latest_metrics(job_id)

        return [_build_metric_dict(job_metric) for job_metric in job_metrics]

    def update(
        self,
        job_id: int,
        metric_name: str,
        metric_value: float,
        metric_step: int,
        metric_timestamp: datetime.datetime | None,
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

        job = self._uow.job_repo.get_one(job_id, DeletionPolicy.NOT_DELETED)

        metric = self._uow.job_repo.get_metric_step(
            job_id, metric_name=metric_name, metric_step=metric_step
        )

        value, special_value = _prepare_metric_value(metric_value)
        timestamp = (
            metric_timestamp
            if metric_timestamp is not None
            else datetime.datetime.now(tz=datetime.timezone.utc)
        )

        with self._uow():
            if metric is None:
                new_metric = models.JobMetric(
                    name=metric_name,
                    value=value,
                    special_value=special_value,
                    step=metric_step,
                    timestamp=timestamp,
                    job_resource=job.resource,
                )

                self._uow.job_repo.add_metric(new_metric)
            else:
                metric.value = value
                metric.special_value = special_value
                metric.timestamp = timestamp

        return {
            "name": metric_name,
            "value": value if special_value is None else special_value,
        }


class JobIdMetricsSnapshotsService(ServiceContextService):
    """The service methods for retrieving the historical metrics of a
    job by unique id and metric name."""

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
            page_length: The maximum number of metric records to be returned.
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

        history_page, total_num_metrics = self._uow.job_repo.get_metric_history_paged(
            job_id,
            metric_name,
            page_index,
            page_length,
        )

        metrics_page = [
            {
                "name": metric.name,
                "value": metric.value
                if metric.special_value is None
                else metric.special_value,
                "step": metric.step,
                "timestamp": metric.timestamp,
            }
            for metric in history_page
        ]
        return metrics_page, total_num_metrics


class ExperimentJobService(ServiceContextService):
    """The service methods for submitting and retrieving jobs within an experiment
    namespace."""

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

        return _create_job(
            context=self._context,
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
        show_deleted: bool = False,
        **kwargs,
    ) -> tuple[list[utils.JobDict], int]:
        """Fetch a list of jobs for a given experiment, optionally filtering by search
        string and paging parameters.

        Args:
            experiment_id: The unique id of the experiment.
            search_string: A search string used to filter results.
            page_index: The index of the first page to be returned.
            page_length: The maximum number of jobs to be returned.
            sort_by_string: The name of the column to sort.
            descending: Boolean indicating whether to sort by descending or not.
            show_deleted: Boolean indicating whether to include deleted jobs.

        Returns:
            A tuple containing a list of jobs and the total number of jobs matching the
            query.

        Raises:
            EntityDoesNotExistError: If the experiment is not found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get full list of jobs for experiment", experiment_id=experiment_id)

        search_struct = parse_search_text(search_string)

        deletion_policy = (
            DeletionPolicy.ANY if show_deleted else DeletionPolicy.NOT_DELETED
        )

        jobs, total_num_jobs = self._uow.job_repo.get_by_filters_paged(
            None,
            experiment_id,
            search_struct,
            page_index,
            page_length,
            sort_by_string,
            descending,
            deletion_policy,
        )

        artifacts = self._uow.artifact_repo.get_by_job(
            *[job.resource_id for job in jobs],
            deletion_policy=deletion_policy,
        )

        return _build_job_dicts(list(jobs), list(artifacts)), total_num_jobs


class ExperimentJobIdService(ServiceContextService):
    """The service methods for getting or deleting a specific job within an experiment
    namespace."""

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
        job = self._uow.job_repo.get_one(
            job_id, DeletionPolicy.NOT_DELETED, experiment_id
        )

        artifacts = self._uow.artifact_repo.get_by_job(
            job_id, deletion_policy=DeletionPolicy.NOT_DELETED
        )

        return utils.JobDict(job=job, artifacts=list(artifacts), has_draft=False)

    def delete(self, experiment_id: int, job_id: int, **kwargs) -> dict[str, Any]:
        """Delete a job.

        Args:
            experiment_id: The unique id of the experiment.
            job_id: The unique id of the job.

        Returns:
            A dictionary reporting the status of the request.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        job = self._uow.job_repo.get_one(
            job_id, DeletionPolicy.NOT_DELETED, experiment_id
        )

        with self._uow():
            # No-op if already deleted
            self._uow.job_repo.delete(job)

        log.debug("Job deleted", job_id=job_id)

        return {"status": "Success", "id": [job_id]}


class ExperimentJobIdStatusService(ServiceContextService):
    """The service methods for retrieving the status of a job by unique id."""

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

        job = self._uow.job_repo.get_one(
            job_id, DeletionPolicy.NOT_DELETED, experiment_id
        )

        return {"status": job.status, "id": job.resource_id}

    def modify(
        self,
        experiment_id: int,
        job_id: int,
        status: str,
        **kwargs,
    ) -> dict[str, Any] | None:
        """Modify a Job's status by unique id

        Args:
            experiment_id: The unique id of the experiment.
            job_id: The unique id of the job.
            status: The new status of the job.

        Returns:
            The status message job object if found, otherwise an error message.
        """

        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Modify job status by id", job_id=job_id, status=status)

        with self._uow():
            new_job = self._uow.job_repo.set_status(
                job_id=job_id,
                status=status,
                deletion_policy=DeletionPolicy.NOT_DELETED,
                experiment_id=experiment_id,
            )

        log.debug(
            "Job status modification successful",
            job_id=job_id,
            status=new_job.status,
        )

        return {"status": new_job.status, "id": job_id}


class ExperimentJobIdMlflowrunService(ServiceContextService):
    """The service methods for managing the mlflow run id of a job by unique id."""

    def get(self, experiment_id: int, job_id: int, **kwargs) -> dict[str, Any]:
        """Fetch a job's mlflow run id by its unique id.

        Args:
            experiment_id: The unique id of the experiment.
            job_id: The unique id of the job.

        Returns:
            The status message job object if found, otherwise an error message.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get job status by id", job_id=job_id)

        job = self._uow.job_repo.get_one(
            job_id, DeletionPolicy.NOT_DELETED, experiment_id
        )

        mlflow_run_id = (
            job.mlflow_run.mlflow_run_id.hex if job.mlflow_run is not None else None
        )
        return {"mlflow_run_id": mlflow_run_id}

    def create(
        self,
        experiment_id: int,
        job_id: int,
        mlflow_run_id: str,
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

        job = self._uow.job_repo.get_one(
            job_id, DeletionPolicy.NOT_DELETED, experiment_id
        )

        if job.mlflow_run is not None:
            raise JobMlflowRunAlreadySetError

        with self._uow():
            job.mlflow_run = models.JobMlflowRun(
                job_resource_id=job.resource_id,
                mlflow_run_id=mlflow_run_id,
            )

        log.debug(
            "Setting Job mlflow run id successful",
            job_id=job_id,
            mlflow_run_id=mlflow_run_id,
        )

        return {"mlflow_run_id": job.mlflow_run.mlflow_run_id.hex}


class JobIdMlflowrunService(ServiceContextService):
    """The service methods for managing the mlflow run id of a job by unique id."""

    def get(self, job_id: int, **kwargs) -> str | None:
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

        job = self._uow.job_repo.get_one(job_id, DeletionPolicy.NOT_DELETED)

        return job.mlflow_run.mlflow_run_id.hex if job.mlflow_run is not None else None

    def create(
        self,
        job_id: int,
        mlflow_run_id: str,
        **kwargs,
    ) -> dict[str, Any] | None:
        """Set a Job's mlflow run id by unique id

        Args:
            job_id: The unique id of the job.
            mlflow_run_id: The unique id of the mlflow run.

        Returns:
            The status message job object if found, otherwise an error message.
        """

        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug(
            "Set the job's mlflow run id", job_id=job_id, mlflow_run_id=mlflow_run_id
        )

        job = self._uow.job_repo.get_one(job_id, DeletionPolicy.NOT_DELETED)

        if job.mlflow_run is not None:
            raise JobMlflowRunAlreadySetError

        with self._uow():
            job.mlflow_run = models.JobMlflowRun(
                job_resource_id=job.resource_id,
                mlflow_run_id=mlflow_run_id,
            )

        log.debug(
            "Setting Job mlflow run id successful",
            job_id=job_id,
            mlflow_run_id=mlflow_run_id,
        )

        return {"mlflow_run_id": job.mlflow_run.mlflow_run_id.hex}


class ExperimentMetricsService(ServiceContextService):
    """The service methods for retrieving metrics attached to jobs in the experiment."""

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

        search_struct = parse_search_text(search_string)

        jobs, total_num_jobs = self._uow.job_repo.get_by_filters_paged(
            None,
            experiment_id,
            search_struct,
            page_index,
            page_length,
            sort_by_string,
            descending,
            DeletionPolicy.NOT_DELETED,
        )

        metrics_by_job_id = self._uow.job_repo.get_latest_metrics_for_jobs(
            job.resource_id for job in jobs
        )
        metrics_for_jobs = [
            {
                "id": job.resource_id,
                "metrics": [
                    _build_metric_dict(metric)
                    for metric in metrics_by_job_id.get(job.resource_id, [])
                ],
            }
            for job in jobs
        ]
        return metrics_for_jobs, total_num_jobs


class JobLogService(ServiceContextService):
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

        with self._uow():
            job_logs = self._uow.job_repo.add_logs(job_resource_id, records)

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
        job_id: int,
        page_index: int,
        page_length: int,
        search_string: str,
        sort_by_string: str,
        descending: bool,
        severity: list[str] | None = None,
        **kwargs,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        Get log records from the database, for the given job.

        Args:
            job_id: The resource ID of a job
            index: Zero-based index of the first log record to return
            page_length: The number of records to return
            search_string: A search string used to filter results.
            sort_by_string: The name of the column to sort.
            descending: Boolean indicating whether to sort by descending or not.
            severity: list of severities to filter by

        Returns:
            A 2-tuple including (1) The list of records comprising this page,
            each complying with JobLogRecordSchema, and (2) the total number of
            records across all pages.
        """

        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get job logs", job_id=job_id)

        search_struct = parse_search_text(search_string)

        return self._uow.job_repo.get_logs(
            job_id,
            search_struct,
            page_index,
            page_length,
            sort_by_string,
            descending,
            severity,
        )


def _build_job_dicts(
    jobs: list[models.Job], artifacts: list[models.Artifact]
) -> list[utils.JobDict]:
    job_dicts: dict[int, utils.JobDict] = {
        job.resource_id: utils.JobDict(
            job=job,
            artifacts=[],
            has_draft=False,
        )
        for job in jobs
    }

    for artifact in artifacts:
        job_dicts[artifact.job_id]["artifacts"].append(artifact)

    return list(job_dicts.values())


def _prepare_metric_value(metric_value: float) -> tuple[float, str | None]:
    """Prepare a metric value for storage in database.

    Used to detect if the float is a special value (NaN, +Inf, -Inf), which needs
    special handling before it can be stored in a database.

    Args:
        metric_value: The metric value to prepare, may be a special value
            (float("nan"), float("inf"), float("-inf)).

    Returns:
        A tuple containing the prepared metric value and a special value string
        if applicable.
    """
    is_special_value = math.isnan(metric_value) or math.isinf(metric_value)
    special_value = str(metric_value) if is_special_value else None
    value = 0.0 if is_special_value else metric_value
    return value, special_value


def _build_metric_dict(metric: models.JobMetric) -> dict[str, Any]:
    return {
        "name": metric.name,
        "value": metric.value if metric.special_value is None else metric.special_value,
    }
