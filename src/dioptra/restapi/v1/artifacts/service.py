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
"""The server-side functions that perform artifact endpoint operations."""

from typing import Any, Final, cast

import structlog
from flask_login import current_user
from injector import inject
from sqlalchemy import Integer, Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import aliased
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import db, models
from dioptra.restapi.errors import (
    BackendDatabaseError,
    DioptraError,
    EntityDoesNotExistError,
    EntityExistsError,
    EntityRelationshipDoesNotExistError,
    JobMlflowRunNotSetError,
    SortParameterValidationError,
)
from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.entity_types import EntityType
from dioptra.restapi.v1.groups.service import GroupIdService
from dioptra.restapi.v1.jobs.service import JobIdMlflowrunService, JobIdService
from dioptra.restapi.v1.plugins.service import (
    PluginIdSnapshotIdService,
    PluginTaskIdService,
)
from dioptra.restapi.v1.shared.job_run_store import JobRunStoreProtocol
from dioptra.restapi.v1.shared.search_parser import construct_sql_query_filters

LOGGER: BoundLogger = structlog.stdlib.get_logger()

SEARCHABLE_FIELDS: Final[dict[str, Any]] = {
    "artifactPath": lambda x: models.Artifact.location.has(
        models.ArtifactLocation.relative_path.like(x, escape="/")
    ),
    "description": lambda x: models.Artifact.description.like(x, escape="/"),
    "tag": lambda x: models.Artifact.tags.any(models.Tag.name.like(x, escape="/")),
}
SORTABLE_FIELDS: Final[dict[str, Any]] = {
    "id": models.Resource.resource_id,
    "artifactPath": models.ArtifactLocation.relative_path,
    "createdOn": models.Artifact.created_on,
    "lastModifiedOn": models.Resource.last_modified_on,
    "description": models.Artifact.description,
    "job": models.Artifact.job_id,
}


class ArtifactTaskHelper(object):
    @inject
    def __init__(
        self,
        plugin_id_snapshot_id_service: PluginIdSnapshotIdService,
        plugin_task_id_service: PluginTaskIdService,
    ) -> None:
        """Initialize the artifact service.

        All arguments are provided via dependency injection.

        Args:
            plugin_id_snapshot_id_service: An PluginIdSnapshotIdService object.
            plugin_task_id_service: A PluginTaskIdService object.
        """
        self._plugin_id_snapshot_id_service = plugin_id_snapshot_id_service
        self._plugin_task_id_service = plugin_task_id_service

    def associate_task(
        self,
        artifact: models.Artifact,
        plugin_snapshot_id: int | None,
        task_id: int | None,
    ) -> None:
        if task_id is not None:
            if plugin_snapshot_id is None:
                raise DioptraError(
                    "plugin_snapshot_id must be provided if task_id is provided"
                )
            # verify the plugin task exists and then associate
            plugin_task = self._plugin_task_id_service.get(task_id=task_id)
            if not isinstance(plugin_task, models.ArtifactTask):
                raise DioptraError("task_id provided was not an Artifact Task")
            plugin_plugin_file = (
                self._plugin_id_snapshot_id_service.get_plugin_plugin_file(
                    plugin_snapshot_id, plugin_task.plugin_file_resource_snapshot_id
                )
            )
            if plugin_plugin_file is None:
                raise EntityRelationshipDoesNotExistError(
                    [EntityType.PLUGIN, EntityType.PLUGIN_FILE],
                    plugin_snapshot_id=plugin_snapshot_id,
                    plugin_file_snapshot_id=plugin_task.plugin_file_resource_snapshot_id,
                )
            # associate this artifact with the task
            artifact.task = plugin_task
            artifact.plugin_plugin_file = plugin_plugin_file
        elif plugin_snapshot_id is not None:
            raise DioptraError(
                "task_id must be provided if plugin_snapshot_id is provided"
            )


