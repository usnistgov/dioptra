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
from dioptra.restapi.db.models.constants import group_lock_types, resource_lock_types
from dioptra.restapi.db.repository.queues import QueueRepository
from dioptra.restapi.errors import (
    DraftAlreadyExistsError,
    DraftDoesNotExistError,
    EntityDeletedError,
    EntityDoesNotExistError,
    EntityExistsError,
    MismatchedResourceTypeError,
    ReadOnlyLockError,
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


@pytest.fixture
def resource_status(existence_status, db_session, account, fake_data):
    """
    This fixture produces a resource according to each ExistenceResult value,
    e.g. exists, deleted, not-exists.  Each produced value is a
    (snapshot, status) 2-tuple, giving the resource created and corresponding
    status value.
    """

    queue = fake_data.queue(account.user, account.group)

    if existence_status is not utils.ExistenceResult.DOES_NOT_EXIST:
        db_session.add(queue)

        if existence_status is utils.ExistenceResult.DELETED:
            lock = models.ResourceLock(resource_lock_types.DELETE, queue.resource)
            db_session.add(lock)

        db_session.commit()

    return queue, existence_status


@pytest.fixture(
    params=_STATUS_COMBOS,
    ids=_STATUS_COMBO_IDS,
)
def resource_status_combo(request, db_session, account, fake_data):
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
        ep = models.EntryPoint(
            "", epres, account.user, f"ep{idx}", "graph:", "artifacts_input:", [], []
        )

        # If creating an existing/deleted resource, create several snapshots;
        # this fixture will just return the latest one.  It allows better
        # testing of methods to get latest snapshots, if there are old
        # snapshots (actual wrong answers).
        if status in (utils.ExistenceResult.EXISTS, utils.ExistenceResult.DELETED):

            db_session.add(ep)

            for snap_idx in range(3):
                ep = models.EntryPoint(
                    ep.description,
                    ep.resource,
                    ep.creator,
                    f"ep{idx}-{snap_idx}",
                    ep.task_graph,
                    ep.artifact_graph,
                    ep.parameters,
                    ep.artifact_parameters,
                )
                # make sure this is later than the previous snapshot
                ep.created_on = ep.created_on + datetime.timedelta(hours=snap_idx + 1)
                db_session.add(ep)

            if status is utils.ExistenceResult.DELETED:
                lock = models.ResourceLock(resource_lock_types.DELETE, epres)
                db_session.add(lock)

        # else: status is DOES_NOT_EXIST, do not add to session; no point in
        # creating additional snapshots.

        child_snaps.append(ep)

    db_session.commit()

    return child_snaps, set(request.param)


@pytest.fixture
def resource_parent_combo(resource_status_combo, db_session, account, fake_data):
    """
    This fixture produces (parent snap, child snaps, status_set) 3-tuples, for
    all combinations of child status.
    """

    child_snaps, statuses = resource_status_combo

    parent = fake_data.experiment(account.user, account.group)
    db_session.add(parent)

    # Add the exists/deleted children to parent, but not the not-exists
    # children.  That way, the not-exists children aren't inadvertently added
    # to the DB when we commit.
    not_exists_children = []
    for child in child_snaps:
        if child.resource_snapshot_id is not None:
            parent.children.append(child.resource)
        else:
            not_exists_children.append(child)

    db_session.commit()

    # Now, add the non-exists children, and do not commit.
    parent.children.extend(c.resource for c in not_exists_children)

    try:
        # Prevent the non-exists children from being accidentally added due
        # to autoflush, which messes up the test setup.
        db_session.autoflush = False
        yield parent, child_snaps, statuses
    finally:
        db_session.autoflush = True
        # Rollback is necessary to remove pending table changes from the
        # transaction before the rest of the unit test teardown drops all the
        # tables.  Dropping and changing the same table in the same transaction
        # doesn't work well.
        db_session.rollback()


@pytest.fixture
def queue_filter_setup(account, db_session, fake_data):

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
        db_session.add(queue_object)

    db_session.commit()

    # Create tag objects
    tag_names = set(itertools.chain.from_iterable(info["tags"] for info in queue_info))
    tags_by_name = {}
    for tag_name in tag_names:
        tag_object = fake_data.tag(account.user, account.group)
        tag_object.name = tag_name
        tags_by_name[tag_name] = tag_object
        db_session.add(tag_object)

    db_session.commit()

    # Link tags to queues
    for info, queue_object in zip(queue_info, queue_objects):
        for tag_name in info["tags"]:
            queue_object.tags.append(tags_by_name[tag_name])

    db_session.commit()

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


def test_user_exists(db_session, account):
    result = utils.user_exists(db_session, account.user)

    assert result == utils.ExistenceResult.EXISTS


def test_user_not_exists(db_session, account):
    user2 = models.User("user2", "password2", "user2@example.org")
    result = utils.user_exists(db_session, user2)

    assert result == utils.ExistenceResult.DOES_NOT_EXIST

    # Also try with bad ID
    user2.user_id = 999999
    result = utils.user_exists(db_session, user2)

    assert result == utils.ExistenceResult.DOES_NOT_EXIST


def test_user_deleted(db_session, account):
    user2 = models.User("user2", "password2", "user2@example.org")
    user_delete_lock = models.UserLock("delete", user2)
    db_session.add_all((user2, user_delete_lock))
    db_session.commit()

    result = utils.user_exists(db_session, user2)
    assert result == utils.ExistenceResult.DELETED


def test_assert_user_exists(db_session, account):
    utils.assert_user_exists(db_session, account.user, utils.DeletionPolicy.NOT_DELETED)
    utils.assert_user_exists(db_session, account.user, utils.DeletionPolicy.ANY)

    with pytest.raises(EntityExistsError):
        utils.assert_user_exists(db_session, account.user, utils.DeletionPolicy.DELETED)


def test_assert_user_exists_not_exists(db_session, account):
    user2 = models.User("user2", "password2", "user2@example.org")

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_user_exists(db_session, user2, utils.DeletionPolicy.NOT_DELETED)

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_user_exists(db_session, user2, utils.DeletionPolicy.DELETED)

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_user_exists(db_session, user2, utils.DeletionPolicy.ANY)

    # Also try with bad ID
    user2.user_id = 999999

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_user_exists(db_session, user2, utils.DeletionPolicy.NOT_DELETED)

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_user_exists(db_session, user2, utils.DeletionPolicy.DELETED)

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_user_exists(db_session, user2, utils.DeletionPolicy.ANY)


def test_assert_user_exists_deleted(db_session, account):
    user2 = models.User("user2", "password2", "user2@example.org")
    user_delete_lock = models.UserLock("delete", user2)
    db_session.add_all((user2, user_delete_lock))
    db_session.commit()

    with pytest.raises(EntityDeletedError):
        utils.assert_user_exists(db_session, user2, utils.DeletionPolicy.NOT_DELETED)

    utils.assert_user_exists(db_session, user2, utils.DeletionPolicy.DELETED)
    utils.assert_user_exists(db_session, user2, utils.DeletionPolicy.ANY)


def test_group_exists(db_session, account):
    result = utils.group_exists(db_session, account.group)

    assert result == utils.ExistenceResult.EXISTS


def test_group_not_exists(db_session, account):
    user2 = models.User("user2", "password2", "user2@example.org")
    group2 = models.Group("group2", user2)

    result = utils.group_exists(db_session, group2)

    assert result == utils.ExistenceResult.DOES_NOT_EXIST

    # Also try with bad ID
    group2.group_id = 999999
    result = utils.group_exists(db_session, group2)

    assert result == utils.ExistenceResult.DOES_NOT_EXIST


def test_group_deleted(db_session, account):
    user2 = models.User("user2", "password2", "user2@example.org")
    group2 = models.Group("group2", user2)
    group_delete_lock = models.GroupLock("delete", group2)
    db_session.add_all((user2, group2, group_delete_lock))
    db_session.commit()

    result = utils.group_exists(db_session, group2)
    assert result == utils.ExistenceResult.DELETED


def test_assert_group_exists(db_session, account):
    utils.assert_group_exists(
        db_session, account.group, utils.DeletionPolicy.NOT_DELETED
    )
    utils.assert_group_exists(db_session, account.group, utils.DeletionPolicy.ANY)

    with pytest.raises(EntityExistsError):
        utils.assert_group_exists(
            db_session, account.group, utils.DeletionPolicy.DELETED
        )


def test_assert_group_exists_not_exists(db_session, account):
    user2 = models.User("user2", "password2", "group2@example.org")
    group2 = models.Group("group2", user2)

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_group_exists(db_session, group2, utils.DeletionPolicy.NOT_DELETED)

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_group_exists(db_session, group2, utils.DeletionPolicy.DELETED)

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_group_exists(db_session, group2, utils.DeletionPolicy.ANY)

    # Also try with bad ID
    group2.group_id = 999999

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_group_exists(db_session, group2, utils.DeletionPolicy.NOT_DELETED)

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_group_exists(db_session, group2, utils.DeletionPolicy.DELETED)

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_group_exists(db_session, group2, utils.DeletionPolicy.ANY)


def test_assert_group_exists_deleted(db_session, account):
    user2 = models.User("user2", "password2", "group2@example.org")
    group2 = models.Group("group2", user2)
    group_delete_lock = models.GroupLock("delete", group2)
    db_session.add_all((group2, user2, group_delete_lock))
    db_session.commit()

    with pytest.raises(EntityDeletedError):
        utils.assert_group_exists(db_session, group2, utils.DeletionPolicy.NOT_DELETED)

    utils.assert_group_exists(db_session, group2, utils.DeletionPolicy.DELETED)
    utils.assert_group_exists(db_session, group2, utils.DeletionPolicy.ANY)


def test_assert_user_does_not_exist_user_exists(db_session, account):
    with pytest.raises(EntityExistsError):
        utils.assert_user_does_not_exist(
            db_session, account.user, utils.DeletionPolicy.NOT_DELETED
        )

    utils.assert_user_does_not_exist(
        db_session, account.user, utils.DeletionPolicy.DELETED
    )

    with pytest.raises(EntityExistsError):
        utils.assert_user_does_not_exist(
            db_session, account.user, utils.DeletionPolicy.ANY
        )


def test_assert_user_does_not_exist_user_not_exists(db_session, account):
    user2 = models.User("user2", "password2", "user2@example.org")

    utils.assert_user_does_not_exist(
        db_session, user2, utils.DeletionPolicy.NOT_DELETED
    )
    utils.assert_user_does_not_exist(db_session, user2, utils.DeletionPolicy.DELETED)
    utils.assert_user_does_not_exist(db_session, user2, utils.DeletionPolicy.ANY)

    # Also try with bad ID
    user2.user_id = 999999

    utils.assert_user_does_not_exist(
        db_session, user2, utils.DeletionPolicy.NOT_DELETED
    )
    utils.assert_user_does_not_exist(db_session, user2, utils.DeletionPolicy.DELETED)
    utils.assert_user_does_not_exist(db_session, user2, utils.DeletionPolicy.ANY)


def test_assert_user_does_not_exist_user_deleted(db_session, account):
    user2 = models.User("user2", "password2", "user2@example.org")
    user_delete_lock = models.UserLock("delete", user2)
    db_session.add_all((user2, user_delete_lock))
    db_session.commit()

    utils.assert_user_does_not_exist(
        db_session, user2, utils.DeletionPolicy.NOT_DELETED
    )

    with pytest.raises(EntityDeletedError):
        utils.assert_user_does_not_exist(
            db_session, user2, utils.DeletionPolicy.DELETED
        )

    with pytest.raises(EntityDeletedError):
        utils.assert_user_does_not_exist(db_session, user2, utils.DeletionPolicy.ANY)


def test_assert_group_does_not_exist_group_exists(db_session, account):
    with pytest.raises(EntityExistsError):
        utils.assert_group_does_not_exist(
            db_session, account.group, utils.DeletionPolicy.NOT_DELETED
        )

    utils.assert_group_does_not_exist(
        db_session, account.group, utils.DeletionPolicy.DELETED
    )

    with pytest.raises(EntityExistsError):
        utils.assert_group_does_not_exist(
            db_session, account.group, utils.DeletionPolicy.ANY
        )


def test_assert_group_does_not_exist_group_not_exists(db_session, account):
    user2 = models.User("user2", "password2", "user2@example.org")
    group2 = models.Group("group2", user2)

    utils.assert_group_does_not_exist(
        db_session, group2, utils.DeletionPolicy.NOT_DELETED
    )
    utils.assert_group_does_not_exist(db_session, group2, utils.DeletionPolicy.DELETED)
    utils.assert_group_does_not_exist(db_session, group2, utils.DeletionPolicy.ANY)

    # Also try with bad ID
    group2.group_id = 999999

    utils.assert_group_does_not_exist(
        db_session, group2, utils.DeletionPolicy.NOT_DELETED
    )
    utils.assert_group_does_not_exist(db_session, group2, utils.DeletionPolicy.DELETED)
    utils.assert_group_does_not_exist(db_session, group2, utils.DeletionPolicy.ANY)


def test_assert_group_does_not_exist_group_deleted(db_session, account):
    user2 = models.User("user2", "password2", "user2@example.org")
    group2 = models.Group("group2", user2)
    group_delete_lock = models.GroupLock("delete", group2)
    db_session.add_all((user2, group2, group_delete_lock))
    db_session.commit()

    utils.assert_group_does_not_exist(
        db_session, group2, utils.DeletionPolicy.NOT_DELETED
    )

    with pytest.raises(EntityDeletedError):
        utils.assert_group_does_not_exist(
            db_session, group2, utils.DeletionPolicy.DELETED
        )

    with pytest.raises(EntityDeletedError):
        utils.assert_group_does_not_exist(db_session, group2, utils.DeletionPolicy.ANY)


def test_resource_exists(db_session, fake_data, account):
    queue = fake_data.queue(account.user, account.group)
    db_session.add(queue)
    db_session.commit()

    result = utils.resource_exists(db_session, queue)
    assert result is utils.ExistenceResult.EXISTS


def test_resource_not_exists(db_session, fake_data, account):
    queue = fake_data.queue(account.user, account.group)

    result = utils.resource_exists(db_session, queue)
    assert result is utils.ExistenceResult.DOES_NOT_EXIST


def test_resource_deleted(db_session, fake_data, account):
    queue = fake_data.queue(account.user, account.group)
    db_session.add(queue)
    db_session.commit()

    lock = models.ResourceLock("delete", queue.resource)
    db_session.add(lock)
    db_session.commit()

    result = utils.resource_exists(db_session, queue)
    assert result is utils.ExistenceResult.DELETED


def test_resources_exist(db_session, fake_data, account):
    queues = [fake_data.queue(account.user, account.group) for _ in range(3)]

    queue_lock = models.ResourceLock("delete", queues[2].resource)

    db_session.add_all(queues)
    db_session.add(queue_lock)
    db_session.commit()

    other_queue = fake_data.queue(account.user, account.group)
    queues.append(other_queue)

    expected = {
        queues[0].resource_id: utils.ExistenceResult.EXISTS,
        queues[1].resource_id: utils.ExistenceResult.EXISTS,
        queues[2].resource_id: utils.ExistenceResult.DELETED,
        # other_queue doesn't show up here, since it was not committed and
        # never got an ID.
    }

    actual = utils.resources_exist(db_session, queues)

    assert actual == expected

    # try with just a bad ID
    actual = utils.resources_exist(db_session, [999999])

    assert actual == {999999: utils.ExistenceResult.DOES_NOT_EXIST}


def test_resource_children_exist(db_session, fake_data, account):

    exp = fake_data.experiment(account.user, account.group)

    ep1res = models.Resource("entry_point", account.group)
    ep1 = models.EntryPoint(
        "", ep1res, account.user, "ep1", "graph:", "artifact_inputs:", [], []
    )

    ep2res = models.Resource("entry_point", account.group)
    ep2 = models.EntryPoint(
        "", ep2res, account.user, "ep2", "graph:", "artifact_inputs:", [], []
    )
    ep2lock = models.ResourceLock(resource_lock_types.DELETE, ep2res)

    exp.children.extend((ep1res, ep2res))

    db_session.add_all((exp, ep1, ep2, ep2lock))
    db_session.commit()

    child_status = utils.resource_children_exist(db_session, exp)

    expected = {
        ep1.resource_id: utils.ExistenceResult.EXISTS,
        ep2.resource_id: utils.ExistenceResult.DELETED,
    }

    assert child_status == expected

    # try with just the experiment ID:
    child_status = utils.resource_children_exist(db_session, exp.resource_id)
    assert child_status == expected


def test_resource_modifiable_modifiable(db_session, fake_data, account):
    queue = fake_data.queue(account.user, account.group)
    db_session.add(queue)
    db_session.commit()

    assert utils.resource_modifiable(db_session, queue.resource)
    assert utils.resource_modifiable(db_session, queue)
    assert utils.resource_modifiable(db_session, queue.resource_id)
    assert utils.resource_modifiable(db_session, 999999)


def test_resource_modifiable_readonly(db_session, fake_data, account):
    queue = fake_data.queue(account.user, account.group)
    lock = models.ResourceLock(resource_lock_types.READONLY, queue.resource)
    db_session.add_all((queue, lock))
    db_session.commit()

    assert not utils.resource_modifiable(db_session, queue.resource)
    assert not utils.resource_modifiable(db_session, queue)
    assert not utils.resource_modifiable(db_session, queue.resource_id)


def test_assert_resource_exists(db_session, resource_status, deletion_policy):

    snap, status = resource_status

    exc = helpers.expected_exception_for_combined_status([status], deletion_policy)

    if exc:
        with pytest.raises(exc):
            utils.assert_resource_exists(db_session, snap, deletion_policy)

        # Try with just an ID
        if snap.resource_id is not None:
            with pytest.raises(exc):
                utils.assert_resource_exists(
                    db_session, snap.resource_id, deletion_policy
                )

    else:
        utils.assert_resource_exists(db_session, snap, deletion_policy)

        # Try with just an ID
        if snap.resource_id is not None:
            utils.assert_resource_exists(db_session, snap.resource_id, deletion_policy)


def test_assert_resource_exists_bad_id(db_session):
    with pytest.raises(EntityDoesNotExistError):
        utils.assert_resource_exists(
            db_session, 999999, utils.DeletionPolicy.NOT_DELETED
        )

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_resource_exists(db_session, 999999, utils.DeletionPolicy.ANY)

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_resource_exists(db_session, 999999, utils.DeletionPolicy.DELETED)


def test_assert_resource_does_not_exist(db_session, resource_status, deletion_policy):
    snap, status = resource_status

    exc = helpers.expected_exception_for_not_exists(status, deletion_policy)

    if exc:
        with pytest.raises(exc):
            utils.assert_resource_does_not_exist(db_session, snap, deletion_policy)

        if snap.resource_id is not None:
            # Try with just an ID
            with pytest.raises(exc):
                utils.assert_resource_does_not_exist(
                    db_session, snap.resource_id, deletion_policy
                )

    else:
        utils.assert_resource_does_not_exist(db_session, snap, deletion_policy)

        if snap.resource_id is not None:
            # Try with just an ID
            utils.assert_resource_does_not_exist(
                db_session, snap.resource_id, deletion_policy
            )


def test_assert_resource_does_not_exist_bad_id(db_session):
    utils.assert_resource_does_not_exist(
        db_session, 999999, utils.DeletionPolicy.NOT_DELETED
    )

    utils.assert_resource_does_not_exist(db_session, 999999, utils.DeletionPolicy.ANY)

    utils.assert_resource_does_not_exist(
        db_session, 999999, utils.DeletionPolicy.DELETED
    )


def test_assert_resources_exist(db_session, resource_status_combo, deletion_policy):
    snaps, statuses = resource_status_combo

    exc = helpers.expected_exception_for_combined_status(
        statuses,
        deletion_policy,
    )

    if exc:
        with pytest.raises(exc):
            utils.assert_resources_exist(db_session, snaps, deletion_policy)

    else:
        # exc is None, therefore this should not throw
        utils.assert_resources_exist(db_session, snaps, deletion_policy)


def test_assert_resources_exist_non_sized(
    db_session, resource_status_combo, deletion_policy
):
    snaps, statuses = resource_status_combo

    # This is iterable, but not len-able (i.e. not "sized")
    snaps_nonsized = (snap for snap in snaps)

    # resources_exist() produces no results for these does-not-exist objects
    # since they have no ID.  And since snaps_nonsized isn't len-able, their
    # presence can't be inferred that way either.  So they will basically be
    # ignored.  So we expect exceptions on that basis.
    statuses_except_not_exists = [
        s for s in statuses if s is not utils.ExistenceResult.DOES_NOT_EXIST
    ]

    exc = helpers.expected_exception_for_combined_status(
        statuses_except_not_exists,
        deletion_policy,
    )

    if exc:
        with pytest.raises(exc):
            utils.assert_resources_exist(db_session, snaps_nonsized, deletion_policy)

    else:
        # exc is None, therefore this should not throw
        utils.assert_resources_exist(db_session, snaps_nonsized, deletion_policy)


def test_assert_resources_exist_via_ids(
    db_session, resource_status_combo, deletion_policy
):
    snaps, statuses = resource_status_combo

    # Do the check via IDs, and use "999999" as a stand-in for non-existent
    # resources.
    snap_ids = [snap.resource_id or 999999 for snap in snaps]

    exc = helpers.expected_exception_for_combined_status(
        statuses,
        deletion_policy,
    )

    if exc:
        with pytest.raises(exc):
            utils.assert_resources_exist(db_session, snap_ids, deletion_policy)

    else:
        # exc is None, therefore this should not throw
        utils.assert_resources_exist(db_session, snap_ids, deletion_policy)


def test_assert_resource_children_exist(
    db_session, resource_parent_combo, deletion_policy
):
    parent_snap, _, statuses = resource_parent_combo

    exc = helpers.expected_exception_for_combined_status(
        statuses,
        deletion_policy,
    )

    if exc:
        with pytest.raises(exc):
            utils.assert_resource_children_exist(
                db_session, parent_snap, deletion_policy
            )

    else:
        # exc is None, therefore this should not throw
        utils.assert_resource_children_exist(db_session, parent_snap, deletion_policy)


def test_assert_resource_children_exist_via_parent_id(
    db_session, resource_parent_combo, deletion_policy
):
    parent_snap, _, statuses = resource_parent_combo

    # When given a parent ID, resource_children_exist() can't consult a
    # "children" attribute to get the children, it has to query the database.
    # Obviously, it will not find non-existent children that way.  Therefore,
    # they will be effectively ignored.  So we expect exceptions on that basis.
    statuses_except_not_exists = [
        s for s in statuses if s is not utils.ExistenceResult.DOES_NOT_EXIST
    ]

    exc = helpers.expected_exception_for_combined_status(
        statuses_except_not_exists,
        deletion_policy,
    )

    if exc:
        with pytest.raises(exc):
            utils.assert_resource_children_exist(
                db_session, parent_snap.resource_id, deletion_policy
            )

    else:
        # exc is None, therefore this should not throw
        utils.assert_resource_children_exist(
            db_session, parent_snap.resource_id, deletion_policy
        )


def test_assert_resource_modifiable_modifiable(db_session, fake_data, account):
    queue = fake_data.queue(account.user, account.group)

    utils.assert_resource_modifiable(db_session, queue)
    utils.assert_resource_modifiable(db_session, queue.resource)
    utils.assert_resource_modifiable(db_session, 999999)

    db_session.add(queue)
    db_session.commit()
    utils.assert_resource_modifiable(db_session, queue)
    utils.assert_resource_modifiable(db_session, queue.resource)
    utils.assert_resource_modifiable(db_session, queue.resource_id)


def test_assert_resource_modifiable_readonly(db_session, fake_data, account):
    queue = fake_data.queue(account.user, account.group)
    lock = models.ResourceLock(resource_lock_types.READONLY, queue.resource)
    db_session.add_all((queue, lock))
    db_session.commit()

    with pytest.raises(ReadOnlyLockError):
        utils.assert_resource_modifiable(db_session, queue)

    with pytest.raises(ReadOnlyLockError):
        utils.assert_resource_modifiable(db_session, queue.resource)

    with pytest.raises(ReadOnlyLockError):
        utils.assert_resource_modifiable(db_session, queue.resource_id)


@pytest.mark.parametrize(
    "resource_type, should_error",
    [
        ("job", True),
        ("queue", False),
    ],
)
def test_assert_resource_type_resource(
    db_session, account, resource_type, should_error
):
    resource = models.Resource(resource_type=resource_type, owner=account.group)

    if should_error:
        with pytest.raises(MismatchedResourceTypeError):
            utils.assert_resource_type(db_session, resource, "queue")
    else:
        utils.assert_resource_type(db_session, resource, "queue")


@pytest.mark.parametrize(
    "resource_type, snap_type, should_error",
    [
        ("queue", "queue", False),
        ("queue", "job", True),
        ("job", "queue", True),
        ("job", "job", True),
    ],
)
def test_assert_resource_type_snapshot(
    db_session, account, resource_type, snap_type, should_error
):
    resource = models.Resource(resource_type=resource_type, owner=account.group)
    snap = models.Queue("description", resource, account.user, "queue1")
    snap.resource_type = snap_type

    if should_error:
        with pytest.raises(MismatchedResourceTypeError):
            utils.assert_resource_type(db_session, snap, "queue")
    else:
        utils.assert_resource_type(db_session, snap, "queue")


def test_assert_resource_type_id(db_session, fake_data, account):
    queue = fake_data.queue(account.user, account.group)
    db_session.add(queue)
    db_session.commit()

    utils.assert_resource_type(db_session, queue.resource_id, "queue")

    with pytest.raises(MismatchedResourceTypeError):
        utils.assert_resource_type(db_session, queue.resource_id, "job")

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_resource_type(db_session, 999999, "queue")


def test_snapshot_exists(db_session, fake_data, account):
    queue = fake_data.queue(account.user, account.group)
    db_session.add(queue)
    db_session.commit()

    result = utils.snapshot_exists(db_session, queue)
    assert result

    result = utils.snapshot_exists(db_session, queue.resource_snapshot_id)
    assert result


def test_snapshot_not_exists(db_session, fake_data, account):
    queue = fake_data.queue(account.user, account.group)
    result = utils.snapshot_exists(db_session, queue)
    assert not result

    queue.resource_snapshot_id = 999999
    result = utils.snapshot_exists(db_session, queue)
    assert not result

    result = utils.snapshot_exists(db_session, queue.resource_snapshot_id)
    assert not result


def test_assert_snapshot_exists(db_session, fake_data, account):
    queue = fake_data.queue(account.user, account.group)
    db_session.add(queue)
    db_session.commit()

    utils.assert_snapshot_exists(db_session, queue)
    utils.assert_snapshot_exists(db_session, queue.resource_snapshot_id)


def test_assert_snapshot_exists_not_exists(db_session, fake_data, account):
    queue = fake_data.queue(account.user, account.group)

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_snapshot_exists(db_session, queue)

    with pytest.raises(EntityDoesNotExistError):
        utils.assert_snapshot_exists(db_session, 999999)


def test_assert_snapshot_does_not_exist(db_session, fake_data, account):
    queue = fake_data.queue(account.user, account.group)
    db_session.add(queue)
    db_session.commit()

    with pytest.raises(EntityExistsError):
        utils.assert_snapshot_does_not_exist(db_session, queue)

    with pytest.raises(EntityExistsError):
        utils.assert_snapshot_does_not_exist(db_session, queue.resource_snapshot_id)


def test_assert_snapshot_does_not_exist_not_exists(db_session, fake_data, account):
    queue = fake_data.queue(account.user, account.group)

    utils.assert_snapshot_does_not_exist(db_session, queue)
    utils.assert_snapshot_does_not_exist(db_session, 999999)


def test_draft_exists(db_session, account):
    draft = models.DraftResource("queue", {}, account.group, account.user)
    db_session.add(draft)
    db_session.commit()

    assert utils.draft_exists(db_session, draft)
    assert utils.draft_exists(db_session, draft.draft_resource_id)
    assert not utils.draft_exists(db_session, 999999)

    draft_not_saved = models.DraftResource("queue", {}, account.group, account.user)
    assert not utils.draft_exists(db_session, draft_not_saved)


def test_assert_draft_exists(db_session, account):
    draft = models.DraftResource("queue", {}, account.group, account.user)
    db_session.add(draft)
    db_session.commit()

    utils.assert_draft_exists(db_session, draft)
    utils.assert_draft_exists(db_session, draft.draft_resource_id)

    with pytest.raises(DraftDoesNotExistError):
        utils.assert_draft_exists(db_session, 999999)

    draft_not_saved = models.DraftResource("queue", {}, account.group, account.user)
    with pytest.raises(DraftDoesNotExistError):
        utils.assert_draft_exists(db_session, draft_not_saved)


def test_assert_draft_does_not_exist(db_session, account):
    draft = models.DraftResource("queue", {}, account.group, account.user)
    db_session.add(draft)
    db_session.commit()

    with pytest.raises(DraftAlreadyExistsError):
        utils.assert_draft_does_not_exist(db_session, draft)

    with pytest.raises(DraftAlreadyExistsError):
        utils.assert_draft_does_not_exist(db_session, draft.draft_resource_id)

    utils.assert_draft_does_not_exist(db_session, 999999)

    draft_not_saved = models.DraftResource("queue", {}, account.group, account.user)
    utils.assert_draft_does_not_exist(db_session, draft_not_saved)


def test_delete_resource(db_session, account, fake_data):
    queue = fake_data.queue(account.user, account.group)
    db_session.add(queue)
    db_session.commit()

    utils.delete_resource(db_session, queue)

    lock = db_session.get(
        models.ResourceLock, (queue.resource_id, resource_lock_types.DELETE)
    )
    assert lock

    # Should be a no-op
    utils.delete_resource(db_session, queue)


def test_delete_resource_not_exists(db_session, account, fake_data):
    queue = fake_data.queue(account.user, account.group)

    with pytest.raises(EntityDoesNotExistError):
        utils.delete_resource(db_session, queue)


def test_get_resource_lock_types(db_session, account, fake_data):
    queue = fake_data.queue(account.user, account.group)
    delete_lock = models.ResourceLock(resource_lock_types.DELETE, queue.resource)
    readonly_lock = models.ResourceLock(resource_lock_types.READONLY, queue.resource)

    db_session.add_all((queue, delete_lock, readonly_lock))
    db_session.commit()

    lock_types = utils.get_resource_lock_types(db_session, queue)
    assert lock_types == {
        utils.ResourceLockType.READONLY,
        utils.ResourceLockType.DELETED,
    }

    lock_types = utils.get_resource_lock_types(db_session, queue.resource)
    assert lock_types == {
        utils.ResourceLockType.READONLY,
        utils.ResourceLockType.DELETED,
    }

    lock_types = utils.get_resource_lock_types(db_session, queue.resource_id)
    assert lock_types == {
        utils.ResourceLockType.READONLY,
        utils.ResourceLockType.DELETED,
    }

    lock_types = utils.get_resource_lock_types(db_session, 999999)
    assert not lock_types


def test_add_resource_lock_types_resource_not_exist(db_session, account, fake_data):
    queue = fake_data.queue(account.user, account.group)

    # Ok to add locks to a non-existent resource, if an object is passed
    utils.add_resource_lock_types(
        db_session,
        queue,
        {utils.ResourceLockType.READONLY, utils.ResourceLockType.DELETED},
    )

    assert len(queue.resource.locks) == 2
    assert any(
        lock.resource_lock_type == resource_lock_types.DELETE
        for lock in queue.resource.locks
    )
    assert any(
        lock.resource_lock_type == resource_lock_types.READONLY
        for lock in queue.resource.locks
    )
    # important since we didn't commit the above changes
    db_session.rollback()

    # using non-existent resource ID will cause an error
    with pytest.raises(EntityDoesNotExistError):
        utils.add_resource_lock_types(
            db_session,
            999999,
            {utils.ResourceLockType.READONLY, utils.ResourceLockType.DELETED},
        )


def test_add_resource_lock_types_resource_exists(db_session, account, fake_data):
    queue = fake_data.queue(account.user, account.group)
    db_session.add(queue)
    db_session.commit()

    utils.add_resource_lock_types(
        db_session,
        queue,
        {utils.ResourceLockType.READONLY, utils.ResourceLockType.DELETED},
    )
    db_session.commit()

    assert queue.resource.is_readonly
    assert queue.resource.is_deleted

    # add a lock the resource already has; should be ok (even though it is
    # deleted), since we're not actually making any changes
    utils.add_resource_lock_types(db_session, queue, {utils.ResourceLockType.READONLY})
    db_session.commit()

    assert queue.resource.is_readonly
    assert queue.resource.is_deleted

    # add no locks; should not change anything
    utils.add_resource_lock_types(
        db_session,
        queue,
        set(),
    )
    db_session.commit()

    assert queue.resource.is_readonly
    assert queue.resource.is_deleted


def test_add_resource_lock_types_resource_deleted(db_session, account, fake_data):
    queue = fake_data.queue(account.user, account.group)
    lock = models.ResourceLock(resource_lock_types.DELETE, queue.resource)
    db_session.add_all((queue, lock))
    db_session.commit()

    # deleting a deleted resource is ok
    utils.add_resource_lock_types(db_session, queue, {utils.ResourceLockType.DELETED})
    db_session.commit()

    assert queue.resource.is_deleted
    assert not queue.resource.is_readonly

    # other locks on deleted resources are not ok
    with pytest.raises(EntityDeletedError):
        utils.add_resource_lock_types(
            db_session, queue, {utils.ResourceLockType.READONLY}
        )

    # adding no locks is ok
    utils.add_resource_lock_types(db_session, queue, set())
    db_session.commit()

    assert queue.resource.is_deleted
    assert not queue.resource.is_readonly


def test_add_resource_lock_types_resource_readonly(db_session, account, fake_data):
    queue = fake_data.queue(account.user, account.group)
    lock = models.ResourceLock(resource_lock_types.READONLY, queue.resource)
    db_session.add_all((queue, lock))
    db_session.commit()

    # deleting a readonly resource is not ok
    with pytest.raises(ReadOnlyLockError):
        utils.add_resource_lock_types(
            db_session, queue, {utils.ResourceLockType.DELETED}
        )

    # adding readonly to a readonly resource is ok
    utils.add_resource_lock_types(db_session, queue, {utils.ResourceLockType.READONLY})

    assert not queue.resource.is_deleted
    assert queue.resource.is_readonly

    # adding no locks is ok
    utils.add_resource_lock_types(db_session, queue, set())
    db_session.commit()

    assert not queue.resource.is_deleted
    assert queue.resource.is_readonly


def test_assert_resource_name_available(
    db_session, account, fake_data, queue_filter_setup
):
    queue = fake_data.queue(account.user, account.group)
    queue.name = "Elfreda"  # already taken

    with pytest.raises(EntityExistsError):
        utils.assert_resource_name_available(db_session, queue)

    queue.name = "UnusedName"
    utils.assert_resource_name_available(db_session, queue)


def test_assert_snapshot_name_available(db_session, queue_filter_setup):
    elfreda = next(q for q in queue_filter_setup if q.name == "Elfreda")

    # "Zelda" already taken by a different resource
    elfreda_new = models.Queue("a queue", elfreda.resource, elfreda.creator, "Zelda")
    with pytest.raises(EntityExistsError):
        utils.assert_snapshot_name_available(db_session, elfreda_new)

    elfreda_new.name = "UnusedName"
    utils.assert_snapshot_name_available(db_session, elfreda_new)

    # Also ok to leave the name the same
    elfreda_new.name = "Elfreda"
    utils.assert_snapshot_name_available(db_session, elfreda_new)


def test_get_latest_snapshots(db_session, resource_status_combo, deletion_policy):

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
        db_session, snap_class, snaps, deletion_policy
    )

    assert _same_snapshots(expected_latest_snaps, latest_snaps)

    # Also try passing a single, for length-1 combos
    if len(snaps) == 1:
        if len(expected_latest_snaps) > 0:
            expected_latest_snap = expected_latest_snaps[0]
        else:
            expected_latest_snap = None

        latest_snap = utils.get_latest_snapshots(
            db_session, snap_class, snaps[0], deletion_policy
        )

        assert latest_snap == expected_latest_snap


