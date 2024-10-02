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
from dioptra.restapi.db.shared_errors import (
    ResourceDeletedError,
    ResourceExistsError,
    ResourceNotFoundError,
)
from dioptra.restapi.errors import EntityExistsError, SearchParseError

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


def get_group_id(group: Group | int) -> int | None:
    """
    Helper for APIs which allow a Group domain object or group_id integer
    primary key value.  This normalizes the value to the group_id value, or
    None (if a Group object was passed with a null .group_id attribute).

    Args:
        group: A group object, group_id integer primary key value

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


def user_exists(session: CompatibleSession[S], user: User) -> ExistenceResult:
    """
    Check whether the given user exists in the database, and if so, whether
    it was deleted or not.

    Args:
        session: An SQLAlchemy session
        user: A User object

    Returns:
        One of the ExistenceResult enum values
    """
    if user.user_id is None:
        exists = ExistenceResult.DOES_NOT_EXIST
    else:
        # May as well get existence + deletion status in one query.  I think
        # this ought to be more efficient than getting the whole User object
        # and then checking .is_deleted.
        stmt = (
            sa.select(User.user_id, UserLock.user_lock_type)
            .outerjoin(UserLock)
            .where(User.user_id == user.user_id)
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


def snapshot_exists(session: CompatibleSession[S], snapshot: ResourceSnapshot) -> bool:
    """
    Check whether the given snapshot exists in the database.  Snapshots can't
    be individually deleted (only the resources), so a deletion check is not
    applicable here.

    Args:
        session: An SQLAlchemy session
        snapshot: Any snapshot object

    Returns:
        True if the snapshot exists; False if not
    """

    if snapshot.resource_snapshot_id is None:
        exists = False

    else:
        sub_stmt: sa.Select = (
            sa.select(sa.literal_column("1"))
            .select_from(ResourceSnapshot)
            .where(
                ResourceSnapshot.resource_snapshot_id == snapshot.resource_snapshot_id
            )
        )
        exists_stmt = sa.select(sub_stmt.exists())

        exists = session.scalar(exists_stmt)

        # For mypy.  I think a "select exists(....)" should always return true
        # or false.
        assert exists is not None

    return exists


def assert_user_exists(
    session: CompatibleSession[S], user: User, deletion_policy: DeletionPolicy
) -> None:
    """
    Check whether the given user exists in the database.  This function accepts
    a policy value expressing the caller's preference with respect to deleted
    users.  A deleted user may be treated as either existing or non-existing:

        ANY: Check whether the user exists in the database at all (deletion
             state doesn't matter)
        NOT_DELETED: Check whether the user exists in the database and is not
             deleted
        DELETED: Check whether the user exists in the database and is deleted

    Args:
        session: An SQLAlchemy session
        user: A User object
        deletion_policy: One of the DeletionPolicy enum values

    Raises:
        Exception: if the user is not found, relative to deletion policy
    """
    existence_result = user_exists(session, user)

    user_id = "<no-ID>" if user.user_id is None else user.user_id
    user_name = "<no-name>" if user.username is None else user.username

    _assert_exists(deletion_policy, existence_result, "User", f"{user_id}/{user_name}")


def assert_group_exists(
    session: CompatibleSession[S], group: Group | int, deletion_policy: DeletionPolicy
) -> None:
    """
    Check whether the given group exists in the database.  This function accepts
    a policy value expressing the caller's preference with respect to deleted
    groups.  A deleted group may be treated as either existing or non-existing:

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
        Exception: if the group is not found, relative to deletion policy
    """
    existence_result = group_exists(session, group)

    group_id = get_group_id(group)
    if isinstance(group, int):
        obj_id = str(group_id)
    else:
        obj_id = f"{group_id}/{group.name}"

    _assert_exists(deletion_policy, existence_result, "Group", obj_id)


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
        ResourceNotFoundError: if the resource is not found (even deleted)
        ResourceDeletedError: if the resource exists and is deleted, an
            error with respect to the NOT_DELETED policy
        ResourceExistsError: if the resource exists and is not deleted, an
            error with respect to the DELETED policy
    """
    existence_result = resource_exists(session, resource)

    resource_id = get_resource_id(resource)
    if isinstance(resource, int):
        resource_type = None
    else:
        resource_type = resource.resource_type

    if existence_result is ExistenceResult.DOES_NOT_EXIST:
        raise ResourceNotFoundError(resource_id, resource_type)

    elif existence_result is ExistenceResult.EXISTS:
        if deletion_policy is DeletionPolicy.DELETED:
            raise ResourceExistsError(resource_id, resource_type)

    elif existence_result is ExistenceResult.DELETED:
        if deletion_policy is DeletionPolicy.NOT_DELETED:
            raise ResourceDeletedError(resource_id, resource_type)


def assert_snapshot_exists(
    session: CompatibleSession[S], snapshot: ResourceSnapshot
) -> None:
    """
    Check whether the given snapshot exists in the database.  Snapshots can't
    be individually deleted (only the resources), so deletion policy is not
    applicable here.

    Args:
        session: An SQLAlchemy session
        snapshot: A snapshot object

    Raises:
        Exception if the snapshot doesn't exist
    """

    if not snapshot_exists(session, snapshot):
        snapshot_id = str(snapshot.resource_snapshot_id or "<no-ID>")
        snapshot_type = snapshot.resource_type or "<no-type>"

        raise Exception(f"{snapshot_type} snapshot not found: {snapshot_id}")


def assert_user_does_not_exist(
    session: CompatibleSession[S], user: User, deletion_policy: DeletionPolicy
) -> None:
    """
    Check whether the given user exists in the database.  This function accepts
    a policy value expressing the caller's preference with respect to deleted
    users.  A deleted user may be treated as either existing or non-existing:

        ANY: Ensure the user does not exist in the database at all (deletion
             state doesn't matter).  Same as user_exists(...) == DOES_NOT_EXIST
        NOT_DELETED: Ensure the user doesn't exist as non-deleted (deleted is
                     ok).  Same as user_exists(...) != EXISTS
        DELETED: Ensure the user doesn't exist as deleted (non-deleted ok)
                 Same as user_exists(...) != DELETED

    Args:
        session: An SQLAlchemy session
        user: A User object
        deletion_policy: One of the DeletionPolicy enum values

    Raises:
        Exception: if the user is found, relative to deletion policy
    """
    existence_result = user_exists(session, user)

    user_id = "<no-ID>" if user.user_id is None else user.user_id
    user_name = "<no-name>" if user.username is None else user.username

    _assert_does_not_exist(
        deletion_policy, existence_result, "User", f"{user_id}/{user_name}"
    )


def assert_group_does_not_exist(
    session: CompatibleSession[S], group: Group | int, deletion_policy: DeletionPolicy
) -> None:
    """
    Check whether the given group exists in the database.  This function accepts
    a policy value expressing the caller's preference with respect to deleted
    groups.  A deleted group may be treated as either existing or non-existing:

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
        Exception: if the group is found, relative to deletion policy
    """
    existence_result = group_exists(session, group)

    group_id = get_group_id(group)
    if isinstance(group, int):
        obj_id = str(group_id)
    else:
        obj_id = f"{group_id}/{group.name}"

    _assert_does_not_exist(deletion_policy, existence_result, "Group", obj_id)


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
        ResourceExistsError: if the resource is found and is not deleted, an
            error with respect to policies ANY and NOT_DELETED
        ResourceDeletedError: if the resource is found and is deleted, an
            error with respect to policies ANY and DELETED
    """
    existence_result = resource_exists(session, resource)

    resource_id = get_resource_id(resource)
    if isinstance(resource, int):
        resource_type = None
    else:
        resource_type = resource.resource_type

    if existence_result is ExistenceResult.EXISTS:
        if deletion_policy is not DeletionPolicy.DELETED:
            raise ResourceExistsError(resource_id, resource_type)

    elif existence_result is ExistenceResult.DELETED:
        if deletion_policy is not DeletionPolicy.NOT_DELETED:
            raise ResourceDeletedError(resource_id, resource_type)

    # else: ExistenceResult.DOES_NOT_EXIST.  deletion policy doesn't matter in
    # this case; the object does not exist at all.


def assert_snapshot_does_not_exist(
    session: CompatibleSession[S], snapshot: ResourceSnapshot
) -> None:
    """
    Check whether the given snapshot exists in the database.  Snapshots can't
    be individually deleted (only the resources), so deletion policy is not
    applicable here.

    Args:
        session: An SQLAlchemy session
        snapshot: A snapshot object

    Raises:
        Exception: if the snapshot exists
    """

    snapshot_id = str(snapshot.resource_snapshot_id or "<no-ID>")
    snapshot_type = snapshot.resource_type or "<no-type>"

    if snapshot_exists(session, snapshot):
        raise Exception(f"{snapshot_type} snapshot exists: {snapshot_id}")


def _assert_exists(
    deletion_policy: DeletionPolicy,
    existence_result: ExistenceResult,
    obj_type: str,
    obj_id: str,
) -> None:
    """
    Common code for checking existence relative to deletion policy.

    Args:
        deletion_policy: One of the DeletionPolicy enum values
        existence_result: One of the ExistenceResult enum values
        obj_type: Brief word(s) to describe the kind of object (e.g. a
            "user", "queue", etc), used in error messages
        obj_id: Brief word(s) to identify the particular object being checked,
            e.g. an ID, name, etc, used in error messages
    """
    if existence_result is ExistenceResult.DOES_NOT_EXIST:
        raise Exception(f"{obj_type} does not exist: {obj_id}")

    elif existence_result is ExistenceResult.EXISTS:
        if deletion_policy is DeletionPolicy.DELETED:
            raise Exception(f"{obj_type} exists, not deleted: {obj_id}")

    elif existence_result is ExistenceResult.DELETED:
        if deletion_policy is DeletionPolicy.NOT_DELETED:
            raise Exception(f"{obj_type} is deleted: {obj_id}")


def _assert_does_not_exist(
    deletion_policy: DeletionPolicy,
    existence_result: ExistenceResult,
    obj_type: str,
    obj_id: str,
):
    """
    Common code for checking non-existence relative to deletion policy.

    Args:
        deletion_policy: One of the DeletionPolicy enum values
        existence_result: One of the ExistenceResult enum values
        obj_type: Brief word(s) to describe the kind of object (e.g. a
            "user", "queue", etc), used in error messages
        obj_id: Brief word(s) to identify the particular object being checked,
            e.g. an ID, name, etc, used in error messages
    """
    if existence_result is ExistenceResult.EXISTS:
        if deletion_policy is not DeletionPolicy.DELETED:
            raise Exception(f"{obj_type} exists, not deleted: {obj_id}")

    elif existence_result is ExistenceResult.DELETED:
        if deletion_policy is not DeletionPolicy.NOT_DELETED:
            raise Exception(f"{obj_type} exists (deleted): {obj_id}")

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
        Exception: if the given user is not in the given group
    """

    # Assume existence checks on user and group were already done, so they are
    # known to exist.
    membership = session.get(GroupMember, (user.user_id, group.group_id))

    if not membership:
        raise Exception(
            f"User ({user.user_id}/{user.username}) is not in group ({group.group_id}/{group.name})"  # noqa: B950
        )


def check_user_collision(session: CompatibleSession[S], user: User) -> None:
    """
    Factored out check from user and group repositories.  Their create methods
    can both create users, so both need to ensure requirements are met.

    Args:
        session: An SQLAlchemy session
        user: A User object

    Raises:
        UsernameNotAvailableError: if the given user's username collides with
            an existing user's username
        UserEmailNotAvailableError: If the given user's email address collides
            with an existing user's email address
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
        ResourceNotFoundError: if the resource does not exist
    """

    exists_result = resource_exists(session, resource)

    if exists_result is ExistenceResult.DOES_NOT_EXIST:
        resource_id = get_resource_id(resource)
        resource_type = None if isinstance(resource, int) else resource.resource_type
        raise ResourceNotFoundError(resource_id, resource_type)

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
        SearchParseError: If a search string cannot be parsed.
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
