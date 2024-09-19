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
from dioptra.restapi.db.repository.utils import DeletionPolicy
from dioptra.restapi.db.shared_errors import (
    ResourceDeletedError,
    ResourceExistsError,
    ResourceNotFoundError,
)


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

    with pytest.raises(ResourceExistsError):
        queue_repo.create(queue)


def test_queue_create_queue_exists_deleted(queue_repo, account, db, fake_data):
    queue = fake_data.queue(account.user, account.group)
    db.session.add(queue)
    db.session.commit()

    queue_lock = m.ResourceLock(resource_lock_types.DELETE, queue.resource)
    db.session.add(queue_lock)
    db.session.commit()

    with pytest.raises(ResourceDeletedError):
        queue_repo.create(queue)


def test_queue_create_user_not_exists(queue_repo, account, db, fake_data):
    u2 = m.User("user2", "password2", "user2@example.org")
    resource = m.Resource("queue", account.group)
    queue = m.Queue("description", resource, u2, "a queue")

    with pytest.raises(Exception):
        queue_repo.create(queue)


def test_queue_create_group_not_exist(queue_repo, account, db, fake_data):
    g2 = m.Group("group2", account.user)
    resource = m.Resource("queue", g2)
    queue = m.Queue("description", resource, account.user, "a queue")

    with pytest.raises(Exception):
        queue_repo.create(queue)


def test_queue_create_user_not_member(queue_repo, account, db, fake_data):
    u2 = m.User("user2", "password2", "user2@example.org")
    g2 = m.Group("group2", u2)
    db.session.add(g2)
    db.session.add(u2)
    db.session.commit()

    resource = m.Resource("queue", g2)
    queue = m.Queue("description", resource, account.user, "a queue")
    with pytest.raises(Exception):
        queue_repo.create(queue)


def test_queue_create_name_collision(queue_repo, account, db, fake_data):
    queue1 = fake_data.queue(account.user, account.group)
    queue_repo.create(queue1)
    db.session.commit()

    queue2 = fake_data.queue(account.user, account.group)
    queue2.name = queue1.name

    with pytest.raises(Exception):
        queue_repo.create(queue2)


def test_queue_create_wrong_resource_type(queue_repo, account, db, fake_data):
    experiment_resource = m.Resource("experiment", account.group)
    queue = m.Queue("description", experiment_resource, account.user, "name")

    with pytest.raises(Exception):
        queue_repo.create(queue)


def test_queue_get_by_name(queue_repo, account, db, fake_data):
    queue = fake_data.queue(account.user, account.group)
    db.session.add(queue)
    db.session.commit()

    check_queue = queue_repo.get_by_name(queue.name, account.group, DeletionPolicy.ANY)
    assert check_queue == queue

    check_queue = queue_repo.get_by_name(
        queue.name, account.group, DeletionPolicy.NOT_DELETED
    )
    assert check_queue == queue

    check_queue = queue_repo.get_by_name(
        queue.name, account.group, DeletionPolicy.DELETED
    )
    assert not check_queue

    # Add another queue owned by another group with the same name; ensure
    # get_by_name() using the same name but different group, yields the other
    # queue.
    account2 = fake_data.account()
    db.session.add(account2.group)
    db.session.commit()

    queue2 = fake_data.queue(account2.user, account2.group)
    queue2.name = queue.name
    db.session.add(queue2)
    db.session.commit()

    check_queue = queue_repo.get_by_name(
        queue.name, account2.group, DeletionPolicy.NOT_DELETED
    )
    assert check_queue == queue2
    assert check_queue != queue