def test_get_one_latest_snapshot(db_session, resource_status, deletion_policy):

    snap, status = resource_status

    exc = helpers.expected_exception_for_combined_status((status,), deletion_policy)

    if exc:
        with pytest.raises(exc):
            utils.get_one_latest_snapshot(db_session, type(snap), snap, deletion_policy)
    else:
        expected_latest_snaps = helpers.find_expected_snaps_for_deletion_policy(
            (snap,), deletion_policy
        )

        latest_snap = utils.get_one_latest_snapshot(
            db_session, type(snap), snap.resource_id, deletion_policy
        )

        assert latest_snap == expected_latest_snaps[0]


def test_get_latest_child_snapshots(db_session, resource_parent_combo, deletion_policy):

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
        db_session, child_class, parent, deletion_policy
    )

    assert _same_snapshots(latest_snaps, expected_latest_snaps)


def test_get_latest_child_snapshots_parent_not_exist(db_session, deletion_policy):
    with pytest.raises(EntityDoesNotExistError):
        utils.get_latest_child_snapshots(
            db_session,
            models.Queue,
            999999,
            deletion_policy,
        )


def test_get_latest_child_snapshots_parent_deleted(
    db_session, fake_data, account, deletion_policy
):
    exp = fake_data.experiment(account.user, account.group)
    lock = models.ResourceLock(resource_lock_types.DELETE, exp.resource)
    db_session.add_all((exp, lock))
    db_session.commit()

    with pytest.raises(EntityDeletedError):
        utils.get_latest_child_snapshots(
            db_session,
            models.Queue,
            exp,
            deletion_policy,
        )


