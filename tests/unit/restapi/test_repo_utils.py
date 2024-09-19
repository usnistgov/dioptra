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

import dioptra.restapi.db.models as models
import dioptra.restapi.db.repository.utils as utils
from dioptra.restapi.db.models.constants import resource_lock_types
from dioptra.restapi.db.shared_errors import (
    ResourceDeletedError, ResourceExistsError, ResourceNotFoundError
)


def test_user_exists(db, account):
    result = utils.user_exists(db.session, account.user)

    assert result == utils.ExistenceResult.EXISTS


def test_user_not_exists(db, account):
    user2 = models.User("user2", "password2", "user2@example.org")
    result = utils.user_exists(db.session, user2)

    assert result == utils.ExistenceResult.DOES_NOT_EXIST

    # Also try with bad ID
    user2.user_id = 999999
    result = utils.user_exists(db.session, user2)

    assert result == utils.ExistenceResult.DOES_NOT_EXIST


def test_user_deleted(db, account):
    user2 = models.User("user2", "password2", "user2@example.org")
    user_delete_lock = models.UserLock("delete", user2)
    db.session.add_all((user2, user_delete_lock))
    db.session.commit()

    result = utils.user_exists(db.session, user2)
    assert result == utils.ExistenceResult.DELETED


def test_assert_user_exists(db, account):
    utils.assert_user_exists(db.session, account.user, utils.DeletionPolicy.NOT_DELETED)
    utils.assert_user_exists(db.session, account.user, utils.DeletionPolicy.ANY)

    with pytest.raises(Exception):
        utils.assert_user_exists(db.session, account.user, utils.DeletionPolicy.DELETED)


def test_assert_user_exists_not_exists(db, account):
    user2 = models.User("user2", "password2", "user2@example.org")

    with pytest.raises(Exception):
        utils.assert_user_exists(db.session, user2, utils.DeletionPolicy.NOT_DELETED)

    with pytest.raises(Exception):
        utils.assert_user_exists(db.session, user2, utils.DeletionPolicy.DELETED)

    with pytest.raises(Exception):
        utils.assert_user_exists(db.session, user2, utils.DeletionPolicy.ANY)

    # Also try with bad ID
    user2.user_id = 999999

    with pytest.raises(Exception):
        utils.assert_user_exists(db.session, user2, utils.DeletionPolicy.NOT_DELETED)

    with pytest.raises(Exception):
        utils.assert_user_exists(db.session, user2, utils.DeletionPolicy.DELETED)

    with pytest.raises(Exception):
        utils.assert_user_exists(db.session, user2, utils.DeletionPolicy.ANY)


def test_assert_user_exists_deleted(db, account):
    user2 = models.User("user2", "password2", "user2@example.org")
    user_delete_lock = models.UserLock("delete", user2)
    db.session.add_all((user2, user_delete_lock))
    db.session.commit()

    with pytest.raises(Exception):
        utils.assert_user_exists(db.session, user2, utils.DeletionPolicy.NOT_DELETED)

    utils.assert_user_exists(db.session, user2, utils.DeletionPolicy.DELETED)
    utils.assert_user_exists(db.session, user2, utils.DeletionPolicy.ANY)


def test_group_exists(db, account):
    result = utils.group_exists(db.session, account.group)

    assert result == utils.ExistenceResult.EXISTS


def test_group_not_exists(db, account):
    user2 = models.User("user2", "password2", "user2@example.org")
    group2 = models.Group("group2", user2)

    result = utils.group_exists(db.session, group2)

    assert result == utils.ExistenceResult.DOES_NOT_EXIST

    # Also try with bad ID
    group2.group_id = 999999
    result = utils.group_exists(db.session, group2)

    assert result == utils.ExistenceResult.DOES_NOT_EXIST


def test_group_deleted(db, account):
    user2 = models.User("user2", "password2", "user2@example.org")
    group2 = models.Group("group2", user2)
    group_delete_lock = models.GroupLock("delete", group2)
    db.session.add_all((user2, group2, group_delete_lock))
    db.session.commit()

    result = utils.group_exists(db.session, group2)
    assert result == utils.ExistenceResult.DELETED


def test_assert_group_exists(db, account):
    utils.assert_group_exists(
        db.session, account.group, utils.DeletionPolicy.NOT_DELETED
    )
    utils.assert_group_exists(db.session, account.group, utils.DeletionPolicy.ANY)

    with pytest.raises(Exception):
        utils.assert_group_exists(
            db.session, account.group, utils.DeletionPolicy.DELETED
        )


