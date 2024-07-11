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
import uuid

import pytest

from dioptra.restapi.db.models import Group, GroupMember, User
from dioptra.restapi.db.repository.errors import (
    UserEmailNotAvailableError,
    UsernameNotAvailableError,
)
from dioptra.restapi.db.repository.utils import DeletionPolicy, assert_user_exists


def test_user_create(user_repo, account, db):
    u2 = User("user2", "password2", "user2@example.org")

    user_repo.create(u2, account.group, read=True, share_read=True)
    db.session.commit()

    assert_user_exists(db.session, u2, DeletionPolicy.NOT_DELETED)

    membership = db.session.get(GroupMember, (u2.user_id, account.group.group_id))
    assert membership.read
    assert not membership.write
    assert membership.share_read
    assert not membership.share_write


def test_user_create_group_not_exist(user_repo, account, db):
    u2 = User("user2", "password2", "user2@example.org")
    g2 = Group("group2", u2)

    with pytest.raises(Exception):
        user_repo.create(u2, g2)


def test_user_create_user_already_exists(user_repo, account, db):
    with pytest.raises(Exception):
        user_repo.create(account.user, account.group)


def test_user_create_collision(user_repo, account):

    user_colliding_name = User(account.user.username, "password2", "user2@example.org")
    with pytest.raises(UsernameNotAvailableError):
        user_repo.create(user_colliding_name, account.group)

    user_colliding_email = User("user2", "password2", account.user.email_address)
    with pytest.raises(UserEmailNotAvailableError):
        user_repo.create(user_colliding_email, account.group)


def test_user_delete(user_repo, account, db):
    user_repo.delete(account.user)
    db.session.commit()

    user = user_repo.get(account.user.user_id, DeletionPolicy.ANY)
    assert user.is_deleted

    # should be a no-op
    user_repo.delete(account.user)


def test_user_delete_not_exists(user_repo, account):

    u2 = User("user2", "password2", "user2@example.org")
    with pytest.raises(Exception):
        user_repo.delete(u2)


def test_user_get(user_repo, account):
    user = user_repo.get(account.user.user_id, DeletionPolicy.NOT_DELETED)
    assert user == account.user

    user = user_repo.get(account.user.user_id, DeletionPolicy.DELETED)
    assert not user

    user = user_repo.get(account.user.user_id, DeletionPolicy.ANY)
    assert user == account.user


def test_user_get_deleted(user_repo, account, db):
    # Deletes the only user; may break in the future if that violates a
    # consistency rule.  We might have to create more users, so we can delete
    # one.
    user_repo.delete(account.user)
    db.session.commit()

    user = user_repo.get(account.user.user_id, DeletionPolicy.NOT_DELETED)
    assert not user

    user = user_repo.get(account.user.user_id, DeletionPolicy.DELETED)
    assert user == account.user

    user = user_repo.get(account.user.user_id, DeletionPolicy.ANY)
    assert user == account.user


def test_user_get_not_exist(user_repo, account):
    user = user_repo.get(999999, DeletionPolicy.NOT_DELETED)
    assert not user

    user = user_repo.get(999999, DeletionPolicy.DELETED)
    assert not user

    user = user_repo.get(999999, DeletionPolicy.ANY)
    assert not user


def test_user_get_by_name(user_repo, account):
    user = user_repo.get_by_name(account.user.username, DeletionPolicy.ANY)
    assert user == account.user
    assert not user.is_deleted

    user = user_repo.get_by_name(account.user.username, DeletionPolicy.NOT_DELETED)
    assert user == account.user
    assert not user.is_deleted

    user = user_repo.get_by_name(account.user.username, DeletionPolicy.DELETED)
    assert not user


def test_user_get_by_name_deleted(user_repo, account, db):
    # Deletes the only user; may break in the future if that violates a
    # consistency rule.  We might have to create more users, so we can delete
    # one.
    user_repo.delete(account.user)
    db.session.commit()

    user = user_repo.get_by_name(account.user.username, DeletionPolicy.ANY)
    assert user == account.user
    assert user.is_deleted

    user = user_repo.get_by_name(account.user.username, DeletionPolicy.NOT_DELETED)
    assert not user

    user = user_repo.get_by_name(account.user.username, DeletionPolicy.DELETED)
    assert user == account.user
    assert user.is_deleted


def test_user_get_by_name_not_exist(user_repo, account):

    user = user_repo.get_by_name("foo", DeletionPolicy.ANY)
    assert not user

    user = user_repo.get_by_name("foo", DeletionPolicy.NOT_DELETED)
    assert not user

    user = user_repo.get_by_name("foo", DeletionPolicy.DELETED)
    assert not user


def test_user_get_by_alternative_id(user_repo, account):
    user = user_repo.get_by_alternative_id(
        account.user.alternative_id, DeletionPolicy.ANY
    )
    assert user == account.user
    assert not user.is_deleted

    user = user_repo.get_by_alternative_id(
        account.user.alternative_id, DeletionPolicy.NOT_DELETED
    )
    assert user == account.user
    assert not user.is_deleted

    user = user_repo.get_by_alternative_id(
        account.user.alternative_id, DeletionPolicy.DELETED
    )
    assert not user


