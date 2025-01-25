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
import typing
from collections.abc import Callable, Iterable

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
    SearchParseError,
    UserNotInGroupError,
)

# General ORM-using code ought to be compatible with "plain" SQLAlchemy or
# flask_sqlalchemy's ORM sessions (the latter are of generic type
# scoped_session[S], where S is a session type).  Any old Session, right?
S = typing.TypeVar("S", bound=Session)
CompatibleSession = Session | scoped_session[S]

# Type alias for search field callbacks
SearchFieldCallback = Callable[[str], sae.ColumnElement[bool]]


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
        True if the snapshot exists; False if not
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

    _assert_exists(deletion_policy, existence_result, "user", user_id, user_id=user_id)


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

    _assert_exists(
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

    _assert_exists(
        deletion_policy,
        existence_result,
        resource_type,
        resource_id,
        resource_id=resource_id,
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


def _assert_exists(
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


def delete_resource(
    session: CompatibleSession[S], resource: Resource | ResourceSnapshot | int
) -> None:
    """
    Common routine for deleting a resource.  No-op if the resource is already
    deleted.

    Args:
        session: An SQLAlchemy session
        resource: A resource, snapshot, or resource_id integer primary key
            value

    Raises:
        EntityDoesNotExistError: if the resource does not exist
    """

    exists_result = resource_exists(session, resource)

    if exists_result is ExistenceResult.DOES_NOT_EXIST:
        resource_id = get_resource_id(resource)
        resource_type = None if isinstance(resource, int) else resource.resource_type
        raise EntityDoesNotExistError(resource_type, resource_id=resource_id)

    elif exists_result is ExistenceResult.EXISTS:

        # here, we really need the Resource object; ResourceLock's constructor
        # is just designed that way.
        if isinstance(resource, int):
            resource_obj = session.get(Resource, resource)
        elif isinstance(resource, ResourceSnapshot):
            resource_obj = resource.resource
        else:
            resource_obj = resource

        lock = ResourceLock(resource_lock_types.DELETE, resource_obj)
        session.add(lock)

    # else: exists_result is DELETED; nothing to do.


def _construct_sql_search_value(search_term: str) -> str:
    """
    Constructs a search value for a SQL query by replacing wildcards,
    escaping and un-escaping.  The escape character is assumed to be "/".

    Args:
        search_value: A search term

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
