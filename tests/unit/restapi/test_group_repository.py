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
import pytest
from sqlalchemy.orm.session import Session as DBSession

from dioptra.restapi.db.models import Group, GroupMember, User
from dioptra.restapi.db.repository.utils import DeletionPolicy
from dioptra.restapi.errors import (
    EntityDeletedError,
    EntityDoesNotExistError,
    EntityExistsError,
    GroupNeedsAManagerError,
    GroupNeedsAUserError,
    UserIsManagerError,
    UserNeedsAGroupError,
    UserNotInGroupError,
)


def test_group_create_with_existing_user(group_repo, account, db_session: DBSession):

    group = Group("initial_group", account.user)

    group_repo.create(group)

    db_session.commit()

    check_group = db_session.get_one(Group, group.group_id)
    check_user = db_session.get_one(User, account.user.user_id)

    assert check_group == group
    assert check_user == account.user
    assert len(check_group.members) == 1

    member_perms = check_group.members[0]
    assert member_perms.user == account.user
    assert member_perms.read
    assert member_perms.write
    assert member_perms.share_read
    assert member_perms.share_write


def test_group_create_with_new_user(group_repo, db_session: DBSession):

    creator = User("creator_username", "password", "creator@example.org")
    group = Group("initial_group", creator)

    group_repo.create(group)

    db_session.commit()

    check_group = db_session.get_one(Group, group.group_id)
    check_user = db_session.get_one(User, creator.user_id)

    assert check_group == group
    assert check_user == creator
    assert len(check_group.members) == 1

    member_perms = check_group.members[0]
    assert member_perms.user == creator
    assert member_perms.read
    assert member_perms.write
    assert member_perms.share_read
    assert member_perms.share_write


def test_group_create_exists(group_repo, account):

    with pytest.raises(EntityExistsError):
        group_repo.create(account.group)

    # A similar test: create a new group object but set its ID to a
    # value which has already been used.
    new_group = Group("new group", account.user)
    new_group.group_id = account.group.group_id
    with pytest.raises(EntityExistsError):
        group_repo.create(new_group)


def test_group_create_user_exists(group_repo, account, db_session: DBSession):

    group = Group("new group", account.user)
    group_repo.create(group)
    db_session.commit()

    assert len(group.members) == 1
    assert group.members[0].user == account.user
    assert group.creator == account.user


def test_group_create_name_collision(group_repo, account):
    g2 = Group(account.group.name, account.user)

    with pytest.raises(EntityExistsError):
        group_repo.create(g2)


def test_group_create_creator_collision(group_repo, account):
    user_colliding_name = User(account.user.username, "password2", "user2@example.org")
    g2 = Group("group2", user_colliding_name)
    with pytest.raises(EntityExistsError):
        group_repo.create(g2)

    user_colliding_email = User("user2", "password2", account.user.email_address)
    g2 = Group("group2", user_colliding_email)
    with pytest.raises(EntityExistsError):
        group_repo.create(g2)


def test_group_create_creator_deleted(
    group_repo, user_repo, account, db_session: DBSession
):

    u2 = User("creator_username", "password", "creator@example.org")
    user_repo.create(u2, account.group)
    db_session.commit()

    user_repo.delete(u2)
    db_session.commit()

    g2 = Group("group2", u2)
    with pytest.raises(EntityDeletedError):
        group_repo.create(g2)


def test_group_delete(group_repo, account, db_session: DBSession):
    group_repo.delete(account.group)
    db_session.commit()
    assert account.group.is_deleted

    # Should be a no-op the second time
    group_repo.delete(account.group)
    assert account.group.is_deleted


def test_group_delete_not_exist(group_repo):
    u2 = User("user2", "password2", "user2@example.org")
    g2 = Group("group2", u2)

    with pytest.raises(EntityDoesNotExistError):
        group_repo.delete(g2)


def test_group_get(group_repo, account):

    group = group_repo.get(account.group.group_id, DeletionPolicy.NOT_DELETED)
    assert group == account.group

    group = group_repo.get(account.group.group_id, DeletionPolicy.DELETED)
    assert not group

    group = group_repo.get(account.group.group_id, DeletionPolicy.ANY)
    assert group == account.group