def test_assert_group_exists_not_exists(db, account):
    user2 = models.User("user2", "password2", "group2@example.org")
    group2 = models.Group("group2", user2)

    with pytest.raises(Exception):
        utils.assert_group_exists(db.session, group2, utils.DeletionPolicy.NOT_DELETED)

    with pytest.raises(Exception):
        utils.assert_group_exists(db.session, group2, utils.DeletionPolicy.DELETED)

    with pytest.raises(Exception):
        utils.assert_group_exists(db.session, group2, utils.DeletionPolicy.ANY)

    # Also try with bad ID
    group2.group_id = 999999

    with pytest.raises(Exception):
        utils.assert_group_exists(db.session, group2, utils.DeletionPolicy.NOT_DELETED)

    with pytest.raises(Exception):
        utils.assert_group_exists(db.session, group2, utils.DeletionPolicy.DELETED)

    with pytest.raises(Exception):
        utils.assert_group_exists(db.session, group2, utils.DeletionPolicy.ANY)


def test_assert_group_exists_deleted(db, account):
    user2 = models.User("user2", "password2", "group2@example.org")
    group2 = models.Group("group2", user2)
    group_delete_lock = models.GroupLock("delete", group2)
    db.session.add_all((group2, user2, group_delete_lock))
    db.session.commit()

    with pytest.raises(Exception):
        utils.assert_group_exists(db.session, group2, utils.DeletionPolicy.NOT_DELETED)

    utils.assert_group_exists(db.session, group2, utils.DeletionPolicy.DELETED)
    utils.assert_group_exists(db.session, group2, utils.DeletionPolicy.ANY)


def test_assert_user_does_not_exist_user_exists(db, account):
    with pytest.raises(Exception):
        utils.assert_user_does_not_exist(
            db.session, account.user, utils.DeletionPolicy.NOT_DELETED
        )

    utils.assert_user_does_not_exist(
        db.session, account.user, utils.DeletionPolicy.DELETED
    )

    with pytest.raises(Exception):
        utils.assert_user_does_not_exist(
            db.session, account.user, utils.DeletionPolicy.ANY
        )


def test_assert_user_does_not_exist_user_not_exists(db, account):
    user2 = models.User("user2", "password2", "user2@example.org")

    utils.assert_user_does_not_exist(
        db.session, user2, utils.DeletionPolicy.NOT_DELETED
    )
    utils.assert_user_does_not_exist(db.session, user2, utils.DeletionPolicy.DELETED)
    utils.assert_user_does_not_exist(db.session, user2, utils.DeletionPolicy.ANY)

    # Also try with bad ID
    user2.user_id = 999999

    utils.assert_user_does_not_exist(
        db.session, user2, utils.DeletionPolicy.NOT_DELETED
    )
    utils.assert_user_does_not_exist(db.session, user2, utils.DeletionPolicy.DELETED)
    utils.assert_user_does_not_exist(db.session, user2, utils.DeletionPolicy.ANY)


def test_assert_user_does_not_exist_user_deleted(db, account):
    user2 = models.User("user2", "password2", "user2@example.org")
    user_delete_lock = models.UserLock("delete", user2)
    db.session.add_all((user2, user_delete_lock))
    db.session.commit()

    utils.assert_user_does_not_exist(
        db.session, user2, utils.DeletionPolicy.NOT_DELETED
    )

    with pytest.raises(Exception):
        utils.assert_user_does_not_exist(
            db.session, user2, utils.DeletionPolicy.DELETED
        )

    with pytest.raises(Exception):
        utils.assert_user_does_not_exist(db.session, user2, utils.DeletionPolicy.ANY)


def test_assert_group_does_not_exist_group_exists(db, account):
    with pytest.raises(Exception):
        utils.assert_group_does_not_exist(
            db.session, account.group, utils.DeletionPolicy.NOT_DELETED
        )

    utils.assert_group_does_not_exist(
        db.session, account.group, utils.DeletionPolicy.DELETED
    )

    with pytest.raises(Exception):
        utils.assert_group_does_not_exist(
            db.session, account.group, utils.DeletionPolicy.ANY
        )


