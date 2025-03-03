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

from collections.abc import Iterable, Sequence
from typing import Any, Final

import sqlalchemy as sa

from dioptra.restapi.db.models import Group, Queue, Resource, Tag
from dioptra.restapi.db.repository.utils import (
    CompatibleSession,
    DeletionPolicy,
    S,
    apply_resource_deletion_policy,
    assert_group_exists,
    assert_resource_does_not_exist,
    assert_resource_exists,
    assert_snapshot_does_not_exist,
    assert_user_exists,
    assert_user_in_group,
    construct_sql_query_filters,
    delete_resource,
    get_group_id,
    get_resource_id,
)
from dioptra.restapi.errors import (
    EntityExistsError,
    MismatchedResourceTypeError,
    SortParameterValidationError,
)


class QueueRepository:

    SEARCHABLE_FIELDS: Final[dict[str, Any]] = {
        "name": lambda x: Queue.name.like(x, escape="/"),
        "description": lambda x: Queue.description.like(x, escape="/"),
        "tag": lambda x: Queue.tags.any(Tag.name.like(x, escape="/")),
    }

    # Maps a general sort criterion name to a Queue attribute name
    SORTABLE_FIELDS: Final[dict[str, str]] = {
        "name": "name",
        "createdOn": "created_on",
        "lastModifiedOn": "last_modified_on",
        "description": "description",
    }

    def __init__(self, session: CompatibleSession[S]):
        self.session = session

    def create(self, queue: Queue) -> None:
        """
        Create a new queue resource.  This creates both the resource and the
        initial snapshot.

        Args:
            queue: The queue to create

        Raises:
            EntityExistsError: if the queue resource or snapshot already
                exists, or the queue name collides with another queue in the
                same group
            EntityDoesNotExistError: if the group owner or user creator does
                not exist
            EntityDeletedError: if the queue, its creator, or its group owner
                is deleted
            UserNotInGroupError: if the user creator is not a member of the
                group who will own the resource
            MismatchedResourceTypeError: if the resource type is not "queue"
        """

        # Consistency rules:
        # - Latest-snapshot queue names must be unique within the owning group
        # - Queue snapshots must be of queue resources
        # - For now, the snapshot creator must be a member of the group who
        #   owns the resource.  I think this will become more complicated when
        #   we implement shares and permissions.

        assert_resource_does_not_exist(self.session, queue, DeletionPolicy.ANY)
        assert_snapshot_does_not_exist(self.session, queue)
        assert_user_exists(self.session, queue.creator, DeletionPolicy.NOT_DELETED)
        assert_group_exists(
            self.session, queue.resource.owner, DeletionPolicy.NOT_DELETED
        )
        assert_user_in_group(self.session, queue.creator, queue.resource.owner)

        check_name = self.get_by_name(
            queue.name, queue.resource.owner, DeletionPolicy.ANY
        )
        if check_name:
            raise EntityExistsError(
                "queue",
                check_name.resource_id,
                name=queue.name,
                group_id=queue.resource.owner.group_id,
            )

        if queue.resource.resource_type != "queue":
            raise MismatchedResourceTypeError("queue", queue.resource.resource_type)

        self.session.add(queue)

    def create_snapshot(self, queue: Queue) -> None:
        """
        Create a new queue snapshot.

        Args:
            queue: A Queue object with the desired snapshot settings

        Raises:
            EntityDoesNotExistError: if the queue resource or snapshot creator
                user does not exist
            EntityExistsError: if the snapshot already exists, or this new
                snapshot's queue name collides with another queue in the same
                group
            EntityDeletedError: if the queue or snapshot creator user are
                deleted
            UserNotInGroupError: if the snapshot creator user is not a member
                of the group who owns the queue
            MismatchedResourceTypeError: if the snapshot's resource's type is
                not "queue"
        """
        # Consistency rules:
        # - Latest-snapshot queue names must be unique within the owning group
        # - Queue snapshots must be of queue resources
        # - Snapshot timestamps must be monotonically increasing(?)
        # - For now, the snapshot creator must be a member of the group who
        #   owns the resource.  I think this will become more complicated when
        #   we implement shares and permissions.

        assert_resource_exists(self.session, queue, DeletionPolicy.NOT_DELETED)
        assert_snapshot_does_not_exist(self.session, queue)
        assert_user_exists(self.session, queue.creator, DeletionPolicy.NOT_DELETED)
        assert_user_in_group(self.session, queue.creator, queue.resource.owner)

        if queue.resource.resource_type != "queue":
            raise MismatchedResourceTypeError("queue", queue.resource.resource_type)

        # In case the name is changing in this snapshot, ensure uniqueness with
        # respect to the owning group.  We must allow repeated queue names
        # within the same resource (e.g. if the name does not change across
        # snapshots), so the requirement only applies with respect to other
        # queue resources in the same group.  So reusing get_by_name() would
        # not work here.
        queue_id = get_resource_id(queue)
        sub_stmt = (
            sa.select(Queue.resource_id)
            .join(Resource)
            .where(
                Queue.name == queue.name,
                # Dunno why mypy has trouble with this expression... could
                # also add a cast, but what to cast it to?
                Resource.owner == queue.resource.owner,  # type: ignore
                Queue.resource_id != queue_id,
            )
        )

        existing_id = self.session.scalar(sub_stmt)
        if existing_id:
            raise EntityExistsError(
                "queue",
                existing_id,
                name=queue.name,
                group_id=queue.resource.owner.group_id,
            )

        # Assume that the new snapshot's created_on timestamp is later than the
        # current latest timestamp?

        self.session.add(queue)

    def delete(self, queue: Queue | int) -> None:
        """
        Delete a queue.  No-op if the queue is already deleted.

        Args:
            queue: A Queue object or resource_id primary key value identifying
                a queue resource

        Raises:
            EntityDoesNotExistError: if the queue does not exist
        """

        delete_resource(self.session, queue)

    def get(
        self,
        resource_ids: int | Iterable[int],
        deletion_policy: DeletionPolicy = DeletionPolicy.NOT_DELETED,
    ) -> Queue | Sequence[Queue] | None:
        """
        Get the latest snapshot of the given queue resource.

        Args:
            resource_ids: A single or iterable of queue resource IDs
            deletion_policy: Whether to look at deleted queues, non-deleted
                queues, or all queues

        Returns:
            A Queue/list of Queue objects, or None/empty list if none were
            found with the given ID(s)
        """

        if isinstance(resource_ids, int):
            resource_id_check = Queue.resource_id == resource_ids
        else:
            resource_id_check = Queue.resource_id.in_(resource_ids)

        # Extra join with Resource is important: the query produces incorrect
        # results without it!
        stmt = (
            sa.select(Queue)
            .join(Resource)
            .where(
                resource_id_check,
                Queue.resource_snapshot_id == Resource.latest_snapshot_id,
            )
        )
        stmt = apply_resource_deletion_policy(stmt, deletion_policy)

        queues: Queue | Sequence[Queue] | None
        if isinstance(resource_ids, int):
            queues = self.session.scalar(stmt)
        else:
            queues = self.session.scalars(stmt).all()

        return queues

    def get_snapshot(
        self,
        snapshot_id: int,
        deletion_policy: DeletionPolicy = DeletionPolicy.NOT_DELETED,
    ) -> Queue | None:
        """
        Get a given queue snapshot.

        Args:
            snapshot_id: The ID of a queue snapshot
            deletion_policy: Whether to look at deleted queues, non-deleted
                queues, or all queues

        Returns:
            A Queue object, or None if one was not found with the given ID
        """
        stmt = sa.select(Queue).where(Queue.resource_snapshot_id == snapshot_id)
        stmt = apply_resource_deletion_policy(stmt, deletion_policy)

        queue = self.session.scalar(stmt)
        return queue

    def get_by_name(
        self,
        name: str,
        group: Group | int,
        deletion_policy: DeletionPolicy = DeletionPolicy.NOT_DELETED,
    ) -> Queue | None:
        """
        Get a queue by name.  This returns the latest version (snapshot) of
        the queue.

        Args:
            name: A queue name
            group: A group/group ID, to disambiguate same-named queues across
                groups
            deletion_policy: Whether to look at deleted queues, non-deleted
                queues, or all queues

        Returns:
            A queue, or None if one was not found

        Raises:
            EntityDoesNotExistError: if the given group does not exist
            EntityDeletedError: if the given group is deleted
        """

        assert_group_exists(self.session, group, DeletionPolicy.NOT_DELETED)

        group_id = get_group_id(group)

        stmt = (
            sa.select(Queue)
            .join(Resource)
            .where(
                Queue.resource_snapshot_id == Resource.latest_snapshot_id,
                Resource.group_id == group_id,
                Queue.name == name,
            )
        )

        stmt = apply_resource_deletion_policy(stmt, deletion_policy)

        queue = self.session.scalar(stmt)

        return queue

    def get_by_filters_paged(
        self,
        group: Group | int | None,
        filters: list[dict],
        page_start: int,
        page_length: int,
        sort_by: str | None,
        descending: bool,
        deletion_policy: DeletionPolicy = DeletionPolicy.NOT_DELETED,
    ) -> tuple[Sequence[Queue], int]:
        """
        Get some queues according to search criteria.

        Args:
            group: Limit queues to those owned by this group; None to not limit
                the search
            filters: Search criteria, see parse_search_text()
            page_start: Zero-based row index where the page should start
            page_length: Maximum number of rows in the page; use <= 0 for
                unlimited length
            sort_by: Sort criterion; must be a key of SORTABLE_FIELDS.  None
                to sort in an implementation-dependent way.
            descending: Whether to sort in descending order; only applicable
                if sort_by is given
            deletion_policy: Whether to look at deleted queues, non-deleted
                queues, or all queues

        Returns:
            A 2-tuple including the page of queues and total count of matching
            queues which exist

        Raises:
            SearchParseError: if filters includes a non-searchable field
            SortParameterValidationError: if sort_by is a non-sortable field
            EntityDoesNotExistError: if the given group does not exist
            EntityDeletedError: if the given group is deleted
        """
        sql_filter = construct_sql_query_filters(filters, self.SEARCHABLE_FIELDS)
        if sort_by:
            if sort_by in self.SORTABLE_FIELDS:
                sort_by = self.SORTABLE_FIELDS[sort_by]
            else:
                raise SortParameterValidationError("queue", sort_by)
        group_id = None if group is None else get_group_id(group)

        if group_id is not None:
            assert_group_exists(self.session, group_id, DeletionPolicy.NOT_DELETED)

        count_stmt = (
            sa.select(sa.func.count())
            .select_from(Queue)
            .join(Resource)
            .where(Queue.resource_snapshot_id == Resource.latest_snapshot_id)
        )

        if group_id is not None:
            count_stmt = count_stmt.where(Resource.group_id == group_id)

        if sql_filter is not None:
            count_stmt = count_stmt.where(sql_filter)

        count_stmt = apply_resource_deletion_policy(count_stmt, deletion_policy)
        current_count = self.session.scalar(count_stmt)

        # For mypy: a "SELECT count(*)..." query should never return NULL.
        assert current_count is not None

        queues: Sequence[Queue]
        if current_count == 0:
            queues = []
        else:
            page_stmt = (
                sa.select(Queue)
                .join(Resource)
                .where(Queue.resource_snapshot_id == Resource.latest_snapshot_id)
            )

            if group_id is not None:
                page_stmt = page_stmt.where(Resource.group_id == group_id)

            if sql_filter is not None:
                page_stmt = page_stmt.where(sql_filter)

            page_stmt = apply_resource_deletion_policy(page_stmt, deletion_policy)

            if sort_by:
                sort_criteria = getattr(Queue, sort_by)
                if descending:
                    sort_criteria = sort_criteria.desc()
            else:
                # *must* enforce a sort order for consistent paging
                sort_criteria = Queue.resource_snapshot_id
            page_stmt = page_stmt.order_by(sort_criteria)

            page_stmt = page_stmt.offset(page_start)
            if page_length > 0:
                page_stmt = page_stmt.limit(page_length)

            queues = self.session.scalars(page_stmt).all()

        return queues, current_count