def test_user_get_by_alternative_id_deleted(user_repo, account, db):
    # Deletes the only user; may break in the future if that violates a
    # consistency rule.  We might have to create more users, so we can delete
    # one.
    user_repo.delete(account.user)
    db.session.commit()

    user = user_repo.get_by_alternative_id(
        account.user.alternative_id, DeletionPolicy.ANY
    )
    assert user == account.user
    assert user.is_deleted

    user = user_repo.get_by_alternative_id(
        account.user.alternative_id, DeletionPolicy.NOT_DELETED
    )
    assert not user

    user = user_repo.get_by_alternative_id(
        account.user.alternative_id, DeletionPolicy.DELETED
    )
    assert user == account.user
    assert user.is_deleted


def test_user_get_by_alternative_id_not_exist(user_repo, account):
    rnd_uuid = uuid.uuid4()
    user = user_repo.get_by_alternative_id(rnd_uuid, DeletionPolicy.ANY)
    assert not user

    user = user_repo.get_by_alternative_id(rnd_uuid, DeletionPolicy.NOT_DELETED)
    assert not user

    user = user_repo.get_by_alternative_id(rnd_uuid, DeletionPolicy.DELETED)
    assert not user


def test_user_get_by_email(user_repo, account):
    user = user_repo.get_by_email(account.user.email_address, DeletionPolicy.ANY)
    assert user == account.user
    assert not user.is_deleted

    user = user_repo.get_by_email(
        account.user.email_address, DeletionPolicy.NOT_DELETED
    )
    assert user == account.user
    assert not user.is_deleted

    user = user_repo.get_by_email(account.user.email_address, DeletionPolicy.DELETED)
    assert not user


def test_user_get_by_email_deleted(user_repo, account, db):
    # Deletes the only user; may break in the future if that violates a
    # consistency rule.  We might have to create more users, so we can delete
    # one.
    user_repo.delete(account.user)
    db.session.commit()

    user = user_repo.get_by_email(account.user.email_address, DeletionPolicy.ANY)
    assert user == account.user
    assert user.is_deleted

    user = user_repo.get_by_email(
        account.user.email_address, DeletionPolicy.NOT_DELETED
    )
    assert not user

    user = user_repo.get_by_email(account.user.email_address, DeletionPolicy.DELETED)
    assert user == account.user
    assert user.is_deleted


def test_user_get_by_email_not_exist(user_repo, account):
    user = user_repo.get_by_email("no-exist@bar.net", DeletionPolicy.ANY)
    assert not user

    user = user_repo.get_by_email("no-exist@bar.net", DeletionPolicy.NOT_DELETED)
    assert not user

    user = user_repo.get_by_email("no-exist@bar.net", DeletionPolicy.DELETED)
    assert not user


def test_user_num_users(user_repo, account, db):

    # Add some more users and delete one
    u2 = User("user2", "password2", "user2@example.org")
    u3 = User("user3", "password3", "user3@example.org")
    user_repo.create(u2, account.group)
    user_repo.create(u3, account.group)

    user_repo.delete(account.user)
    db.session.commit()

    num_total = user_repo.num_users(DeletionPolicy.ANY)
    assert num_total == 3

    num_non_deleted = user_repo.num_users(DeletionPolicy.NOT_DELETED)
    assert num_non_deleted == 2

    num_deleted = user_repo.num_users(DeletionPolicy.DELETED)
    assert num_deleted == 1


def test_user_num_users_no_users(user_repo):
    num_users = user_repo.num_users(DeletionPolicy.ANY)
    assert num_users == 0

    num_users = user_repo.num_users(DeletionPolicy.NOT_DELETED)
    assert num_users == 0

    num_users = user_repo.num_users(DeletionPolicy.DELETED)
    assert num_users == 0


def test_user_get_page(user_repo, account, db):

    users = [account.user]
    # Make a bunch of users
    for n in range(10):
        user = User(f"user{n}", f"password{n}", f"user{n}@example.org")
        users.append(user)
        user_repo.create(user, account.group)
    db.session.commit()

    # Current sort order is by user_id, which automatically increments, so the
    # users ought to come out in the pages in the same order they were
    # inserted.  If we change sort order, this will change.

    # Unsure sqlalchemy always returns lists... just gather from its sequences
    # into lists, to make sure we can compare them.
    page = list(user_repo.get_page(0, 3))
    assert page == users[:3]

    page = list(user_repo.get_page(1, 4))
    assert page == users[1:5]

    page = list(user_repo.get_page(8, 5))
    assert page == users[8:]

    page = list(user_repo.get_page(20, 20))
    assert page == []

    page = list(user_repo.get_page(0, 0))
    assert page == users