def test_assert_group_does_not_exist_group_not_exists(db, account):
    user2 = models.User("user2", "password2", "user2@example.org")
    group2 = models.Group("group2", user2)

    utils.assert_group_does_not_exist(
        db.session, group2, utils.DeletionPolicy.NOT_DELETED
    )
    utils.assert_group_does_not_exist(db.session, group2, utils.DeletionPolicy.DELETED)
    utils.assert_group_does_not_exist(db.session, group2, utils.DeletionPolicy.ANY)

    # Also try with bad ID
    group2.group_id = 999999

    utils.assert_group_does_not_exist(
        db.session, group2, utils.DeletionPolicy.NOT_DELETED
    )
    utils.assert_group_does_not_exist(db.session, group2, utils.DeletionPolicy.DELETED)
    utils.assert_group_does_not_exist(db.session, group2, utils.DeletionPolicy.ANY)


def test_assert_group_does_not_exist_group_deleted(db, account):
    user2 = models.User("user2", "password2", "user2@example.org")
    group2 = models.Group("group2", user2)
    group_delete_lock = models.GroupLock("delete", group2)
    db.session.add_all((user2, group2, group_delete_lock))
    db.session.commit()

    utils.assert_group_does_not_exist(
        db.session, group2, utils.DeletionPolicy.NOT_DELETED
    )

    with pytest.raises(Exception):
        utils.assert_group_does_not_exist(
            db.session, group2, utils.DeletionPolicy.DELETED
        )

    with pytest.raises(Exception):
        utils.assert_group_does_not_exist(db.session, group2, utils.DeletionPolicy.ANY)


def test_resource_exists(db, fake_data, account):
    queue = fake_data.queue(account.user, account.group)
    db.session.add(queue)
    db.session.commit()

    result = utils.resource_exists(db.session, queue)
    assert result is utils.ExistenceResult.EXISTS


def test_resource_not_exists(db, fake_data, account):
    queue = fake_data.queue(account.user, account.group)

    result = utils.resource_exists(db.session, queue)
    assert result is utils.ExistenceResult.DOES_NOT_EXIST


def test_resource_deleted(db, fake_data, account):
    queue = fake_data.queue(account.user, account.group)
    db.session.add(queue)
    db.session.commit()

    lock = models.ResourceLock("delete", queue.resource)
    db.session.add(lock)
    db.session.commit()

    result = utils.resource_exists(db.session, queue)
    assert result is utils.ExistenceResult.DELETED


def test_assert_resource_exists(db, fake_data, account):
    queue = fake_data.queue(account.user, account.group)
    db.session.add(queue)
    db.session.commit()

    utils.assert_resource_exists(db.session, queue, utils.DeletionPolicy.NOT_DELETED)
    utils.assert_resource_exists(db.session, queue, utils.DeletionPolicy.ANY)

    with pytest.raises(ResourceExistsError):
        utils.assert_resource_exists(db.session, queue, utils.DeletionPolicy.DELETED)


def test_assert_resource_exists_not_exists(db, fake_data, account):
    queue = fake_data.queue(account.user, account.group)

    with pytest.raises(ResourceNotFoundError):
        utils.assert_resource_exists(
            db.session, queue, utils.DeletionPolicy.NOT_DELETED
        )

    with pytest.raises(ResourceNotFoundError):
        utils.assert_resource_exists(db.session, queue, utils.DeletionPolicy.ANY)

    with pytest.raises(ResourceNotFoundError):
        utils.assert_resource_exists(db.session, queue, utils.DeletionPolicy.DELETED)

    # Also try with bad ID
    queue.resource_snapshot_id = 999999

    with pytest.raises(ResourceNotFoundError):
        utils.assert_resource_exists(
            db.session, queue, utils.DeletionPolicy.NOT_DELETED
        )

    with pytest.raises(ResourceNotFoundError):
        utils.assert_resource_exists(db.session, queue, utils.DeletionPolicy.ANY)

    with pytest.raises(ResourceNotFoundError):
        utils.assert_resource_exists(db.session, queue, utils.DeletionPolicy.DELETED)


def test_assert_resource_exists_deleted(db, fake_data, account):
    queue = fake_data.queue(account.user, account.group)
    db.session.add(queue)
    db.session.commit()

    lock = models.ResourceLock("delete", queue.resource)
    db.session.add(lock)
    db.session.commit()

    with pytest.raises(ResourceDeletedError):
        utils.assert_resource_exists(
            db.session, queue, utils.DeletionPolicy.NOT_DELETED
        )

    utils.assert_resource_exists(db.session, queue, utils.DeletionPolicy.ANY)

    utils.assert_resource_exists(db.session, queue, utils.DeletionPolicy.DELETED)


