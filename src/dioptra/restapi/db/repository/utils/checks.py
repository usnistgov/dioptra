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
"Checkers" of various kinds, including assert_* style functions which raise
exceptions, and non-assert style functions which just return information
without raising exceptions.
"""
from collections.abc import Iterable, Mapping

import sqlalchemy as sa

import dioptra.restapi.db.models as m
import dioptra.restapi.errors as e
from dioptra.restapi.db.models.constants import (
    group_lock_types,
    resource_lock_types,
    user_lock_types,
)
from dioptra.restapi.db.repository.utils.common import (
    CompatibleSession,
    DeletionPolicy,
    ExistenceResult,
    S,
    get_draft_id,
    get_group_id,
    get_resource_id,
    get_resource_snapshot_id,
    get_user_id,
)


def user_exists(session: CompatibleSession[S], user: m.User | int) -> ExistenceResult:
    """
    Check whether the given user exists in the database, and if so, whether
    it was deleted or not.

    Args:
        session: An SQLAlchemy session
        user: A User object or user_id integer primary key value

    Returns:
        One of the ExistenceResult enum values
    """

    user_id = get_user_id(user)

    if user_id is None:
        exists = ExistenceResult.DOES_NOT_EXIST
    else:
        # May as well get existence + deletion status in one query.  I think
        # this ought to be more efficient than getting the whole User object
        # and then checking .is_deleted.
        stmt = (
            sa.select(m.User.user_id, m.UserLock.user_lock_type)
            .outerjoin(m.UserLock)
            .where(m.User.user_id == user_id)
        )
        results = session.execute(stmt)
        # will need to change if a user may have multiple lock types
        row = results.first()

        if not row:
            exists = ExistenceResult.DOES_NOT_EXIST
        elif row[1] == user_lock_types.DELETE:
            exists = ExistenceResult.DELETED
        else:
            exists = ExistenceResult.EXISTS

    return exists


def group_exists(
    session: CompatibleSession[S], group: m.Group | int
) -> ExistenceResult:
    """
    Check whether the given group exists in the database, and if so, whether
    it was deleted or not.

    Args:
        session: An SQLAlchemy session
        group: A Group object or group_id integer primary key value

    Returns:
        One of the ExistenceResult enum values
    """

    group_id = get_group_id(group)

    if group_id is None:
        exists = ExistenceResult.DOES_NOT_EXIST
    else:
        # May as well get existence + deletion status in one query
        stmt = (
            sa.select(m.Group.group_id, m.GroupLock.group_lock_type)
            .outerjoin(m.GroupLock)
            .where(m.Group.group_id == group_id)
        )
        results = session.execute(stmt)
        # will need to change if a group may have multiple lock types
        row = results.first()

        if not row:
            exists = ExistenceResult.DOES_NOT_EXIST
        elif row[1] == group_lock_types.DELETE:
            exists = ExistenceResult.DELETED
        else:
            exists = ExistenceResult.EXISTS

    return exists


def resource_exists(
    session: CompatibleSession[S], resource: m.Resource | m.ResourceSnapshot | int
) -> ExistenceResult:
    """
    Check whether the given resource exists in the database, and if so, whether
    it was deleted or not.

    Args:
        session: An SQLAlchemy session
        resource: A resource, snapshot (something with a .resource_id
            attribute we can use to identify a resource), or resource_id
            integer primary key value

    Returns:
        One of the ExistenceResult enum values
    """

    resource_id = get_resource_id(resource)

    if resource_id is None:
        exists = ExistenceResult.DOES_NOT_EXIST
    else:
        stmt = (
            sa.select(m.ResourceLock.resource_lock_type)
            .select_from(m.Resource)
            .outerjoin(m.ResourceLock)
            .where(m.Resource.resource_id == resource_id)
            # Note: using "IN ('delete', NULL)" as a shortcut operator doesn't
            # work here, since IN operates via '=', and '=' doesn't behave as
            # expected with nulls.
            .where(
                sa.or_(
                    m.ResourceLock.resource_lock_type == resource_lock_types.DELETE,
                    m.ResourceLock.resource_lock_type == None,  # noqa: E711
                )
            )
        )

        # This really ought to only produce at most one value
        locks = session.scalars(stmt).all()

        if not locks:
            exists = ExistenceResult.DOES_NOT_EXIST
        elif resource_lock_types.DELETE in locks:
            exists = ExistenceResult.DELETED
        else:
            exists = ExistenceResult.EXISTS

    return exists


def resources_exist(
    session: CompatibleSession[S],
    resources: Iterable[m.Resource | m.ResourceSnapshot | int],
) -> dict[int, ExistenceResult]:
    """
    Get bulk existence information for the given resources.  A mapping from
    resource ID to ExistenceResult value is returned.  This mapping may have
    fewer entries than the number of resources passed in, if some resources
    were Resource or ResourceSnapshot objects with null resource IDs.

    Args:
        session: An SQLAlchemy session
        resources: An iterable of resources, snapshots (something with a
            .resource_id attribute we can use to identify a resource), or
            resource_id integer primary key values

    Returns:
        A dict mapping a resource_id to an ExistenceResult enum.
    """
    resource_ids = []
    for resource in resources:
        resource_id = get_resource_id(resource)
        if resource_id is not None:
            resource_ids.append(resource_id)

    if resource_ids:
        status_stmt = (
            sa.select(m.Resource.resource_id, m.ResourceLock.resource_lock_type)
            .outerjoin(m.ResourceLock)
            .where(
                m.Resource.resource_id.in_(resource_ids),
                sa.or_(
                    m.ResourceLock.resource_lock_type == resource_lock_types.DELETE,
                    m.ResourceLock.resource_lock_type == None,  # noqa: E711
                ),
            )
        )

        child_status_result = session.execute(status_stmt)

        # Init to not-exist, update as necessary
        resource_status = dict.fromkeys(resource_ids, ExistenceResult.DOES_NOT_EXIST)
        for resource_id, resource_lock in child_status_result:
            # For mypy: resource_id here comes from Resource.resource_id, which
            # is a primary key column and can't be null.
            assert resource_id is not None
            if resource_lock is None:
                resource_status[resource_id] = ExistenceResult.EXISTS
            else:
                # must == resource_lock_types.DELETE
                resource_status[resource_id] = ExistenceResult.DELETED

    else:
        # Found no resources with IDs
        resource_status = {}

    return resource_status


def resource_children_exist(
    session: CompatibleSession[S], resource: m.Resource | m.ResourceSnapshot | int
) -> dict[int, ExistenceResult]:
    """
    Get bulk existence information for the children of the given resource.  If
    a Resource or ResourceSnapshot object is passed, the children examined are
    those in its "children" attribute; if a resource_id integer is passed,
    the database is consulted to find the children.

    Args:
        session: An SQLAlchemy session
        resource: A resource, snapshot (something with a .resource_id
            attribute we can use to identify a resource), or resource_id
            integer primary key value

    Returns:
        A dict mapping child resource_id to an ExistenceResult enum.  This
        dict may have fewer entries than children if a Resource or
        ResourceSnapshot object were passed, with child objects with null IDs.
    """

    children: Iterable[m.Resource | m.ResourceSnapshot | int]

    if isinstance(resource, (m.Resource, m.ResourceSnapshot)):
        children = resource.children
    else:
        children_stmt = sa.select(
            m.resource_dependencies_table.c.child_resource_id
        ).where(
            m.resource_dependencies_table.c.parent_resource_id == resource,
        )
        children = session.scalars(children_stmt).all()

    child_status = resources_exist(session, children)

    return child_status


def resource_modifiable(
    session: CompatibleSession[S], resource: m.Resource | m.ResourceSnapshot | int
) -> bool:
    """
    Check for a read-only lock on the given resource.  If there is no lock,
    the resource is modifiable.  If the resource does not exist, then there
    will be no lock, and this function will return True.

    Args:
        session: An SQLAlchemy session
        resource: A resource, snapshot (something with a .resource_id
            attribute we can use to identify a resource), or resource_id
            integer primary key value

    Returns:
        True if the resource is modifiable or doesn't exist; False if the
        resource exists and has a read-only lock.

    See Also:
        - :py:func:`get_resource_lock_types`
    """

    resource_id = get_resource_id(resource)

    if resource_id is None:
        modifiable = True
    else:
        stmt: sa.Select = sa.select(sa.literal_column("1")).where(
            m.ResourceLock.resource_id == resource_id,
            m.ResourceLock.resource_lock_type == resource_lock_types.READONLY,
        )
        exists_stmt = sa.select(stmt.exists())

        modifiable = not session.scalar(exists_stmt)

    return modifiable


def snapshot_exists(
    session: CompatibleSession[S], snapshot: m.ResourceSnapshot | int
) -> bool:
    """
    Check whether the given snapshot exists in the database.  Snapshots can't
    be individually deleted (only the resources), so a deletion check is not
    applicable here.

    Args:
        session: An SQLAlchemy session
        snapshot: A snapshot object or resource_snapshot_id integer primary key
            value

    Returns:
        True if the snapshot exists; False if not
    """

    snapshot_id = get_resource_snapshot_id(snapshot)

    exists: bool | None
    if snapshot_id is None:
        exists = False

    else:
        sub_stmt: sa.Select = (
            sa.select(sa.literal_column("1"))
            .select_from(m.ResourceSnapshot)
            .where(m.ResourceSnapshot.resource_snapshot_id == snapshot_id)
        )
        exists_stmt = sa.select(sub_stmt.exists())

        exists = session.scalar(exists_stmt)

        # For mypy.  I think a "select exists(....)" should always return true
        # or false.
        assert exists is not None

    return exists


def draft_exists(session: CompatibleSession[S], draft: m.DraftResource | int) -> bool:
    """
    Check whether the given draft exists in the database.

    Args:
        session: An SQLAlchemy session
        draft: A DraftResource object, or draft_resource_id primary key
            value

    Returns:
        True if the draft exists; False if not
    """
    draft_id = get_draft_id(draft)

    exists: bool | None
    if draft_id is None:
        exists = False
    else:
        sub_stmt: sa.Select = (
            sa.select(sa.literal_column("1"))
            .select_from(m.DraftResource)
            .where(m.DraftResource.draft_resource_id == draft_id)
        )
        exists_stmt = sa.select(sub_stmt.exists())

        exists = session.scalar(exists_stmt)

        # a "SELECT EXISTS(...)" should always return a row (true/false).
        assert exists is not None

    return exists


def assert_user_exists(
    session: CompatibleSession[S], user: m.User | int, deletion_policy: DeletionPolicy
) -> None:
    """
    Check whether the given user exists in the database.  This function accepts
    a policy value expressing the caller's preference with respect to deleted
    users:

        ANY: Check whether the user exists in the database at all (deletion
             state doesn't matter)
        NOT_DELETED: Check whether the user exists in the database and is not
             deleted
        DELETED: Check whether the user exists in the database and is deleted

    Args:
        session: An SQLAlchemy session
        user: A User object or user_id integer primary key value
        deletion_policy: One of the DeletionPolicy enum values

    Raises:
        EntityDoesNotExistError: if the user does not exist in the database
            (deleted or not)
        EntityExistsError: if the user exists and is not deleted, but policy
            was to find a deleted user
        EntityDeletedError: if the user is deleted, but policy was to find
            a non-deleted user
    """
    existence_result = user_exists(session, user)

    user_id = get_user_id(user)

    assert_exists(deletion_policy, existence_result, "user", user_id, user_id=user_id)


def assert_group_exists(
    session: CompatibleSession[S], group: m.Group | int, deletion_policy: DeletionPolicy
) -> None:
    """
    Check whether the given group exists in the database.  This function accepts
    a policy value expressing the caller's preference with respect to deleted
    groups:

        ANY: Check whether the group exists in the database at all (deletion
             state doesn't matter)
        NOT_DELETED: Check whether the group exists in the database and is not
             deleted
        DELETED: Check whether the group exists in the database and is deleted

    Args:
        session: An SQLAlchemy session
        group: A Group object or group_id integer primary key value
        deletion_policy: One of the DeletionPolicy enum values

    Raises:
        EntityDoesNotExistError: if the group does not exist in the database
            (deleted or not)
        EntityExistsError: if the group exists and is not deleted, but policy
            was to find a deleted group
        EntityDeletedError: if the group is deleted, but policy was to find
            a non-deleted group
    """
    existence_result = group_exists(session, group)

    group_id = get_group_id(group)

    assert_exists(
        deletion_policy,
        existence_result,
        "group",
        group_id,
        group_id=group_id,
    )


def assert_resource_exists(
    session: CompatibleSession[S],
    resource: m.Resource | m.ResourceSnapshot | int,
    deletion_policy: DeletionPolicy,
) -> None:
    """
    Check whether the given resource exists in the database.  This function
    accepts a policy value expressing the caller's preference with respect to
    deleted resources:

        ANY: Check whether the resource exists in the database at all (deletion
            state doesn't matter)
        NOT_DELETED: Check whether the resource exists in the database and is
            not deleted
        DELETED: Check whether the resource exists in the database and is
            deleted

    Args:
        session: An SQLAlchemy session
        resource: A resource, snapshot, or resource_id integer primary key
            value
        deletion_policy: One of the DeletionPolicy enum values

    Raises:
        EntityDoesNotExistError: if the resource does not exist in the database
            (deleted or not)
        EntityExistsError: if the resource exists and is not deleted, but
            policy was to find a deleted resource
        EntityDeletedError: if the resource is deleted, but policy was to find
            a non-deleted resource
    """
    existence_result = resource_exists(session, resource)

    resource_id = get_resource_id(resource)
    if isinstance(resource, int):
        resource_type = None
    else:
        resource_type = resource.resource_type

    assert_exists(
        deletion_policy,
        existence_result,
        resource_type,
        resource_id,
        resource_id=resource_id,
    )


def assert_resources_exist(
    session: CompatibleSession[S],
    resources: Iterable[m.Resource | m.ResourceSnapshot | int],
    deletion_policy: DeletionPolicy,
):
    """
    Check whether the given resources exist, relative to the given deletion
    policy.

    Args:
        session: An SQLAlchemy session
        resources: An iterable of resources, snapshots (something with a
            .resource_id attribute we can use to identify a resource), or
            resource_id integer primary key values
        deletion_policy: One of the DeletionPolicy enum values

    Raises:
        EntityDoesNotExistError: if any resource does not exist
        EntityDeletedError: if policy is NOT_DELETED, all resources exist,
            but some were deleted.
        EntityExistsError: if policy is DELETED, all resources exist, and
            some were not deleted.
    """
    resource_status = resources_exist(session, resources)

    try:
        # yeah, I know resources is not "Sized", that's the whole point of the
        # try-except!
        num_resources = len(resources)  # type: ignore
    except TypeError:
        num_resources = None

    _assert_exists_multi(deletion_policy, resource_status, num_resources)


def assert_resource_children_exist(
    session: CompatibleSession[S],
    resource: m.Resource | m.ResourceSnapshot | int,
    deletion_policy: DeletionPolicy,
):
    """
    Check whether the children of the given resource exist, relative to the
    given deletion policy.

    Args:
        session: An SQLAlchemy session
        resource: A resource, snapshot (something with a .resource_id
            attribute we can use to identify a resource), or resource_id
            integer primary key value
        deletion_policy: One of the DeletionPolicy enum values

    Raises:
        EntityDoesNotExistError: if any child of the given resource does not
            exist
        EntityDeletedError: if policy is NOT_DELETED, all children exist,
            but some were deleted.
        EntityExistsError: if policy is DELETED, all children exist, and
            some were not deleted.
    """

    child_status = resource_children_exist(session, resource)

    if isinstance(resource, (m.Resource, m.ResourceSnapshot)):
        num_children = len(resource.children)
    else:
        num_children = None

    _assert_exists_multi(deletion_policy, child_status, num_children)


def assert_resource_modifiable(
    session: CompatibleSession[S],
    resource: m.Resource | m.ResourceSnapshot | int,
) -> None:
    """
    Check for a read-only lock on the given resource.  If there is no lock,
    the resource is modifiable.  If the resource does not exist, then there
    will be no lock, and this function will treat it as modifiable and not
    throw.

    Args:
        session: An SQLAlchemy session
        resource: A resource, snapshot (something with a .resource_id
            attribute we can use to identify a resource), or resource_id
            integer primary key value

    Raises:
        ReadOnlyLockError: if the resource exists and has a read-only lock
    """

    modifiable = resource_modifiable(session, resource)

    if isinstance(resource, (m.Resource, m.ResourceSnapshot)):
        resource_type = resource.resource_type
    else:
        resource_type = None

    if not modifiable:
        raise e.ReadOnlyLockError(resource_type, resource_id=get_resource_id(resource))


def assert_resource_type(
    session: CompatibleSession[S],
    resource: m.Resource | m.ResourceSnapshot | int,
    resource_type: str,
) -> None:
    """
    Check the resource type of the given resource or snapshot.  If a snapshot
    is given, the resource type is checked on both the snapshot and its
    resource, separately.

    Args:
        session: An SQLAlchemy session
        resource: A resource, snapshot (something with a .resource_id
            attribute we can use to identify a resource), or resource_id
            integer primary key value
        resource_type: A resource type

    Raises:
        EntityDoesNotExistError: if a resource_id is given which doesn't
            resolve to a resource
        MismatchedResourceTypeError: if the resource and/or snapshot has the
            wrong resource_type
    """

    if isinstance(resource, int):
        resource_obj = session.get(m.Resource, resource)
        if not resource_obj:
            raise e.EntityDoesNotExistError(None, resource_id=resource)
        resource = resource_obj

    if isinstance(resource, (m.Resource, m.ResourceSnapshot)):
        if resource.resource_type != resource_type:
            raise e.MismatchedResourceTypeError(resource_type, resource.resource_type)

    if isinstance(resource, m.ResourceSnapshot):
        if resource.resource.resource_type != resource_type:
            raise e.MismatchedResourceTypeError(
                resource_type, resource.resource.resource_type
            )


def assert_snapshot_exists(
    session: CompatibleSession[S],
    snapshot: m.ResourceSnapshot | int,
) -> None:
    """
    Check whether the given snapshot exists in the database.  Snapshots can't
    be individually deleted (only the resources), so deletion policy is not
    applicable here.

    Args:
        session: An SQLAlchemy session
        snapshot: A snapshot object

    Raises:
        EntityDoesNotExistError: if the snapshot doesn't exist
    """

    if not snapshot_exists(session, snapshot):
        if isinstance(snapshot, int):
            resource_type = None
        else:
            resource_type = snapshot.resource_type

        snapshot_id = get_resource_snapshot_id(snapshot)

        raise e.EntityDoesNotExistError(resource_type, resource_snapshot_id=snapshot_id)


def assert_draft_exists(
    session: CompatibleSession[S], draft: m.DraftResource | int
) -> None:
    """
    Check whether the given draft exists in the database.

    Args:
        session: An SQLAlchemy session
        draft: A DraftResource object, or draft_resource_id primary key
            value

    Raises:
        DraftDoesNotExistError: if the draft doesn't exist
    """
    if not draft_exists(session, draft):
        draft_id = get_draft_id(draft)
        raise e.DraftDoesNotExistError(draft_resource_id=draft_id)


def assert_user_does_not_exist(
    session: CompatibleSession[S], user: m.User | int, deletion_policy: DeletionPolicy
) -> None:
    """
    Check whether the given user exists in the database.  This function accepts
    a policy value expressing the caller's preference with respect to deleted
    users:

        ANY: Ensure the user does not exist in the database at all (deletion
             state doesn't matter).  Same as user_exists(...) == DOES_NOT_EXIST
        NOT_DELETED: Ensure the user doesn't exist as non-deleted (deleted is
                     ok).  Same as user_exists(...) != EXISTS
        DELETED: Ensure the user doesn't exist as deleted (non-deleted ok)
                 Same as user_exists(...) != DELETED

    Args:
        session: An SQLAlchemy session
        user: A User object or user_id integer primary key value
        deletion_policy: One of the DeletionPolicy enum values

    Raises:
        EntityExistsError: if the user exists and is not deleted but
            policy is NOT_DELETED or ANY
        EntityDeletedError: if the user exists and is deleted but policy is
            DELETED or ANY
    """
    existence_result = user_exists(session, user)

    user_id = get_user_id(user)

    _assert_does_not_exist(
        deletion_policy,
        existence_result,
        "user",
        user_id,
        user_id=user_id,
    )


def assert_group_does_not_exist(
    session: CompatibleSession[S], group: m.Group | int, deletion_policy: DeletionPolicy
) -> None:
    """
    Check whether the given group exists in the database.  This function accepts
    a policy value expressing the caller's preference with respect to deleted
    groups:

        ANY: Ensure the group does not exist in the database at all (deletion
             state doesn't matter).  Same as group_exists(...) == DOES_NOT_EXIST
        NOT_DELETED: Ensure the group doesn't exist as non-deleted (deleted is
                     ok).  Same as group_exists(...) != EXISTS
        DELETED: Ensure the group doesn't exist as deleted (non-deleted ok).
                 Same as group_exists(...) != DELETED

    Args:
        session: An SQLAlchemy session
        group: A Group object or group_id integer primary key value
        deletion_policy: One of the DeletionPolicy enum values

    Raises:
        EntityExistsError: if the group exists and is not deleted but
            policy is NOT_DELETED or ANY
        EntityDeletedError: if the group exists and is deleted but policy is
            DELETED or ANY
    """
    existence_result = group_exists(session, group)

    group_id = get_group_id(group)

    _assert_does_not_exist(
        deletion_policy,
        existence_result,
        "group",
        group_id,
        group_id=group_id,
    )


def assert_resource_does_not_exist(
    session: CompatibleSession[S],
    resource: m.Resource | m.ResourceSnapshot | int,
    deletion_policy: DeletionPolicy,
) -> None:
    """
    Check whether the given resource exists in the database.  This function
    accepts a policy value expressing the caller's preference with respect to
    deleted resources:

        ANY: Ensure the resource does not exist in the database at all (deletion
             state doesn't matter).  Same as resource_exists(...) == DOES_NOT_EXIST
        NOT_DELETED: Ensure the resource doesn't exist as non-deleted (deleted is
                     ok).  Same as resource_exists(...) != EXISTS
        DELETED: Ensure the resource doesn't exist as deleted (non-deleted ok).
                 Same as resource_exists(...) != DELETED

    Args:
        session: An SQLAlchemy session
        resource: A resource, snapshot, or resource_id integer primary key
            value
        deletion_policy: One of the DeletionPolicy enum values

    Raises:
        EntityExistsError: if the resource exists and is not deleted but
            policy is NOT_DELETED or ANY
        EntityDeletedError: if the resource exists and is deleted but policy is
            DELETED or ANY
    """
    existence_result = resource_exists(session, resource)

    resource_id = get_resource_id(resource)
    if isinstance(resource, int):
        resource_type = None
    else:
        resource_type = resource.resource_type

    _assert_does_not_exist(
        deletion_policy,
        existence_result,
        resource_type,
        resource_id,
        resource_id=resource_id,
    )


def assert_snapshot_does_not_exist(
    session: CompatibleSession[S], snapshot: m.ResourceSnapshot | int
) -> None:
    """
    Check whether the given snapshot exists in the database.  Snapshots can't
    be individually deleted (only the resources), so deletion policy is not
    applicable here.

    Args:
        session: An SQLAlchemy session
        snapshot: A snapshot object

    Raises:
        EntityExistsError: if the snapshot exists
    """

    if snapshot_exists(session, snapshot):
        if isinstance(snapshot, int):
            resource_type = None
        else:
            resource_type = snapshot.resource_type

        snapshot_id = get_resource_snapshot_id(snapshot)

        # The snapshot exists (see the "if" statement above), therefore
        # its ID can't be None.
        assert snapshot_id is not None

        raise e.EntityExistsError(
            resource_type,
            snapshot_id,
            resource_snapshot_id=snapshot_id,
        )


def assert_draft_does_not_exist(
    session: CompatibleSession[S], draft: m.DraftResource | int
) -> None:
    """
    Check whether the given draft exists in the database.

    Args:
        session: An SQLAlchemy session
        draft: A DraftResource object, or draft_resource_id primary key
            value

    Raises:
        DraftAlreadyExistsError: if the draft exists
    """
    if draft_exists(session, draft):
        draft_id = get_draft_id(draft)

        # draft_id can't be done if the draft exists in the db
        assert draft_id is not None

        if isinstance(draft, int):
            resource_type = "resource"
        else:
            resource_type = draft.resource_type

        raise e.DraftAlreadyExistsError(resource_type, draft_id)


def assert_can_create_resource(
    session: CompatibleSession[S], snap: m.ResourceSnapshot, resource_type: str
):
    """
    Check whether the given snapshot+resource may be created.  There may also
    be other resource-type-specific criteria; this function tests general
    criteria common to all resource types.

    Args:
        session: An SQLAlchemy session
        snap: The snapshot+resource to create
        resource_type: the resource_type value for the type of resource being
            created.  Used to verify type settings on the snapshot and resource
            objects.

    Raises:
        EntityExistsError: if the resource or snapshot already exists
        EntityDoesNotExistError: if the group owner or user creator do not
            exist, or if any child resource does not exist
        EntityDeletedError: if the resource, its creator, or its group owner
            is deleted, or if all child resources exist but some are deleted
        UserNotInGroupError: if the snapshot creator is not a member of the
            group who will own the resource
        MismatchedResourceTypeError: if the snapshot or resource's type doesn't
            match resource_type
    """
    assert_resource_does_not_exist(session, snap, DeletionPolicy.ANY)
    assert_snapshot_does_not_exist(session, snap)
    assert_user_exists(session, snap.creator, DeletionPolicy.NOT_DELETED)
    assert_group_exists(session, snap.resource.owner, DeletionPolicy.NOT_DELETED)
    assert_user_in_group(session, snap.creator, snap.resource.owner)
    assert_resource_children_exist(session, snap, DeletionPolicy.NOT_DELETED)
    assert_resource_type(session, snap, resource_type)

    # TODO: should check if the children are already parented to a different
    # different resource?  What's the cardinality of parent/child
    # relationships?


def assert_can_create_snapshot(
    session: CompatibleSession[S], snap: m.ResourceSnapshot, resource_type: str
):
    """
    Check whether the given snapshot may be created, of an existing resource.
    There may also be other resource-type-specific criteria; this function
    tests general criteria common to all resource types.

    Args:
        session: An SQLAlchemy session
        snap: A ResourceSnapshot object with the desired snapshot settings
        resource_type: the resource_type value for the type of resource being
            created.  Used to verify type settings on the snapshot and resource
            objects.

    Raises:
        EntityExistsError: if the snapshot already exists
        EntityDoesNotExistError: if the resource or snapshot creator
            user does not exist, or if any child resource does not exist
        EntityDeletedError: if the resource is deleted, snapshot creator user
            is deleted, or if all child resources exist but some are deleted
        ReadOnlyLockError: if the resource exists and has a read-only lock
        UserNotInGroupError: if the snapshot creator user is not a member
            of the group who owns the resource
        MismatchedResourceTypeError: if the snapshot or resource's type doesn't
            match resource_type
    """
    assert_resource_exists(session, snap, DeletionPolicy.NOT_DELETED)
    assert_snapshot_does_not_exist(session, snap)
    assert_resource_modifiable(session, snap)
    assert_user_exists(session, snap.creator, DeletionPolicy.NOT_DELETED)
    assert_user_in_group(session, snap.creator, snap.resource.owner)
    assert_resource_children_exist(session, snap, DeletionPolicy.NOT_DELETED)
    assert_resource_type(session, snap, resource_type)

    # TODO: should check if the children are already parented to a different
    # different resource?  What's the cardinality of parent/child
    # relationships?


def assert_exists(
    deletion_policy: DeletionPolicy,
    existence_result: ExistenceResult,
    obj_type: str | None,
    obj_id: int | None,
    **kwargs,
) -> None:
    """
    Common code for checking existence relative to deletion policy.

    Args:
        deletion_policy: One of the DeletionPolicy enum values
        existence_result: One of the ExistenceResult enum values
        obj_type: Brief word(s) to describe the kind of object which was
            searched for (e.g. a "user", "queue", etc), or None if not known
        obj_id: A primary key value identifying the object which was searched
            for, or None if it did not have an ID
        kwargs: additional descriptive names and values describing the object
            which was searched for

    Raises:
        EntityDoesNotExistError: if the entity does not exist in the database
            (deleted or not)
        EntityExistsError: if the entity exists and is not deleted, but policy
            was to find a deleted entity
        EntityDeletedError: if the entity is deleted, but policy was to find
            a non-deleted entity
    """
    if existence_result is ExistenceResult.DOES_NOT_EXIST:
        raise e.EntityDoesNotExistError(obj_type, **kwargs)

    elif existence_result is ExistenceResult.EXISTS:
        # An object which exists (in the db) must have a non-null ID.  So at
        # this point, obj_id must not be None.
        assert obj_id is not None
        if deletion_policy is DeletionPolicy.DELETED:
            raise e.EntityExistsError(obj_type, obj_id, **kwargs)

    elif existence_result is ExistenceResult.DELETED:
        # Same as above; deleted objects are in the DB too.
        assert obj_id is not None
        if deletion_policy is DeletionPolicy.NOT_DELETED:
            raise e.EntityDeletedError(obj_type, obj_id, **kwargs)


def _assert_exists_multi(
    deletion_policy: DeletionPolicy,
    existence_result: Mapping[int, ExistenceResult],
    expected_number: int | None = None,
):
    """
    Condense multiple existence results into a single result, and throw an
    exception if necessary.

    Applying deletion policy in this case is more complicated.  To be fully
    general, one would need a quantifier to determine how the policy applies to
    multiple results.  E.g. if policy was NOT_DELETED, does that mean at least
    one is not deleted, or all are not deleted?  For now, this is written as
    if the quantifier is "all".  So if policy is NOT_DELETED, *any* deleted
    result will produce an error.  If policy is DELETED, any exists result will
    produce an error.  If there are any not-exists results, that will produce
    an error regardless of policy.

    Args:
        deletion_policy: One of the DeletionPolicy enum values
        existence_result: A mapping from resource ID to an ExistenceResult
            enum value
        expected_number: the number of resources which were checked for
            existence.  If some resources did not exist, and we had no ID to
            use in the mapping, the mapping may not account for every resource
            which was checked.  So this argument helps this function be aware
            of the situation, and produce a not-exists error.

    Raises:
        EntityDoesNotExistError: if any existence result is DOES_NOT_EXIST,
            or expected_number is a number which is greater than the size of
            the existence_result mapping.
        EntityDeletedError: if policy is NOT_DELETED, all resources exist,
            but some were deleted.
        EntityExistsError: if policy is DELETED, all resources exist, and
            some were not deleted.
    """

    # a single resource type doesn't in general make sense with the following
    # errors, since we are checking multiple resources and they need not all be
    # of the same type.

    if expected_number is not None and len(existence_result) < expected_number:
        # Got some objects with null IDs; treat as not exist.  Can't identify
        # the relevant children with numeric IDs, so just use None.
        raise e.EntityDoesNotExistError(
            None,
            resource_id=None,
        )

    elif any(
        status == ExistenceResult.DOES_NOT_EXIST for status in existence_result.values()
    ):
        dne_ids = tuple(
            id_
            for id_, res in existence_result.items()
            if res is ExistenceResult.DOES_NOT_EXIST
        )

        raise e.EntityDoesNotExistError(None, resource_ids=dne_ids)

    elif deletion_policy is DeletionPolicy.NOT_DELETED and any(
        status == ExistenceResult.DELETED for status in existence_result.values()
    ):
        deleted_ids = (
            id_
            for id_, res in existence_result.items()
            if res is ExistenceResult.DELETED
        )

        # EntityDeletedError only supports reporting one thing as having been
        # deleted... so just pick the first deleted ID.
        first_deleted_id = next(deleted_ids)

        raise e.EntityDeletedError(None, first_deleted_id, resource_id=first_deleted_id)

    elif deletion_policy is DeletionPolicy.DELETED and any(
        status == ExistenceResult.EXISTS for status in existence_result.values()
    ):
        exists_ids = (
            id_
            for id_, res in existence_result.items()
            if res is ExistenceResult.EXISTS
        )

        # EntityExistsError only supports reporting one thing as existing...
        # so just pick the first existing ID.
        first_existing_id = next(exists_ids)

        raise e.EntityExistsError(None, first_existing_id, id=first_existing_id)


def _assert_does_not_exist(
    deletion_policy: DeletionPolicy,
    existence_result: ExistenceResult,
    obj_type: str | None,
    obj_id: int | None,
    **kwargs,
):
    """
    Common code for checking non-existence relative to deletion policy.

    Args:
        deletion_policy: One of the DeletionPolicy enum values
        existence_result: One of the ExistenceResult enum values
        obj_type: Brief word(s) to describe the kind of object which was
            searched for (e.g. a "user", "queue", etc), or None if not known
        obj_id: A primary key value identifying the object which was searched
            for, or None if it did not have an ID
        kwargs: additional descriptive names and values describing the object
            which was searched for

    Raises:
        EntityExistsError: if the entity exists and is not deleted but
            policy is NOT_DELETED or ANY, meaning we want to ensure the entity
            is either deleted or non-existent
        EntityDeletedError: if the entity exists and is deleted but policy is
            DELETED or ANY, meaning we want to ensure the entity is either
            existing and not deleted, or non-existent
    """
    if existence_result is ExistenceResult.EXISTS:
        # An object which exists (in the db) must have a non-null ID.  So at
        # this point, obj_id must not be None.
        assert obj_id is not None
        if deletion_policy is not DeletionPolicy.DELETED:
            raise e.EntityExistsError(obj_type, obj_id, **kwargs)

    elif existence_result is ExistenceResult.DELETED:
        # Same as above; deleted objects are in the DB too.
        assert obj_id is not None
        if deletion_policy is not DeletionPolicy.NOT_DELETED:
            raise e.EntityDeletedError(obj_type, obj_id, **kwargs)

    # else: ExistenceResult.DOES_NOT_EXIST.  deletion policy doesn't matter in
    # this case; the object does not exist at all.


def assert_user_in_group(
    session: CompatibleSession[S], user: m.User, group: m.Group
) -> None:
    """
    Ensure the given user is a member of the given group.  This function
    assumes both already exist in the database.  It also ignores the deletion
    status of both.  Existence/deletion status should be checked by the caller
    first, if necessary.

    Args:
        session: An SQLAlchemy session
        user: An existing user
        group: An existing group

    Raises:
        UserNotInGroupError: if the given user is not in the given group
    """

    # Assume existence checks on user and group were already done, so they are
    # known to exist.
    membership = session.get(m.GroupMember, (user.user_id, group.group_id))

    if not membership:
        raise e.UserNotInGroupError(user.user_id, group.group_id)


def check_user_collision(session: CompatibleSession[S], user: m.User) -> None:
    """
    Factored out check from user and group repositories.  Their create methods
    can both create users, so both need to ensure requirements are met.

    Args:
        session: An SQLAlchemy session
        user: A User object

    Raises:
        EntityExistsError: if the given user's username or email address
            collides with an existing/deleted user
    """

    stmt = sa.select(m.User.user_id).where(m.User.username == user.username)
    user_id = session.scalar(stmt)

    if user_id is not None:
        raise e.EntityExistsError("User", user_id, username=user.username)

    stmt = sa.select(m.User.user_id).where(m.User.email_address == user.email_address)
    user_id = session.scalar(stmt)

    if user_id is not None:
        raise e.EntityExistsError("User", user_id, email_address=user.email_address)


def assert_resource_name_available(
    session: CompatibleSession[S],
    snap: m.ResourceSnapshot,
) -> None:
    """
    Check for a name collision when creating a new resource.

    Many resource types have names, and a common requirement is that when a
    resource is being created, its name is not the same as that of another
    resource in the same group.  This function factors out that common check.

    Snap must have an attribute named "name" which contains its name, and its
    type must have a class attribute named "name" which represents the name
    column of its table.

    Args:
        session: An SQLAlchemy session
        snap: A new snapshot of a new resource, with a name

    Raises:
        EntityExistsError: if the given snap's name is the same as another
            snapshot in the same group
    """
    resource_type_class = type(snap)

    stmt = (
        sa.select(resource_type_class.resource_id)
        .join(m.Resource)
        .where(
            resource_type_class.name == snap.name,
            resource_type_class.resource_snapshot_id == m.Resource.latest_snapshot_id,
            # Dunno why mypy has trouble with this expression...
            m.Resource.owner == snap.resource.owner,  # type: ignore
        )
    )

    existing_id = session.scalar(stmt)
    if existing_id:
        raise e.EntityExistsError(
            None,
            existing_id,
            name=snap.name,
            group_id=snap.resource.owner.group_id,
        )


def assert_snapshot_name_available(
    session: CompatibleSession[S],
    snap: m.ResourceSnapshot,
) -> None:
    """
    Check for a name collision when creating a new snapshot.

    Many resource types have names, and a common requirement is that when a
    name is being changed, the new name is not the same as that of a
    different resource in the same group.  This function factors out that
    common check.

    Snap must have an attribute named "name" which contains its name, and its
    type must have a class attribute named "name" which represents the name
    column of its table.

    Args:
        session: An SQLAlchemy session
        snap: A new snapshot of an existing resource, with a name

    Raises:
        EntityExistsError: if the given snap's name is the same as another
            snapshot in the same group

    """

    resource_type_class = type(snap)

    stmt = (
        sa.select(resource_type_class.resource_id)
        .join(m.Resource)
        .where(
            resource_type_class.name == snap.name,
            resource_type_class.resource_snapshot_id == m.Resource.latest_snapshot_id,
            # Dunno why mypy has trouble with this expression...
            m.Resource.owner == snap.resource.owner,  # type: ignore
            resource_type_class.resource_id != snap.resource_id,
        )
    )

    existing_id = session.scalar(stmt)
    if existing_id:
        raise e.EntityExistsError(
            None,
            existing_id,
            name=snap.name,
            group_id=snap.resource.group_id,
        )


__all__ = [
    "assert_can_create_resource",
    "assert_can_create_snapshot",
    "assert_draft_does_not_exist",
    "assert_draft_exists",
    "assert_exists",
    "assert_group_does_not_exist",
    "assert_group_exists",
    "assert_resource_children_exist",
    "assert_resource_does_not_exist",
    "assert_resource_exists",
    "assert_resource_modifiable",
    "assert_resource_name_available",
    "assert_resource_type",
    "assert_resources_exist",
    "assert_snapshot_does_not_exist",
    "assert_snapshot_exists",
    "assert_snapshot_name_available",
    "assert_user_does_not_exist",
    "assert_user_exists",
    "assert_user_in_group",
    "check_user_collision",
    "draft_exists",
    "group_exists",
    "resource_children_exist",
    "resource_exists",
    "resource_modifiable",
    "resources_exist",
    "snapshot_exists",
    "user_exists",
]
