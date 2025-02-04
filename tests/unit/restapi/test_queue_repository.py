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
import datetime

import pytest

import dioptra.restapi.db.models as m
from dioptra.restapi.db.models.constants import resource_lock_types
from dioptra.restapi.errors import (
    EntityDeletedError,
    EntityDoesNotExistError,
    EntityExistsError,
    MismatchedResourceTypeError,
    UserNotInGroupError,
)
import tests.unit.restapi.lib.helpers as helpers


@pytest.fixture
def queue_snap_setup(queue_repo, account, db, fake_data):
    queues = [fake_data.queue(account.user, account.group) for _ in range(3)]

    for queue in queues:
        queue_repo.create(queue)

    db.session.commit()

    # 5 versions each of 3 different queues
    latest_snaps = [None] * len(queues)
    for i in range(1, 6):
        for j, queue in enumerate(queues):
            new_snap = m.Queue(
                queue.description, queue.resource, account.user, f"{queue.name}_{i}"
            )
            new_snap.created_on = queue.created_on + datetime.timedelta(hours=i)

            queue_repo.create_snapshot(new_snap)
            db.session.commit()

            latest_snaps[j] = new_snap

    return queues, latest_snaps


def test_queue_create_queue_not_exists(queue_repo, account, db, fake_data):
    queue = fake_data.queue(account.user, account.group)
    queue_repo.create(queue)
    db.session.commit()

    check_queue = db.session.get(m.Queue, queue.resource_snapshot_id)

    assert check_queue == queue


def test_queue_create_queue_exists(queue_repo, account, db, fake_data):
    queue = fake_data.queue(account.user, account.group)
    db.session.add(queue)
    db.session.commit()

    with pytest.raises(EntityExistsError):
        queue_repo.create(queue)


def test_queue_create_queue_exists_deleted(queue_repo, account, db, fake_data):
    queue = fake_data.queue(account.user, account.group)
    db.session.add(queue)
    db.session.commit()

    queue_lock = m.ResourceLock(resource_lock_types.DELETE, queue.resource)
    db.session.add(queue_lock)
    db.session.commit()

    with pytest.raises(EntityDeletedError):
        queue_repo.create(queue)


def test_queue_create_user_not_exists(queue_repo, account, db, fake_data):
    u2 = m.User("user2", "password2", "user2@example.org")
    resource = m.Resource("queue", account.group)
    queue = m.Queue("description", resource, u2, "a queue")

    with pytest.raises(EntityDoesNotExistError):
        queue_repo.create(queue)


def test_queue_create_group_not_exist(queue_repo, account, db, fake_data):
    g2 = m.Group("group2", account.user)
    resource = m.Resource("queue", g2)
    queue = m.Queue("description", resource, account.user, "a queue")

    with pytest.raises(EntityDoesNotExistError):
        queue_repo.create(queue)


def test_queue_create_user_not_member(queue_repo, account, db, fake_data):
    u2 = m.User("user2", "password2", "user2@example.org")
    g2 = m.Group("group2", u2)
    db.session.add(g2)
    db.session.add(u2)
    db.session.commit()

    resource = m.Resource("queue", g2)
    queue = m.Queue("description", resource, account.user, "a queue")
    with pytest.raises(UserNotInGroupError):
        queue_repo.create(queue)


def test_queue_create_name_collision(queue_repo, account, db, fake_data):
    queue1 = fake_data.queue(account.user, account.group)
    queue_repo.create(queue1)
    db.session.commit()

    queue2 = fake_data.queue(account.user, account.group)
    queue2.name = queue1.name

    with pytest.raises(EntityExistsError):
        queue_repo.create(queue2)


def test_queue_create_wrong_resource_type(queue_repo, account, db, fake_data):
    experiment_resource = m.Resource("experiment", account.group)
    queue = m.Queue("description", experiment_resource, account.user, "name")

    with pytest.raises(MismatchedResourceTypeError):
        queue_repo.create(queue)


def test_queue_create_snapshot(queue_repo, account, db, fake_data):

    queue_snap1 = fake_data.queue(account.user, account.group)
    queue_repo.create(queue_snap1)
    db.session.commit()

    queue_snap2 = m.Queue(
        queue_snap1.description,
        queue_snap1.resource,
        queue_snap1.creator,
        queue_snap1.name,
    )
    queue_repo.create_snapshot(queue_snap2)
    db.session.commit()

    check_resource = db.session.get(m.Resource, queue_snap1.resource_id)
    assert check_resource is not None
    assert len(check_resource.versions) == 2
    assert queue_snap1 in check_resource.versions
    assert queue_snap2 in check_resource.versions
    assert queue_snap1.created_on < queue_snap2.created_on


def test_queue_create_snapshot_snap_exists(queue_repo, account, db, fake_data):

    queue_snap1 = fake_data.queue(account.user, account.group)
    queue_repo.create(queue_snap1)
    db.session.commit()

    with pytest.raises(EntityExistsError):
        queue_repo.create_snapshot(queue_snap1)


def test_queue_create_snapshot_resource_not_exists(queue_repo, account):

    other_resource = m.Resource("queue", account.group)
    queue_snap2 = m.Queue("description", other_resource, account.user, "name")

    with pytest.raises(EntityDoesNotExistError):
        queue_repo.create_snapshot(queue_snap2)