def test_group_get_deleted(group_repo, account, db_session: DBSession):
    group_repo.delete(account.group)
    db_session.commit()

    group = group_repo.get(account.group.group_id, DeletionPolicy.NOT_DELETED)
    assert not group

    group = group_repo.get(account.group.group_id, DeletionPolicy.DELETED)
    assert group == account.group

    group = group_repo.get(account.group.group_id, DeletionPolicy.ANY)
    assert group == account.group


def test_group_get_not_exist(group_repo, account):

    group = group_repo.get(999999, DeletionPolicy.NOT_DELETED)
    assert not group

    group = group_repo.get(999999, DeletionPolicy.DELETED)
    assert not group

    group = group_repo.get(999999, DeletionPolicy.ANY)
    assert not group


def test_group_get_one(group_repo, account):

    group = group_repo.get_one(account.group.group_id, DeletionPolicy.NOT_DELETED)
    assert group == account.group

    with pytest.raises(EntityExistsError):
        group_repo.get_one(account.group.group_id, DeletionPolicy.DELETED)

    group = group_repo.get_one(account.group.group_id, DeletionPolicy.ANY)
    assert group == account.group


def test_group_get_one_deleted(group_repo, account, db_session: DBSession):
    group_repo.delete(account.group)
    db_session.commit()

    with pytest.raises(EntityDeletedError):
        group_repo.get_one(account.group.group_id, DeletionPolicy.NOT_DELETED)

    group = group_repo.get_one(account.group.group_id, DeletionPolicy.DELETED)
    assert group == account.group

    group = group_repo.get_one(account.group.group_id, DeletionPolicy.ANY)
    assert group == account.group


def test_group_get_one_not_exist(group_repo):

    with pytest.raises(EntityDoesNotExistError):
        group_repo.get_one(999999, DeletionPolicy.NOT_DELETED)

    with pytest.raises(EntityDoesNotExistError):
        group_repo.get_one(999999, DeletionPolicy.DELETED)

    with pytest.raises(EntityDoesNotExistError):
        group_repo.get_one(999999, DeletionPolicy.ANY)


def test_group_get_by_name(group_repo, account):

    group = group_repo.get_by_name(account.group.name, DeletionPolicy.NOT_DELETED)
    assert group == account.group

    group = group_repo.get_by_name(account.group.name, DeletionPolicy.DELETED)
    assert not group

    group = group_repo.get_by_name(account.group.name, DeletionPolicy.ANY)
    assert group == account.group


def test_group_get_by_name_deleted(group_repo, account, db_session: DBSession):
    group_repo.delete(account.group)
    db_session.commit()

    group = group_repo.get_by_name(account.group.name, DeletionPolicy.NOT_DELETED)
    assert not group

    group = group_repo.get_by_name(account.group.name, DeletionPolicy.DELETED)
    assert group == account.group

    group = group_repo.get_by_name(account.group.name, DeletionPolicy.ANY)
    assert group == account.group


def test_group_get_by_name_not_exist(group_repo, account, db_session: DBSession):

    group = group_repo.get_by_name("foo", DeletionPolicy.NOT_DELETED)
    assert not group

    group = group_repo.get_by_name("foo", DeletionPolicy.DELETED)
    assert not group

    group = group_repo.get_by_name("foo", DeletionPolicy.ANY)
    assert not group


def test_group_num_groups(group_repo, account, db_session: DBSession):

    g2 = Group("group2", account.user)
    g3 = Group("group3", account.user)
    group_repo.create(g2)
    group_repo.create(g3)
    db_session.commit()

    group_repo.delete(g3)
    db_session.commit()

    assert group_repo.num_groups(DeletionPolicy.ANY) == 3
    assert group_repo.num_groups(DeletionPolicy.NOT_DELETED) == 2
    assert group_repo.num_groups(DeletionPolicy.DELETED) == 1


def test_group_num_members(group_repo, user_repo, account, db_session: DBSession):

    assert group_repo.num_members(account.group) == 1
    assert group_repo.num_members(account.group.group_id) == 1

    u2 = User("user2", "password2", "user2@example.org")
    user_repo.create(u2, account.group)
    db_session.commit()

    group_repo.add_member(account.group, u2)
    db_session.commit()

    assert group_repo.num_members(account.group) == 2
    assert group_repo.num_members(account.group.group_id) == 2


