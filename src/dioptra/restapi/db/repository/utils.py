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

import sqlalchemy as sa
from sqlalchemy.orm import Session, scoped_session

from dioptra.restapi.db.models import Group, GroupLock, User, UserLock
from dioptra.restapi.db.models.constants import GroupLockTypes, UserLockTypes
from dioptra.restapi.db.repository.errors import (
    UserEmailNotAvailableError,
    UsernameNotAvailableError,
)

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
        elif row[1] == UserLockTypes.DELETE:
            exists = ExistenceResult.DELETED
        else:
            exists = ExistenceResult.EXISTS

    return exists


def group_exists(session: CompatibleSession[S], group: Group) -> ExistenceResult:
    """
    Check whether the given group exists in the database, and if so, whether
    it was deleted or not.

    Args:
        session: An SQLAlchemy session
        group: A Group object

    Returns:
        One of the ExistenceResult enum values
    """
    if group.group_id is None:
        exists = ExistenceResult.DOES_NOT_EXIST
    else:
        # May as well get existence + deletion status in one query
        stmt = (
            sa.select(Group.group_id, GroupLock.group_lock_type)
            .outerjoin(GroupLock)
            .where(Group.group_id == group.group_id)
        )
        results = session.execute(stmt)
        # will need to change if a group may have multiple lock types
        row = results.first()

        if not row:
            exists = ExistenceResult.DOES_NOT_EXIST
        elif row[1] == GroupLockTypes.DELETE:
            exists = ExistenceResult.DELETED
        else:
            exists = ExistenceResult.EXISTS

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

    if existence_result == ExistenceResult.DOES_NOT_EXIST:
        raise Exception(f"User does not exist: {user_name}/{user_id}")

    elif existence_result == ExistenceResult.EXISTS:
        if deletion_policy == DeletionPolicy.DELETED:
            raise Exception(f"User exists, not deleted: {user_name}/{user_id}")

    elif existence_result == ExistenceResult.DELETED:
        if deletion_policy == DeletionPolicy.NOT_DELETED:
            raise Exception(f"User is deleted: {user_name}/{user_id}")


def assert_group_exists(
    session: CompatibleSession[S], group: Group, deletion_policy: DeletionPolicy
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
        group: A Group object
        deletion_policy: One of the DeletionPolicy enum values

    Raises:
        Exception: if the group is not found, relative to deletion policy
    """
    existence_result = group_exists(session, group)

    group_id = "<no-ID>" if group.group_id is None else group.group_id
    group_name = "<no-name>" if group.name is None else group.name

    if existence_result == ExistenceResult.DOES_NOT_EXIST:
        raise Exception(f"Group does not exist: {group_name}/{group_id}")

    elif existence_result == ExistenceResult.EXISTS:
        if deletion_policy == DeletionPolicy.DELETED:
            raise Exception(f"Group exists, not deleted: {group_name}/{group_id}")

    elif existence_result == ExistenceResult.DELETED:
        if deletion_policy == DeletionPolicy.NOT_DELETED:
            raise Exception(f"Group is deleted: {group_name}/{group_id}")


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

    if existence_result is ExistenceResult.EXISTS:
        if deletion_policy is not DeletionPolicy.DELETED:
            raise Exception(f"User exists, not deleted: {user_name}/{user_id}")

    elif existence_result is ExistenceResult.DELETED:
        if deletion_policy is not DeletionPolicy.NOT_DELETED:
            raise Exception(f"User exists (deleted): {user_name}/{user_id}")

    # else: ExistenceResult.DOES_NOT_EXIST.  deletion policy doesn't matter in
    # this case; the user does not exist at all.


def assert_group_does_not_exist(
    session: CompatibleSession[S], group: Group, deletion_policy: DeletionPolicy
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
        group: A Group object
        deletion_policy: One of the DeletionPolicy enum values

    Raises:
        Exception: if the group is found, relative to deletion policy
    """
    existence_result = group_exists(session, group)

    group_id = "<no-ID>" if group.group_id is None else group.group_id
    group_name = "<no-name>" if group.name is None else group.name

    if existence_result is ExistenceResult.EXISTS:
        if deletion_policy is not DeletionPolicy.DELETED:
            raise Exception(f"Group exists, not deleted: {group_name}/{group_id}")

    elif existence_result is ExistenceResult.DELETED:
        if deletion_policy is not DeletionPolicy.NOT_DELETED:
            raise Exception(f"Group exists (deleted): {group_name}/{group_id}")

    # else: ExistenceResult.DOES_NOT_EXIST.  deletion policy doesn't matter in
    # this case; the group does not exist at all.


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

    stmt = sa.select(User.username).where(User.username == user.username)
    name_check = session.scalar(stmt)

    if name_check is not None:
        raise UsernameNotAvailableError(
            "User already exists with name: " + user.username
        )

    stmt = sa.select(User.email_address).where(User.email_address == user.email_address)
    email_check = session.scalar(stmt)

    if email_check is not None:
        raise UserEmailNotAvailableError(
            "User already exists with email address: " + user.email_address
        )