class ArtifactService(object):
    """The service methods for registering and managing artifacts by their unique id."""

    @inject
    def __init__(
        self,
        job_id_service: JobIdService,
        job_id_mlflowrun_service: JobIdMlflowrunService,
        group_id_service: GroupIdService,
        artifact_task_helper: ArtifactTaskHelper,
        job_run_store: JobRunStoreProtocol,
    ) -> None:
        """Initialize the artifact service.

        All arguments are provided via dependency injection.

        Args:
            job_id_service: Service that retrieves the producing job.
            job_id_mlflowrun_service: Service that reads the job's current run binding.
            group_id_service: Service that resolves the artifact-owning group.
            artifact_task_helper: Helper that resolves the optional artifact task.
            job_run_store: Store that verifies the uploaded entry for the producing run.
        """
        self._job_id_service = job_id_service
        self._group_id_service = group_id_service
        self._job_id_mlflowrun_service = job_id_mlflowrun_service
        self._artifact_task_helper = artifact_task_helper
        self._job_run_store = job_run_store

    def create(
        self,
        artifact_path: str,
        description: str,
        group_id: int,
        job_id: int,
        plugin_snapshot_id: int | None = None,
        task_id: int | None = None,
        commit: bool = True,
        **kwargs,
    ) -> utils.ArtifactDict:
        """Register an uploaded file or directory under its producing run.

        Each snapshot reads the file or directory uploaded by this job. To use
        the artifact as input to another job, register its artifact task too.

        Note:
            Resetting a job during development starts a new run. Existing
            artifacts continue to use the files from the run that produced them.

        Args:
            artifact_path: Canonical path relative to the producing run.
            description: Description of the artifact.
            group_id: Group that will own the artifact.
            job_id: Job that produced the artifact.
            plugin_snapshot_id: Plugin snapshot that contains the artifact task.
            task_id: Artifact task for serialization and deserialization, if supplied.
                Requires the plugin snapshot ID.
            commit: Whether to commit the registration in this call.
            **kwargs: Optional structured logger supplied as `log`.

        Returns:
            Newly registered artifact and its draft status.

        Raises:
            EntityDoesNotExistError: If the job, group or associated task is missing.
            EntityExistsError: If this path is already registered for the run.
            JobMlflowRunNotSetError: If the producing job has no bound run.
            MlflowRunNotFoundError: If MLflow cannot find the bound run.
            JobStoreError: If the uploaded entry could not be verified.
            DioptraError: If the optional task association is invalid.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        job_dict = self._job_id_service.get(job_id, log=log)
        job = job_dict["job"]
        mlflow_run_id = self._job_id_mlflowrun_service.get(job_id=job_id, log=log)

        if mlflow_run_id is None:
            raise JobMlflowRunNotSetError

        group = self._group_id_service.get(group_id, error_if_not_found=True, log=log)
        # UploadedArtifact describes the file or directory already in job run storage.
        uploaded_artifact = self._job_run_store.find_artifact(
            run_id=mlflow_run_id, artifact_path=artifact_path
        )

        resource = models.Resource(
            resource_type=EntityType.ARTIFACT.db_table_name,
            owner=group,
        )
        new_artifact = models.Artifact(
            description=description,
            is_dir=uploaded_artifact.is_dir,
            file_size=uploaded_artifact.file_size,
            resource=resource,
            creator=current_user,
        )
        self._artifact_task_helper.associate_task(
            artifact=new_artifact,
            plugin_snapshot_id=plugin_snapshot_id,
            task_id=task_id,
        )

        job.children.append(resource)
        db.session.add(new_artifact)
        # Start the registration write before checking whether the path is available.
        db.session.flush()
        prefix = _get_or_create_storage_prefix(uploaded_artifact.storage_prefix)
        _check_duplicate_artifact(prefix.storage_prefix_id, artifact_path)
        new_artifact.location = models.ArtifactLocation(
            storage_prefix_id=prefix.storage_prefix_id, relative_path=artifact_path
        )
        db.session.flush()

        if commit:
            db.session.commit()
            log.debug(
                "Artifact registration successful", artifact_id=new_artifact.resource_id
            )

        return utils.ArtifactDict(artifact=new_artifact, has_draft=False)

    def get(
        self,
        group_id: int | None,
        search_string: str,
        output_params: list[int] | None,
        page_index: int,
        page_length: int,
        sort_by_string: str,
        descending: bool,
        **kwargs,
    ) -> Any:
        """Fetch a list of artifacts, optionally filtering by search string and paging
        parameters.

        Args:
            group_id: A group ID used to filter results.
            search_string: A search string used to filter results.
            output_params: An ordered list of parameter type ids. Used to filter the
                results to just those artifacts that have an artifact task whose output
                value types exactly match the provided list.
            page_index: The index of the first group to be returned.
            page_length: The maximum number of artifacts to be returned.
            sort_by_string: The name of the column to sort.
            descending: Boolean indicating whether to sort by descending or not.

        Returns:
            A tuple containing a list of artifacts and the total number of artifacts
            matching the query.

        Raises:
            SearchNotImplementedError: If a search string is provided.
            BackendDatabaseError: If the database query returns a None when counting
                the number of artifacts.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get full list of artifacts")

        filters = []

        if group_id is not None:
            filters.append(models.Resource.group_id == group_id)

        if search_string:
            filters.append(
                construct_sql_query_filters(search_string, SEARCHABLE_FIELDS)
            )

        stmt = (
            select(func.count(models.Artifact.resource_id))
            .join(models.Resource)
            .join(
                models.ArtifactLocation,
                models.ArtifactLocation.artifact_resource_id
                == models.Artifact.resource_id,
            )
            .where(
                *filters,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.Artifact.resource_snapshot_id,
            )
        )

        if output_params:
            stmt = self._apply_ouput_params_filter(stmt, output_params)

        total_num_artifacts = db.session.scalars(stmt).first()

        if total_num_artifacts is None:
            log.error(
                "The database query returned a None when counting the number of "
                "groups when it should return a number.",
                sql=str(stmt),
            )
            raise BackendDatabaseError

        if total_num_artifacts == 0:
            return [], total_num_artifacts

        # get latest artifact snapshots
        latest_artifacts_stmt = (
            select(models.Artifact)
            .join(models.Resource)
            .join(
                models.ArtifactLocation,
                models.ArtifactLocation.artifact_resource_id
                == models.Artifact.resource_id,
            )
            .where(
                *filters,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.Artifact.resource_snapshot_id,
            )
            .offset(page_index)
            .limit(page_length)
        )

        if output_params:
            latest_artifacts_stmt = self._apply_ouput_params_filter(
                latest_artifacts_stmt, output_params
            )

        if sort_by_string and sort_by_string in SORTABLE_FIELDS:
            sort_column = SORTABLE_FIELDS[sort_by_string]
            if descending:
                sort_column = sort_column.desc()
            else:
                sort_column = sort_column.asc()
            latest_artifacts_stmt = latest_artifacts_stmt.order_by(sort_column)
        elif sort_by_string and sort_by_string not in SORTABLE_FIELDS:
            raise SortParameterValidationError(
                EntityType.ARTIFACT.db_table_name, sort_by_string
            )

        artifacts = db.session.scalars(latest_artifacts_stmt).all()

        drafts_stmt = select(
            models.DraftResource.payload["resource_id"].as_string().cast(Integer)
        ).where(
            models.DraftResource.payload["resource_id"]
            .as_string()
            .cast(Integer)
            .in_(tuple(artifact.resource_id for artifact in artifacts)),
            models.DraftResource.user_id == current_user.user_id,
        )
        artifacts_dict: dict[int, utils.ArtifactDict] = {
            artifact.resource_id: utils.ArtifactDict(artifact=artifact, has_draft=False)
            for artifact in artifacts
        }
        resource_id: int
        for resource_id in db.session.scalars(drafts_stmt):
            artifacts_dict[resource_id]["has_draft"] = True

        return list(artifacts_dict.values()), total_num_artifacts

    def _apply_ouput_params_filter(
        self, stmt: Select, output_params: list[int]
    ) -> Select:
        # creates a comparison for each outuput parameter and makes
        # sure the type is correct for that parameter_number
        for index, p in enumerate(output_params):
            task_alias = aliased(models.ArtifactTask)
            parameter_alias = aliased(models.PluginTaskOutputParameter)
            type_alias = aliased(models.PluginTaskParameterType)
            stmt = (
                stmt.join(models.Artifact.task.of_type(task_alias))
                .join(models.ArtifactTask.output_parameters.of_type(parameter_alias))
                .join(
                    type_alias,
                    type_alias.resource_snapshot_id
                    == parameter_alias.plugin_task_parameter_type_resource_snapshot_id,
                )
                .where(
                    type_alias.resource_id == p,
                    parameter_alias.parameter_number == index,
                )
            )

        # verifies that the number of parameters is what we are looking for
        # prevents picking up artifacts which match the ones we are looking
        # for, but have more parameters
        count_subquery = (
            select(
                models.PluginTaskOutputParameter.task_id,
                func.count().label("param_count"),
            )
            .group_by(models.PluginTaskOutputParameter.task_id)
            .subquery()
        )
        task_alias = aliased(models.ArtifactTask)
        stmt = (
            stmt.join(models.Artifact.task.of_type(task_alias))
            .join(count_subquery, task_alias.task_id == count_subquery.c.task_id)
            .where(
                count_subquery.c.param_count == len(output_params),
            )
        )
        return stmt


