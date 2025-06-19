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
The user repository: data operations related to users
"""
import uuid
from collections.abc import Sequence
from typing import Any, Final

import sqlalchemy as sa

from dioptra.restapi.db.models import Group, GroupManager, GroupMember, User, UserLock
from dioptra.restapi.db.models.constants import UserLockTypes
from dioptra.restapi.db.repository.utils import (
    CompatibleSession,
    DeletionPolicy,
    ExistenceResult,
    S,
    assert_exists,
    assert_group_exists,
    assert_user_does_not_exist,
    assert_user_exists,
    check_user_collision,
    construct_sql_query_filters,
    get_group_id,
    get_user_id,
    user_exists,
)
from dioptra.restapi.errors import EntityDoesNotExistError


class UserRepository:

    SEARCHABLE_FIELDS: Final[dict[str, Any]] = {
        "username": lambda x: User.username.like(x, escape="/"),
        "email": lambda x: User.email_address.like(x, escape="/"),
    }

    def __init__(self, session: CompatibleSession[S]):
        self.session = session

    def create(
        self,
        user: User,
        group: Group,
        read: bool = False,
        write: bool = False,
        share_read: bool = False,
        share_write: bool = False,
    ) -> None:
        """
        Create a user.  Their initial group membership will be the given group.
        The user must not exist and the group must exist.  To bring into
        existence a user and group at the same time, see
        GroupRepository.create().

        Args:
            user: A user; must not already exist in the db
            group: A group; must already exist in the db
            read: read permission
            write: write permission
            share_read: share_read permission
            share_write: share_write permission

        Raises:
            EntityDoesNotExistError: If group does not exist
            EntityExistsError: If user already exists, or the name or email
                collides with an existing user
            EntityDeletedError: If the user or group are deleted
        """

        # Consistency rules:
        # - Every user must be in a group
        # - Every user must have a unique name
        # - Every user must have a unique email address

        assert_group_exists(self.session, group, DeletionPolicy.NOT_DELETED)
        assert_user_does_not_exist(self.session, user, DeletionPolicy.ANY)

        check_user_collision(self.session, user)

        group.members.append(
            GroupMember(
                read=read,
                write=write,
                share_read=share_read,
                share_write=share_write,
                user=user,
            )
        )

        self.session.add(user)

    def delete(self, user: User) -> None:
        """
        Delete a user.  No-op if the user is already deleted.

        Args:
            user: The user to delete

        Raises:
            EntityDoesNotExistError: if the user does not exist
        """

        # TODO: This is very simple, so far.  Do we remove group memberships?
        #     What about owned resource snapshots?

        exists_result = user_exists(self.session, user)
        if exists_result is ExistenceResult.DOES_NOT_EXIST:
            raise EntityDoesNotExistError("user", user_id=user.user_id)

        elif exists_result is ExistenceResult.EXISTS:
            lock = UserLock(UserLockTypes.DELETE, user)
            self.session.add(lock)

    def get(
        self, user_id: int, deletion_policy: DeletionPolicy = DeletionPolicy.NOT_DELETED
    ) -> User | None:
        """
        Get the unique user according to its ID.

        Args:
            user_id: A user ID
            deletion_policy: Whether to look at deleted users, non-deleted
                users, or all users

        Returns:
            A user, or None if one was not found.
        """

        stmt = sa.select(User).where(User.user_id == user_id)
        stmt = _apply_deletion_policy(stmt, deletion_policy)

        user = self.session.scalar(stmt)

        return user

    def get_one(
        self, user_id: int, deletion_policy: DeletionPolicy = DeletionPolicy.NOT_DELETED
    ) -> User:
        """
        Get the unique user according to its ID.  Analogous to .get(), but
        raises exceptions instead of returning None.

        Args:
            user_id: A user ID
            deletion_policy: Whether to look at deleted users, non-deleted
                users, or all users

        Returns:
            A user.

        Raises:
            EntityDoesNotExistError: if the user ID does not resolve to a user
            EntityDeletedError: if deletion policy is NOT_DELETED but the user
                is deleted
            EntityExistsError: if deletion policy is DELETED but the user
                exists and is not deleted
        """

        user = self.session.get(User, user_id)

        if not user:
            existence_result = ExistenceResult.DOES_NOT_EXIST
        elif user.is_deleted:
            existence_result = ExistenceResult.DELETED
        else:
            existence_result = ExistenceResult.EXISTS

        assert_exists(deletion_policy, existence_result, "user", user_id)

        # The above assert_exists() function would have raised an exception,
        # so user can't be none here.
        assert user is not None
        return user

    def get_by_name(
        self,
        username: str,
        deletion_policy: DeletionPolicy = DeletionPolicy.NOT_DELETED,
    ) -> User | None:
        """
        Get a user by username.

        Args:
            username: A username
            deletion_policy: Whether to look at deleted users, non-deleted
                users, or all users

        Returns:
            A user, or None if one was not found
        """
        stmt = sa.select(User).where(User.username == username)
        stmt = _apply_deletion_policy(stmt, deletion_policy)

        # Shouldn't we either return a list or put a unique constraint on
        # the username column?
        user = self.session.scalar(stmt)

        return user

    def get_by_alternative_id(
        self,
        alternative_id: str | uuid.UUID,
        deletion_policy: DeletionPolicy = DeletionPolicy.NOT_DELETED,
    ) -> User | None:
        """
        Get a user by alternative ID.

        Args:
            alternative_id: An alternative ID
            deletion_policy: Whether to look at deleted users, non-deleted
                users, or all users

        Returns:
            A user, or None if one was not found
        """
        stmt = sa.select(User).where(User.alternative_id == alternative_id)
        stmt = _apply_deletion_policy(stmt, deletion_policy)

        user = self.session.scalar(stmt)

        return user

    def get_by_email(
        self, email: str, deletion_policy: DeletionPolicy = DeletionPolicy.NOT_DELETED
    ) -> User | None:
        """
        Get a user by email address.

        Args:
            email: An email address
            deletion_policy: Whether to look at deleted users, non-deleted
                users, or all users

        Returns:
            A user, or None if one was not found
        """
        stmt = sa.select(User).where(User.email_address == email)
        stmt = _apply_deletion_policy(stmt, deletion_policy)

        user = self.session.scalar(stmt)

        return user

    def get_by_filters_paged(
        self,
        filters: list[dict],
        page_start: int,
        page_length: int,
        deletion_policy: DeletionPolicy = DeletionPolicy.NOT_DELETED,
    ) -> tuple[Sequence[User], int]:
        """
        Get some users according to search criteria.

        Args:
            filters: A structure representing search criteria.  See
                parse_search_text().
            page_start: A row index where the returned page should start
            page_length: A row count representing the page length; use <= 0
                for unlimited length
            deletion_policy: Whether to look at deleted users, non-deleted
                users, or all users

        Returns:
            A 2-tuple including a page of User objects, and a count of the
            total number of users matching the criteria
        """
        sql_filter = construct_sql_query_filters(filters, self.SEARCHABLE_FIELDS)

        count_stmt = sa.select(sa.func.count()).select_from(User)
        if sql_filter is not None:
            count_stmt = count_stmt.where(sql_filter)
        count_stmt = _apply_deletion_policy(count_stmt, deletion_policy)
        current_count = self.session.scalar(count_stmt)

        # For mypy: a "SELECT count(*)..." query should never return NULL.
        assert current_count is not None

        users: Sequence[User]
        if current_count == 0:
            users = []
        else:
            page_stmt = sa.select(User)
            if sql_filter is not None:
                page_stmt = page_stmt.where(sql_filter)
            page_stmt = _apply_deletion_policy(page_stmt, deletion_policy)
            # *must* enforce a sort order for consistent paging
            page_stmt = page_stmt.order_by(User.user_id)
            page_stmt = page_stmt.offset(page_start)
            if page_length > 0:
                page_stmt = page_stmt.limit(page_length)

            users = self.session.scalars(page_stmt).all()

        return users, current_count

    def num_users(
        self, deletion_policy: DeletionPolicy = DeletionPolicy.NOT_DELETED
    ) -> int:
        """
        Get the total number of users in the system.

        Args:
            deletion_policy: Whether to look at deleted users, non-deleted
                users, or all users

        Returns:
            The number of users
        """

        stmt = sa.select(sa.func.count()).select_from(User)
        stmt = _apply_deletion_policy(stmt, deletion_policy)

        num_users = self.session.scalar(stmt)

        # The num_users of a "count()" operation surely can't be anything other
        # than an int!
        assert num_users is not None

        return num_users

    def get_member_permissions(
        self, user: User | int, group: Group | int
    ) -> GroupMember | None:
        """
        Get a user's permissions with respect to the given group.

        Args:
            group: A Group object or group_id integer primary key value
            user: A User object or user_id integer primary key value

        Returns:
            A GroupMember object which contains the permissions, or None if
            the given user does not belong to the given group

        Raises:
            EntityDoesNotExistError: if either the user or group does not exist
            EntityDeletedError: if either the user or group is deleted
        """
        assert_group_exists(self.session, group, DeletionPolicy.NOT_DELETED)
        assert_user_exists(self.session, user, DeletionPolicy.NOT_DELETED)

        group_id = get_group_id(group)
        user_id = get_user_id(user)

        membership = self.session.get(GroupMember, (user_id, group_id))

        return membership

    def get_manager_permissions(
        self, user: User | int, group: Group | int
    ) -> GroupManager | None:
        """
        Get a user's group manager permissions with respect to the given group.

        Args:
            group: A Group object or group_id integer primary key value
            user: A User object or user_id integer primary key value

        Returns:
            A GroupManager object which contains the permissions, or None if
            the given user is not a manager of the given group

        Raises:
            EntityDoesNotExistError: if either the user or group does not exist
            EntityDeletedError: if either the user or group is deleted
        """
        assert_group_exists(self.session, group, DeletionPolicy.NOT_DELETED)
        assert_user_exists(self.session, user, DeletionPolicy.NOT_DELETED)

        group_id = get_group_id(group)
        user_id = get_user_id(user)

        manager = self.session.get(GroupManager, (user_id, group_id))

        return manager


def _apply_deletion_policy(
    stmt: sa.Select, deletion_policy: DeletionPolicy
) -> sa.Select:
    """
    Factored out code to add a WHERE clause to a select statement to apply
    deletion policy to it, affecting whether deleted users are searched.

    Args:
        stmt: A select statement to modify
        deletion_policy: The policy to apply

    Returns:
        A modified select statement
    """
    if deletion_policy is DeletionPolicy.NOT_DELETED:
        stmt = stmt.where(User.is_deleted == False)  # noqa: E712
    elif deletion_policy is DeletionPolicy.DELETED:
        stmt = stmt.where(User.is_deleted == True)  # noqa: E712

    return stmt
