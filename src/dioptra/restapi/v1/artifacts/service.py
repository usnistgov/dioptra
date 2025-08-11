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
from sqlalchemy import Integer, func, select
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import db, models
from dioptra.restapi.errors import (
    BackendDatabaseError,
    DioptraError,
    EntityDoesNotExistError,
    EntityExistsError,
    JobMlflowRunNotSetError,
    SortParameterValidationError,
)
from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.entity_types import EntityTypes
from dioptra.restapi.v1.groups.service import GroupIdService
from dioptra.restapi.v1.jobs.service import JobIdMlflowrunService, JobIdService
from dioptra.restapi.v1.plugins.service import (
    PLUGIN_TASK_RESOURCE_TYPE,
    PluginIdSnapshotIdService,
    PluginTaskIdService,
)
from dioptra.restapi.v1.shared.job_run_store import JobRunStoreProtocol
from dioptra.restapi.v1.shared.search_parser import construct_sql_query_filters

LOGGER: BoundLogger = structlog.stdlib.get_logger()

ARTIFACT_RESOURCE_TYPE: Final[EntityTypes] = EntityTypes.ARTIFACT
SEARCHABLE_FIELDS: Final[dict[str, Any]] = {
    "artifactUri": lambda x: models.Artifact.uri.like(x, escape="/"),
    "description": lambda x: models.Artifact.description.like(x, escape="/"),
    "tag": lambda x: models.Artifact.tags.any(models.Tag.name.like(x, escape="/")),
}
SORTABLE_FIELDS: Final[dict[str, Any]] = {
    "uri": models.Artifact.uri,
    "createdOn": models.Artifact.created_on,
    "lastModifiedOn": models.Resource.last_modified_on,
    "description": models.Artifact.description,
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
                raise EntityDoesNotExistError(
                    PLUGIN_TASK_RESOURCE_TYPE,
                    task_id=task_id,
                    plugin_snapshot_id=plugin_snapshot_id,
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
            artifact_uri_service: An ArtifactUriService object.
            job_id_service: A JobIdService object.
            group_id_service: A GroupIdService object.
        """
        self._job_id_service = job_id_service
        self._group_id_service = group_id_service
        self._job_id_mlflowrun_service = job_id_mlflowrun_service
        self._artifact_task_helper = artifact_task_helper
        self._job_run_store = job_run_store

    def create(
        self,
        uri: str,
        description: str,
        group_id: int,
        job_id: int,
        plugin_snapshot_id: int | None = None,
        task_id: int | None = None,
        commit: bool = True,
        **kwargs,
    ) -> utils.ArtifactDict:
        """Create a new artifact.

            Both plugin_snapshot_id and must be None or not None. If None, then the
            artifact is unavailable for use as input into another job and may only be
            downloaded.
        Args:
            uri: The uri of the artifact. This must be globally unique.
            description: The description of the artifact.
            group_id: The group that will own the artifact.
            job_id: the job which owns/produced this artifact
            plugin_snapshot_id: the plugin snapshot id of the plugin
                containing the artifact task used to serialize/deserialize the artifact,
                defaults to None.
            task_id: the task id of the plugin artifact task used to
                serialize/deserialize the artifact, defaults to None
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            utils.ArtifactDict: The newly created artifact object.

        Raises:
            EntityExistsError: If the artifact already exists.
            MLFlowError: If the mlflow run id does not exist.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        job_dict = self._job_id_service.get(job_id, log=log)
        job = job_dict["job"]
        job_artifacts = job_dict["artifacts"]
        mlflow_run_id = self._job_id_mlflowrun_service.get(job_id=job_id, log=log)

        if mlflow_run_id is None:
            raise JobMlflowRunNotSetError

        # check if an artifact with the same uri and job_id has already been created
        duplicate = _find_artifact(job_artifacts, uri)
        if duplicate is not None:
            raise EntityExistsError(
                ARTIFACT_RESOURCE_TYPE, duplicate.resource_id, uri=uri
            )
        artifact = self._job_run_store.find_artifact(run_id=mlflow_run_id, uri=uri)

        group = self._group_id_service.get(group_id, error_if_not_found=True, log=log)

        resource = models.Resource(
            resource_type=ARTIFACT_RESOURCE_TYPE.get_db_schema_name(), owner=group
        )
        new_artifact = models.Artifact(
            uri=uri,
            description=description,
            is_dir=artifact.is_dir,
            file_size=artifact.file_size,
            resource=resource,
            creator=current_user,
        )
        db.session.add(new_artifact)
        job.children.append(new_artifact.resource)

        self._artifact_task_helper.associate_task(
            artifact=new_artifact,
            plugin_snapshot_id=plugin_snapshot_id,
            task_id=task_id,
        )

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
            .where(
                *filters,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.Artifact.resource_snapshot_id,
            )
        )
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
            .where(
                *filters,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.Artifact.resource_snapshot_id,
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
            latest_artifacts_stmt = latest_artifacts_stmt.order_by(sort_column)
        elif sort_by_string and sort_by_string not in SORTABLE_FIELDS:
            raise SortParameterValidationError(ARTIFACT_RESOURCE_TYPE, sort_by_string)

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
        for resource_id in db.session.scalars(drafts_stmt):
            artifacts_dict[resource_id]["has_draft"] = True

        return list(artifacts_dict.values()), total_num_artifacts


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
            raise EntityDoesNotExistError(
                ARTIFACT_RESOURCE_TYPE, artifact_id=artifact_id
            )

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

        artifact = cast(
            models.Artifact,
            artifact_dict.get(ARTIFACT_RESOURCE_TYPE.get_db_schema_name(), None),
        )
        has_draft = cast(bool, artifact_dict.get("has_draft"))

        new_artifact = models.Artifact(
            uri=artifact.uri,
            description=description,
            resource=artifact.resource,
            is_dir=artifact.is_dir,
            file_size=artifact.file_size,
            creator=current_user,
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

        return [
            utils.ArtifactFileDict(
                file_size=element.file_size,
                relative_path=element.relative_path,
                is_dir=element.is_dir,
            )
            for element in self._job_run_store.get_artifact_file_list(
                base_uri=artifact.uri,
                subfolder_path="",
            )
        ]


def _find_artifact(
    job_artifacts: list[models.Artifact], new_artifact_uri: str
) -> models.Artifact | None:
    for artifact in job_artifacts:
        if new_artifact_uri == artifact.uri:
            return artifact
    return None
