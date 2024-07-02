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
from __future__ import annotations

from typing import Any, Final, cast

import structlog
from flask_login import current_user
from injector import inject
from sqlalchemy import Integer, func, select
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import db, models
from dioptra.restapi.errors import BackendDatabaseError
from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.groups.service import GroupIdService
from dioptra.restapi.v1.jobs.service import ExperimentJobIdService, JobIdService
from dioptra.restapi.v1.shared.search_parser import construct_sql_query_filters

from .errors import ArtifactAlreadyExistsError, ArtifactDoesNotExistError

LOGGER: BoundLogger = structlog.stdlib.get_logger()

RESOURCE_TYPE: Final[str] = "artifact"
SEARCHABLE_FIELDS: Final[dict[str, Any]] = {
    "uri": lambda x: models.Artifact.uri.like(x, escape="/"),
    "description": lambda x: models.Artifact.description.like(x, escape="/"),
}


class ArtifactService(object):
    """The service methods for registering and managing artifacts by their unique id."""

    @inject
    def __init__(
        self,
        artifact_uri_service: ArtifactUriService,
        job_id_service: JobIdService,
        group_id_service: GroupIdService,
    ) -> None:
        """Initialize the artifact service.

        All arguments are provided via dependency injection.

        Args:
            artifact_uri_service: An ArtifactUriService object.
            job_id_service: A JobIdService object.
            group_id_service: A GroupIdService object.
        """
        self._artifact_uri_service = artifact_uri_service
        self._job_id_service = job_id_service
        self._group_id_service = group_id_service

    def create(
        self,
        uri: str,
        description: str,
        group_id: int,
        job_id: int,
        commit: bool = True,
        **kwargs,
    ) -> utils.ArtifactDict:
        """Create a new artifact.

        Args:
            uri: The uri of the artifact. This must be globally unique.
            description: The description of the artifact.
            group_id: The group that will own the artifact.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The newly created artifact object.

        Raises:
            ArtifactAlreadyExistsError: If the artifact already exists.

        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        if self._artifact_uri_service.get(uri, log=log) is not None:
            log.debug("Artifact uri already exists", uri=uri)
            raise ArtifactAlreadyExistsError

        job_dict = cast(
            utils.JobDict,
            self._job_id_service.get(job_id, error_if_not_found=True, log=log),
        )
        job = job_dict["job"]

        group = self._group_id_service.get(group_id, error_if_not_found=True, log=log)

        resource = models.Resource(resource_type="artifact", owner=group)
        new_artifact = models.Artifact(
            uri=uri,
            description=description,
            resource=resource,
            creator=current_user,
        )
        job.children.append(new_artifact.resource)
        db.session.add(new_artifact)

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
        **kwargs,
    ) -> Any:
        """Fetch a list of artifacts, optionally filtering by search string and paging
        parameters.

        Args:
            group_id: A group ID used to filter results.
            search_string: A search string used to filter results.
            page_index: The index of the first group to be returned.
            page_length: The maximum number of artifacts to be returned.

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

        filters = list()

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
        lastest_artifacts_stmt = (
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
        artifacts = db.session.scalars(lastest_artifacts_stmt).all()

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


class JobArtifactService(object):
    """The service methods for registering and managing artifacts by their unique id."""

    @inject
    def __init__(
        self,
        artifact_service: ArtifactService,
        experiment_job_id_service: ExperimentJobIdService,
    ) -> None:
        """Initialize the artifact service.

        All arguments are provided via dependency injection.

        Args:
            artifact_service: An ArtifactService object.
            experiment_job_id_service: A JobIdService object.
        """
        self._artifact_service = artifact_service
        self._experiment_job_id_service = experiment_job_id_service

    def create(
        self,
        experiment_id: int,
        job_id: int,
        uri: str,
        description: str,
        commit: bool = True,
        **kwargs,
    ) -> utils.ArtifactDict:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        job_dict = cast(
            utils.JobDict,
            self._experiment_job_id_service.get(
                experiment_id, job_id, error_if_not_found=True, log=log
            ),
        )
        job = job_dict["job"]

        resource = models.Resource(resource_type="artifact", owner=job.resource.owner)
        new_artifact = models.Artifact(
            uri=uri,
            description=description,
            resource=resource,
            creator=current_user,
        )
        job.children.append(new_artifact.resource)
        db.session.add(new_artifact)

        if commit:
            db.session.commit()
            log.debug(
                "Artifact registration successful", artifact_id=new_artifact.resource_id
            )

        return utils.ArtifactDict(artifact=new_artifact, has_draft=False)


class ArtifactUriService(object):
    """The service methods for managing artifacts by their uri."""

    def get(
        self,
        artifact_uri: str,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> utils.ArtifactDict | None:
        """Fetch an artifact by its unique uri.

        Args:
            artifact_uri: the unique uri of the artifact.
            error_if_not_found: If True, raise an error if the artifact is not found.
                Defaults to False.


        Returns:
            The artifact object if found, otherwise None.

        Raises:
            ArtifactDoesNotExistError: If the artifact is not found and
                `error_if_not_found` is True.

        """

        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get artifact by id", artifact_uri=artifact_uri)

        stmt = (
            select(models.Artifact)
            .join(models.Resource)
            .where(
                models.Artifact.uri == artifact_uri,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.Artifact.resource_snapshot_id,
            )
        )
        artifact = db.session.scalars(stmt).first()

        if artifact is None:
            if error_if_not_found:
                log.debug("Artifact not found", artifact_uri=artifact_uri)
                raise ArtifactDoesNotExistError

            return None

        return artifact


class ArtifactIdService(object):
    """The service methods for retrieving artifacts by their unique id."""

    def get(
        self,
        artifact_id: int,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> utils.ArtifactDict | None:
        """Fetch a artifact by its unique id.

        Args:
            artifact_id: The unique id of the artifact.
            error_if_not_found: If True, raise an error if the artifact is not found.
                Defaults to False.

        Returns:
            The artifact object if found, otherwise None.

        Raises:
            ArtifactDoesNotExistError: If the artifact is not found and
                `error_if_not_found` is True.
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
            if error_if_not_found:
                log.debug("Artifact not found", artifact_id=artifact_id)
                raise ArtifactDoesNotExistError

            return None

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
        error_if_not_found: bool = False,
        commit: bool = True,
        **kwargs,
    ) -> utils.ArtifactDict | None:
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
            ArtifactDoesNotExistError: If the artifact is not found and
                `error_if_not_found` is True.
            ArtifactAlreadyExistsError: If the artifact name already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        artifact_dict = self.get(
            artifact_id, error_if_not_found=error_if_not_found, log=log
        )

        if artifact_dict is None:
            return None

        artifact = artifact_dict["artifact"]
        has_draft = artifact_dict["has_draft"]

        new_artifact = models.Artifact(
            uri=artifact.uri,
            description=description,
            resource=artifact.resource,
            creator=current_user,
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