class ArtifactIdService(object):
    """The service methods for retrieving artifacts by their unique id."""

    @inject
    def __init__(
        self,
        artifact_task_helper: ArtifactTaskHelper,
        job_run_store: JobRunStoreProtocol,
    ) -> None:
        """Initialize the artifact service.

        All arguments are provided via dependency injection.

        Args:
            artifact_task_helper: A ArtifactTaskHelper object.
        """
        self._artifact_task_helper = artifact_task_helper
        self._job_run_store = job_run_store

    def get(
        self,
        artifact_id: int,
        **kwargs,
    ) -> utils.ArtifactDict:
        """Fetch a artifact by its unique id.

        Args:
            artifact_id: The unique id of the artifact.

        Returns:
            The artifact object.

        Raises:
            EntityDoesNotExistError: If the artifact is not found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get artifact by id", artifact_id=artifact_id)

        stmt = (
            select(models.Artifact)
            .join(models.Resource)
            .where(
                models.Artifact.resource_id == artifact_id,
                models.Artifact.resource_snapshot_id
                == models.Resource.latest_snapshot_id,
                models.Resource.is_deleted == False,  # noqa: E712
            )
        )
        artifact = db.session.scalars(stmt).first()

        if artifact is None:
            raise EntityDoesNotExistError(EntityType.ARTIFACT, artifact_id=artifact_id)

        drafts_stmt = (
            select(models.DraftResource.draft_resource_id)
            .where(
                models.DraftResource.payload["resource_id"].as_string().cast(Integer)
                == artifact.resource_id,
                models.DraftResource.user_id == current_user.user_id,
            )
            .exists()
            .select()
        )
        has_draft = db.session.scalar(drafts_stmt)

        return utils.ArtifactDict(artifact=artifact, has_draft=has_draft)

    def modify(
        self,
        artifact_id: int,
        description: str,
        plugin_snapshot_id: int | None = None,
        task_id: int | None = None,
        commit: bool = True,
        **kwargs,
    ) -> utils.ArtifactDict:
        """Modify a artifact.

        Args:
            artifact_id: The unique id of the artifact.
            description: The new description of the artifact.
            error_if_not_found: If True, raise an error if the group is not found.
                Defaults to False.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The updated artifact object.

        Raises:
            EntityDoesNotExistError: If the artifact is not found and
                `error_if_not_found` is True.
            EntityExistsError: If the artifact name already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        artifact_dict = self.get(artifact_id, log=log)

        artifact = artifact_dict.get("artifact")
        has_draft = cast(bool, artifact_dict.get("has_draft"))

        new_artifact = models.Artifact(
            location=artifact.location,  # pyright: ignore
            description=description,  # pyright: ignore
            resource=artifact.resource,  # pyright: ignore
            is_dir=artifact.is_dir,  # pyright: ignore
            file_size=artifact.file_size,  # pyright: ignore
            creator=current_user,  # pyright: ignore
        )
        self._artifact_task_helper.associate_task(
            artifact=new_artifact,
            plugin_snapshot_id=plugin_snapshot_id,
            task_id=task_id,
        )
        db.session.add(new_artifact)

        if commit:
            db.session.commit()
            log.debug(
                "Artifact modification successful",
                artifact_id=artifact_id,
                description=description,
            )

        return utils.ArtifactDict(artifact=new_artifact, has_draft=has_draft)

    def get_listing(
        self,
        artifact_id: int,
        **kwargs,
    ) -> list[utils.ArtifactFileDict]:
        """Gets the listing for an artifact.

        Args:
            artifact_id: The unique id of the artifact.

        Returns:
            The updated artifact object.

        Raises:
            EntityDoesNotExistError: If the artifact is not found.
            EntityExistsError: If the artifact name already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        artifact_dict = self.get(artifact_id, log=log)

        artifact = artifact_dict["artifact"]
        location = utils.require_artifact_location(artifact)

        return [
            utils.ArtifactFileDict(
                file_size=element.file_size,
                relative_path=element.relative_path,
                is_dir=element.is_dir,
            )
            for element in self._job_run_store.get_artifact_file_list(
                storage_prefix=location.storage_prefix.relative_prefix,
                artifact_path=location.relative_path,
            )
        ]


def _get_or_create_storage_prefix(relative_prefix: str) -> models.ArtifactStoragePrefix:
    """Find or create the run directory shared by registrations in this transaction."""
    query = (
        select(models.ArtifactStoragePrefix)
        .where(models.ArtifactStoragePrefix.relative_prefix == relative_prefix)
        .with_for_update()
    )
    prefix = db.session.scalar(query)
    if prefix is not None:
        return prefix

    try:
        with db.session.begin_nested():
            prefix = models.ArtifactStoragePrefix(relative_prefix=relative_prefix)
            db.session.add(prefix)
            db.session.flush()
    except IntegrityError:
        # A concurrent registration may have created this prefix first.
        existing = db.session.scalar(query)
        if existing is None:
            raise
        return existing
    return prefix


def _check_duplicate_artifact(storage_prefix_id: int, artifact_path: str) -> None:
    """Reject a second active artifact at the same storage location."""
    duplicate_id = db.session.scalar(
        select(models.ArtifactLocation.artifact_resource_id)
        .join(models.Resource)
        .where(
            models.ArtifactLocation.storage_prefix_id == storage_prefix_id,
            models.ArtifactLocation.relative_path == artifact_path,
            models.Resource.is_deleted.is_(False),
        )
        .limit(1)
    )
    if duplicate_id is not None:
        raise EntityExistsError(
            EntityType.ARTIFACT, duplicate_id, artifact_path=artifact_path
        )
