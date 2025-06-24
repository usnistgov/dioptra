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
import enum
import itertools
import typing
from collections.abc import Callable, Iterable, Mapping, Sequence, Set

import sqlalchemy as sa
import sqlalchemy.sql.expression as sae
from sqlalchemy.orm import Session, aliased, scoped_session

from dioptra.restapi.db.models import (
    DraftResource,
    Group,
    GroupLock,
    GroupMember,
    Resource,
    ResourceLock,
    ResourceSnapshot,
    User,
    UserLock,
    resource_dependencies_table,
)
from dioptra.restapi.db.models.constants import (
    group_lock_types,
    resource_lock_types,
    user_lock_types,
)
from dioptra.restapi.errors import (
    DraftAlreadyExistsError,
    DraftDoesNotExistError,
    EntityDeletedError,
    EntityDoesNotExistError,
    EntityExistsError,
    MismatchedResourceTypeError,
    ReadOnlyLockError,
    SearchParseError,
    SortParameterValidationError,
    UserNotInGroupError,
)

# General ORM-using code ought to be compatible with "plain" SQLAlchemy or
# flask_sqlalchemy's ORM sessions (the latter are of generic type
# scoped_session[S], where S is a session type).  Any old Session, right?
S = typing.TypeVar("S", bound=Session)
CompatibleSession = Session | scoped_session[S]

# Type alias for search field callbacks
SearchFieldCallback = Callable[[str], sae.ColumnElement[bool]]

# May be bound to a resource-type-specific ResourceSnapshot subclass,
# i.e. represents our python class representation of a resource type.
ResourceT = typing.TypeVar("ResourceT", bound=ResourceSnapshot)


class ExistenceResult(enum.Enum):
    """
    Existence check results, which can communicate deletion status
    """

    # Item does not exist (not even deleted)
    DOES_NOT_EXIST = enum.auto()
    # Item exists, is not deleted
    EXISTS = enum.auto()
    # Item exists, but is deleted
    DELETED = enum.auto()


class DeletionPolicy(enum.Enum):
    """
    Policy values concerning deletion status
    """

    # Disregard deletion state/don't care
    ANY = enum.auto()
    # Non-deleted items only
    NOT_DELETED = enum.auto()
    # Deleted items only
    DELETED = enum.auto()


class ResourceLockType(enum.Enum):
    """
    Types of resource lock
    """

    DELETED = resource_lock_types.DELETE
    READONLY = resource_lock_types.READONLY


def get_user_id(user: User | int) -> int | None:
    """
    Helper for APIs which allow a User domain object or user_id integer
    primary key value.  This normalizes the value to the user_id value, or
    None (if a User object was passed with a null .user_id attribute).

    Args:
        user: A User object or user_id integer primary key value

    Returns:
        A user ID or None
    """
    if isinstance(user, int):
        user_id = user
    else:
        user_id = user.user_id

    return user_id


def get_group_id(group: Group | int) -> int | None:
    """
    Helper for APIs which allow a Group domain object or group_id integer
    primary key value.  This normalizes the value to the group_id value, or
    None (if a Group object was passed with a null .group_id attribute).

    Args:
        group: A Group object or group_id integer primary key value

    Returns:
        A group ID or None
    """
    if isinstance(group, int):
        group_id = group
    else:
        group_id = group.group_id

    return group_id


def get_resource_id(resource: Resource | ResourceSnapshot | int) -> int | None:
    """
    Helper for APIs which allow a Resource/ResourceSnapshot object or
    resource_id integer primary key value.  This normalizes the value to the
    resource_id value, or None (if an object was passed with a null
    .resource_id attribute).

    Args:
        resource: A resource, snapshot, or resource_id integer primary key
            value

    Returns:
        A resource ID or None
    """
    if isinstance(resource, int):
        resource_id = resource

    else:
        # This hack should not in theory be necessary.  But when creating a
        # snapshot, SQLAlchemy doesn't seem to set foreign key attributes when
        # setting the "resource" relationship attribute.  That means that when
        # creating a snapshot via an existing resource, the snapshot's
        # .resource_id attribute may still be null, whereas
        # .resource.resource_id is non-null.  For us, it means we can't trust a
        # null .resource_id attribute on a snapshot.  It may mean there is no
        # corresponding resource, or it may mean SQLAlchemy just didn't set the
        # attribute.  So if 'resource' is a snapshot with a null .resource_id,
        # make a second attempt to get a resource ID via .resource.resource_id.
        resource_id = resource.resource_id
        if (
            resource_id is None
            and isinstance(resource, ResourceSnapshot)
            and resource.resource
        ):
            resource_id = resource.resource.resource_id

    return resource_id


def get_draft_id(draft: DraftResource | int) -> int | None:
    """
    Helper for APIs which allow a DraftResource object or draft_resource_id
    integer primary key value.  This normalizes the value to the
    draft_resource_id value, or None (if a DraftResource object was passed
    with a null .draft_resource_id attribute).

    Args:
        draft: A DraftResource object or draft_resource_id integer primary key
            value

    Returns:
        A draft ID or None
    """
    if isinstance(draft, int):
        draft_id = draft
    else:
        draft_id = draft.draft_resource_id

    return draft_id