def test_group_num_members_not_exist(group_repo, account):
    g2 = Group("group2", account.user)

    with pytest.raises(EntityDoesNotExistError):
        group_repo.num_members(g2)


def test_group_num_managers(group_repo, user_repo, account, db_session: DBSession):

    assert group_repo.num_managers(account.group) == 1
    assert group_repo.num_managers(account.group.group_id) == 1

    u2 = User("user2", "password2", "user2@example.org")
    user_repo.create(u2, account.group)
    db_session.commit()

    group_repo.add_manager(account.group, u2)
    db_session.commit()

    assert group_repo.num_managers(account.group) == 2
    assert group_repo.num_managers(account.group.group_id) == 2


def test_group_num_managers_not_exist(group_repo, account):
    g2 = Group("group2", account.user)

    with pytest.raises(EntityDoesNotExistError):
        group_repo.num_managers(g2)


def test_group_add_manager(group_repo, user_repo, account, db_session: DBSession):
    u2 = User("user2", "password2", "user2@example.org")
    user_repo.create(u2, account.group)
    db_session.commit()

    group_repo.add_manager(account.group, u2, admin=True)

    mgr = user_repo.get_manager_permissions(u2, account.group)

    assert mgr
    assert mgr.user == u2
    assert mgr.group == account.group
    assert not mgr.owner
    assert mgr.admin

    # add a second time: should be a no-op; permissions ignored
    group_repo.add_manager(account.group, u2, admin=False)
    mgr = user_repo.get_manager_permissions(u2, account.group)
    assert mgr.admin


def test_group_add_manager_not_exist(group_repo, account):
    u2 = User("user2", "password2", "user2@example.org")
    g2 = Group("group2", u2)

    with pytest.raises(EntityDoesNotExistError):
        group_repo.add_manager(g2, account.user)

    with pytest.raises(EntityDoesNotExistError):
        group_repo.add_manager(account.group, u2)


def test_group_add_manager_not_member(group_repo, account, db_session: DBSession):
    u2 = User("user2", "password2", "user2@example.org")
    g2 = Group("group2", u2)
    group_repo.create(g2)
    db_session.commit()

    # user2 is in group2, not account.group
    with pytest.raises(UserNotInGroupError):
        group_repo.add_manager(account.group, u2)


def test_group_remove_manager_one_group_one_manager(group_repo, account):

    with pytest.raises(GroupNeedsAManagerError):
        group_repo.remove_manager(account.group, account.user)


def test_group_remove_manager_non_member(group_repo, account, db_session: DBSession):
    u2 = User("user2", "password2", "user2@example.org")
    g2 = Group("group2", u2)
    group_repo.create(g2)
    db_session.commit()

    # u2 not a member/manager; so this is a no-op
    group_repo.remove_manager(account.group, u2)


def test_group_remove_manager_ok(group_repo, user_repo, account, db_session: DBSession):
    u2 = User("user2", "password2", "user2@example.org")
    user_repo.create(u2, account.group)
    db_session.commit()

    group_repo.add_manager(account.group, u2)
    db_session.commit()

    # Two managers, one group: we should be able to delete a manager now
    group_repo.remove_manager(account.group, account.user)
    db_session.commit()

    assert group_repo.num_managers(account.group) == 1
    assert account.group.managers[0].user == u2


def test_group_remove_manager_not_exist(group_repo, account):
    u2 = User("user2", "password2", "user2@example.org")
    g2 = Group("group2", u2)

    with pytest.raises(EntityDoesNotExistError):
        group_repo.remove_manager(account.group, u2)

    with pytest.raises(EntityDoesNotExistError):
        group_repo.remove_manager(g2, account.user)


