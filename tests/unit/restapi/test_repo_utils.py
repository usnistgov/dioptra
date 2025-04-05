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
import itertools
import re

import pytest

import dioptra.restapi.db.models as models
import dioptra.restapi.db.repository.utils as utils
import tests.unit.restapi.lib.helpers as helpers
from dioptra.restapi.db.models.constants import resource_lock_types
from dioptra.restapi.db.repository.queues import QueueRepository
from dioptra.restapi.errors import (
    EntityDeletedError,
    EntityDoesNotExistError,
    EntityExistsError,
    SearchParseError,
    SortParameterValidationError,
)

_STATUS_COMBOS = list(
    itertools.chain.from_iterable(
        itertools.combinations(utils.ExistenceResult, n)
        for n in range(0, len(utils.ExistenceResult) + 1)
    )
)

_STATUS_COMBO_IDS = [
    "-".join(status.name.lower() for status in combo) for combo in _STATUS_COMBOS
]


@pytest.fixture(
    params=_STATUS_COMBOS,
    ids=_STATUS_COMBO_IDS,
)
def resource_status_combo(request, db, account, fake_data):
    """
    This parameterized fixture produces resources in all status combinations,
    e.g. exists+deleted, deleted+not-exists, etc.  Each produced value is a
    (snapshots, status_set) 2-tuple, giving the resources created and the
    status combo they represent.  snapshots is a list of snapshots; status_set
    is a set of ExistenceResult enum values.
    """

    child_snaps = []
    for idx, status in enumerate(request.param):

        epres = models.Resource("entry_point", account.group)
        ep = models.EntryPoint("", epres, account.user, f"ep{idx}", "graph:", [])

        # If creating an existing/deleted resource, create several snapshots;
        # this fixture will just return the latest one.  It allows better
        # testing of methods to get latest snapshots, if there are old
        # snapshots (actual wrong answers).
        if status in (utils.ExistenceResult.EXISTS, utils.ExistenceResult.DELETED):

            db.session.add(ep)

            for snap_idx in range(3):
                ep = models.EntryPoint(
                    ep.description,
                    ep.resource,
                    ep.creator,
                    f"ep{idx}-{snap_idx}",
                    ep.task_graph,
                    ep.parameters,
                )
                # make sure this is later than the previous snapshot
                ep.created_on = ep.created_on + datetime.timedelta(hours=snap_idx + 1)
                db.session.add(ep)

            if status is utils.ExistenceResult.DELETED:
                lock = models.ResourceLock(resource_lock_types.DELETE, epres)
                db.session.add(lock)

        # else: status is DOES_NOT_EXIST, do not add to session; no point in
        # creating additional snapshots.

        child_snaps.append(ep)

    db.session.commit()

    return child_snaps, set(request.param)


@pytest.fixture
def resource_parent_combo(resource_status_combo, db, account, fake_data):
    """
    This fixture produces (parent snap, child snaps, status_set) 3-tuples, for
    all combinations of child status.
    """

    child_snaps, statuses = resource_status_combo

    parent = fake_data.experiment(account.user, account.group)
    db.session.add(parent)

    # Add the exists/deleted children to parent, but not the not-exists
    # children.  That way, the not-exists children aren't inadvertently added
    # to the DB when we commit.
    not_exists_children = []
    for child in child_snaps:
        if child.resource_snapshot_id is not None:
            parent.children.append(child.resource)
        else:
            not_exists_children.append(child)

    db.session.commit()

    # Now, add the non-exists children, and do not commit.
    parent.children.extend(c.resource for c in not_exists_children)

    try:
        # Prevent the non-exists children from being accidentally added due
        # to autoflush, which messes up the test setup.
        db.session.autoflush = False
        yield parent, child_snaps, statuses
    finally:
        db.session.autoflush = True
        # Rollback is necessary to remove pending table changes from the
        # transaction before the rest of the unit test teardown drops all the
        # tables.  Dropping and changing the same table in the same transaction
        # doesn't work well.
        db.session.rollback()