def test_queue_create_snapshot_creator_not_member(queue_repo, account, db, fake_data):

    queue_snap1 = fake_data.queue(account.user, account.group)
    queue_repo.create(queue_snap1)
    db.session.commit()

    u2 = m.User("user2", "password2", "user2@example.org")
    g2 = m.Group("group2", u2)
    db.session.add(g2)
    db.session.add(u2)
    db.session.commit()

    queue_snap2 = m.Queue(
        queue_snap1.description, queue_snap1.resource, u2, queue_snap1.name
    )

    with pytest.raises(UserNotInGroupError):
        queue_repo.create_snapshot(queue_snap2)


def test_queue_create_snapshot_name_collision(queue_repo, account, db, fake_data):

    queue1_snap1 = fake_data.queue(account.user, account.group)
    queue_repo.create(queue1_snap1)
    db.session.commit()

    queue2_snap1 = fake_data.queue(account.user, account.group)
    queue_repo.create(queue2_snap1)
    db.session.commit()

    queue2_snap2 = m.Queue(
        queue2_snap1.description,
        queue2_snap1.resource,
        queue2_snap1.creator,
        queue1_snap1.name,
    )

    with pytest.raises(EntityExistsError):
        queue_repo.create_snapshot(queue2_snap2)

    # Create a queue in a different group which has the same name as a queue in
    # account.group.  This ought to be allowed since the groups are different.
    account2 = fake_data.account()
    db.session.add(account2.group)
    db.session.commit()

    queue3_snap1 = fake_data.queue(account2.user, account2.group)
    queue_repo.create(queue3_snap1)
    db.session.commit()

    queue3_snap2 = m.Queue(
        queue3_snap1.description,
        queue3_snap1.resource,
        queue3_snap1.creator,
        queue1_snap1.name,
    )
    queue_repo.create_snapshot(queue3_snap2)
    db.session.commit()


def test_queue_create_snapshot_wrong_resource_type(queue_repo, account, db, fake_data):

    queue_snap1 = fake_data.queue(account.user, account.group)
    queue_repo.create(queue_snap1)
    db.session.commit()

    experiment = fake_data.experiment(account.user, account.group)
    db.session.add(experiment)
    db.session.commit()

    queue_snap2 = m.Queue(
        queue_snap1.description, experiment.resource, account.user, experiment.name
    )
    with pytest.raises(MismatchedResourceTypeError):
        queue_repo.create_snapshot(queue_snap2)


def test_queue_delete(queue_repo, db, queue_snap_setup):
    queues, latest_snaps = queue_snap_setup

    queue_repo.delete(queues[0])
    db.session.commit()
    assert queues[0].resource.is_deleted

    # Second time should be a no-op
    queue_repo.delete(queues[0])
    db.session.commit()
    assert queues[0].resource.is_deleted


def test_queue_delete_not_exist(queue_repo, account, fake_data):
    queue = fake_data.queue(account.user, account.group)

    with pytest.raises(EntityDoesNotExistError):
        queue_repo.delete(queue)


def test_queue_get_by_name_exists(
    db, fake_data, account, queue_repo, deletion_policy
):
    queue1 = fake_data.queue(account.user, account.group)
    queue2 = m.Queue(queue1.description, queue1.resource, queue1.creator, queue1.name)

    if queue1.created_on == queue2.created_on:
        queue2.created_on = queue2.created_on + datetime.timedelta(hours=1)

    db.session.add_all((queue1, queue2))
    db.session.commit()

    snap = queue_repo.get_by_name(queue1.name, queue1.resource.owner, deletion_policy)

    expected_snaps = helpers.find_expected_snaps_for_deletion_policy(
        [queue2], deletion_policy
    )
    expected_snap = expected_snaps[0] if expected_snaps else None

    assert snap == expected_snap


def test_queue_get_by_name_deleted(
    db, fake_data, account, queue_repo, deletion_policy
):
    queue1 = fake_data.queue(account.user, account.group)
    queue2 = m.Queue(queue1.description, queue1.resource, queue1.creator, queue1.name)

    if queue1.created_on == queue2.created_on:
        queue2.created_on = queue2.created_on + datetime.timedelta(hours=1)

    lock = m.ResourceLock(resource_lock_types.DELETE, queue1.resource)

    db.session.add_all((queue1, queue2, lock))
    db.session.commit()

    snap = queue_repo.get_by_name(queue1.name, queue1.resource.owner, deletion_policy)

    expected_snaps = helpers.find_expected_snaps_for_deletion_policy(
        [queue2], deletion_policy
    )
    expected_snap = expected_snaps[0] if expected_snaps else None

    assert snap == expected_snap


def test_queue_get_by_name_not_exist(
    db, fake_data, account, queue_repo, deletion_policy
):
    queue1 = fake_data.queue(account.user, account.group)

    snap = queue_repo.get_by_name(queue1.name, queue1.resource.owner, deletion_policy)

    expected_snaps = helpers.find_expected_snaps_for_deletion_policy(
        [queue1], deletion_policy
    )
    expected_snap = expected_snaps[0] if expected_snaps else None

    assert snap == expected_snap
