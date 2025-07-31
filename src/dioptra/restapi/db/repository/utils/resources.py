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
Functionality common to resource repositories.
"""

import enum
import itertools
import typing
from collections.abc import Iterable, Sequence, Set

import sqlalchemy as sa
import sqlalchemy.orm as sao

import dioptra.restapi.db.models as m
import dioptra.restapi.errors as e
from dioptra.restapi.db.models.constants import resource_lock_types
from dioptra.restapi.db.repository.utils.checks import (
    assert_exists,
    assert_group_exists,
    assert_resource_exists,
    assert_resources_exist,
    resource_exists,
)
from dioptra.restapi.db.repository.utils.common import (
    CompatibleSession,
    DeletionPolicy,
    ExistenceResult,
    S,
    get_group_id,
    get_resource_id,
)
from dioptra.restapi.db.repository.utils.search import construct_sql_query_filters
from dioptra.restapi.v1.entity_types import EntityTypes

# May be bound to a resource-type-specific ResourceSnapshot subclass,
# i.e. represents our python class representation of a resource type.
ResourceT = typing.TypeVar("ResourceT", bound=m.ResourceSnapshot)


class ResourceLockType(enum.Enum):
    """
    Types of resource lock
    """

    DELETED = resource_lock_types.DELETE
    READONLY = resource_lock_types.READONLY


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
    resource_alias = sao.aliased(m.Resource)

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
def get_latest_snapshots(
    session: CompatibleSession[S],
    snap_class: typing.Type[ResourceT],
    resources: int | m.Resource | m.ResourceSnapshot,
    deletion_policy: DeletionPolicy,
) -> ResourceT | None: ...


@typing.overload
def get_latest_snapshots(
    session: CompatibleSession[S],
    snap_class: typing.Type[ResourceT],
    resources: Iterable[int | m.Resource | m.ResourceSnapshot],
    deletion_policy: DeletionPolicy,
) -> Sequence[ResourceT]: ...


def get_latest_snapshots(
    session: CompatibleSession[S],
    snap_class: typing.Type[ResourceT],
    resources: (
        int
        | m.Resource
        | m.ResourceSnapshot
        | Iterable[int | m.Resource | m.ResourceSnapshot]
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
    if isinstance(resources, (int, m.Resource, m.ResourceSnapshot)):
        resource_id_check = snap_class.resource_id == get_resource_id(resources)
    else:
        resource_id_check = snap_class.resource_id.in_(
            get_resource_id(res) for res in resources
        )

    # Extra join with Resource is important: the query produces incorrect
    # results without it!
    stmt = (
        sa.select(snap_class)
        .join(m.Resource)
        .where(
            resource_id_check,
            snap_class.resource_snapshot_id == m.Resource.latest_snapshot_id,
        )
    )
    stmt = apply_resource_deletion_policy(stmt, deletion_policy)

    snaps: ResourceT | Sequence[ResourceT] | None
    if isinstance(resources, (int, m.Resource, m.ResourceSnapshot)):
        snaps = session.scalar(stmt)
    else:
        snaps = session.scalars(stmt).all()

    return snaps


def get_one_latest_snapshot(
    session: CompatibleSession[S],
    snap_class: typing.Type[ResourceT],
    resource: int | m.Resource | m.ResourceSnapshot,
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
    elif isinstance(resource, (m.Resource, m.ResourceSnapshot)):
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
    parent: m.Resource | m.ResourceSnapshot | int,
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

    child_resources: Sequence[m.Resource | int]
    if isinstance(parent, (m.Resource, m.ResourceSnapshot)):
        child_resources = parent.children
    else:
        stmt = sa.select(m.resource_dependencies_table.c.child_resource_id).where(
            m.resource_dependencies_table.c.parent_resource_id == parent
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
def get_snapshot_by_name(  # type: ignore[overload-overlap]
    session: CompatibleSession[S],
    snap_class: typing.Type[ResourceT],
    name: str,
    group: m.Group | int,
    deletion_policy: DeletionPolicy,
) -> ResourceT | None: ...


@typing.overload
def get_snapshot_by_name(
    session: CompatibleSession[S],
    snap_class: typing.Type[ResourceT],
    name: Iterable[str],
    group: m.Group | int,
    deletion_policy: DeletionPolicy,
) -> Sequence[ResourceT]: ...


def get_snapshot_by_name(
    session: CompatibleSession[S],
    snap_class: typing.Type[ResourceT],
    name: str | Iterable[str],
    group: m.Group | int,
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
        .join(m.Resource)
        .where(
            snap_class.resource_snapshot_id == m.Resource.latest_snapshot_id,
            m.Resource.group_id == group_id,
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
    parent: m.Resource | m.ResourceSnapshot | int,
    new_children: Iterable[m.Resource | ResourceT | int],
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
        temp = session.get(m.Resource, parent)
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
    parent: m.Resource | m.ResourceSnapshot | int,
    new_children: Iterable[m.Resource | ResourceT | int],
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
        temp = session.get(m.Resource, parent)
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
    parent: m.Resource | m.ResourceSnapshot | int,
    child: m.Resource | m.ResourceSnapshot | int,
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
        temp = session.get(m.Resource, parent)
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
    session: CompatibleSession[S], resource: m.Resource | m.ResourceSnapshot | int
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
        raise e.EntityDoesNotExistError(
            EntityTypes.get_from_string(resource_type), resource_id=resource_id
        )

    elif exists_result is ExistenceResult.EXISTS:
        add_resource_lock_types(session, resource, {ResourceLockType.DELETED})

    # else: exists_result is DELETED; nothing to do.


def get_resource_lock_types(
    session: CompatibleSession[S],
    resource: m.Resource | m.ResourceSnapshot | int,
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
        stmt = sa.select(m.ResourceLock).where(
            m.ResourceLock.resource_id == resource_id
        )

        locks = session.scalars(stmt)
        for lock in locks:
            lock_types.add(ResourceLockType(lock.resource_lock_type))

    return lock_types


def add_resource_lock_types(
    session: CompatibleSession[S],
    resource: m.Resource | m.ResourceSnapshot | int,
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

    if isinstance(resource, (m.Resource, m.ResourceSnapshot)):
        resource_type = EntityTypes.get_from_string(resource.resource_type)
    else:
        resource_type = EntityTypes.NONE

    resource_id = get_resource_id(resource)

    existing_lock_types = get_resource_lock_types(session, resource)
    types_to_add = lock_types - existing_lock_types

    if ResourceLockType.DELETED in existing_lock_types:
        # resource_id can't be None if the resource is deleted; it must exist
        # in the db with a delete lock
        assert resource_id is not None
        if types_to_add:
            raise e.EntityDeletedError(
                resource_type,
                resource_id,
                resource_id=resource_id,
            )

    if ResourceLockType.READONLY in existing_lock_types:
        if types_to_add:
            raise e.ReadOnlyLockError(
                EntityTypes.get_from_string(resource_type), resource_id=resource_id
            )

    else:
        # here, we really need the Resource object; ResourceLock's
        # constructor is just designed that way.
        if isinstance(resource, int):
            resource_obj = session.get(m.Resource, resource)
            if not resource_obj:
                raise e.EntityDoesNotExistError(
                    EntityTypes.get_from_string(resource_type), resource_id=resource
                )
        elif isinstance(resource, m.ResourceSnapshot):
            resource_obj = resource.resource
        else:
            resource_obj = resource

        for lock_type in types_to_add:
            lock = m.ResourceLock(lock_type.value, resource_obj)
            session.add(lock)


def get_by_filters_paged(
    session: CompatibleSession[S],
    snap_class: typing.Type[ResourceT],
    sortable_fields: dict[str, str],
    searchable_fields: dict[str, typing.Any],
    group: m.Group | int | None,
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
            raise e.SortParameterValidationError(EntityTypes.RESOURCE, sort_by)
    group_id = None if group is None else get_group_id(group)

    if group_id is not None:
        assert_group_exists(session, group_id, DeletionPolicy.NOT_DELETED)

    count_stmt = (
        sa.select(sa.func.count())
        .select_from(snap_class)
        .join(m.Resource)
        .where(snap_class.resource_snapshot_id == m.Resource.latest_snapshot_id)
    )

    if group_id is not None:
        count_stmt = count_stmt.where(m.Resource.group_id == group_id)

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
            .join(m.Resource)
            .where(snap_class.resource_snapshot_id == m.Resource.latest_snapshot_id)
        )

        if group_id is not None:
            page_stmt = page_stmt.where(m.Resource.group_id == group_id)

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


__all__ = [
    "ResourceLockType",
    "ResourceT",
    "add_resource_lock_types",
    "append_resource_children",
    "apply_resource_deletion_policy",
    "delete_resource",
    "get_by_filters_paged",
    "get_latest_child_snapshots",
    "get_latest_snapshots",
    "get_one_latest_snapshot",
    "get_resource_lock_types",
    "get_snapshot_by_name",
    "set_resource_children",
    "unlink_child",
]