@pytest.fixture
def queue_filter_setup(account, db, fake_data):

    # These are fixed, so I can write tests against them.  It's not really
    # possible to do that without some fixed data.  E.g. you can't write a
    # pattern to match some names if you don't know the names.  You can't
    # search by a tag which matches a few queues, if you don't know which
    # queues have which tags.
    queue_info = [
        {
            "name": "Elfreda",
            "description": "Type city nor painting Democrat.",
            "tags": ["because", "support", "early"],
        },
        {
            "name": "Lorelai",
            "description": "Miss daughter bill information performance.",
            "tags": ["want", "use", "quickly"],
        },
        {
            "name": "Zelda",
            "description": "System prepare suddenly toward activity.",
            "tags": ["continue", "use", "down"],
        },
        {
            "name": "Reanna",
            "description": "Upon rich time model.",
            "tags": ["early", "down", "quickly"],
        },
        {
            "name": "Adelle",
            "description": "What know continue true.",
            "tags": ["because", "before", "continue"],
        },
        {
            "name": "Kizzy",
            "description": "Great crime reveal chair.",
            "tags": ["use", "quickly", "early"],
        },
        {
            "name": "Allannah",
            "description": "Institution life chair two them.",
            "tags": ["early", "continue", "down"],
        },
        {
            "name": "Jodi",
            "description": "Society learn easy along set world down however.",
            "tags": ["support", "before", "use"],
        },
        {
            "name": "Kaylani",
            "description": "Himself work wait service.",
            "tags": ["support", "early", "defense"],
        },
        {
            "name": "Arn",
            "description": "Responsibility program middle room interest guy.",
            "tags": ["use", "down", "early"],
        },
    ]

    # Create queue objects
    queue_objects = []
    for info in queue_info:
        queue_object = fake_data.queue(account.user, account.group)
        queue_object.name = info["name"]
        queue_object.description = info["description"]
        queue_objects.append(queue_object)
        db.session.add(queue_object)

    db.session.commit()

    # Create tag objects
    tag_names = set(itertools.chain.from_iterable(info["tags"] for info in queue_info))
    tags_by_name = {}
    for tag_name in tag_names:
        tag_object = fake_data.tag(account.user, account.group)
        tag_object.name = tag_name
        tags_by_name[tag_name] = tag_object
        db.session.add(tag_object)

    db.session.commit()

    # Link tags to queues
    for info, queue_object in zip(queue_info, queue_objects):
        for tag_name in info["tags"]:
            queue_object.tags.append(tags_by_name[tag_name])

    db.session.commit()

    return queue_objects


def _same_snapshots(snaps1, snaps2):
    """
    Check whether the given snapshots are equal in an order-agnostic way.
    This allows for variation in the order results come back from database
    queries, for example.
    """
    idset1 = {utils.get_resource_snapshot_id(snap) for snap in snaps1}
    idset2 = {utils.get_resource_snapshot_id(snap) for snap in snaps2}

    return idset1 == idset2


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

    with pytest.raises(EntityExistsError):
        utils.assert_user_exists(db.session, account.user, utils.DeletionPolicy.DELETED)


def test_assert_user_exists_not_exists(db, account):
    user2 = models.User("user2", "password2", "user2@example.org")

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_user_exists(db.session, user2, utils.DeletionPolicy.NOT_DELETED)

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_user_exists(db.session, user2, utils.DeletionPolicy.DELETED)

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_user_exists(db.session, user2, utils.DeletionPolicy.ANY)

    # Also try with bad ID
    user2.user_id = 999999

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_user_exists(db.session, user2, utils.DeletionPolicy.NOT_DELETED)

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_user_exists(db.session, user2, utils.DeletionPolicy.DELETED)

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_user_exists(db.session, user2, utils.DeletionPolicy.ANY)


def test_assert_user_exists_deleted(db, account):
    user2 = models.User("user2", "password2", "user2@example.org")
    user_delete_lock = models.UserLock("delete", user2)
    db.session.add_all((user2, user_delete_lock))
    db.session.commit()

    with pytest.raises(EntityDeletedError):
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

    with pytest.raises(EntityExistsError):
        utils.assert_group_exists(
            db.session, account.group, utils.DeletionPolicy.DELETED
        )


def test_assert_group_exists_not_exists(db, account):
    user2 = models.User("user2", "password2", "group2@example.org")
    group2 = models.Group("group2", user2)

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_group_exists(db.session, group2, utils.DeletionPolicy.NOT_DELETED)

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_group_exists(db.session, group2, utils.DeletionPolicy.DELETED)

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_group_exists(db.session, group2, utils.DeletionPolicy.ANY)

    # Also try with bad ID
    group2.group_id = 999999

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_group_exists(db.session, group2, utils.DeletionPolicy.NOT_DELETED)

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_group_exists(db.session, group2, utils.DeletionPolicy.DELETED)

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_group_exists(db.session, group2, utils.DeletionPolicy.ANY)