def test_queue_get_by_name_deleted(queue_repo, account, db, fake_data):
    queue = fake_data.queue(account.user, account.group)
    db.session.add(queue)
    db.session.commit()

    queue_lock = m.ResourceLock(resource_lock_types.DELETE, queue.resource)
    db.session.add(queue_lock)
    db.session.commit()

    check_queue = queue_repo.get_by_name(queue.name, account.group, DeletionPolicy.ANY)
    assert check_queue == queue

    check_queue = queue_repo.get_by_name(
        queue.name, account.group, DeletionPolicy.NOT_DELETED
    )
    assert not check_queue

    check_queue = queue_repo.get_by_name(
        queue.name, account.group, DeletionPolicy.DELETED
    )
    assert check_queue == queue


def test_queue_get_by_name_not_exist(queue_repo, account, db, fake_data):
    check_queue = queue_repo.get_by_name("foo", account.group, DeletionPolicy.ANY)
    assert not check_queue

    check_queue = queue_repo.get_by_name(
        "foo", account.group, DeletionPolicy.NOT_DELETED
    )
    assert not check_queue

    check_queue = queue_repo.get_by_name("foo", account.group, DeletionPolicy.DELETED)
    assert not check_queue

    # Try getting an existing queue via the wrong group
    queue = fake_data.queue(account.user, account.group)
    queue_repo.create(queue)
    db.session.commit()

    account2 = fake_data.account()
    db.session.add(account2.group)
    db.session.commit()

    check_queue = queue_repo.get_by_name(queue.name, account2.group, DeletionPolicy.ANY)
    assert not check_queue

    check_queue = queue_repo.get_by_name(
        queue.name, account2.group, DeletionPolicy.NOT_DELETED
    )
    assert not check_queue

    check_queue = queue_repo.get_by_name(
        queue.name, account2.group, DeletionPolicy.DELETED
    )
    assert not check_queue


def test_queue_get_by_name_multi_version(queue_repo, account, db, fake_data):
    queuesnap1 = fake_data.queue(account.user, account.group)
    # We can't rely on auto-timestamping here; the instances are created too
    # quickly and can coincidentally get identical timestamps.
    queuesnap1.created_on = datetime.datetime.fromisoformat(
        "1992-07-22T12:17:31.410801Z"
    )

    queuesnap2 = m.Queue(
        queuesnap1.description, queuesnap1.resource, queuesnap1.creator, queuesnap1.name
    )
    queuesnap2.created_on = datetime.datetime.fromisoformat(
        "1998-10-23T20:39:53.132405Z"
    )

    db.session.add_all([queuesnap1, queuesnap2])
    db.session.commit()

    # Should only get the latest version
    queue = queue_repo.get_by_name(
        queuesnap1.name, account.group, DeletionPolicy.NOT_DELETED
    )

    assert queue == queuesnap2


def test_queue_get_by_name_old_name(queue_repo, account, db):
    # Ensure getting a queue by an old name doesn't return an old queue
    # snapshot.
    queue_res = m.Resource("queue", account.group)
    queue = m.Queue("desc", queue_res, account.user, "name1")
    queue_repo.create(queue)
    db.session.commit()

    queue_name2 = m.Queue("desc", queue_res, account.user, "name2")
    queue_repo.create_snapshot(queue_name2)
    db.session.commit()

    check_queue = queue_repo.get_by_name(
        "name1", account.group, DeletionPolicy.NOT_DELETED
    )
    assert not check_queue

    check_queue = queue_repo.get_by_name(
        "name2", account.group, DeletionPolicy.NOT_DELETED
    )
    assert check_queue == queue_name2

    check_queue = queue_repo.get_by_name(
        "name1", account.group, DeletionPolicy.DELETED
    )
    assert not check_queue

    check_queue = queue_repo.get_by_name(
        "name2", account.group, DeletionPolicy.DELETED
    )
    assert not check_queue

    check_queue = queue_repo.get_by_name(
        "name1", account.group, DeletionPolicy.ANY
    )
    assert not check_queue

    check_queue = queue_repo.get_by_name(
        "name2", account.group, DeletionPolicy.ANY
    )
    assert check_queue == queue_name2


