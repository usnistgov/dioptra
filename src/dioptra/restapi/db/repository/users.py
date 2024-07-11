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

import sqlalchemy as sa

from dioptra.restapi.db.models import Group, GroupManager, GroupMember, User, UserLock
from dioptra.restapi.db.models.constants import UserLockTypes
from dioptra.restapi.db.repository.utils import (
    CompatibleSession,
    DeletionPolicy,
    ExistenceResult,
    S,
    assert_group_exists,
    assert_user_does_not_exist,
    assert_user_exists,
    check_user_collision,
    user_exists,
)


class UserRepository:

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
            Exception: If group does not exist, user already exists, or
                user is invalid (e.g. has a colliding username)
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
            Exception: if the user does not exist
        """

        # TODO: This is very simple, so far.  Do we remove group memberships?
        #     What about owned resource snapshots?

        # Perhaps I could have implemented this entirely via user_exists(),
        # but using the assert_* call does give me the standardized exception
        # and error message when the user does not exist.
        assert_user_exists(self.session, user, DeletionPolicy.ANY)

        exists_result = user_exists(self.session, user)

        if exists_result is ExistenceResult.EXISTS:
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

    def get_page(
        self,
        page_start: int,
        page_length: int,
        deletion_policy: DeletionPolicy = DeletionPolicy.NOT_DELETED,
    ) -> Sequence[User]:
        """
        Get a "page" of users.  The page start is a user index (not a page
        index).  Use index zero to start at the beginning.  Using a page start
        that's beyond the last user will result in an empty sequence, not an
        error.  The number of users returned will not be larger than
        page_length (if it is > 0), but might be smaller.

        Args:
            page_start: A user start index (use 0 for the first page)
            page_length: Page length, in terms of number of users per page.
                If <= 0, don't limit page length (get all remaining users)
            deletion_policy: Whether to look at deleted users, non-deleted
                users, or all users

        Returns:
            A sequence of users
        """
        stmt = sa.select(User)
        stmt = _apply_deletion_policy(stmt, deletion_policy)

        # *must* enforce a sort order for consistent paging
        stmt = stmt.order_by(User.user_id).offset(page_start)

        if page_length > 0:
            stmt = stmt.limit(page_length)

        return self.session.scalars(stmt).all()

    def get_member_permissions(self, user: User, group: Group) -> GroupMember | None:
        """
        Get a user's permissions with respect to the given group.

        Args:
            group: A group
            user: A user

        Returns:
            A GroupMember object which contains the permissions, or None if
            the given user does not belong to the given group

        Raises:
            Exception: if either the user or group does not exist
        """
        assert_group_exists(self.session, group, DeletionPolicy.NOT_DELETED)
        assert_user_exists(self.session, user, DeletionPolicy.NOT_DELETED)

        membership = self.session.get(GroupMember, (user.user_id, group.group_id))

        return membership

    def get_manager_permissions(self, user: User, group: Group) -> GroupManager | None:
        """
        Get a user's group manager permissions with respect to the given group.

        Args:
            group: A group
            user: A user

        Returns:
            A GroupManager object which contains the permissions, or None if
            the given user is not a manager of the given group

        Raises:
            Exception: if either the user or group does not exist
        """
        assert_group_exists(self.session, group, DeletionPolicy.NOT_DELETED)
        assert_user_exists(self.session, user, DeletionPolicy.NOT_DELETED)

        manager = self.session.get(GroupManager, (user.user_id, group.group_id))

        return manager

    def set_member_permissions(
        self,
        user: User,
        group: Group,
        read: bool | None = None,
        write: bool | None = None,
        share_read: bool | None = None,
        share_write: bool | None = None,
    ) -> None:
        """
        Set a user's permissions with respect to the given group.  Use None as
        a permission value if needed, to leave a permission as-is.

        Args:
            group: A group
            user: A user
            read: The read permission to set
            write: The write permission to set
            share_read: The share_read permission to set
            share_write: The share_write permission to set

        Raises:
            Exception: If the user or group don't exist, or if the given user
                is not a member of the given group
        """

        # TODO: is this method really necessary?  Users could call
        #     get_member_permissions() to get a GroupMember object and then
        #     modify permissions themselves.

        assert_group_exists(self.session, group, DeletionPolicy.NOT_DELETED)
        assert_user_exists(self.session, user, DeletionPolicy.NOT_DELETED)

        membership = self.session.get(GroupMember, (user.user_id, group.group_id))

        if membership:
            if read is not None:
                membership.read = read
            if write is not None:
                membership.write = write
            if share_read is not None:
                membership.share_read = share_read
            if share_write is not None:
                membership.share_write = share_write

        else:
            raise Exception(
                f"Not a member: user={user.user_id}, group={group.group_id}"
            )

    def set_manager_permissions(
        self,
        user: User,
        group: Group,
        owner: bool | None = None,
        admin: bool | None = None,
    ) -> None:
        """
        Set a manager's permissions with respect to the given group.  Use None
        as a permission value if needed, to leave a permission as-is.

        Args:
            group: A group
            user: A user
            owner: The owner permission to set
            admin: The admin permission to set

        Raises:
            Exception: if the user or group don't exist, or if the given user
                is not a manager of the given group
        """

        # TODO: is this method really necessary?  Users could call
        #     get_manager_permissions() to get a GroupManager object and then
        #     modify permissions themselves.

        assert_group_exists(self.session, group, DeletionPolicy.NOT_DELETED)
        assert_user_exists(self.session, user, DeletionPolicy.NOT_DELETED)

        manager = self.session.get(GroupManager, (user.user_id, group.group_id))

        if manager:
            if owner is not None:
                manager.owner = owner
            if admin is not None:
                manager.admin = admin

        else:
            raise Exception(
                f"Not a manager: user={user.user_id}, group={group.group_id}"
            )


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