def test_assert_group_exists_deleted(db, account):
    user2 = models.User("user2", "password2", "group2@example.org")
    group2 = models.Group("group2", user2)
    group_delete_lock = models.GroupLock("delete", group2)
    db.session.add_all((group2, user2, group_delete_lock))
    db.session.commit()

    with pytest.raises(EntityDeletedError):
        utils.assert_group_exists(db.session, group2, utils.DeletionPolicy.NOT_DELETED)

    utils.assert_group_exists(db.session, group2, utils.DeletionPolicy.DELETED)
    utils.assert_group_exists(db.session, group2, utils.DeletionPolicy.ANY)


def test_assert_user_does_not_exist_user_exists(db, account):
    with pytest.raises(EntityExistsError):
        utils.assert_user_does_not_exist(
            db.session, account.user, utils.DeletionPolicy.NOT_DELETED
        )

    utils.assert_user_does_not_exist(
        db.session, account.user, utils.DeletionPolicy.DELETED
    )

    with pytest.raises(EntityExistsError):
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

    with pytest.raises(EntityDeletedError):
        utils.assert_user_does_not_exist(
            db.session, user2, utils.DeletionPolicy.DELETED
        )

    with pytest.raises(EntityDeletedError):
        utils.assert_user_does_not_exist(db.session, user2, utils.DeletionPolicy.ANY)


def test_assert_group_does_not_exist_group_exists(db, account):
    with pytest.raises(EntityExistsError):
        utils.assert_group_does_not_exist(
            db.session, account.group, utils.DeletionPolicy.NOT_DELETED
        )

    utils.assert_group_does_not_exist(
        db.session, account.group, utils.DeletionPolicy.DELETED
    )

    with pytest.raises(EntityExistsError):
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

    with pytest.raises(EntityDeletedError):
        utils.assert_group_does_not_exist(
            db.session, group2, utils.DeletionPolicy.DELETED
        )

    with pytest.raises(EntityDeletedError):
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


def test_resources_exist(db, fake_data, account):
    queues = [fake_data.queue(account.user, account.group) for _ in range(3)]

    queue_lock = models.ResourceLock("delete", queues[2].resource)

    db.session.add_all(queues)
    db.session.add(queue_lock)
    db.session.commit()

    other_queue = fake_data.queue(account.user, account.group)
    queues.append(other_queue)

    expected = {
        queues[0].resource_id: utils.ExistenceResult.EXISTS,
        queues[1].resource_id: utils.ExistenceResult.EXISTS,
        queues[2].resource_id: utils.ExistenceResult.DELETED,
        # other_queue doesn't show up here, since it was not committed and
        # never got an ID.
    }

    actual = utils.resources_exist(db.session, queues)

    assert actual == expected

    # try with just a bad ID
    actual = utils.resources_exist(db.session, [999999])

    assert actual == {999999: utils.ExistenceResult.DOES_NOT_EXIST}


def test_resource_children_exist(db, fake_data, account):

    exp = fake_data.experiment(account.user, account.group)

    ep1res = models.Resource("entry_point", account.group)
    ep1 = models.EntryPoint("", ep1res, account.user, "ep1", "graph:", [])

    ep2res = models.Resource("entry_point", account.group)
    ep2 = models.EntryPoint("", ep2res, account.user, "ep2", "graph:", [])
    ep2lock = models.ResourceLock(resource_lock_types.DELETE, ep2res)

    exp.children.extend((ep1res, ep2res))

    db.session.add_all((exp, ep1, ep2, ep2lock))
    db.session.commit()

    child_status = utils.resource_children_exist(db.session, exp)

    expected = {
        ep1.resource_id: utils.ExistenceResult.EXISTS,
        ep2.resource_id: utils.ExistenceResult.DELETED,
    }

    assert child_status == expected

    # try with just the experiment ID:
    child_status = utils.resource_children_exist(db.session, exp.resource_id)
    assert child_status == expected