def test_queue_get_by_name_old_name_deleted(queue_repo, account, db):
    # Ensure getting a queue by an old name doesn't return an old queue
    # snapshot (deleted version).
    queue_res = m.Resource("queue", account.group)
    queue = m.Queue("desc", queue_res, account.user, "name1")
    queue_repo.create(queue)
    db.session.commit()

    queue_name2 = m.Queue("desc", queue_res, account.user, "name2")
    queue_repo.create_snapshot(queue_name2)
    db.session.commit()

    queue_repo.delete(queue_name2)
    db.session.commit()

    check_queue = queue_repo.get_by_name(
        "name1", account.group, DeletionPolicy.NOT_DELETED
    )
    assert not check_queue

    check_queue = queue_repo.get_by_name(
        "name2", account.group, DeletionPolicy.NOT_DELETED
    )
    assert not check_queue

    check_queue = queue_repo.get_by_name(
        "name1", account.group, DeletionPolicy.DELETED
    )
    assert not check_queue

    check_queue = queue_repo.get_by_name(
        "name2", account.group, DeletionPolicy.DELETED
    )
    assert check_queue == queue_name2

    check_queue = queue_repo.get_by_name(
        "name1", account.group, DeletionPolicy.ANY
    )
    assert not check_queue

    check_queue = queue_repo.get_by_name(
        "name2", account.group, DeletionPolicy.ANY
    )
    assert check_queue == queue_name2


def test_queue_get_by_name_old_name_not_exist(queue_repo, account, db):
    # Ensure getting a queue by an old name doesn't return an old queue
    # snapshot (does not exist version).

    check_queue = queue_repo.get_by_name(
        "name1", account.group, DeletionPolicy.NOT_DELETED
    )
    assert not check_queue

    check_queue = queue_repo.get_by_name(
        "name2", account.group, DeletionPolicy.NOT_DELETED
    )
    assert not check_queue

    check_queue = queue_repo.get_by_name(
        "name1", account.group, DeletionPolicy.DELETED
    )
    assert not check_queue

    check_queue = queue_repo.get_by_name(
        "name2", account.group, DeletionPolicy.DELETED
    )
    assert not check_queue

    check_queue = queue_repo.get_by_name(
        "name1", account.group, DeletionPolicy.ANY
    )
    assert not check_queue

    check_queue = queue_repo.get_by_name(
        "name2", account.group, DeletionPolicy.ANY
    )
    assert not check_queue


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

    with pytest.raises(Exception):
        queue_repo.create_snapshot(queue_snap1)


def test_queue_create_snapshot_resource_not_exists(queue_repo, account):

    other_resource = m.Resource("queue", account.group)
    queue_snap2 = m.Queue("description", other_resource, account.user, "name")

    with pytest.raises(ResourceNotFoundError):
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

    with pytest.raises(Exception):
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

    with pytest.raises(Exception):
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
    with pytest.raises(Exception):
        queue_repo.create_snapshot(queue_snap2)


def test_queue_get_single(queue_repo, queue_snap_setup):
    queues, latest_snaps = queue_snap_setup

    latest_snap = queue_repo.get(queues[0].resource_id, DeletionPolicy.NOT_DELETED)
    assert latest_snap == latest_snaps[0]

    latest_snap = queue_repo.get(queues[0].resource_id, DeletionPolicy.DELETED)
    assert latest_snap is None

    latest_snap = queue_repo.get(queues[0].resource_id, DeletionPolicy.ANY)
    assert latest_snap == latest_snaps[0]


def test_queue_get_single_deleted(queue_repo, db, queue_snap_setup):
    queues, latest_snaps = queue_snap_setup

    # Delete a queue
    queue_lock = m.ResourceLock(resource_lock_types.DELETE, queues[0].resource)
    db.session.add(queue_lock)
    db.session.commit()

    latest_snap = queue_repo.get(queues[0].resource_id, DeletionPolicy.NOT_DELETED)
    assert latest_snap is None

    latest_snap = queue_repo.get(queues[0].resource_id, DeletionPolicy.DELETED)
    assert latest_snap == latest_snaps[0]

    latest_snap = queue_repo.get(queues[0].resource_id, DeletionPolicy.ANY)
    assert latest_snap == latest_snaps[0]