def test_get_snapshot_by_name(
    db_session, account, resource_status_combo, deletion_policy
):
    snaps, _ = resource_status_combo

    if len(snaps) == 0:
        # Doesn't really matter which class we use for an empty combo
        snap_class = models.Queue
    else:
        snap_class = type(snaps[0])

    expected_latest_snaps = helpers.find_expected_snaps_for_deletion_policy(
        snaps, deletion_policy
    )

    all_snap_names = [snap.name for snap in snaps]
    all_snap_names.append("doesnt exist")  # add a garbage name too

    latest_snaps = utils.get_snapshot_by_name(
        db_session, snap_class, all_snap_names, account.group, deletion_policy
    )

    assert _same_snapshots(expected_latest_snaps, latest_snaps)

    # Also try passing a single, for length-1 combos
    if len(snaps) == 1:
        if len(expected_latest_snaps) > 0:
            expected_latest_snap = expected_latest_snaps[0]
        else:
            expected_latest_snap = None

        latest_snap = utils.get_snapshot_by_name(
            db_session, snap_class, snaps[0].name, account.group, deletion_policy
        )

        assert latest_snap == expected_latest_snap


def test_get_snapshot_by_name_dupe_name(db_session, account, fake_data):
    # Make two resources with the same name in two groups.  Ensure
    # we get the right resource from each group.
    account2 = fake_data.account()
    db_session.add(account2.group)
    db_session.commit()

    queue1 = fake_data.queue(account.user, account.group)
    queue2 = fake_data.queue(account2.user, account2.group)
    queue2.name = queue1.name
    db_session.add_all((queue1, queue2))
    db_session.commit()

    check_queue = utils.get_snapshot_by_name(
        db_session,
        models.Queue,
        queue1.name,
        account.group,
        utils.DeletionPolicy.NOT_DELETED,
    )

    assert check_queue == queue1
    assert check_queue != queue2

    check_queue = utils.get_snapshot_by_name(
        db_session,
        models.Queue,
        queue2.name,
        account2.group,
        utils.DeletionPolicy.NOT_DELETED,
    )

    assert check_queue == queue2
    assert check_queue != queue1


