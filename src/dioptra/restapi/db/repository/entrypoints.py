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
The entrypoints repository: data operations related to entrypoints
"""

from collections.abc import Iterable, Sequence
from typing import Any, Final, overload

import dioptra.restapi.db.repository.utils as utils
from dioptra.restapi.db.models import (
    EntryPoint,
    Experiment,
    Group,
    Plugin,
    Queue,
    Resource,
    ResourceSnapshot,
    Tag,
)
from dioptra.restapi.errors import EntityDoesNotExistError


class EntrypointRepository:
    SEARCHABLE_FIELDS: Final[dict[str, Any]] = {
        "name": lambda x: EntryPoint.name.like(x, escape="/"),
        "description": lambda x: EntryPoint.description.like(x, escape="/"),
        "task_graph": lambda x: EntryPoint.task_graph.like(x, escape="/"),
        "artifact_graph": lambda x: EntryPoint.artifact_graph.like(x, escape="/"),
        "tag": lambda x: EntryPoint.tags.any(Tag.name.like(x, escape="/")),
    }

    # Maps a general sort criterion name to an EntryPoint attribute
    SORTABLE_FIELDS: Final[dict[str, Any]] = {
        "name": EntryPoint.name,
        "createdOn": EntryPoint.created_on,
        "lastModifiedOn": Resource.last_modified_on,
        "description": EntryPoint.description,
    }

    def __init__(self, session: utils.CompatibleSession[utils.S]):
        self.session = session

    def create(self, entrypoint: EntryPoint):
        """
        Create a new entrypoint resource.  This creates both the resource and
        the initial snapshot.

        Args:
            entrypoint: The entrypoint to create

        Raises:
            EntityExistsError: if the entrypoint resource or snapshot already
                exists, or the entrypoint name collides with another entrypoint
                in the same group
            EntityDoesNotExistError: if any child entry point doesn't exist, or
                the group owner or user creator do not exist
            EntityDeletedError: if the entrypoint, its creator, or its group
                owner is deleted, or if all entrypoint children exist but some
                are deleted
            UserNotInGroupError: if the entrypoint creator is not a member of
                the group who will own the resource
            MismatchedResourceTypeError: if the snapshot or resource's type is
                not "entrypoint"
        """
        utils.assert_can_create_resource(self.session, entrypoint, "entry_point")
        utils.assert_resource_name_available(self.session, entrypoint)

        self.session.add(entrypoint)

    def create_snapshot(self, entrypoint: Experiment):
        """
        Create a new entrypoint snapshot.

        Args:
            entrypoint: An EntryPoint object with the desired snapshot settings

        Raises:
            EntityDoesNotExistError: if the entrypoint resource, snapshot
                creator user, or any child entry point does not exist
            EntityExistsError: if the snapshot already exists, or this new
                snapshot's entrypoint name collides with another entrypoint in
                the same group
            EntityDeletedError: if the entrypoint resource is deleted, snapshot
                creator user is deleted, or if all child resources exist but
                some are deleted
            UserNotInGroupError: if the snapshot creator user is not a member
                of the group who owns the entrypoint
            MismatchedResourceTypeError: if the snapshot or resource's type is
                not "entrypoint"
        """
        utils.assert_can_create_snapshot(self.session, entrypoint, "entry_point")
        utils.assert_snapshot_name_available(self.session, entrypoint)

        # Assume that the new snapshot's created_on timestamp is later than the
        # current latest timestamp?

        self.session.add(entrypoint)

    @overload
    def get(
        self,
        resource_ids: int,
        deletion_policy: utils.DeletionPolicy,
    ) -> EntryPoint | None: ...

    @overload
    def get(
        self,
        resource_ids: Iterable[int],
        deletion_policy: utils.DeletionPolicy,
    ) -> Sequence[EntryPoint]: ...

    def get(
        self,
        resource_ids: int | Iterable[int],
        deletion_policy: utils.DeletionPolicy = utils.DeletionPolicy.NOT_DELETED,
    ) -> EntryPoint | Sequence[EntryPoint] | None:
        """
        Get the latest snapshot of the given entrypoint resource(s).

        Args:
            resource_ids: A single or iterable of entrypoint resource IDs
            deletion_policy: Whether to look at deleted entrypoints,
                non-deleted entrypoints, or all entrypoints

        Returns:
            A EntryPoint/list of EntryPoint objects, or None/empty list if
            none were found with the given ID(s)
        """
        return utils.get_latest_snapshots(
            self.session, EntryPoint, resource_ids, deletion_policy
        )

    def get_one(
        self,
        resource_id: int,
        deletion_policy: utils.DeletionPolicy,
        error_if_not_found=False,
    ) -> EntryPoint:
        """
        Get the latest snapshot of the given entrypoint resource; require that
        exactly one is found, or raise an exception.

        Args:
            resource_id: A resource ID
            deletion_policy: Whether to look at deleted entrypoints, non-deleted
                entrypoints, or all entrypoints
            error_if_not_found: If True, raise an error if the entrypoint is not found.

        Returns:
            An EntryPoint object

        Raises:
            EntityDoesNotExistError: if the entrypoint does not exist in the
                database (deleted or not)
            EntityExistsError: if the entrypoint exists and is not deleted, but
                policy was to find a deleted entrypoint
            EntityDeletedError: if the entrypoint is deleted, but policy was to
                find a non-deleted entrypoint
        """
        entrypoint = utils.get_one_latest_snapshot(
            self.session, EntryPoint, resource_id, deletion_policy
        )

        if entrypoint is None and error_if_not_found:
            raise EntityDoesNotExistError("entry_point", entrypoint_id=resource_id)

        return entrypoint

    def get_one_snapshot(
        self,
        snapshot_id: int,
        deletion_policy: utils.DeletionPolicy,
    ) -> EntryPoint:
        """
        Get the a specific entrypoint snapshot given the resource snapshot ID; require
        that exactly one is found, or raise an exception.

        Args:
            snapshot_id: A resource snapshot ID
            deletion_policy: Whether to look at deleted entrypoints, non-deleted
                entrypoints, or all entrypoints

        Returns:
            An EntryPoint object

        Raises:
            EntityDoesNotExistError: if the entrypoint does not exist in the
                database (deleted or not)
            EntityExistsError: if the entrypoint exists and is not deleted, but
                policy was to find a deleted entrypoint
            EntityDeletedError: if the entrypoint is deleted, but policy was to
                find a non-deleted entrypoint
        """
        return utils.get_one_snapshot(
            self.session, EntryPoint, snapshot_id, deletion_policy
        )

    def get_by_name(
        self,
        name: str,
        group: Group | int,
        deletion_policy: utils.DeletionPolicy = utils.DeletionPolicy.NOT_DELETED,
    ) -> EntryPoint | None:
        """
        Get an entrypoint by name.  This returns the latest version (snapshot)
        of the entrypoint.

        Args:
            name: An entrypoint name
            group: A group/group ID, to disambiguate same-named entrypoints
                across groups
            deletion_policy: Whether to look at deleted entrypoints,
                non-deleted entrypoints, or all entrypoints

        Returns:
            An entrypoint, or None if one was not found

        Raises:
            EntityDoesNotExistError: if the given group does not exist
            EntityDeletedError: if the given group is deleted
        """
        return utils.get_snapshot_by_name(
            self.session, EntryPoint, name, group, deletion_policy
        )

    def get_entrypoints(
        self,
        entrypoint: EntryPoint | int,
        deletion_policy: utils.DeletionPolicy = utils.DeletionPolicy.NOT_DELETED,
    ) -> Sequence[EntryPoint]:
        """
        Get the child entry points of the given entrypoint as their latest
        snapshots.  If an EntryPoint object is given, the returned sequence
        may be shorter than len(entrypoint.children) if any of the children
        don't exist, or were filtered out due to deletion policy.

        Args:
            entrypoint: An EntryPoint object or resource_id integer primary key
                value
            deletion_policy: Whether to look at deleted entry points,
                non-deleted entry points, or all entry points

        Returns:
            The entry points

        Raises:
            EntityDoesNotExistError: if parent does not exist
            EntityDeletedError: if parent is deleted
        """

        return utils.get_latest_child_snapshots(
            self.session,
            EntryPoint,
            entrypoint,
            deletion_policy,
        )

    def add_queues(
        self,
        entrypoint: EntryPoint | int,
        queues: Iterable[Queue | Resource | int],
    ) -> Sequence[Queue]:
        """
        Add the given entry points as children of the given experiment.

        Args:
            experiment: An Experiment object or resource_id integer primary key value
            children: The entry points to add

        Returns:
            The complete list of queue children, as latest snapshots (including both
            pre-existing and new children).

        Raises:
            EntityDoesNotExistError: if parent or any new child does not exist
            EntityDeletedError: if parent or any new child is deleted
        """
        snaps = utils.append_resource_children(self.session, Queue, entrypoint, queues)
        return [snap for snap in snaps if isinstance(snap, Queue)]

    def unlink_child(
        self,
        entrypoint: EntryPoint | int,
        child: Queue | Plugin | int,
    ):
        """
        "Unlink" the given child resource from the given entrypoint.  This
        only severs the relationship; it does not delete either resource.  If
        there is no parent/child relationship, this is a no-op.

        Args:
            experiment: An entrypoint or resource_id integer primary key value
            child: A queue or plugin or resource_id integer primary key value

        Raises:
            EntityDoesNotExistError: if parent or child do not exist
        """
        utils.unlink_child(self.session, entrypoint, child)

    def unlink_queues(
        self,
        entrypoint: EntryPoint | int,
    ) -> Sequence[int]:
        """
        "Unlink" the given child resource from the given entrypoint.  This
        only severs the relationship; it does not delete either resource.  If
        there is no parent/child relationship, this is a no-op.

        Args:
            experiment: An entrypoint or resource_id integer primary key value
            child: A queue or plugin or resource_id integer primary key value

        Raises:
            EntityDoesNotExistError: if parent or child do not exist
        """
        return utils.unlink_children(self.session, entrypoint, "queue")

    def delete(self, entrypoint: EntryPoint | int) -> None:
        """
        Delete an entrypoint.  No-op if the entrypoint is already deleted.

        Args:
            entrypoint: A Experiment object or resource_id primary key value
                identifying an entrypoint resource

        Raises:
            EntityDoesNotExistError: if the entrypoint does not exist
        """

        utils.delete_resource(self.session, entrypoint)

    def get_by_filters_paged(
        self,
        group: Group | int | None,
        filters: list[dict],
        page_start: int,
        page_length: int,
        sort_by: str | None,
        descending: bool,
        deletion_policy: utils.DeletionPolicy = utils.DeletionPolicy.NOT_DELETED,
    ) -> tuple[Sequence[EntryPoint], int]:
        """
        Get some entrypoints according to search criteria.

        Args:
            group: Limit entrypoints to those owned by this group; None to not
                limit the search
            filters: Search criteria, see parse_search_text()
            page_start: Zero-based row index where the page should start
            page_length: Maximum number of rows in the page; use <= 0 for
                unlimited length
            sort_by: Sort criterion; must be a key of SORTABLE_FIELDS.  None
                to sort in an implementation-dependent way.
            descending: Whether to sort in descending order; only applicable
                if sort_by is given
            deletion_policy: Whether to look at deleted entrypoints, non-deleted
                entrypoints, or all entrypoints

        Returns:
            A 2-tuple including the page of entrypoints and total count of
            matching entrypoints which exist

        Raises:
            SearchParseError: if filters includes a non-searchable field
            SortParameterValidationError: if sort_by is a non-sortable field
            EntityDoesNotExistError: if the given group does not exist
            EntityDeletedError: if the given group is deleted
        """

        return utils.get_by_filters_paged(
            self.session,
            EntryPoint,
            self.SORTABLE_FIELDS,
            self.SEARCHABLE_FIELDS,
            group,
            filters,
            page_start,
            page_length,
            sort_by,
            descending,
            deletion_policy,
        )
