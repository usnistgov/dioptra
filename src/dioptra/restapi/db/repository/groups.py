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
The group repository: data operations related to groups
"""
from typing import Final

import sqlalchemy as sa

from dioptra.restapi.db.models import Group, GroupLock, GroupManager, GroupMember, User
from dioptra.restapi.db.models.constants import GroupLockTypes
from dioptra.restapi.db.repository.errors import GroupNameNotAvailableError
from dioptra.restapi.db.repository.utils import (
    CompatibleSession,
    DeletionPolicy,
    ExistenceResult,
    S,
    assert_group_does_not_exist,
    assert_group_exists,
    assert_user_exists,
    check_user_collision,
    group_exists,
    user_exists,
)

GROUP_CREATOR_MANAGER_PERMISSIONS: Final[dict[str, bool]] = {
    "owner": True,
    "admin": True,
}

GROUP_CREATOR_MEMBER_PERMISSIONS: Final[dict[str, bool]] = {
    "read": True,
    "write": True,
    "share_read": True,
    "share_write": True,
}


class GroupRepository:

    def __init__(self, session: CompatibleSession[S]):
        self.session = session

    def create(self, group) -> None:
        """
        Create a new group.  The group's creator will be its initial member.

        Args:
            group: A group object representing the new group

        Raises:
            Exception: if the group already exists
        """

        # Consistency rules:
        # - A group must have at least one member
        # - Each group must have a different name
        # - Group creators must not have been deleted
        # - If creator is new, all rules regarding user creation

        # Special allowance here for the group creator (user) to not exist.
        # This is necessary to allow bootstrapping a system with no user or
        # group: both will need to come into existence simultaneously.

        assert_group_does_not_exist(self.session, group, DeletionPolicy.ANY)

        if group.name is not None and self.get_by_name(group.name, DeletionPolicy.ANY):
            # Assume this name uniqueness constraint applies with respect to
            # all groups, not just non-deleted groups.
            raise GroupNameNotAvailableError("Group name already taken: " + group.name)

        # Because we may be creating a new user, we need to check things
        # similarly to UserRepository.create().  We can't just invoke that
        # method because it has different preconditions (the group must exist,
        # the user must not exist).
        user_exists_result = user_exists(self.session, group.creator)
        if user_exists_result is ExistenceResult.DOES_NOT_EXIST:
            # Creator is new; make sure properties are okay
            check_user_collision(self.session, group.creator)
        elif user_exists_result is ExistenceResult.DELETED:
            # Should probably enforce this until instructed otherwise
            raise Exception(
                "Group creator (user) must not have been deleted: "
                + group.creator.user_id
            )

        # Creator is always the first group member.
        group.members.append(
            GroupMember(user=group.creator, **GROUP_CREATOR_MEMBER_PERMISSIONS)
        )

        group.managers.append(
            GroupManager(user=group.creator, **GROUP_CREATOR_MANAGER_PERMISSIONS)
        )

        self.session.add(group)

    def delete(self, group: Group) -> None:
        """
        Delete a group.  No-op if the group is already deleted.

        Args:
            group: The group to delete

        Raises:
            Exception: if the group does not exist
        """

        # TODO: This is very simple, so far.  Do we remove group members?  What
        #     about owned resources?

        # Perhaps I could have implemented this entirely via group_exists(),
        # but using the assert_* call does give me the standardized exception
        # and error message when the group does not exist.
        assert_group_exists(self.session, group, DeletionPolicy.ANY)

        exists_result = group_exists(self.session, group)

        if exists_result is ExistenceResult.EXISTS:
            lock = GroupLock(GroupLockTypes.DELETE, group)
            self.session.add(lock)

    def get(
        self,
        group_id: int,
        deletion_policy: DeletionPolicy = DeletionPolicy.NOT_DELETED,
    ) -> Group | None:
        """
        Get a group by ID.

        Args:
            group_id: The ID of a group
            deletion_policy: Whether to look at deleted groups, non-deleted
                groups, or all groups

        Returns:
            The group, or None if one was not found
        """
        stmt = sa.select(Group).where(Group.group_id == group_id)
        stmt = _apply_deletion_policy(stmt, deletion_policy)

        group = self.session.scalar(stmt)

        return group

    def get_by_name(
        self, name: str, deletion_policy: DeletionPolicy = DeletionPolicy.NOT_DELETED
    ) -> Group | None:
        """
        Get a group by name.

        Args:
            name: a group name
            deletion_policy: Whether to look at deleted groups, non-deleted
                groups, or all groups

        Returns:
            A group, or None if one was not found
        """
        stmt = sa.select(Group).where(Group.name == name)
        stmt = _apply_deletion_policy(stmt, deletion_policy)

        # Shouldn't we either return a list or put a unique constraint on the
        # name column?
        group = self.session.scalar(stmt)

        return group

    def num_groups(
        self, deletion_policy: DeletionPolicy = DeletionPolicy.NOT_DELETED
    ) -> int:
        """
        Get the number of groups in the system.

        Args:
            deletion_policy: Whether to look at deleted groups, non-deleted
                groups, or all groups

        Returns:
            A group count
        """

        stmt = sa.select(sa.func.count()).select_from(Group)
        stmt = _apply_deletion_policy(stmt, deletion_policy)

        num_groups = self.session.scalar(stmt)

        # I don't see how "select count(*) ..." can return anything other than
        # an integer.
        assert num_groups is not None

        return num_groups

    def num_members(self, group: Group) -> int:
        """
        Get the number of members in the given group.  This is done in a way
        that's hopefully more efficient than len(group.members).

        Args:
            group: A group

        Returns:
            A member count

        Raises:
            Exception: if the group does not exist
        """

        assert_group_exists(self.session, group, DeletionPolicy.NOT_DELETED)

        # len(group.members) might require actually reading all the rows and
        # translating them into objects.  I hope to avoid that.
        num_members_stmt = (
            sa.select(sa.func.count())
            .select_from(GroupMember)
            .where(GroupMember.group_id == group.group_id)
        )

        num_members = self.session.scalar(num_members_stmt)

        # I don't see how "select count(*) ..." can return anything other than
        # an integer.
        assert num_members is not None

        return num_members

    def num_managers(self, group: Group) -> int:
        """
        Get the number of managers in the given group.  This is done in a way
        that's hopefully more efficient than len(group.managers).

        Args:
            group: A group

        Returns:
            A manager count

        Raises:
            Exception: if the group does not exist
        """

        assert_group_exists(self.session, group, DeletionPolicy.NOT_DELETED)

        # len(group.members) might require actually reading all the rows and
        # translating them into objects.  I hope to avoid that.
        num_members_stmt = (
            sa.select(sa.func.count())
            .select_from(GroupManager)
            .where(GroupManager.group_id == group.group_id)
        )

        num_managers = self.session.scalar(num_members_stmt)

        # I don't see how "select count(*) ..." can return anything other than
        # an integer.
        assert num_managers is not None

        return num_managers

    def add_manager(
        self, group: Group, user: User, owner: bool = False, admin: bool = False
    ) -> GroupManager:
        """
        Add a user to the managership of the given group.  If the user is
        already a manager, this is a no-op.  Permissions are ignored in that
        case.  To modify permissions for an existing manager, see
        UserRepository.set_manager_permissions().

        Args:
            group: A group
            user: A user
            owner: owner permission
            admin: admin permission

        Returns:
            The resulting GroupManager object (new or old)

        Raises:
            Exception: If the user or group do not exist, or if the user to
                be made manager is not a group member
        """

        # Consistency rule:
        # - a manager must be a member

        assert_group_exists(self.session, group, DeletionPolicy.NOT_DELETED)
        assert_user_exists(self.session, user, DeletionPolicy.NOT_DELETED)

        member = self.session.get(GroupMember, (user.user_id, group.group_id))
        if not member:
            raise Exception(
                f"Not a group member: user {user.user_id}/{user.username},"
                f" group {group.group_id}/{group.name}"
            )

        manager = self.session.get(GroupManager, (user.user_id, group.group_id))

        if not manager:
            manager = GroupManager(
                user=user,
                owner=owner,
                admin=admin,
            )
            group.managers.append(manager)

        return manager

    def remove_manager(self, group: Group, user: User) -> None:
        """
        Remove a manager of a group.  This is a no-op if the user is not a
        manager of the group.

        Args:
            group: A group
            user: A user

        Raises:
            Exception: if either user or group does not exist, or if removal
                would leave the group without any managers
        """

        # Consistency rule:
        # - a group must have at least one manager

        assert_group_exists(self.session, group, DeletionPolicy.NOT_DELETED)
        assert_user_exists(self.session, user, DeletionPolicy.NOT_DELETED)

        num_managers = self.num_managers(group)

        if num_managers == 1:
            if group.managers[0].user_id == user.user_id:
                raise Exception(
                    f"Can't remove user {user.user_id} from managers of group"
                    f" {group.group_id}: group would have no managers"
                )
            # else: the given user is not a manager of the group; nothing to do

        else:
            # else, num_managers ought to be > 1, unless we messed up somewhere
            # else
            manager = self.session.get(GroupManager, (user.user_id, group.group_id))
            if manager:
                self.session.delete(manager)

    def add_member(
        self,
        group: Group,
        user: User,
        read: bool = False,
        write: bool = False,
        share_read: bool = False,
        share_write: bool = False,
    ) -> GroupMember:
        """
        Add a user to the membership of the given group.  If the user is
        already a member, this is a no-op.  Permissions are ignored in that
        case.  To modify permissions for an existing member, see
        UserRepository.set_member_permissions().

        Args:
            group: A group
            user: A user
            read: read permission
            write: write permission
            share_read: share_read permission
            share_write: share_write permission

        Returns:
            The resulting GroupMember object (new or old)

        Raises:
            Exception: If the user or group do not exist
        """

        assert_group_exists(self.session, group, DeletionPolicy.NOT_DELETED)
        assert_user_exists(self.session, user, DeletionPolicy.NOT_DELETED)

        member = self.session.get(GroupMember, (user.user_id, group.group_id))

        if not member:
            member = GroupMember(
                read=read,
                write=write,
                share_read=share_read,
                share_write=share_write,
                user=user,
            )
            group.members.append(member)

        return member

    def remove_member(self, group: Group, user: User) -> None:
        """
        Remove a user from a group.  This is a no-op if the user is not a
        member of the group.

        Args:
            group: A group
            user: A user

        Raises:
            Exception: if either the user or group does not exist, or if
                removal would leave either the group userless or the user
                groupless.
        """

        # Consistency rules:
        # - A group must have at least one member
        # - A user must be in at least one group

        assert_group_exists(self.session, group, DeletionPolicy.NOT_DELETED)
        assert_user_exists(self.session, user, DeletionPolicy.NOT_DELETED)

        num_members = self.num_members(group)

        if num_members == 1:
            if group.members[0].user_id == user.user_id:
                raise Exception(
                    f"Can't remove user {user.user_id} from group"
                    f" {group.group_id}: group would have no members"
                )
            # else: the given user is not in the group; nothing to do
        else:

            # Group has more than one user, so we won't violate that
            # consistency rule.  But does user belong to any other groups?
            num_groups_stmt = (
                sa.select(sa.func.count())
                .select_from(GroupMember)
                .where(GroupMember.user_id == user.user_id)
            )
            num_groups = self.session.scalar(num_groups_stmt)

            if num_groups == 1:
                if user.group_memberships[0].group_id == group.group_id:
                    raise Exception(
                        f"Can't remove user {user.user_id} from group"
                        f" {group.group_id}: user would belong to no groups"
                    )
                # else: the given user is not in the group; nothing to do
            else:

                # User has more than one group membership, so we are free to
                # remove them from this group.
                member = self.session.get(GroupMember, (user.user_id, group.group_id))
                if member:
                    self.session.delete(member)


def _apply_deletion_policy(
    stmt: sa.Select, deletion_policy: DeletionPolicy
) -> sa.Select:
    """
    Factored out code to add a WHERE clause to a select statement to apply
    deletion policy to it, affecting whether deleted groups are searched.

    Args:
        stmt: A select statement to modify
        deletion_policy: The policy to apply

    Returns:
        A modified select statement
    """
    if deletion_policy is DeletionPolicy.NOT_DELETED:
        stmt = stmt.where(Group.is_deleted == False)  # noqa: E712
    elif deletion_policy is DeletionPolicy.DELETED:
        stmt = stmt.where(Group.is_deleted == True)  # noqa: E712

    return stmt