def test_get_snapshot_by_name_deleted(account, db_session, fake_data):
    queue = fake_data.queue(account.user, account.group)
    db_session.add(queue)
    db_session.commit()

    queue_lock = models.ResourceLock(resource_lock_types.DELETE, queue.resource)
    db_session.add(queue_lock)
    db_session.commit()

    check_queue = utils.get_snapshot_by_name(
        db_session, models.Queue, queue.name, account.group, utils.DeletionPolicy.ANY
    )
    assert check_queue == queue

    check_queue = utils.get_snapshot_by_name(
        db_session,
        models.Queue,
        queue.name,
        account.group,
        utils.DeletionPolicy.NOT_DELETED,
    )
    assert not check_queue

    check_queue = utils.get_snapshot_by_name(
        db_session,
        models.Queue,
        queue.name,
        account.group,
        utils.DeletionPolicy.DELETED,
    )
    assert check_queue == queue


def test_get_snapshot_by_name_not_exist(account, db_session, fake_data):
    check_queue = utils.get_snapshot_by_name(
        db_session, models.Queue, "foo", account.group, utils.DeletionPolicy.ANY
    )
    assert not check_queue

    check_queue = utils.get_snapshot_by_name(
        db_session, models.Queue, "foo", account.group, utils.DeletionPolicy.NOT_DELETED
    )
    assert not check_queue

    check_queue = utils.get_snapshot_by_name(
        db_session, models.Queue, "foo", account.group, utils.DeletionPolicy.DELETED
    )
    assert not check_queue

    # Try getting an existing queue via the wrong group
    queue = fake_data.queue(account.user, account.group)
    db_session.add(queue)
    db_session.commit()

    account2 = fake_data.account()
    db_session.add(account2.group)
    db_session.commit()

    check_queue = utils.get_snapshot_by_name(
        db_session, models.Queue, queue.name, account2.group, utils.DeletionPolicy.ANY
    )
    assert not check_queue

    check_queue = utils.get_snapshot_by_name(
        db_session,
        models.Queue,
        queue.name,
        account2.group,
        utils.DeletionPolicy.NOT_DELETED,
    )
    assert not check_queue

    check_queue = utils.get_snapshot_by_name(
        db_session,
        models.Queue,
        queue.name,
        account2.group,
        utils.DeletionPolicy.DELETED,
    )
    assert not check_queue