def test_assert_resource_exists(db, fake_data, account):
    queue = fake_data.queue(account.user, account.group)
    db.session.add(queue)
    db.session.commit()

    utils.assert_resource_exists(db.session, queue, utils.DeletionPolicy.NOT_DELETED)
    utils.assert_resource_exists(db.session, queue, utils.DeletionPolicy.ANY)

    with pytest.raises(EntityExistsError):
        utils.assert_resource_exists(db.session, queue, utils.DeletionPolicy.DELETED)


def test_assert_resource_exists_not_exists(db, fake_data, account):
    queue = fake_data.queue(account.user, account.group)

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_resource_exists(
            db.session, queue, utils.DeletionPolicy.NOT_DELETED
        )

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_resource_exists(db.session, queue, utils.DeletionPolicy.ANY)

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_resource_exists(db.session, queue, utils.DeletionPolicy.DELETED)

    # Also try with bad ID
    queue.resource_snapshot_id = 999999

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_resource_exists(
            db.session, queue, utils.DeletionPolicy.NOT_DELETED
        )

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_resource_exists(db.session, queue, utils.DeletionPolicy.ANY)

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_resource_exists(db.session, queue, utils.DeletionPolicy.DELETED)


def test_assert_resource_exists_deleted(db, fake_data, account):
    queue = fake_data.queue(account.user, account.group)
    db.session.add(queue)
    db.session.commit()

    lock = models.ResourceLock("delete", queue.resource)
    db.session.add(lock)
    db.session.commit()

    with pytest.raises(EntityDeletedError):
        utils.assert_resource_exists(
            db.session, queue, utils.DeletionPolicy.NOT_DELETED
        )

    utils.assert_resource_exists(db.session, queue, utils.DeletionPolicy.ANY)

    utils.assert_resource_exists(db.session, queue, utils.DeletionPolicy.DELETED)


def test_assert_resource_does_not_exist_resource_exists(db, fake_data, account):
    queue = fake_data.queue(account.user, account.group)
    db.session.add(queue)
    db.session.commit()

    with pytest.raises(EntityExistsError):
        utils.assert_resource_does_not_exist(
            db.session, queue, utils.DeletionPolicy.NOT_DELETED
        )

    with pytest.raises(EntityExistsError):
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

    with pytest.raises(EntityDeletedError):
        utils.assert_resource_does_not_exist(
            db.session, queue, utils.DeletionPolicy.ANY
        )

    with pytest.raises(EntityDeletedError):
        utils.assert_resource_does_not_exist(
            db.session, queue, utils.DeletionPolicy.DELETED
        )


def test_assert_resources_exist(db, resource_status_combo, deletion_policy):
    snaps, statuses = resource_status_combo

    exc = helpers.expected_exception_for_combined_status(
        statuses,
        deletion_policy,
    )

    if exc:
        with pytest.raises(exc):
            utils.assert_resources_exist(db.session, snaps, deletion_policy)

    else:
        # exc is None, therefore this should not throw
        utils.assert_resources_exist(db.session, snaps, deletion_policy)


def test_assert_resource_children_exist(db, resource_parent_combo, deletion_policy):
    parent_snap, _, statuses = resource_parent_combo

    exc = helpers.expected_exception_for_combined_status(
        statuses,
        deletion_policy,
    )

    if exc:
        with pytest.raises(exc):
            utils.assert_resource_children_exist(
                db.session, parent_snap, deletion_policy
            )

    else:
        # exc is None, therefore this should not throw
        utils.assert_resource_children_exist(db.session, parent_snap, deletion_policy)


def test_snapshot_exists(db, fake_data, account):
    queue = fake_data.queue(account.user, account.group)
    db.session.add(queue)
    db.session.commit()

    result = utils.snapshot_exists(db.session, queue)
    assert result

    result = utils.snapshot_exists(db.session, queue.resource_snapshot_id)
    assert result


def test_snapshot_not_exists(db, fake_data, account):
    queue = fake_data.queue(account.user, account.group)
    result = utils.snapshot_exists(db.session, queue)
    assert not result

    queue.resource_snapshot_id = 999999
    result = utils.snapshot_exists(db.session, queue)
    assert not result

    result = utils.snapshot_exists(db.session, queue.resource_snapshot_id)
    assert not result


def test_assert_snapshot_exists(db, fake_data, account):
    queue = fake_data.queue(account.user, account.group)
    db.session.add(queue)
    db.session.commit()

    utils.assert_snapshot_exists(db.session, queue)
    utils.assert_snapshot_exists(db.session, queue.resource_snapshot_id)


