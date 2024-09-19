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

import sqlalchemy as sa

from dioptra.restapi.db.models import Group, Queue, Resource
from dioptra.restapi.db.repository.errors import QueueAlreadyExistsError
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
    delete_resource,
    get_group_id,
    get_resource_id,
)
from dioptra.restapi.db.shared_errors import ResourceError


class QueueRepository:
    def __init__(self, session: CompatibleSession[S]):
        self.session = session

    def create(self, queue: Queue) -> None:
        """
        Create a new queue resource.  This creates both the resource and the
        initial snapshot.

        Args:
            queue: The queue to create
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
            raise QueueAlreadyExistsError("Queue name already exists")

        if queue.resource.resource_type != "queue":
            raise Exception(
                f'Queue resource type must be "queue": {queue.resource.resource_type}'
            )

        self.session.add(queue)

    def create_snapshot(self, queue: Queue) -> None:
        """
        Create a new queue snapshot.

        Args:
            queue: A Queue object with the desired snapshot settings
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
            raise Exception(
                f'Queue resource type must be "queue": {queue.resource.resource_type}'
            )

        # In case the name is changing in this snapshot, ensure uniqueness with
        # respect to the owning group.  We must allow repeated queue names
        # within the same resource (e.g. if the name does not change across
        # snapshots), so the requirement only applies with respect to other
        # queue resources in the same group.  So reusing get_by_name() would
        # not work here.
        queue_id = get_resource_id(queue)
        sub_stmt: sa.Select = (
            sa.select(sa.literal_column("1"))
            .select_from(Queue)
            .join(Resource)
            .where(
                Queue.name == queue.name,
                # Dunno why mypy has trouble with this expression... could
                # also add a cast, but what to cast it to?
                Resource.owner == queue.resource.owner,  # type: ignore
                Queue.resource_id != queue_id,
            )
        )

        exists_stmt = sa.select(sub_stmt.exists())
        exists = self.session.scalar(exists_stmt)
        if exists:
            raise QueueAlreadyExistsError("Queue name in use: " + queue.name)

        # Assume that the new snapshot's created_on timestamp is later than the
        # current latest timestamp?

        self.session.add(queue)

    def delete(self, queue: Queue | int) -> None:
        """
        Delete a queue.  No-op if the queue is already deleted.

        Args:
            queue: A Queue object or resource_id primary key value identifying
                a queue resource
        """

        try:
            delete_resource(self.session, queue)
        except ResourceError as e:
            # if an integer ID was passed, the exception here won't include
            # the resource type, so ensure it's set
            if not e.resource_type:
                e.resource_type = "queue"
            raise

    def get(
        self,
        resource_ids: int | Iterable[int],
        deletion_policy: DeletionPolicy = DeletionPolicy.NOT_DELETED,
    ) -> Queue | Sequence[Queue] | None:
        """
        Get the latest snapshot of the given queue resource.

        Args:
            resource_ids: An ID or iterable of IDs of queue resource IDs
            deletion_policy: Whether to look at deleted queues, non-deleted
                queue, or all queues

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
                queue, or all queues

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
                queue, or all queues

        Returns:
            A queue, or None if one was not found
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