def test_get_snapshot_by_name_multi_version(account, db_session, fake_data):
    queuesnap1 = fake_data.queue(account.user, account.group)
    # We can't rely on auto-timestamping here; the instances are created too
    # quickly and can coincidentally get identical timestamps.
    queuesnap1.created_on = datetime.datetime.fromisoformat(
        "1992-07-22T12:17:31.410801Z"
    )

    queuesnap2 = models.Queue(
        queuesnap1.description, queuesnap1.resource, queuesnap1.creator, queuesnap1.name
    )
    queuesnap2.created_on = datetime.datetime.fromisoformat(
        "1998-10-23T20:39:53.132405Z"
    )

    db_session.add_all([queuesnap1, queuesnap2])
    db_session.commit()

    # Should only get the latest version
    queue = utils.get_snapshot_by_name(
        db_session,
        models.Queue,
        queuesnap1.name,
        account.group,
        utils.DeletionPolicy.NOT_DELETED,
    )

    assert queue == queuesnap2


def test_get_snapshot_by_name_old_name(account, db_session):
    # Ensure getting a queue by an old name doesn't return an old queue
    # snapshot.
    queue_res = models.Resource("queue", account.group)
    queue = models.Queue("desc", queue_res, account.user, "name1")
    db_session.add(queue)
    db_session.commit()

    queue_name2 = models.Queue("desc", queue_res, account.user, "name2")
    db_session.add(queue_name2)
    db_session.commit()

    check_queue = utils.get_snapshot_by_name(
        db_session,
        models.Queue,
        "name1",
        account.group,
        utils.DeletionPolicy.NOT_DELETED,
    )
    assert not check_queue

    check_queue = utils.get_snapshot_by_name(
        db_session,
        models.Queue,
        "name2",
        account.group,
        utils.DeletionPolicy.NOT_DELETED,
    )
    assert check_queue == queue_name2

    check_queue = utils.get_snapshot_by_name(
        db_session, models.Queue, "name1", account.group, utils.DeletionPolicy.DELETED
    )
    assert not check_queue

    check_queue = utils.get_snapshot_by_name(
        db_session, models.Queue, "name2", account.group, utils.DeletionPolicy.DELETED
    )
    assert not check_queue

    check_queue = utils.get_snapshot_by_name(
        db_session, models.Queue, "name1", account.group, utils.DeletionPolicy.ANY
    )
    assert not check_queue

    check_queue = utils.get_snapshot_by_name(
        db_session, models.Queue, "name2", account.group, utils.DeletionPolicy.ANY
    )
    assert check_queue == queue_name2