def test_assert_snapshot_exists_not_exists(db, fake_data, account):
    queue = fake_data.queue(account.user, account.group)

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_snapshot_exists(db.session, queue)

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_snapshot_exists(db.session, 999999)


def test_assert_snapshot_does_not_exist(db, fake_data, account):
    queue = fake_data.queue(account.user, account.group)
    db.session.add(queue)
    db.session.commit()

    with pytest.raises(EntityExistsError):
        utils.assert_snapshot_does_not_exist(db.session, queue)

    with pytest.raises(EntityExistsError):
        utils.assert_snapshot_does_not_exist(db.session, queue.resource_snapshot_id)


def test_assert_snapshot_does_not_exist_not_exists(db, fake_data, account):
    queue = fake_data.queue(account.user, account.group)

    utils.assert_snapshot_does_not_exist(db.session, queue)
    utils.assert_snapshot_does_not_exist(db.session, 999999)


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

    with pytest.raises(EntityDoesNotExistError):
        utils.delete_resource(db.session, queue)


def test_get_latest_snapshots(db, resource_status_combo, deletion_policy):

    snaps, _ = resource_status_combo

    if len(snaps) == 0:
        # Doesn't really matter which class we use for an empty combo
        snap_class = models.Queue
    else:
        snap_class = type(snaps[0])

    expected_latest_snaps = helpers.find_expected_snaps_for_deletion_policy(
        snaps, deletion_policy
    )

    latest_snaps = utils.get_latest_snapshots(
        db.session, snap_class, snaps, deletion_policy
    )

    assert _same_snapshots(expected_latest_snaps, latest_snaps)

    # Also try passing a single, for length-1 combos
    if len(snaps) == 1:
        if len(expected_latest_snaps) > 0:
            expected_latest_snap = expected_latest_snaps[0]
        else:
            expected_latest_snap = None

        latest_snap = utils.get_latest_snapshots(
            db.session, snap_class, snaps[0], deletion_policy
        )

        assert latest_snap == expected_latest_snap


def test_get_latest_child_snapshots(db, resource_parent_combo, deletion_policy):

    parent, child_snaps, _ = resource_parent_combo

    if len(child_snaps) == 0:
        # It would make more sense to query a table corresponding to a legal
        # child resource type relative to the parent type, but that would be
        # ambiguous if there is more than one legal type.  Or maybe some parent
        # types only admit a single child type, and we could use that one.  But
        # the implementation doesn't actually care.  Wrong child class just
        # means you'll query the wrong table and not get any results.  If there
        # are no children, then it doesn't matter.
        child_class = models.Queue
    else:
        child_class = type(child_snaps[0])

    expected_latest_snaps = helpers.find_expected_snaps_for_deletion_policy(
        child_snaps, deletion_policy
    )

    latest_snaps = utils.get_latest_child_snapshots(
        db.session, child_class, parent, deletion_policy
    )

    assert _same_snapshots(latest_snaps, expected_latest_snaps)


def test_get_latest_child_snapshots_parent_not_exist(db, deletion_policy):
    with pytest.raises(EntityDoesNotExistError):
        utils.get_latest_child_snapshots(
            db.session,
            models.Queue,
            999999,
            deletion_policy,
        )


def test_get_latest_child_snapshots_parent_deleted(
    db, fake_data, account, deletion_policy
):
    exp = fake_data.experiment(account.user, account.group)
    lock = models.ResourceLock(resource_lock_types.DELETE, exp.resource)
    db.session.add_all((exp, lock))
    db.session.commit()

    with pytest.raises(EntityDeletedError):
        utils.get_latest_child_snapshots(
            db.session,
            models.Queue,
            exp,
            deletion_policy,
        )


def test_set_resource_children(db, fake_data, account, resource_status_combo):

    snaps, statuses = resource_status_combo
    if len(snaps) == 0:
        # Doesn't really matter which class we use for an empty combo
        snap_class = models.Queue
    else:
        snap_class = type(snaps[0])

    exp = fake_data.experiment(account.user, account.group)
    db.session.add(exp)
    db.session.commit()

    exc = helpers.expected_exception_for_combined_status(
        statuses, utils.DeletionPolicy.NOT_DELETED
    )

    if exc:
        with pytest.raises(exc):
            utils.set_resource_children(db.session, snap_class, exp, snaps)

    else:
        result_children = utils.set_resource_children(
            db.session, snap_class, exp, snaps
        )
        db.session.commit()

        assert _same_snapshots(snaps, result_children)


