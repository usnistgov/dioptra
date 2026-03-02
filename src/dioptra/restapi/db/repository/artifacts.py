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
The artifact repository: data operations related to artifacts
"""

from collections.abc import Iterable, Sequence
from typing import Any, Final, overload

from sqlalchemy import Select, func, select
from sqlalchemy.orm import aliased

import dioptra.restapi.db.repository.utils as utils
from dioptra.restapi.db.models import Artifact, Group, Resource, Tag
from dioptra.restapi.db.models.plugins import (
    ArtifactTask,
    PluginTaskOutputParameter,
    PluginTaskParameterType,
)


class ArtifactRepository:
    SEARCHABLE_FIELDS: Final[dict[str, Any]] = {
        "artifactUri": lambda x: Artifact.uri.like(x, escape="/"),
        "description": lambda x: Artifact.description.like(x, escape="/"),
        "tag": lambda x: Artifact.tags.any(Tag.name.like(x, escape="/")),
    }

    # Maps a general sort criterion name to a Artifact attribute
    SORTABLE_FIELDS: Final[dict[str, Any]] = {
        "uri": Artifact.uri,
        "createdOn": Artifact.created_on,
        "lastModifiedOn": Resource.last_modified_on,
        "description": Artifact.description,
        "job": Artifact.job_id,
    }

    def __init__(self, session: utils.CompatibleSession[utils.S]):
        self.session = session

    def create(self, artifact: Artifact) -> None:
        """
        Create a new artifact resource.  This creates both the resource and the
        initial snapshot.

        Args:
            artifact: The artifact to create

        Raises:
            EntityExistsError: if the artifact resource or snapshot already
                exists, or the artifact name collides with another artifact in the
                same group
            EntityDoesNotExistError: if the group owner or user creator does
                not exist
            EntityDeletedError: if the artifact, its creator, or its group owner
                is deleted
            UserNotInGroupError: if the user creator is not a member of the
                group who will own the resource
            MismatchedResourceTypeError: if the snapshot or resource's type is
                not "artifact"
        """

        # Consistency rules:
        # - Latest-snapshot artifact uris must be unique within the owning job
        # - Artifact snapshots must be of artifact resources
        # - For now, the snapshot creator must be a member of the group who
        #   owns the resource.  I think this will become more complicated when
        #   we implement shares and permissions.

        utils.assert_can_create_resource(self.session, artifact, "artifact")

        self.session.add(artifact)

    def create_snapshot(self, artifact: Artifact) -> None:
        """
        Create a new artifact snapshot.

        Args:
            artifact: A Artifact object with the desired snapshot settings

        Raises:
            EntityDoesNotExistError: if the artifact resource or snapshot creator
                user does not exist
            EntityExistsError: if the snapshot already exists, or this new
                snapshot's artifact name collides with another artifact in the same
                group
            EntityDeletedError: if the artifact or snapshot creator user are
                deleted
            UserNotInGroupError: if the snapshot creator user is not a member
                of the group who owns the artifact
            MismatchedResourceTypeError: if the snapshot or resource's type is
                not "artifact"
        """
        # Consistency rules:
        # - Latest-snapshot artifact uris must be unique within the owning job
        # - Artifact snapshots must be of artifact resources
        # - Snapshot timestamps must be monotonically increasing(?)
        # - For now, the snapshot creator must be a member of the group who
        #   owns the resource.  I think this will become more complicated when
        #   we implement shares and permissions.

        utils.assert_can_create_snapshot(self.session, artifact, "artifact")

        # Assume that the new snapshot's created_on timestamp is later than the
        # current latest timestamp?

        self.session.add(artifact)

    def delete(self, artifact: Artifact | int) -> None:
        """
        Delete a artifact.  No-op if the artifact is already deleted.

        Args:
            artifact: A Artifact object or resource_id primary key value identifying
                a artifact resource

        Raises:
            EntityDoesNotExistError: if the artifact does not exist
        """

        utils.delete_resource(self.session, artifact)

    @overload
    def get(
        self,
        resource_ids: int,
        deletion_policy: utils.DeletionPolicy,
    ) -> Artifact | None: ...

    @overload
    def get(
        self,
        resource_ids: Iterable[int],
        deletion_policy: utils.DeletionPolicy,
    ) -> Sequence[Artifact]: ...

    def get(
        self,
        resource_ids: int | Iterable[int],
        deletion_policy: utils.DeletionPolicy = utils.DeletionPolicy.NOT_DELETED,
    ) -> Artifact | Sequence[Artifact] | None:
        """
        Get the latest snapshot of the given artifact resource.

        Args:
            resource_ids: A single or iterable of artifact resource IDs
            deletion_policy: Whether to look at deleted artifacts, non-deleted
                artifacts, or all artifacts

        Returns:
            A Artifact/list of Artifact objects, or None/empty list if none were
            found with the given ID(s)
        """

        return utils.get_latest_snapshots(
            self.session, Artifact, resource_ids, deletion_policy
        )

    def get_by_job(
        self, *job_ids: int, deletion_policy: utils.DeletionPolicy
    ) -> Sequence[Artifact]:
        """
        Get the latest Artifact snapshots associated with the given Job ID(s).

        Args:
            job_ids: One or more Job resource IDs.
            deletion_policy: Whether to look at deleted artifacts, non-deleted
                artifacts, or all artifacts

        Returns:
            A list of Artifact objects, or empty list if none were found with the given
            Job ID.
        """
        return utils.get_latest_snapshots_where(
            self.session,
            Artifact,
            Artifact.job_id.in_(job_ids),
            deletion_policy=deletion_policy,
        )

    def get_one(
        self,
        resource_id: int,
        deletion_policy: utils.DeletionPolicy,
    ) -> Artifact:
        """
        Get the latest snapshot of the given artifact resource; require that
        exactly one is found, or raise an exception.

        Args:
            resource_id: A resource ID
            deletion_policy: Whether to look at deleted artifacts, non-deleted
                artifacts, or all artifacts

        Returns:
            A Artifact object

        Raises:
            EntityDoesNotExistError: if the artifact does not exist in the
                database (deleted or not)
            EntityExistsError: if the artifact exists and is not deleted, but
                policy was to find a deleted artifact
            EntityDeletedError: if the artifact is deleted, but policy was to find
                a non-deleted artifact
        """
        return utils.get_one_latest_snapshot(
            self.session, Artifact, resource_id, deletion_policy
        )

    def get_one_snapshot(
        self,
        snapshot_id: int,
        deletion_policy: utils.DeletionPolicy,
    ) -> Artifact:
        """
        Get the a specific artifact snapshot given the resource snapshot ID; require
        that exactly one is found, or raise an exception.

        Args:
            snapshot_id: A resource snapshot ID
            deletion_policy: Whether to look at deleted artifacts, non-deleted
                artifacts, or all artifacts

        Returns:
            An Artifact object

        Raises:
            EntityDoesNotExistError: if the artifact does not exist in the
                database (deleted or not)
            EntityExistsError: if the artifact exists and is not deleted, but
                policy was to find a deleted artifact
            EntityDeletedError: if the artifact is deleted, but policy was to
                find a non-deleted artifact
        """
        return utils.get_one_snapshot(
            self.session, Artifact, snapshot_id, deletion_policy
        )

    def get_by_name(
        self,
        name: str,
        group: Group | int,
        deletion_policy: utils.DeletionPolicy = utils.DeletionPolicy.NOT_DELETED,
    ) -> Artifact | None:
        """
        Get a artifact by name.  This returns the latest version (snapshot) of
        the artifact.

        Args:
            name: A artifact name
            group: A group/group ID, to disambiguate same-named artifacts across
                groups
            deletion_policy: Whether to look at deleted artifacts, non-deleted
                artifacts, or all artifacts

        Returns:
            A artifact, or None if one was not found

        Raises:
            EntityDoesNotExistError: if the given group does not exist
            EntityDeletedError: if the given group is deleted
        """
        return utils.get_snapshot_by_name(
            self.session, Artifact, name, group, deletion_policy
        )

    def get_by_filters_paged(
        self,
        group: Group | int | None,
        filters: list[dict],
        output_params: list[int] | None,
        page_start: int,
        page_length: int,
        sort_by: str | None,
        descending: bool,
        deletion_policy: utils.DeletionPolicy = utils.DeletionPolicy.NOT_DELETED,
    ) -> tuple[Sequence[Artifact], int]:
        """
        Get some artifacts according to search criteria.

        Args:
            group: Limit artifacts to those owned by this group; None to not limit
                the search
            filters: Search criteria, see parse_search_text()
            page_start: Zero-based row index where the page should start
            page_length: Maximum number of rows in the page; use <= 0 for
                unlimited length
            sort_by: Sort criterion; must be a key of SORTABLE_FIELDS.  None
                to sort in an implementation-dependent way.
            descending: Whether to sort in descending order; only applicable
                if sort_by is given
            deletion_policy: Whether to look at deleted artifacts, non-deleted
                artifacts, or all artifacts

        Returns:
            A 2-tuple including the page of artifacts and total count of matching
            artifacts which exist

        Raises:
            SearchParseError: if filters includes a non-searchable field
            SortParameterValidationError: if sort_by is a non-sortable field
            EntityDoesNotExistError: if the given group does not exist
            EntityDeletedError: if the given group is deleted
        """

        output_params_filter = []
        if output_params is not None:
            output_params_filter.append(
                lambda stmt: self._apply_ouput_params_filter(stmt, output_params)
            )

        return utils.get_by_filters_paged(
            self.session,
            Artifact,
            self.SORTABLE_FIELDS,
            self.SEARCHABLE_FIELDS,
            group,
            filters,
            page_start,
            page_length,
            sort_by,
            descending,
            deletion_policy,
            output_params_filter,
        )

    def _apply_ouput_params_filter(
        self, stmt: Select, output_params: list[int]
    ) -> Select:
        # creates a comparison for each outuput parameter and makes
        # sure the type is correct for that parameter_number
        for index, p in enumerate(output_params):
            task_alias = aliased(ArtifactTask)
            parameter_alias = aliased(PluginTaskOutputParameter)
            type_alias = aliased(PluginTaskParameterType)
            stmt = (
                stmt.join(Artifact.task.of_type(task_alias))
                .join(ArtifactTask.output_parameters.of_type(parameter_alias))
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
                PluginTaskOutputParameter.task_id,
                func.count().label("param_count"),
            )
            .group_by(PluginTaskOutputParameter.task_id)
            .subquery()
        )
        task_alias = aliased(ArtifactTask)
        stmt = (
            stmt.join(Artifact.task.of_type(task_alias))
            .join(count_subquery, task_alias.task_id == count_subquery.c.task_id)
            .where(
                count_subquery.c.param_count == len(output_params),
            )
        )
        return stmt