def test_get_snapshot_by_name_old_name_deleted(account, db_session):
    # Ensure getting a queue by an old name doesn't return an old queue
    # snapshot (deleted version).
    queue_res = models.Resource("queue", account.group)
    queue = models.Queue("desc", queue_res, account.user, "name1")
    db_session.add(queue)
    db_session.commit()

    queue_name2 = models.Queue("desc", queue_res, account.user, "name2")
    db_session.add(queue_name2)
    db_session.commit()

    lock = models.ResourceLock(resource_lock_types.DELETE, queue_res)
    db_session.add(lock)
    db_session.commit()

    check_queue = utils.get_snapshot_by_name(
        db_session,
        models.Queue,
        "name1",
        account.group,
        utils.DeletionPolicy.NOT_DELETED,
    )
    assert not check_queue

    check_queue = utils.get_snapshot_by_name(
        db_session,
        models.Queue,
        "name2",
        account.group,
        utils.DeletionPolicy.NOT_DELETED,
    )
    assert not check_queue

    check_queue = utils.get_snapshot_by_name(
        db_session, models.Queue, "name1", account.group, utils.DeletionPolicy.DELETED
    )
    assert not check_queue

    check_queue = utils.get_snapshot_by_name(
        db_session, models.Queue, "name2", account.group, utils.DeletionPolicy.DELETED
    )
    assert check_queue == queue_name2

    check_queue = utils.get_snapshot_by_name(
        db_session, models.Queue, "name1", account.group, utils.DeletionPolicy.ANY
    )
    assert not check_queue

    check_queue = utils.get_snapshot_by_name(
        db_session, models.Queue, "name2", account.group, utils.DeletionPolicy.ANY
    )
    assert check_queue == queue_name2