def get_resource_snapshot_id(snapshot: ResourceSnapshot | int) -> int | None:
    """
    Helper for APIs which allow a ResourceSnapshot object or
    resource_snapshot_id integer primary key value.  This normalizes the value
    to the resource_snapshot_id value, or None (if a ResourceSnapshot object
    was passed with a null .resource_snapshot_id attribute).

    Args:
        snapshot: A ResourceSnapshot object or resource_snapshot_id integer
            primary key value

    Returns:
        A resource snapshot ID or None
    """
    if isinstance(snapshot, int):
        snapshot_id = snapshot
    else:
        snapshot_id = snapshot.resource_snapshot_id

    return snapshot_id


def user_exists(session: CompatibleSession[S], user: User | int) -> ExistenceResult:
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
            sa.select(User.user_id, UserLock.user_lock_type)
            .outerjoin(UserLock)
            .where(User.user_id == user_id)
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


def group_exists(session: CompatibleSession[S], group: Group | int) -> ExistenceResult:
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
            sa.select(Group.group_id, GroupLock.group_lock_type)
            .outerjoin(GroupLock)
            .where(Group.group_id == group_id)
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
    session: CompatibleSession[S], resource: Resource | ResourceSnapshot | int
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
            sa.select(ResourceLock.resource_lock_type)
            .select_from(Resource)
            .outerjoin(ResourceLock)
            .where(Resource.resource_id == resource_id)
            # Note: using "IN ('delete', NULL)" as a shortcut operator doesn't
            # work here, since IN operates via '=', and '=' doesn't behave as
            # expected with nulls.
            .where(
                sa.or_(
                    ResourceLock.resource_lock_type == resource_lock_types.DELETE,
                    ResourceLock.resource_lock_type == None,  # noqa: E711
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
    resources: Iterable[Resource | ResourceSnapshot | int],
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
            sa.select(Resource.resource_id, ResourceLock.resource_lock_type)
            .outerjoin(ResourceLock)
            .where(
                Resource.resource_id.in_(resource_ids),
                sa.or_(
                    ResourceLock.resource_lock_type == resource_lock_types.DELETE,
                    ResourceLock.resource_lock_type == None,  # noqa: E711
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
    session: CompatibleSession[S], resource: Resource | ResourceSnapshot | int
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

    children: Iterable[Resource | ResourceSnapshot | int]

    if isinstance(resource, (Resource, ResourceSnapshot)):
        children = resource.children
    else:
        children_stmt = sa.select(
            resource_dependencies_table.c.child_resource_id
        ).where(
            resource_dependencies_table.c.parent_resource_id == resource,
        )
        children = session.scalars(children_stmt).all()

    child_status = resources_exist(session, children)

    return child_status


def resource_modifiable(
    session: CompatibleSession[S], resource: Resource | ResourceSnapshot | int
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
            ResourceLock.resource_id == resource_id,
            ResourceLock.resource_lock_type == resource_lock_types.READONLY,
        )
        exists_stmt = sa.select(stmt.exists())

        modifiable = not session.scalar(exists_stmt)

    return modifiable


def snapshot_exists(
    session: CompatibleSession[S], snapshot: ResourceSnapshot | int
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
            .select_from(ResourceSnapshot)
            .where(ResourceSnapshot.resource_snapshot_id == snapshot_id)
        )
        exists_stmt = sa.select(sub_stmt.exists())

        exists = session.scalar(exists_stmt)

        # For mypy.  I think a "select exists(....)" should always return true
        # or false.
        assert exists is not None

    return exists


def draft_exists(session: CompatibleSession[S], draft: DraftResource | int) -> bool:
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
            .select_from(DraftResource)
            .where(DraftResource.draft_resource_id == draft_id)
        )
        exists_stmt = sa.select(sub_stmt.exists())

        exists = session.scalar(exists_stmt)

        # a "SELECT EXISTS(...)" should always return a row (true/false).
        assert exists is not None

    return exists


def assert_user_exists(
    session: CompatibleSession[S], user: User | int, deletion_policy: DeletionPolicy
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
    session: CompatibleSession[S], group: Group | int, deletion_policy: DeletionPolicy
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
    resource: Resource | ResourceSnapshot | int,
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
    resources: Iterable[Resource | ResourceSnapshot | int],
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
    resource: Resource | ResourceSnapshot | int,
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

    if isinstance(resource, (Resource, ResourceSnapshot)):
        num_children = len(resource.children)
    else:
        num_children = None

    _assert_exists_multi(deletion_policy, child_status, num_children)


def assert_resource_modifiable(
    session: CompatibleSession[S],
    resource: Resource | ResourceSnapshot | int,
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

    if isinstance(resource, (Resource, ResourceSnapshot)):
        resource_type = resource.resource_type
    else:
        resource_type = None

    if not modifiable:
        raise ReadOnlyLockError(resource_type, resource_id=get_resource_id(resource))


def assert_resource_type(
    session: CompatibleSession[S],
    resource: Resource | ResourceSnapshot | int,
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
        resource_obj = session.get(Resource, resource)
        if not resource_obj:
            raise EntityDoesNotExistError(None, resource_id=resource)
        resource = resource_obj

    if isinstance(resource, (Resource, ResourceSnapshot)):
        if resource.resource_type != resource_type:
            raise MismatchedResourceTypeError(resource_type, resource.resource_type)

    if isinstance(resource, ResourceSnapshot):
        if resource.resource.resource_type != resource_type:
            raise MismatchedResourceTypeError(
                resource_type, resource.resource.resource_type
            )


def assert_snapshot_exists(
    session: CompatibleSession[S],
    snapshot: ResourceSnapshot | int,
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

        raise EntityDoesNotExistError(resource_type, resource_snapshot_id=snapshot_id)


def assert_draft_exists(
    session: CompatibleSession[S], draft: DraftResource | int
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
        raise DraftDoesNotExistError(draft_resource_id=draft_id)


def assert_user_does_not_exist(
    session: CompatibleSession[S], user: User | int, deletion_policy: DeletionPolicy
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
    session: CompatibleSession[S], group: Group | int, deletion_policy: DeletionPolicy
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
    resource: Resource | ResourceSnapshot | int,
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
    session: CompatibleSession[S], snapshot: ResourceSnapshot | int
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

        raise EntityExistsError(
            resource_type,
            snapshot_id,
            resource_snapshot_id=snapshot_id,
        )


def assert_draft_does_not_exist(
    session: CompatibleSession[S], draft: DraftResource | int
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

        raise DraftAlreadyExistsError(resource_type, draft_id)


def assert_can_create_resource(
    session: CompatibleSession[S], snap: ResourceSnapshot, resource_type: str
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
    session: CompatibleSession[S], snap: ResourceSnapshot, resource_type: str
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
        raise EntityDoesNotExistError(obj_type, **kwargs)

    elif existence_result is ExistenceResult.EXISTS:
        # An object which exists (in the db) must have a non-null ID.  So at
        # this point, obj_id must not be None.
        assert obj_id is not None
        if deletion_policy is DeletionPolicy.DELETED:
            raise EntityExistsError(obj_type, obj_id, **kwargs)

    elif existence_result is ExistenceResult.DELETED:
        # Same as above; deleted objects are in the DB too.
        assert obj_id is not None
        if deletion_policy is DeletionPolicy.NOT_DELETED:
            raise EntityDeletedError(obj_type, obj_id, **kwargs)


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
        raise EntityDoesNotExistError(
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

        raise EntityDoesNotExistError(None, resource_ids=dne_ids)

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

        raise EntityDeletedError(None, first_deleted_id, resource_id=first_deleted_id)

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

        raise EntityExistsError(None, first_existing_id, id=first_existing_id)


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
            raise EntityExistsError(obj_type, obj_id, **kwargs)

    elif existence_result is ExistenceResult.DELETED:
        # Same as above; deleted objects are in the DB too.
        assert obj_id is not None
        if deletion_policy is not DeletionPolicy.NOT_DELETED:
            raise EntityDeletedError(obj_type, obj_id, **kwargs)

    # else: ExistenceResult.DOES_NOT_EXIST.  deletion policy doesn't matter in
    # this case; the object does not exist at all.


def assert_user_in_group(
    session: CompatibleSession[S], user: User, group: Group
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
    membership = session.get(GroupMember, (user.user_id, group.group_id))

    if not membership:
        raise UserNotInGroupError(user.user_id, group.group_id)


def check_user_collision(session: CompatibleSession[S], user: User) -> None:
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

    stmt = sa.select(User.user_id).where(User.username == user.username)
    user_id = session.scalar(stmt)

    if user_id is not None:
        raise EntityExistsError("User", user_id, username=user.username)

    stmt = sa.select(User.user_id).where(User.email_address == user.email_address)
    user_id = session.scalar(stmt)

    if user_id is not None:
        raise EntityExistsError("User", user_id, email_address=user.email_address)


def assert_resource_name_available(
    session: CompatibleSession[S],
    snap: ResourceSnapshot,
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
        .join(Resource)
        .where(
            resource_type_class.name == snap.name,
            resource_type_class.resource_snapshot_id == Resource.latest_snapshot_id,
            # Dunno why mypy has trouble with this expression...
            Resource.owner == snap.resource.owner,  # type: ignore
        )
    )

    existing_id = session.scalar(stmt)
    if existing_id:
        raise EntityExistsError(
            None,
            existing_id,
            name=snap.name,
            group_id=snap.resource.owner.group_id,
        )


def assert_snapshot_name_available(
    session: CompatibleSession[S],
    snap: ResourceSnapshot,
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
        .join(Resource)
        .where(
            resource_type_class.name == snap.name,
            resource_type_class.resource_snapshot_id == Resource.latest_snapshot_id,
            # Dunno why mypy has trouble with this expression...
            Resource.owner == snap.resource.owner,  # type: ignore
            resource_type_class.resource_id != snap.resource_id,
        )
    )

    existing_id = session.scalar(stmt)
    if existing_id:
        raise EntityExistsError(
            None,
            existing_id,
            name=snap.name,
            group_id=snap.resource.group_id,
        )


def apply_resource_deletion_policy(
    stmt: sa.Select, deletion_policy: DeletionPolicy
) -> sa.Select:
    """
    Factored out code to add components to a SELECT statement to apply deletion
    policy to it, affecting whether deleted resources are searched.  This
    function is intended to apply to snapshot queries; it adds a join to
    Resource, which will use the foreign key relationship between Resource and
    ResourceSnapshot which already exists.  But it could in theory work with
    any other select statement having a table which has a defined foreign key
    relationship with Resource.

    Args:
        stmt: A snapshot select statement to modify
        deletion_policy: The policy to apply

    Returns:
        A modified select statement
    """

    # Use an alias, just in case the given select statement already includes a
    # join with Resource.
    resource_alias = aliased(Resource)

    if deletion_policy is DeletionPolicy.NOT_DELETED:
        stmt = stmt.join(resource_alias).where(
            resource_alias.is_deleted == False  # noqa: E712
        )
    elif deletion_policy is DeletionPolicy.DELETED:
        stmt = stmt.join(resource_alias).where(
            resource_alias.is_deleted == True  # noqa: E712
        )

    return stmt


@typing.overload
def get_latest_snapshots(  # noqa: E704
    session: CompatibleSession[S],
    snap_class: typing.Type[ResourceT],
    resources: int | Resource | ResourceSnapshot,
    deletion_policy: DeletionPolicy,
) -> ResourceT | None: ...


@typing.overload
def get_latest_snapshots(  # noqa: E704
    session: CompatibleSession[S],
    snap_class: typing.Type[ResourceT],
    resources: Iterable[int | Resource | ResourceSnapshot],
    deletion_policy: DeletionPolicy,
) -> Sequence[ResourceT]: ...


def get_latest_snapshots(
    session: CompatibleSession[S],
    snap_class: typing.Type[ResourceT],
    resources: (
        int | Resource | ResourceSnapshot | Iterable[int | Resource | ResourceSnapshot]
    ),
    deletion_policy: DeletionPolicy,
) -> ResourceT | Sequence[ResourceT] | None:
    """
    Get the latest snapshot(s) of the given resource(s).  If "resources"
    is passed as snapshots already, they are not assumed to be the latest.
    The database is still queried and a list of possibly different snapshots
    is returned.

    Args:
        session: An SQLAlchemy session
        snap_class: A ResourceSnapshot subclass, which represents the type
            of resource to get
        resources: A single or iterable of resources, resource snapshots,
            or integer resource IDs, for which to obtain the latest snapshots
        deletion_policy: Whether to look at deleted resources, non-deleted
            resources, or all resources

    Returns:
        A snapshot/list of snapshots, or None/empty list if none were found
        with the given ID(s)
    """
    if isinstance(resources, (int, Resource, ResourceSnapshot)):
        resource_id_check = snap_class.resource_id == get_resource_id(resources)
    else:
        resource_id_check = snap_class.resource_id.in_(
            get_resource_id(res) for res in resources
        )

    # Extra join with Resource is important: the query produces incorrect
    # results without it!
    stmt = (
        sa.select(snap_class)
        .join(Resource)
        .where(
            resource_id_check,
            snap_class.resource_snapshot_id == Resource.latest_snapshot_id,
        )
    )
    stmt = apply_resource_deletion_policy(stmt, deletion_policy)

    snaps: ResourceT | Sequence[ResourceT] | None
    if isinstance(resources, (int, Resource, ResourceSnapshot)):
        snaps = session.scalar(stmt)
    else:
        snaps = session.scalars(stmt).all()

    return snaps


def get_one_latest_snapshot(
    session: CompatibleSession[S],
    snap_class: typing.Type[ResourceT],
    resource: int | Resource | ResourceSnapshot,
    deletion_policy: DeletionPolicy,
) -> ResourceT:
    """
    Get the latest snapshot of the given resource; require that exactly one is
    found, or raise an exception.

    Args:
        session: An SQLAlchemy session
        snap_class: A ResourceSnapshot subclass, which represents the type
            of resource to get
        resource: A resource, resource snapshot, or integer resource ID,
            for which to obtain the latest snapshot
        deletion_policy: Whether to look at deleted resources, non-deleted
            resources, or all resources

    Returns:
        A snapshot

    Raises:
        EntityDoesNotExistError: if the resource does not exist in the database
            (deleted or not)
        EntityExistsError: if the resource exists and is not deleted, but
            policy was to find a deleted resource
        EntityDeletedError: if the resource is deleted, but policy was to find
            a non-deleted resource
    """

    # ignore deletion_policy here and get whatever is in the DB.  We need it
    # to determine its status, to figure out which exception we need to throw
    # (if any).
    latest = get_latest_snapshots(session, snap_class, resource, DeletionPolicy.ANY)

    if latest is None:
        existence_result = ExistenceResult.DOES_NOT_EXIST
    elif latest.resource.is_deleted:
        existence_result = ExistenceResult.DELETED
    else:
        existence_result = ExistenceResult.EXISTS

    resource_id: int | None
    if latest:
        resource_type = latest.resource_type
        resource_id = latest.resource_id
    elif isinstance(resource, (Resource, ResourceSnapshot)):
        resource_type = resource.resource_type
        resource_id = get_resource_id(resource)
    else:  # resource is an int
        resource_type = None
        resource_id = resource

    # Here, we combine the passed-in deletion policy with existence, to
    # determine the exception.
    assert_exists(deletion_policy, existence_result, resource_type, resource_id)

    # The above assert_exists() function would have raised an exception, so
    # latest can't be None here.
    assert latest is not None
    return latest


def get_latest_child_snapshots(
    session: CompatibleSession[S],
    child_class: typing.Type[ResourceT],
    parent: Resource | ResourceSnapshot | int,
    deletion_policy: DeletionPolicy,
) -> Sequence[ResourceT]:
    """
    Get the children of the given resource as their latest snapshots.  If
    parent is a Resource or ResourceSnapshot object, the returned sequence
    may be shorter than len(parent.children) if any of the children don't
    exist, or were filtered out due to deletion policy.

    Args:
        session: An SQLAlchemy session
        child_class: A ResourceSnapshot subclass, which represents which type
            of resource to get (the child type)
        parent: A resource, snapshot, or resource_id integer primary key
            value
        deletion_policy: Whether to look at deleted child resources,
            non-deleted resources, or all resources

    Returns:
        The child snapshots

    Raises:
        EntityDoesNotExistError: if parent does not exist
        EntityDeletedError: if parent is deleted
    """

    assert_resource_exists(session, parent, DeletionPolicy.NOT_DELETED)

    child_resources: Sequence[Resource | int]
    if isinstance(parent, (Resource, ResourceSnapshot)):
        child_resources = parent.children
    else:
        stmt = sa.select(resource_dependencies_table.c.child_resource_id).where(
            resource_dependencies_table.c.parent_resource_id == parent
        )
        child_resources = session.scalars(stmt).all()

    child_snaps = get_latest_snapshots(
        session,
        child_class,
        child_resources,
        deletion_policy,
    )

    return child_snaps


# The type ignore below is necessary because it seems to be impossible to
# express the correct types in the overloads below.  Mypy treats "str" as
# compatible with "Iterable[str]".  Technically that's not wrong, since you can
# iterate through a string and get strings (all length-1, the individual
# characters).  But the implementation special cases str as:
#
#     if isinstance(name, str):
#         ...  # first overload
#     else:
#         ...  # second overload
#
# So what I really need to be able to express are two cases: (1) str and
# (2) Iterable[str] *but not str itself!*  I think there is no way to write a
# type annotation with a negative clause which excludes a special case.  So
# mypy gives the error that the overloads "overlap with incompatible return
# types".  It also says: "Flipping the order of overloads will fix this error",
# and it did make the error go away, but also causes mypy to misunderstand
# function calls (match them to the wrong overload).  So it's really just
# trading one mypy error for another.
#
# It seems the only thing you can do for now is use the overload order below,
# and turn the overload-overlap error off.
#
# See also:
# https://github.com/python/typing/issues/256
# https://github.com/python/mypy/issues/11001
@typing.overload
def get_snapshot_by_name(  # type: ignore[overload-overlap]  # noqa: E704
    session: CompatibleSession[S],
    snap_class: typing.Type[ResourceT],
    name: str,
    group: Group | int,
    deletion_policy: DeletionPolicy,
) -> ResourceT | None: ...


@typing.overload
def get_snapshot_by_name(  # noqa: E704
    session: CompatibleSession[S],
    snap_class: typing.Type[ResourceT],
    name: Iterable[str],
    group: Group | int,
    deletion_policy: DeletionPolicy,
) -> Sequence[ResourceT]: ...


def get_snapshot_by_name(
    session: CompatibleSession[S],
    snap_class: typing.Type[ResourceT],
    name: str | Iterable[str],
    group: Group | int,
    deletion_policy: DeletionPolicy,
) -> ResourceT | Sequence[ResourceT] | None:
    """
    Get the latest snapshot(s) of resource(s), by name(s).

    snap_class must have an attribute named "name" which maps to the name
    column of its table.

    Args:
        session: An SQLAlchemy session
        snap_class: A ResourceSnapshot subclass, which represents which type
            of resource to get, with a "name" attribute
        name: The name(s) to search for as a single string or iterable of
            strings
        group: A group/group ID, to disambiguate same-named resources across
            groups
        deletion_policy: Whether to look at deleted resources, non-deleted
            resources, or all resources

    Returns:
        If a single name is passed, a resource snapshot is returned, or None
        if one was not found with the given name.  If an iterable of names is
        passed, a sequence of snapshots is returned, which will be empty if
        none were found.

    Raises:
        EntityDoesNotExistError: if the given group does not exist
        EntityDeletedError: if the given group is deleted
    """
    assert_group_exists(session, group, DeletionPolicy.NOT_DELETED)
    group_id = get_group_id(group)

    if isinstance(name, str):
        name_check = snap_class.name == name
    else:
        name_check = snap_class.name.in_(name)

    stmt = (
        sa.select(snap_class)
        .join(Resource)
        .where(
            snap_class.resource_snapshot_id == Resource.latest_snapshot_id,
            Resource.group_id == group_id,
            name_check,
        )
    )

    stmt = apply_resource_deletion_policy(stmt, deletion_policy)

    resource: ResourceT | Sequence[ResourceT] | None
    if isinstance(name, str):
        resource = session.scalar(stmt)
    else:
        resource = session.scalars(stmt).all()

    return resource


def set_resource_children(
    session: CompatibleSession[S],
    child_class: typing.Type[ResourceT],
    parent: Resource | ResourceSnapshot | int,
    new_children: Iterable[Resource | ResourceT | int],
) -> Sequence[ResourceT]:
    """
    Set the children of the given resource to the given children.  This
    replaces all existing children with the given resources.

    Args:
        session: An SQLAlchemy session
        child_class: A ResourceSnapshot subclass, which represents which type
            of resource is being set (the child type)
        parent: A resource, snapshot, or resource_id integer primary key
            value
        new_children: The children to set

    Returns:
        The new children, as their latest snapshots

    Raises:
        EntityDoesNotExistError: if parent or any child does not exist
        EntityDeletedError: if parent or any child is deleted
    """

    assert_resource_exists(session, parent, DeletionPolicy.NOT_DELETED)
    assert_resources_exist(session, new_children, DeletionPolicy.NOT_DELETED)

    if isinstance(parent, int):
        temp = session.get(Resource, parent)
        # I just checked parent exists above, so the above .get() should not
        # return None.
        assert temp is not None
        parent = temp

    child_snaps = get_latest_snapshots(
        session,
        child_class,
        new_children,
        DeletionPolicy.ANY,
    )

    # Direct assignment like:
    #     parent.children = [child.resource for child in child_snaps]
    # produces a mypy typing error.
    parent.children.clear()
    parent.children.extend(child.resource for child in child_snaps)

    return child_snaps


def append_resource_children(
    session: CompatibleSession[S],
    child_class: typing.Type[ResourceT],
    parent: Resource | ResourceSnapshot | int,
    new_children: Iterable[Resource | ResourceT | int],
) -> list[ResourceT]:
    """
    Add the given children to the given parent.

    Args:
        session: An SQLAlchemy session
        child_class: A ResourceSnapshot subclass, which represents which type
            of resource is being added (the child type)
        parent: A resource, snapshot, or resource_id integer primary key
            value
        new_children: The children to add

    Returns:
        The complete list of resulting children, as latest snapshots (including
        both pre-existing and new children).

    Raises:
        EntityDoesNotExistError: if parent or any new child does not exist
        EntityDeletedError: if parent or any new child is deleted
    """

    assert_resource_exists(session, parent, DeletionPolicy.NOT_DELETED)
    assert_resources_exist(session, new_children, DeletionPolicy.NOT_DELETED)

    if isinstance(parent, int):
        temp = session.get(Resource, parent)
        # I just checked parent exists above, so the above .get() should not
        # return None.
        assert temp is not None
        parent = temp

    existing_child_snaps = get_latest_child_snapshots(
        session, child_class, parent, DeletionPolicy.ANY
    )

    new_child_ids = {get_resource_id(new_child) for new_child in new_children}

    # Don't trust the new children are disjoint from the old...
    new_child_ids.difference_update(
        get_resource_id(child) for child in existing_child_snaps
    )

    # I checked above all children existed, so the set should not have any
    # Nones in it.  I don't think there's an assert you can use for this...
    # so have to cast.
    # ... and I can't just assign back to new_child_ids... so gotta create a
    # second variable!
    new_child_ids2 = typing.cast(set[int], new_child_ids)

    new_child_snaps = get_latest_snapshots(
        session,
        child_class,
        new_child_ids2,
        # we already checked above that all children existed anyway...
        DeletionPolicy.ANY,
    )

    parent.children.extend(
        new_child_snap.resource for new_child_snap in new_child_snaps
    )

    # Sequences don't support "+" for concatenation
    return list(itertools.chain(existing_child_snaps, new_child_snaps))


def unlink_child(
    session: CompatibleSession[S],
    parent: Resource | ResourceSnapshot | int,
    child: Resource | ResourceSnapshot | int,
):
    """
    "Unlink" the given child from the given parent.  This only severs the
    relationship; it does not delete either resource.  If there is no
    parent/child relationship, this is a no-op.

    Args:
        session: An SQLAlchemy session
        parent: A resource, snapshot, or resource_id integer primary key
            value
        child: A resource, snapshot, or resource_id integer primary key
            value

    Raises:
        EntityDoesNotExistError: if parent or child do not exist
    """
    assert_resource_exists(session, parent, DeletionPolicy.ANY)
    assert_resource_exists(session, child, DeletionPolicy.ANY)

    # We need a parent object...
    if isinstance(parent, int):
        temp = session.get(Resource, parent)
        # I just checked parent exists above, so the above .get() should not
        # return None.
        assert temp is not None
        parent = temp

    # ... but a child ID
    child_id = get_resource_id(child)

    for idx, child in enumerate(parent.children):
        if child.resource_id == child_id:
            del parent.children[idx]
            break


def delete_resource(
    session: CompatibleSession[S], resource: Resource | ResourceSnapshot | int
) -> None:
    """
    Common routine for deleting a resource.  No-op if the resource is already
    deleted.  This function differs from add_resource_lock_types() in that this
    function requires that the given resource exists.

    Args:
        session: An SQLAlchemy session
        resource: A resource, snapshot, or resource_id integer primary key
            value

    Raises:
        EntityDoesNotExistError: if the resource does not exist
        ReadOnlyLockError: if the resource exists, is not deleted, and has a
            read-only lock

    See Also:
        - :py:func:`add_resource_lock_types`
    """

    exists_result = resource_exists(session, resource)

    if exists_result is ExistenceResult.DOES_NOT_EXIST:
        resource_id = get_resource_id(resource)
        resource_type = None if isinstance(resource, int) else resource.resource_type
        raise EntityDoesNotExistError(resource_type, resource_id=resource_id)

    elif exists_result is ExistenceResult.EXISTS:
        add_resource_lock_types(session, resource, {ResourceLockType.DELETED})

    # else: exists_result is DELETED; nothing to do.


def get_resource_lock_types(
    session: CompatibleSession[S],
    resource: Resource | ResourceSnapshot | int,
) -> set[ResourceLockType]:
    """
    Get the types of locks set on the given resource.  This does not return
    the actual lock objects, just their types as ResourceLockType enum values.
    For use cases targeting the read-only lock specifically, see also
    resource_modifiable()/assert_resource_modifiable().  Those functions only
    check for the existence of the lock but don't return it, so they can be
    more efficient.

    Args:
        session: An SQLAlchemy session
        resource: A resource, snapshot, or resource_id integer primary key
            value

    Returns:
        A set of ResourceLockType values.  The set will be empty if the
        resource doesn't exist.

    See Also:
        - :py:func:`resource_modifiable`
        - :py:func:`assert_resource_modifiable`
    """
    lock_types = set()

    resource_id = get_resource_id(resource)
    if resource_id is not None:
        stmt = sa.select(ResourceLock).where(ResourceLock.resource_id == resource_id)

        locks = session.scalars(stmt)
        for lock in locks:
            lock_types.add(ResourceLockType(lock.resource_lock_type))

    return lock_types


def add_resource_lock_types(
    session: CompatibleSession[S],
    resource: Resource | ResourceSnapshot | int,
    lock_types: Set[ResourceLockType],
) -> None:
    """
    Add ResourceLock objects of the given types, for the given resource.
    This function does not require the resource to exist, if it is given as a
    Resource or ResourceSnapshot object.  This is so locks can be added to
    resources as part of their creation, within the same transaction.  If
    resource is given as an integer resource ID, and the ID does not resolve to
    a resource, an exception is raised.

    If any of the given lock types already exist on the resource, they are
    skipped and don't produce an error.

    This function doesn't prohibit adding a delete lock to a non-existent
    resource (i.e. bringing a resource into existence in an already-deleted
    state), although that may not be useful.

    Args:
        session: An SQLAlchemy session
        resource: A resource, snapshot, or resource_id integer primary key
            value
        lock_types: The lock types to add

    Raises:
        EntityDeletedError: if a lock would be added to a deleted resource
        EntityDoesNotExistError: if resource was given as an int which didn't
            resolve to a resource
        ReadOnlyLockError: if lock would be added to a non-deleted readonly
            resource

    See Also:
        - :py:func:`delete_resource`
    """

    if isinstance(resource, (Resource, ResourceSnapshot)):
        resource_type = resource.resource_type
    else:
        resource_type = None

    resource_id = get_resource_id(resource)

    existing_lock_types = get_resource_lock_types(session, resource)
    types_to_add = lock_types - existing_lock_types

    if ResourceLockType.DELETED in existing_lock_types:
        # resource_id can't be None if the resource is deleted; it must exist
        # in the db with a delete lock
        assert resource_id is not None
        if types_to_add:
            raise EntityDeletedError(
                resource_type, resource_id, resource_id=resource_id
            )

    if ResourceLockType.READONLY in existing_lock_types:
        if types_to_add:
            raise ReadOnlyLockError(resource_type, resource_id=resource_id)

    else:

        # here, we really need the Resource object; ResourceLock's
        # constructor is just designed that way.
        if isinstance(resource, int):
            resource_obj = session.get(Resource, resource)
            if not resource_obj:
                raise EntityDoesNotExistError(resource_type, resource_id=resource)
        elif isinstance(resource, ResourceSnapshot):
            resource_obj = resource.resource
        else:
            resource_obj = resource

        for lock_type in types_to_add:
            lock = ResourceLock(lock_type.value, resource_obj)
            session.add(lock)


def get_by_filters_paged(
    session: CompatibleSession[S],
    snap_class: typing.Type[ResourceT],
    sortable_fields: dict[str, str],
    searchable_fields: dict[str, typing.Any],
    group: Group | int | None,
    filters: list[dict],
    page_start: int,
    page_length: int,
    sort_by: str | None,
    descending: bool,
    deletion_policy: DeletionPolicy = DeletionPolicy.NOT_DELETED,
) -> tuple[Sequence[ResourceT], int]:
    """
    Get some resources according to search criteria.

    Args:
        session: An SQLAlchemy session
        snap_class: A ResourceSnapshot subclass, which represents which type
            of resource to get
        sortable_fields: Determines the legal values for the "sort_by"
            argument.  This is a dict which maps a legal sort_by value to
            the name of an attribute of the "snap_class" argument.  The
            attribute value corresponds to a table column to sort by.
        searchable_fields: Determines the legal filters in the "filters"
            argument.  This is a dict which maps from a search field name to a
            function of one argument which transforms a query string to an
            SQLAlchemy expression usable in the WHERE clause of a SELECT
            statement, i.e. to filter table rows.  The query string will be
            an SQL "LIKE" pattern.
        group: Limit resources to those owned by this group; None to not limit
            the search
        filters: Search criteria, see parse_search_text()
        page_start: Zero-based row index where the page should start
        page_length: Maximum number of rows in the page; use <= 0 for
            unlimited length
        sort_by: Sort criterion; must be a key of sortable_fields.  None
            to sort in an implementation-dependent way.
        descending: Whether to sort in descending order; only applicable
            if sort_by is given
        deletion_policy: Whether to look at deleted resources, non-deleted
            resources, or all resources

    Returns:
        A 2-tuple including the page of resources and total count of matching
        resources which exist

    Raises:
        SearchParseError: if filters includes a non-searchable field
        SortParameterValidationError: if sort_by is a non-sortable field
        EntityDoesNotExistError: if the given group does not exist
        EntityDeletedError: if the given group is deleted
    """
    sql_filter = construct_sql_query_filters(filters, searchable_fields)
    if sort_by:
        if sort_by in sortable_fields:
            sort_by = sortable_fields[sort_by]
        else:
            raise SortParameterValidationError("resource", sort_by)
    group_id = None if group is None else get_group_id(group)

    if group_id is not None:
        assert_group_exists(session, group_id, DeletionPolicy.NOT_DELETED)

    count_stmt = (
        sa.select(sa.func.count())
        .select_from(snap_class)
        .join(Resource)
        .where(snap_class.resource_snapshot_id == Resource.latest_snapshot_id)
    )

    if group_id is not None:
        count_stmt = count_stmt.where(Resource.group_id == group_id)

    if sql_filter is not None:
        count_stmt = count_stmt.where(sql_filter)

    count_stmt = apply_resource_deletion_policy(count_stmt, deletion_policy)
    current_count = session.scalar(count_stmt)

    # For mypy: a "SELECT count(*)..." query should never return NULL.
    assert current_count is not None

    snaps: Sequence[ResourceT]
    if current_count == 0:
        snaps = []
    else:
        page_stmt = (
            sa.select(snap_class)
            .join(Resource)
            .where(snap_class.resource_snapshot_id == Resource.latest_snapshot_id)
        )

        if group_id is not None:
            page_stmt = page_stmt.where(Resource.group_id == group_id)

        if sql_filter is not None:
            page_stmt = page_stmt.where(sql_filter)

        page_stmt = apply_resource_deletion_policy(page_stmt, deletion_policy)

        if sort_by:
            sort_criteria = getattr(snap_class, sort_by)
            if descending:
                sort_criteria = sort_criteria.desc()
        else:
            # *must* enforce a sort order for consistent paging
            sort_criteria = snap_class.resource_snapshot_id
        page_stmt = page_stmt.order_by(sort_criteria)

        page_stmt = page_stmt.offset(page_start)
        if page_length > 0:
            page_stmt = page_stmt.limit(page_length)

        snaps = session.scalars(page_stmt).all()

    return snaps, current_count


def _construct_sql_search_value(search_term: str) -> str:
    """
    Constructs a search value for a SQL query by replacing wildcards,
    escaping and un-escaping.  The escape character is assumed to be "/".

    Args:
        search_term: A search term

    Returns:
        A string to be used as the value in the WHERE clause of a SQL query.
    """
    if search_term == "*":
        search_term = "%"
    elif search_term == "?":
        search_term = "_"
    else:
        search_term = search_term.replace("/", r"//")
        search_term = search_term.replace("%", r"/%")
        search_term = search_term.replace("_", r"/_")
        search_term = search_term.replace(r"\\", "\\")
        search_term = search_term.replace(r"\*", "*")
        search_term = search_term.replace(r"\?", "?")
        search_term = search_term.replace(r"\"", '"')
        search_term = search_term.replace(r"\'", "'")
        search_term = search_term.replace(r"\n", "\n")

    return search_term


def construct_sql_query_filters(
    parsed_search_terms: list[dict], searchable_fields: dict[str, SearchFieldCallback]
) -> sae.ColumnElement[bool] | None:
    """
    Constructs a search filter to be used by sqlalchemy.

    Args:
        parsed_search_terms: A data structure describing a search; see
            parse_search_text()
        searchable_fields: A dict which maps from a search field name to a
            function of one argument which transforms a query string to an
            SQLAlchemy expression usable in the WHERE clause of a SELECT
            statement, i.e. to filter table rows.  The query string will be
            an SQL "LIKE" pattern.

    Returns:
        A filter that can be used in a sqlalchemy query, or None if no search
        terms were given.

    Raises:
        SearchParseError: if parsed_search_terms includes a field which is
            not supported (i.e. not None and not in searchable_fields)
    """
    filter_fns: Iterable[SearchFieldCallback]

    query_filters = []
    for search_term in parsed_search_terms:
        field = search_term["field"]
        values = search_term["value"]

        sql_search_values = (_construct_sql_search_value(value) for value in values)

        if field is None:
            # if no field, create a "fuzzier" combined search pattern
            combined_search_value = "%" + "%".join(sql_search_values) + "%"
            filter_fns = searchable_fields.values()
        else:
            combined_search_value = "".join(sql_search_values)
            filter_fn = searchable_fields.get(field)
            if filter_fn:
                filter_fns = (filter_fn,)
            else:
                # The "context" arg was originally the whole search string, but
                # that is not known here (only the results of parsing it).
                # The parsing has already succeeded at this point, so the
                # exception class name doesn't make any sense.  Need to rethink
                # the error class?
                raise SearchParseError(field, f"'{field}' is not a valid field")

        search_exprs = [filter_fn(combined_search_value) for filter_fn in filter_fns]

        if len(search_exprs) == 1:
            # avoid useless 1-arg OR
            combined_search_expr = search_exprs[0]
        else:
            combined_search_expr = sa.or_(*search_exprs)

        query_filters.append(combined_search_expr)

    if not query_filters:
        result = None
    elif len(query_filters) == 1:
        # avoid useless 1-arg AND
        result = query_filters[0]
    else:
        result = sa.and_(*query_filters)

    return result