def test_assert_resource_does_not_exist_resource_exists(db, fake_data, account):
    queue = fake_data.queue(account.user, account.group)
    db.session.add(queue)
    db.session.commit()

    with pytest.raises(ResourceExistsError):
        utils.assert_resource_does_not_exist(
            db.session, queue, utils.DeletionPolicy.NOT_DELETED
        )

    with pytest.raises(ResourceExistsError):
        utils.assert_resource_does_not_exist(
            db.session, queue, utils.DeletionPolicy.ANY
        )

    utils.assert_resource_does_not_exist(
        db.session, queue, utils.DeletionPolicy.DELETED
    )


def test_assert_resource_does_not_exist_resource_not_exists(db, fake_data, account):
    queue = fake_data.queue(account.user, account.group)

    utils.assert_resource_does_not_exist(
        db.session, queue, utils.DeletionPolicy.NOT_DELETED
    )

    utils.assert_resource_does_not_exist(db.session, queue, utils.DeletionPolicy.ANY)

    utils.assert_resource_does_not_exist(
        db.session, queue, utils.DeletionPolicy.DELETED
    )

    # Also try with bad ID
    queue.resource_snapshot_id = 999999

    utils.assert_resource_does_not_exist(
        db.session, queue, utils.DeletionPolicy.NOT_DELETED
    )

    utils.assert_resource_does_not_exist(db.session, queue, utils.DeletionPolicy.ANY)

    utils.assert_resource_does_not_exist(
        db.session, queue, utils.DeletionPolicy.DELETED
    )


def test_assert_resource_does_not_exist_resource_deleted(db, fake_data, account):
    queue = fake_data.queue(account.user, account.group)
    db.session.add(queue)
    db.session.commit()

    lock = models.ResourceLock("delete", queue.resource)
    db.session.add(lock)
    db.session.commit()

    utils.assert_resource_does_not_exist(
        db.session, queue, utils.DeletionPolicy.NOT_DELETED
    )

    with pytest.raises(ResourceDeletedError):
        utils.assert_resource_does_not_exist(
            db.session, queue, utils.DeletionPolicy.ANY
        )

    with pytest.raises(ResourceDeletedError):
        utils.assert_resource_does_not_exist(
            db.session, queue, utils.DeletionPolicy.DELETED
        )


def test_snapshot_exists(db, fake_data, account):
    queue = fake_data.queue(account.user, account.group)
    db.session.add(queue)
    db.session.commit()

    result = utils.snapshot_exists(db.session, queue)
    assert result


def test_snapshot_not_exists(db, fake_data, account):
    queue = fake_data.queue(account.user, account.group)
    result = utils.snapshot_exists(db.session, queue)
    assert not result

    queue.resource_snapshot_id = 999999
    result = utils.snapshot_exists(db.session, queue)
    assert not result


def test_assert_snapshot_exists(db, fake_data, account):
    queue = fake_data.queue(account.user, account.group)
    db.session.add(queue)
    db.session.commit()

    utils.assert_snapshot_exists(db.session, queue)


def test_assert_snapshot_exists_not_exists(db, fake_data, account):
    queue = fake_data.queue(account.user, account.group)

    with pytest.raises(Exception):
        utils.assert_snapshot_exists(db.session, queue)


def test_assert_snapshot_does_not_exist(db, fake_data, account):
    queue = fake_data.queue(account.user, account.group)
    db.session.add(queue)
    db.session.commit()

    with pytest.raises(Exception):
        utils.assert_snapshot_does_not_exist(db.session, queue)


def test_assert_snapshot_does_not_exist_not_exists(db, fake_data, account):
    queue = fake_data.queue(account.user, account.group)

    utils.assert_snapshot_does_not_exist(db.session, queue)


def test_delete_resource(db, account, fake_data):
    queue = fake_data.queue(account.user, account.group)
    db.session.add(queue)
    db.session.commit()

    utils.delete_resource(db.session, queue)

    lock = db.session.get(
        models.ResourceLock, (queue.resource_id, resource_lock_types.DELETE)
    )
    assert lock

    # Should be a no-op
    utils.delete_resource(db.session, queue)


def test_delete_resource_not_exists(db, account, fake_data):
    queue = fake_data.queue(account.user, account.group)

    with pytest.raises(ResourceNotFoundError):
        utils.delete_resource(db.session, queue)