def test_set_resource_children_parent_not_exist(db):
    with pytest.raises(EntityDoesNotExistError):
        utils.set_resource_children(db.session, models.Queue, 999999, [])


def test_set_resource_children_parent_deleted(db, fake_data, account):
    exp = fake_data.experiment(account.user, account.group)
    lock = models.ResourceLock(resource_lock_types.DELETE, exp.resource)
    db.session.add_all((exp, lock))
    db.session.commit()

    with pytest.raises(EntityDeletedError):
        utils.set_resource_children(db.session, models.EntryPoint, exp, [])


def test_append_resource_children(db, fake_data, account, resource_status_combo):
    snaps, statuses = resource_status_combo
    if len(snaps) == 0:
        # Doesn't really matter which class we use for an empty combo
        snap_class = models.Queue
    else:
        snap_class = type(snaps[0])

    exp = fake_data.experiment(account.user, account.group)
    db.session.add(exp)
    db.session.commit()

    exc = helpers.expected_exception_for_combined_status(
        statuses, utils.DeletionPolicy.NOT_DELETED
    )

    if exc:
        with pytest.raises(exc):
            utils.append_resource_children(db.session, snap_class, exp, snaps)

    else:
        result_children = utils.append_resource_children(
            db.session, snap_class, exp, snaps
        )
        db.session.commit()

        assert _same_snapshots(snaps, result_children)

        # Since append_resource_children() is sensitive to pre-existing
        # children and will not add the same child twice, we should be able
        # to append the children again with no effect.
        result_children = utils.append_resource_children(
            db.session, snap_class, exp, snaps
        )
        db.session.commit()

        assert _same_snapshots(snaps, result_children)


def test_append_resource_children_parent_not_exist(db):
    with pytest.raises(EntityDoesNotExistError):
        utils.append_resource_children(db.session, models.Queue, 999999, [])


def test_append_resource_children_parent_deleted(db, fake_data, account):
    exp = fake_data.experiment(account.user, account.group)
    lock = models.ResourceLock(resource_lock_types.DELETE, exp.resource)
    db.session.add_all((exp, lock))
    db.session.commit()

    with pytest.raises(EntityDeletedError):
        utils.append_resource_children(db.session, models.EntryPoint, exp, [])


def test_unlink_child(db, fake_data, account):
    exp = fake_data.experiment(account.user, account.group)

    epres1 = models.Resource("entry_point", account.group)
    ep1 = models.EntryPoint("", epres1, account.user, "ep1", "graph:", [])

    epres2 = models.Resource("entry_point", account.group)
    ep2 = models.EntryPoint("", epres2, account.user, "ep2", "graph:", [])

    exp.children.extend((ep1.resource, ep2.resource))
    db.session.add(exp)
    db.session.commit()

    assert len(exp.children) == 2
    utils.unlink_child(db.session, exp, ep1)
    db.session.commit()

    assert exp.children == [ep2.resource]


def test_unlink_child_parent_not_exist(db):
    with pytest.raises(EntityDoesNotExistError):
        utils.unlink_child(db.session, 1, 2)


def test_unlink_child_child_not_exist(db, fake_data, account):
    exp = fake_data.experiment(account.user, account.group)
    db.session.add(exp)
    db.session.commit()

    with pytest.raises(EntityDoesNotExistError):
        utils.unlink_child(db.session, exp, 999999)


def test_filter_all_unsorted(db, queue_filter_setup):

    results, count = utils.get_by_filters_paged(
        db.session,
        models.Queue,
        QueueRepository.SORTABLE_FIELDS,
        QueueRepository.SEARCHABLE_FIELDS,
        group=None,
        filters=[],  # empty list means get all; no filtering
        page_start=0,
        page_length=0,  # <=0 means get all, no page limit
        sort_by=None,
        descending=False,
        deletion_policy=utils.DeletionPolicy.NOT_DELETED,
    )

    assert count == 10
    assert len(results) == 10

    # no order guarantee, so sort both lists
    sorted_results = sorted(results, key=lambda q: q.resource_snapshot_id)
    sorted_queues = sorted(queue_filter_setup, key=lambda q: q.resource_snapshot_id)

    assert sorted_results == sorted_queues