def test_group_add_member(group_repo, account, db_session: DBSession):
    u2 = User("user2", "password2", "user2@example.org")
    g2 = Group("group2", u2)
    group_repo.create(g2)
    db_session.commit()

    group_repo.add_member(
        account.group, u2, read=True, write=False, share_read=False, share_write=True
    )
    db_session.commit()

    assert len(account.group.members) == 2
    assert any(member.user_id == u2.user_id for member in account.group.members)

    # Do it again; should be a no-op
    group_repo.add_member(account.group, u2)

    membership = db_session.get(GroupMember, (u2.user_id, account.group.group_id))
    assert membership.read
    assert not membership.write
    assert not membership.share_read
    assert membership.share_write


def test_group_add_member_not_exist(group_repo, account):
    u2 = User("user2", "password2", "user2@example.org")
    g2 = Group("group2", u2)

    with pytest.raises(EntityDoesNotExistError):
        group_repo.add_member(g2, account.user)

    with pytest.raises(EntityDoesNotExistError):
        group_repo.add_member(account.group, u2)


def test_group_remove_member_one_group_one_user(
    group_repo, account, db_session: DBSession
):

    with pytest.raises(GroupNeedsAUserError):
        group_repo.remove_member(account.group, account.user)


def test_group_remove_member_group_too_small(
    group_repo, account, db_session: DBSession
):

    g2 = Group("group2", account.user)
    group_repo.create(g2)
    db_session.commit()

    # Now, member is in two groups, but can't be removed from either since it
    # would make the groups empty.
    with pytest.raises(GroupNeedsAUserError):
        group_repo.remove_member(account.group, account.user)


def test_group_remove_member_too_few_memberships(
    group_repo, account, db_session: DBSession
):

    # Add a second member to the group
    u2 = User("user2", "password2", "user2@example.org")
    account.group.members.append(
        GroupMember(read=True, write=True, share_read=True, share_write=True, user=u2)
    )

    db_session.add(u2)
    db_session.commit()

    # now, the group has enough members, but neither user has enough
    # memberships for them to be removable from the group.

    with pytest.raises(UserNeedsAGroupError):
        group_repo.remove_member(account.group, account.user)


def test_group_remove_member_non_member(
    group_repo, account, db_session: DBSession, fake_data
):
    account2 = fake_data.account()
    db_session.add_all((account2.group, account2.user))
    db_session.commit()

    # Should be no-ops
    group_repo.remove_member(account2.group, account.user)
    group_repo.remove_member(account.group, account2.user)


def test_group_remove_member_ok(group_repo, account, db_session: DBSession, fake_data):
    account2 = fake_data.account()

    account2.group.members.append(
        GroupMember(
            read=True, write=True, share_read=True, share_write=True, user=account.user
        )
    )

    account.group.members.append(
        GroupMember(
            read=True, write=True, share_read=True, share_write=True, user=account2.user
        )
    )

    db_session.add_all((account2.user, account2.group))
    db_session.commit()

    # Two users in two groups; we should now be able to remove a non-manager
    # user.

    group_repo.remove_member(account.group, account2.user)
    db_session.commit()

    check_member = db_session.get(
        GroupMember, (account2.user.user_id, account.group.group_id)
    )
    assert check_member is None
    assert not any(
        member.user_id == account2.user.user_id for member in account.group.members
    )
    assert len(account.group.members) == 1
    assert len(account2.group.members) == 2


def test_group_remove_member_manager(
    group_repo, account, db_session: DBSession, fake_data
):
    account2 = fake_data.account()

    account2.group.members.append(
        GroupMember(
            read=True, write=True, share_read=True, share_write=True, user=account.user
        )
    )

    account.group.members.append(
        GroupMember(
            read=True, write=True, share_read=True, share_write=True, user=account2.user
        )
    )

    db_session.add_all((account2.user, account2.group))
    db_session.commit()

    # Two users in two groups; we can remove non-manager members, but we should
    # not be able to remove manager members.

    with pytest.raises(UserIsManagerError):
        group_repo.remove_member(account.group, account.user)


def test_group_remove_member_not_exist(group_repo, account):
    u2 = User("user2", "password2", "user2@example.org")
    g2 = Group("group2", u2)

    with pytest.raises(EntityDoesNotExistError):
        group_repo.remove_member(account.group, u2)

    with pytest.raises(EntityDoesNotExistError):
        group_repo.remove_member(g2, account.user)