def test_get_snapshot_by_name_group_not_exists(db_session, fake_data, account):

    queue = fake_data.queue(account.user, account.group)
    db_session.add(queue)
    db_session.commit()

    group2 = models.Group("group2", account.user)

    with pytest.raises(EntityDoesNotExistError):
        utils.get_snapshot_by_name(
            db_session, models.Queue, queue.name, group2, utils.DeletionPolicy.ANY
        )

    with pytest.raises(EntityDoesNotExistError):
        utils.get_snapshot_by_name(
            db_session, models.Queue, queue.name, 999999, utils.DeletionPolicy.ANY
        )


def test_get_snapshot_by_name_group_deleted(db_session, fake_data, account):
    queue = fake_data.queue(account.user, account.group)
    lock = models.GroupLock(group_lock_types.DELETE, account.group)
    db_session.add_all((queue, lock))
    db_session.commit()

    with pytest.raises(EntityDeletedError):
        utils.get_snapshot_by_name(
            db_session,
            models.Queue,
            queue.name,
            account.group,
            utils.DeletionPolicy.ANY,
        )


def test_set_resource_children(db_session, fake_data, account, resource_status_combo):

    snaps, statuses = resource_status_combo
    if len(snaps) == 0:
        # Doesn't really matter which class we use for an empty combo
        snap_class = models.Queue
    else:
        snap_class = type(snaps[0])

    exp = fake_data.experiment(account.user, account.group)
    db_session.add(exp)
    db_session.commit()

    exc = helpers.expected_exception_for_combined_status(
        statuses, utils.DeletionPolicy.NOT_DELETED
    )

    if exc:
        with pytest.raises(exc):
            utils.set_resource_children(db_session, snap_class, exp, snaps)

    else:
        result_children = utils.set_resource_children(
            db_session, snap_class, exp, snaps
        )
        db_session.commit()

        assert _same_snapshots(snaps, result_children)