@pytest.mark.parametrize(
    "sort_by, sort_key",
    [
        ("name", lambda q: q.name),
        ("createdOn", lambda q: q.created_on),
        # takes toooo long!
        # ("lastModifiedOn", lambda q: q.resource.last_modified_on),
        ("description", lambda q: q.description),
    ],
)
def test_filter_all_sorted(db, queue_filter_setup, sort_by, sort_key):

    results, count = utils.get_by_filters_paged(
        db.session,
        models.Queue,
        QueueRepository.SORTABLE_FIELDS,
        QueueRepository.SEARCHABLE_FIELDS,
        group=None,
        filters=[],  # empty list means get all; no filtering
        page_start=0,
        page_length=0,  # <=0 means get all, no page limit
        sort_by=sort_by,
        descending=False,
        deletion_policy=utils.DeletionPolicy.NOT_DELETED,
    )

    assert count == 10
    assert len(results) == 10

    sorted_queues = sorted(queue_filter_setup, key=sort_key)
    assert results == sorted_queues

    # Try again, this time sorting the other way
    results, count = utils.get_by_filters_paged(
        db.session,
        models.Queue,
        QueueRepository.SORTABLE_FIELDS,
        QueueRepository.SEARCHABLE_FIELDS,
        group=None,
        filters=[],  # empty list means get all; no filtering
        page_start=0,
        page_length=0,  # <=0 means get all, no page limit
        sort_by=sort_by,
        descending=True,
        deletion_policy=utils.DeletionPolicy.NOT_DELETED,
    )

    assert count == 10
    assert len(results) == 10

    sorted_queues = sorted(queue_filter_setup, key=sort_key, reverse=True)
    assert results == sorted_queues


@pytest.mark.parametrize(
    "page_start, page_length",
    [
        (0, 4),
        (1, 4),
        (5, 99),
        (99, 999),
    ],
)
def test_filter_all_paging(db, queue_filter_setup, page_start, page_length):

    results, count = utils.get_by_filters_paged(
        db.session,
        models.Queue,
        QueueRepository.SORTABLE_FIELDS,
        QueueRepository.SEARCHABLE_FIELDS,
        group=None,
        filters=[],  # empty list means get all; no filtering
        page_start=page_start,
        page_length=page_length,
        sort_by="name",
        descending=False,
        deletion_policy=utils.DeletionPolicy.NOT_DELETED,
    )

    assert count == 10
    # page_length if the page is fully contained in the data; 10 - page_start
    # if page_length takes you off the end; but no less than zero.
    assert len(results) == max(0, min(10 - page_start, page_length))

    sorted_queues = sorted(queue_filter_setup, key=lambda q: q.name)
    assert results == sorted_queues[page_start : page_start + page_length]


def test_filter_name(db, queue_filter_setup):

    results, count = utils.get_by_filters_paged(
        db.session,
        models.Queue,
        QueueRepository.SORTABLE_FIELDS,
        QueueRepository.SEARCHABLE_FIELDS,
        group=None,
        filters=[{"field": "name", "value": ["Jodi"]}],
        page_start=0,
        page_length=0,
        sort_by=None,
        descending=False,
        deletion_policy=utils.DeletionPolicy.NOT_DELETED,
    )

    jodi = next(q for q in queue_filter_setup if q.name == "Jodi")

    assert count == 1
    assert results == [jodi]

    results, count = utils.get_by_filters_paged(
        db.session,
        models.Queue,
        QueueRepository.SORTABLE_FIELDS,
        QueueRepository.SEARCHABLE_FIELDS,
        group=None,
        # when field is non-null, values are all just concatenated, so this
        # produces the same results
        filters=[{"field": "name", "value": ["Jo", "di"]}],
        page_start=0,
        page_length=0,
        sort_by=None,
        descending=False,
        deletion_policy=utils.DeletionPolicy.NOT_DELETED,
    )

    assert count == 1
    assert results == [jodi]


def test_filter_name_wild_1(db, queue_filter_setup):

    results, count = utils.get_by_filters_paged(
        db.session,
        models.Queue,
        QueueRepository.SORTABLE_FIELDS,
        QueueRepository.SEARCHABLE_FIELDS,
        group=None,
        # names which end with "i"
        filters=[{"field": "name", "value": ["*", "i"]}],
        page_start=0,
        page_length=0,
        sort_by="name",
        descending=False,
        deletion_policy=utils.DeletionPolicy.NOT_DELETED,
    )

    objs_ending_with_i = sorted(
        (q for q in queue_filter_setup if q.name.endswith("i")), key=lambda q: q.name
    )

    assert count == 3
    assert results == objs_ending_with_i