def test_user_get_page_deleted(user_repo, account, db):

    users = [account.user]
    # Make a bunch of users
    for n in range(10):
        user = User(f"user{n}", f"password{n}", f"user{n}@example.org")
        users.append(user)
        user_repo.create(user, account.group)
    db.session.commit()

    # Delete some
    user_repo.delete(users[2])
    user_repo.delete(users[6])
    user_repo.delete(users[8])
    db.session.commit()

    # Current sort order is by user_id, which automatically increments, so the
    # users ought to come out in the pages in the same order they were
    # inserted.  If we change sort order, this will change.

    # Unsure sqlalchemy always returns lists... just gather from its sequences
    # into lists, to make sure we can compare them.
    page = list(user_repo.get_page(0, 3, DeletionPolicy.NOT_DELETED))
    assert page == [users[0], users[1], users[3]]

    page = list(user_repo.get_page(0, 3, DeletionPolicy.DELETED))
    assert page == [users[2], users[6], users[8]]

    page = list(user_repo.get_page(0, 3, DeletionPolicy.ANY))
    assert page == users[:3]


def test_user_get_member_permissions(user_repo, account, db):
    u2 = User("user2", "password2", "user2@example.org")
    user_repo.create(
        u2, account.group, read=True, write=False, share_read=False, share_write=True
    )
    db.session.commit()

    perms = user_repo.get_member_permissions(u2, account.group)
    assert perms.read
    assert not perms.write
    assert not perms.share_read
    assert perms.share_write


def test_user_get_member_permissions_not_exist(user_repo, account):
    u2 = User("user2", "password2", "user2@example.org")
    g2 = Group("group2", u2)

    with pytest.raises(Exception):
        user_repo.get_member_permissions(u2, account.group)

    with pytest.raises(Exception):
        user_repo.get_member_permissions(account.user, g2)

    with pytest.raises(Exception):
        user_repo.get_member_permissions(u2, g2)


def test_user_get_manager_permissions(user_repo, account):

    mgr = user_repo.get_manager_permissions(account.user, account.group)

    assert mgr.user == account.user
    assert mgr.group == account.group
    assert mgr.admin
    assert mgr.owner


def test_user_get_manager_permissions_not_exist(user_repo, account):
    u2 = User("user2", "password2", "user2@example.org")
    g2 = Group("group2", u2)

    with pytest.raises(Exception):
        user_repo.get_manager_permissions(u2, account.group)

    with pytest.raises(Exception):
        user_repo.get_manager_permissions(account.user, g2)


def test_user_get_manager_permissions_not_manager(user_repo, account, db):
    u2 = User("user2", "password2", "user2@example.org")
    user_repo.create(u2, account.group)
    db.session.commit()

    mgr = user_repo.get_manager_permissions(u2, account.group)

    assert not mgr


def test_user_set_member_permissions(user_repo, account, db):

    user_repo.set_member_permissions(
        account.user,
        account.group,
        read=True,
        write=False,
        share_read=False,
        share_write=True,
    )
    db.session.commit()

    membership = user_repo.get_member_permissions(account.user, account.group)
    assert membership.read
    assert not membership.write
    assert not membership.share_read
    assert membership.share_write

    # Leave some perms None and ensure they don't change
    user_repo.set_member_permissions(
        account.user, account.group, read=False, share_read=True
    )
    db.session.commit()

    membership = user_repo.get_member_permissions(account.user, account.group)
    assert not membership.read
    assert not membership.write
    assert membership.share_read
    assert membership.share_write


def test_user_set_member_permissions_membership_not_exist(
    user_repo, group_repo, account, db
):

    u2 = User("user2", "password2", "user2@example.org")
    g2 = Group("group2", u2)
    group_repo.create(g2)
    db.session.commit()

    with pytest.raises(Exception):
        user_repo.set_member_permissions(
            u2,
            account.group,
            read=False,
            write=True,
            share_read=True,
            share_write=False,
        )


def test_user_set_member_permissions_user_group_not_exist(user_repo, account):

    u2 = User("user2", "password2", "user2@example.org")
    g2 = Group("group2", u2)

    with pytest.raises(Exception):
        user_repo.set_member_permissions(u2, account.group)

    with pytest.raises(Exception):
        user_repo.set_member_permissions(account.user, g2)


def test_user_set_manager_permissions(user_repo, account, db):

    user_repo.set_manager_permissions(
        account.user, account.group, owner=False, admin=True
    )
    db.session.commit()

    manager = user_repo.get_manager_permissions(account.user, account.group)

    assert not manager.owner
    assert manager.admin

    # Leave some perms None and ensure they don't change
    user_repo.set_manager_permissions(account.user, account.group, admin=False)
    db.session.commit()

    manager = user_repo.get_manager_permissions(account.user, account.group)

    assert not manager.owner
    assert not manager.admin


def test_user_set_manager_permissions_managership_not_exist(user_repo, account, db):

    # u2 is a regular member, not a manager
    u2 = User("user2", "password2", "user2@example.org")
    user_repo.create(u2, account.group)
    db.session.commit()

    with pytest.raises(Exception):
        user_repo.set_manager_permissions(u2, account.group)


def test_user_set_manager_permissions_user_group_not_exist(user_repo, account):

    u2 = User("user2", "password2", "user2@example.org")
    g2 = Group("group2", u2)

    with pytest.raises(Exception):
        user_repo.set_manager_permissions(u2, account.group)

    with pytest.raises(Exception):
        user_repo.set_manager_permissions(account.user, g2)