def test_queue_get_single_not_exist(queue_repo, queue_snap_setup):

    latest_snap = queue_repo.get(999999, DeletionPolicy.NOT_DELETED)
    assert latest_snap is None

    latest_snap = queue_repo.get(999999, DeletionPolicy.DELETED)
    assert latest_snap is None

    latest_snap = queue_repo.get(999999, DeletionPolicy.ANY)
    assert latest_snap is None


def test_queue_get_multi(queue_repo, queue_snap_setup):
    queues, latest_snaps = queue_snap_setup

    # For these multi-return-value cases, I actually don't think the
    # order of returned snapshots is guaranteed.
    check_latest = queue_repo.get(
        (queues[0].resource_id, queues[2].resource_id), DeletionPolicy.NOT_DELETED
    )
    assert check_latest == [latest_snaps[0], latest_snaps[2]]

    check_latest = queue_repo.get(
        (queues[0].resource_id, queues[2].resource_id), DeletionPolicy.DELETED
    )
    assert check_latest == []

    check_latest = queue_repo.get(
        (queues[0].resource_id, queues[2].resource_id), DeletionPolicy.ANY
    )
    assert check_latest == [latest_snaps[0], latest_snaps[2]]

    # Try with other iterable types (iterables of resource IDs)
    check_latest = queue_repo.get(
        [queues[0].resource_id, queues[2].resource_id], DeletionPolicy.ANY
    )
    assert check_latest == [latest_snaps[0], latest_snaps[2]]

    check_latest = queue_repo.get(
        {queues[0].resource_id, queues[2].resource_id}, DeletionPolicy.ANY
    )
    assert check_latest == [latest_snaps[0], latest_snaps[2]]


def test_queue_get_multi_deleted(queue_repo, db, queue_snap_setup):
    queues, latest_snaps = queue_snap_setup

    # ... and delete one
    lock = m.ResourceLock(resource_lock_types.DELETE, queues[0].resource)
    db.session.add(lock)
    db.session.commit()

    # For these multi-return-value cases, I actually don't think the
    # order of returned snapshots is guaranteed.
    check_latest = queue_repo.get(
        (queues[0].resource_id, queues[2].resource_id), DeletionPolicy.NOT_DELETED
    )
    assert check_latest == [latest_snaps[2]]

    check_latest = queue_repo.get(
        (queues[0].resource_id, queues[2].resource_id), DeletionPolicy.DELETED
    )
    assert check_latest == [latest_snaps[0]]

    check_latest = queue_repo.get(
        (queues[0].resource_id, queues[2].resource_id), DeletionPolicy.ANY
    )
    assert check_latest == [latest_snaps[0], latest_snaps[2]]


def test_queue_get_multi_not_exist(queue_repo, queue_snap_setup):
    queues, latest_snaps = queue_snap_setup

    # For these multi-return-value cases, I actually don't think the
    # order of returned snapshots is guaranteed.
    check_latest = queue_repo.get(
        (999999, queues[2].resource_id), DeletionPolicy.NOT_DELETED
    )
    assert check_latest == [latest_snaps[2]]

    check_latest = queue_repo.get((999999, 888888), DeletionPolicy.NOT_DELETED)
    assert check_latest == []

    check_latest = queue_repo.get(
        (999999, queues[2].resource_id), DeletionPolicy.DELETED
    )
    assert check_latest == []

    check_latest = queue_repo.get((queues[2].resource_id, 999999), DeletionPolicy.ANY)
    assert check_latest == [latest_snaps[2]]


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

    with pytest.raises(ResourceNotFoundError):
        queue_repo.delete(queue)