def test_filter_name_wild_2(db, queue_filter_setup):

    results, count = utils.get_by_filters_paged(
        db.session,
        models.Queue,
        QueueRepository.SORTABLE_FIELDS,
        QueueRepository.SEARCHABLE_FIELDS,
        group=None,
        filters=[{"field": "name", "value": ["Ze", "?", "da"]}],
        page_start=0,
        page_length=0,
        sort_by=None,
        descending=False,
        deletion_policy=utils.DeletionPolicy.NOT_DELETED,
    )

    zelda = next(q for q in queue_filter_setup if q.name == "Zelda")

    assert count == 1
    assert results == [zelda]


def test_filter_tag(db, queue_filter_setup):

    results, count = utils.get_by_filters_paged(
        db.session,
        models.Queue,
        QueueRepository.SORTABLE_FIELDS,
        QueueRepository.SEARCHABLE_FIELDS,
        group=None,
        filters=[{"field": "tag", "value": ["continue"]}],
        page_start=0,
        page_length=0,
        sort_by="name",
        descending=False,
        deletion_policy=utils.DeletionPolicy.NOT_DELETED,
    )

    continues = sorted(
        (q for q in queue_filter_setup if "continue" in (tag.name for tag in q.tags)),
        key=lambda q: q.name,
    )

    assert count == len(continues)
    assert results == continues


def test_filter_null_field_1(db, queue_filter_setup):

    # "down" just happens to be a word which occurs both as a tag
    # and in a description.  ("continue" is another one.)
    results, count = utils.get_by_filters_paged(
        db.session,
        models.Queue,
        QueueRepository.SORTABLE_FIELDS,
        QueueRepository.SEARCHABLE_FIELDS,
        group=None,
        # None field name means search all fields in a fuzzy way
        filters=[{"field": None, "value": ["down"]}],
        page_start=0,
        page_length=0,
        sort_by="name",
        descending=False,
        deletion_policy=utils.DeletionPolicy.NOT_DELETED,
    )

    downs = sorted(
        (
            q
            for q in queue_filter_setup
            if "down" in (tag.name for tag in q.tags)
            or "down" in q.description
            or "down" in q.name
        ),
        key=lambda q: q.name,
    )

    assert count == len(downs)
    assert results == downs


def test_filter_null_field_2(db, queue_filter_setup):

    results, count = utils.get_by_filters_paged(
        db.session,
        models.Queue,
        QueueRepository.SORTABLE_FIELDS,
        QueueRepository.SEARCHABLE_FIELDS,
        group=None,
        # Find objects with two "o"s in any of their searchable fields
        filters=[{"field": None, "value": ["o", "o"]}],
        page_start=0,
        page_length=0,
        sort_by="name",
        descending=False,
        deletion_policy=utils.DeletionPolicy.NOT_DELETED,
    )

    # equivalent to the search above
    o_re = re.compile(r"o.*o", re.S)

    oos = sorted(
        (
            q
            for q in queue_filter_setup
            if any(o_re.search(t.name) for t in q.tags)
            or o_re.search(q.description)
            or o_re.search(q.name)
        ),
        key=lambda q: q.name,
    )

    assert count == len(oos)
    assert results == oos


def test_filter_unsupported_sort(db):
    with pytest.raises(SortParameterValidationError):
        utils.get_by_filters_paged(
            db.session,
            models.Queue,
            QueueRepository.SORTABLE_FIELDS,
            QueueRepository.SEARCHABLE_FIELDS,
            group=None,
            filters=[],
            page_start=0,
            page_length=0,
            sort_by="wrong",
            descending=False,
            deletion_policy=utils.DeletionPolicy.NOT_DELETED,
        )


def test_filter_unsupported_field(db):
    with pytest.raises(SearchParseError):
        utils.get_by_filters_paged(
            db.session,
            models.Queue,
            QueueRepository.SORTABLE_FIELDS,
            QueueRepository.SEARCHABLE_FIELDS,
            group=None,
            filters=[{"field": "wrong", "value": ["foo"]}],
            page_start=0,
            page_length=0,
            sort_by=None,
            descending=False,
            deletion_policy=utils.DeletionPolicy.NOT_DELETED,
        )