def test_set_resource_children_parent_not_exist(db_session):
    with pytest.raises(EntityDoesNotExistError):
        utils.set_resource_children(db_session, models.Queue, 999999, [])


def test_set_resource_children_parent_deleted(db_session, fake_data, account):
    exp = fake_data.experiment(account.user, account.group)
    lock = models.ResourceLock(resource_lock_types.DELETE, exp.resource)
    db_session.add_all((exp, lock))
    db_session.commit()

    with pytest.raises(EntityDeletedError):
        utils.set_resource_children(db_session, models.EntryPoint, exp, [])


def test_append_resource_children(
    db_session, fake_data, account, resource_status_combo
):
    snaps, statuses = resource_status_combo
    if len(snaps) == 0:
        # Doesn't really matter which class we use for an empty combo
        snap_class = models.Queue
    else:
        snap_class = type(snaps[0])

    exp = fake_data.experiment(account.user, account.group)
    db_session.add(exp)
    db_session.commit()

    exc = helpers.expected_exception_for_combined_status(
        statuses, utils.DeletionPolicy.NOT_DELETED
    )

    if exc:
        with pytest.raises(exc):
            utils.append_resource_children(db_session, snap_class, exp, snaps)

    else:
        result_children = utils.append_resource_children(
            db_session, snap_class, exp, snaps
        )
        db_session.commit()

        assert _same_snapshots(snaps, result_children)

        # Since append_resource_children() is sensitive to pre-existing
        # children and will not add the same child twice, we should be able
        # to append the children again with no effect.
        result_children = utils.append_resource_children(
            db_session, snap_class, exp, snaps
        )
        db_session.commit()

        assert _same_snapshots(snaps, result_children)


def test_append_resource_children_parent_not_exist(db_session):
    with pytest.raises(EntityDoesNotExistError):
        utils.append_resource_children(db_session, models.Queue, 999999, [])


def test_append_resource_children_parent_deleted(db_session, fake_data, account):
    exp = fake_data.experiment(account.user, account.group)
    lock = models.ResourceLock(resource_lock_types.DELETE, exp.resource)
    db_session.add_all((exp, lock))
    db_session.commit()

    with pytest.raises(EntityDeletedError):
        utils.append_resource_children(db_session, models.EntryPoint, exp, [])


def test_unlink_child(db_session, fake_data, account):
    exp = fake_data.experiment(account.user, account.group)

    epres1 = models.Resource("entry_point", account.group)
    ep1 = models.EntryPoint(
        "", epres1, account.user, "ep1", "graph:", "artifacts_input:", [], []
    )

    epres2 = models.Resource("entry_point", account.group)
    ep2 = models.EntryPoint(
        "", epres2, account.user, "ep2", "graph:", "artifacts_input:", [], []
    )

    exp.children.extend((ep1.resource, ep2.resource))
    db_session.add(exp)
    db_session.commit()

    assert len(exp.children) == 2
    utils.unlink_child(db_session, exp, ep1)
    db_session.commit()

    assert exp.children == [ep2.resource]


def test_unlink_child_parent_not_exist(db_session):
    with pytest.raises(EntityDoesNotExistError):
        utils.unlink_child(db_session, 1, 2)


def test_unlink_child_child_not_exist(db_session, fake_data, account):
    exp = fake_data.experiment(account.user, account.group)
    db_session.add(exp)
    db_session.commit()

    with pytest.raises(EntityDoesNotExistError):
        utils.unlink_child(db_session, exp, 999999)


def test_filter_all_unsorted(db_session, queue_filter_setup):

    results, count = utils.get_by_filters_paged(
        db_session,
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
def test_filter_all_sorted(db_session, queue_filter_setup, sort_by, sort_key):

    results, count = utils.get_by_filters_paged(
        db_session,
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
        db_session,
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
def test_filter_all_paging(db_session, queue_filter_setup, page_start, page_length):

    results, count = utils.get_by_filters_paged(
        db_session,
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


def test_filter_name(db_session, queue_filter_setup):

    results, count = utils.get_by_filters_paged(
        db_session,
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
        db_session,
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


def test_filter_name_wild_1(db_session, queue_filter_setup):

    results, count = utils.get_by_filters_paged(
        db_session,
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


def test_filter_name_wild_2(db_session, queue_filter_setup):

    results, count = utils.get_by_filters_paged(
        db_session,
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


def test_filter_tag(db_session, queue_filter_setup):

    results, count = utils.get_by_filters_paged(
        db_session,
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


def test_filter_null_field_1(db_session, queue_filter_setup):

    # "down" just happens to be a word which occurs both as a tag
    # and in a description.  ("continue" is another one.)
    results, count = utils.get_by_filters_paged(
        db_session,
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


def test_filter_null_field_2(db_session, queue_filter_setup):

    results, count = utils.get_by_filters_paged(
        db_session,
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


def test_filter_unsupported_sort(db_session):
    with pytest.raises(SortParameterValidationError):
        utils.get_by_filters_paged(
            db_session,
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


def test_filter_unsupported_field(db_session):
    with pytest.raises(SearchParseError):
        utils.get_by_filters_paged(
            db_session,
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
