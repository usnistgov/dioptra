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
Functionality common across repos and repo utils
"""

import enum
import typing

from sqlalchemy.orm import Session, scoped_session

import dioptra.restapi.db.models as m

# General ORM-using code ought to be compatible with "plain" SQLAlchemy or
# flask_sqlalchemy's ORM sessions (the latter are of generic type
# scoped_session[S], where S is a session type).  Any old Session, right?
S = typing.TypeVar("S", bound=Session)
CompatibleSession = Session | scoped_session[S]


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


def get_user_id(user: m.User | int) -> int | None:
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


def get_group_id(group: m.Group | int) -> int | None:
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


def get_resource_id(resource: m.Resource | m.ResourceSnapshot | int) -> int | None:
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
            and isinstance(resource, m.ResourceSnapshot)
            and resource.resource
        ):
            resource_id = resource.resource.resource_id

    return resource_id


def get_draft_id(draft: m.DraftResource | int) -> int | None:
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


def get_resource_snapshot_id(snapshot: m.ResourceSnapshot | int) -> int | None:
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


__all__ = [
    "CompatibleSession",
    "DeletionPolicy",
    "ExistenceResult",
    "S",
    "get_draft_id",
    "get_group_id",
    "get_resource_id",
    "get_resource_snapshot_id",
    "get_user_id",
]
