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

import pytest

import dioptra.restapi.db.models as models
import dioptra.restapi.db.repository.utils as utils
import dioptra.restapi.errors as errors
import tests.unit.restapi.lib.helpers as helpers
from dioptra.restapi.db.models.constants import (
    group_lock_types,
    resource_lock_types,
    user_lock_types,
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
def entrypoint_status_combo(request, db, account, fake_data):
    """
    This parameterized fixture produces entrypoints in all status
    combinations, e.g. exists+deleted, deleted+not-exists, etc.  Each produced
    entrypoint is a (entrypoints, status_set) 2-tuple, giving the snapshots
    created and the status combo they represent.  status_set is a set of
    ExistenceResult enum values.
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
def experiment_children_combo(entrypoint_status_combo, db, account, fake_data):
    """
    This fixture produces (experiment parent snap, entrypoint child snaps,
    status_set) 3-tuples, for all combinations of child status.
    """

    child_snaps, statuses = entrypoint_status_combo

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

    return parent, child_snaps, statuses


@pytest.fixture
def experiment_children_combo_no_commit(entrypoint_status_combo, account, fake_data):
    """
    This fixture produces (experiment parent snap, entrypoint child snaps,
    status_set) 3-tuples, for all combinations of child status, but does not
    add/commit the parent experiment to the database (children are still
    committed as necessary).
    """

    child_snaps, statuses = entrypoint_status_combo

    parent = fake_data.experiment(account.user, account.group)
    parent.children.extend(c.resource for c in child_snaps)

    return parent, child_snaps, statuses


@pytest.fixture
def experiment_snapshot_children_combo_no_commit(
    entrypoint_status_combo, db, account, fake_data
):
    """
    This fixture tries to create objects to test snapshot creation.  It creates
    two snapshots of the same resource where the first snap has no children,
    and the second has the children set up according to the status combo.  The
    resource, first snapshot, and existing children are committed to the
    database; the second snapshot and non-existing children are not, so that
    it can be used to test snapshot creation.

    Returned are both experiment snapshots, the child entrypoint snapshots, and
    the child status combo.
    """

    child_snaps, statuses = entrypoint_status_combo

    exp_snap1 = fake_data.experiment(account.user, account.group)
    db.session.add(exp_snap1)
    db.session.commit()

    exp_snap2 = models.Experiment("", exp_snap1.resource, account.user, "exp_snap2")

    # Force timestamp ahead, in case these are created so quickly they get the
    # same timestamp.
    if exp_snap1.created_on == exp_snap2.created_on:
        exp_snap2.created_on = exp_snap1.created_on + datetime.timedelta(hours=1)

    exp_snap2.children.extend(c.resource for c in child_snaps)

    try:
        # Prevent non-exists resources from being accidentally added due to
        # autoflush, which messes up the test setup.
        db.session.autoflush = False
        yield exp_snap1, exp_snap2, child_snaps, statuses
    finally:
        db.session.autoflush = True
        # Rollback is necessary to remove pending table changes from the
        # transaction before the rest of the unit test teardown drops all the
        # tables.  Dropping and changing the same table in the same transaction
        # doesn't work well.
        db.session.rollback()


def test_experiment_create_not_exists(
    experiment_children_combo_no_commit, db, experiment_repo
):

    experiment, _, child_statuses = experiment_children_combo_no_commit

    exc = helpers.expected_exception_for_combined_status(
        child_statuses,
        utils.DeletionPolicy.NOT_DELETED,
    )

    if exc:
        with pytest.raises(exc):
            experiment_repo.create(experiment)

    else:
        # Should not error
        experiment_repo.create(experiment)
        db.session.commit()


def test_experiment_create_exists(experiment_children_combo, experiment_repo):
    experiment, _, _ = experiment_children_combo

    with pytest.raises(errors.EntityExistsError):
        experiment_repo.create(experiment)


def test_experiment_create_exists_deleted(
    experiment_children_combo, db, experiment_repo
):
    experiment, _, _ = experiment_children_combo
    lock = models.ResourceLock(resource_lock_types.DELETE, experiment.resource)
    db.session.add(lock)
    db.session.commit()

    with pytest.raises(errors.EntityDeletedError):
        experiment_repo.create(experiment)


def test_experiment_create_user_not_exist(fake_data, account, experiment_repo):
    experiment = fake_data.experiment(account.user, account.group)

    user2 = models.User("user2", "pass2", "user2@example.org")
    experiment.creator = user2

    with pytest.raises(errors.EntityDoesNotExistError):
        experiment_repo.create(experiment)


def test_experiment_create_user_deleted(db, fake_data, account, experiment_repo):
    experiment = fake_data.experiment(account.user, account.group)

    lock = models.UserLock(user_lock_types.DELETE, experiment.creator)
    db.session.add(lock)
    db.session.commit()

    with pytest.raises(errors.EntityDeletedError):
        experiment_repo.create(experiment)


def test_experiment_create_group_not_exist(fake_data, account, experiment_repo):
    experiment = fake_data.experiment(account.user, account.group)

    user2 = models.User("user2", "pass2", "user2@example.org")
    group2 = models.Group("group2", user2)
    experiment.resource.owner = group2

    with pytest.raises(errors.EntityDoesNotExistError):
        experiment_repo.create(experiment)


def test_experiment_create_group_deleted(db, fake_data, account, experiment_repo):
    experiment = fake_data.experiment(account.user, account.group)

    lock = models.GroupLock(group_lock_types.DELETE, account.group)
    db.session.add(lock)
    db.session.commit()

    with pytest.raises(errors.EntityDeletedError):
        experiment_repo.create(experiment)


def test_experiment_create_user_not_member(db, fake_data, account, experiment_repo):
    experiment = fake_data.experiment(account.user, account.group)

    user2 = models.User("user2", "pass2", "user2@example.org")
    group2 = models.Group("group2", user2)
    db.session.add(group2)
    db.session.commit()

    experiment.resource.owner = group2
    with pytest.raises(errors.UserNotInGroupError):
        experiment_repo.create(experiment)


def test_experiment_create_name_collision(db, fake_data, account, experiment_repo):
    experiment = fake_data.experiment(account.user, account.group)
    experiment_repo.create(experiment)
    db.session.commit()

    exp2 = fake_data.experiment(account.user, account.group)
    exp2.name = experiment.name
    with pytest.raises(errors.EntityExistsError):
        experiment_repo.create(exp2)


def test_experiment_create_name_reuse(db, fake_data, account, experiment_repo):
    experiment = fake_data.experiment(account.user, account.group)
    experiment_repo.create(experiment)
    db.session.commit()

    lock = models.ResourceLock(resource_lock_types.DELETE, experiment.resource)
    db.session.add(lock)
    db.session.commit()

    # Once a resource is deleted, creating a new resource with that name is allowed.
    exp2 = fake_data.experiment(account.user, account.group)
    exp2.name = experiment.name
    experiment_repo.create(exp2)
    db.session.commit()

    check_exp = db.session.get(models.Experiment, exp2.resource_snapshot_id)
    assert check_exp == exp2


def test_experiment_create_wrong_resource_type(fake_data, account, experiment_repo):
    experiment = fake_data.experiment(account.user, account.group)
    experiment.resource_type = "queue"

    with pytest.raises(errors.MismatchedResourceTypeError):
        experiment_repo.create(experiment)

    experiment.resource_type = "experiment"
    experiment.resource.resource_type = "queue"

    with pytest.raises(errors.MismatchedResourceTypeError):
        experiment_repo.create(experiment)


def test_experiment_create_snapshot_resource_exists(
    experiment_snapshot_children_combo_no_commit, db, experiment_repo
):

    snap1, snap2, _, statuses = experiment_snapshot_children_combo_no_commit

    exc = helpers.expected_exception_for_combined_status(
        statuses, utils.DeletionPolicy.NOT_DELETED
    )

    if exc:
        with pytest.raises(exc):
            experiment_repo.create_snapshot(snap2)

    else:
        experiment_repo.create_snapshot(snap2)
        db.session.commit()

        check_resource = db.session.get(models.Resource, snap2.resource_id)
        assert check_resource is not None
        assert len(check_resource.versions) == 2
        assert snap1 in check_resource.versions
        assert snap2 in check_resource.versions
        assert snap1.created_on < snap2.created_on


def test_experiment_create_snapshot_resource_not_exist(
    fake_data, account, experiment_repo
):

    experiment = fake_data.experiment(account.user, account.group)

    with pytest.raises(errors.EntityDoesNotExistError):
        experiment_repo.create_snapshot(experiment)


def test_experiment_create_snapshot_resource_deleted(
    db, fake_data, account, experiment_repo
):

    experiment = fake_data.experiment(account.user, account.group)
    lock = models.ResourceLock(resource_lock_types.DELETE, experiment.resource)
    db.session.add_all((experiment, lock))
    db.session.commit()

    with pytest.raises(errors.EntityDeletedError):
        experiment_repo.create_snapshot(experiment)


def test_experiment_create_snapshot_snapshot_exists(
    db, fake_data, account, experiment_repo
):

    experiment = fake_data.experiment(account.user, account.group)
    db.session.add(experiment)
    db.session.commit()

    with pytest.raises(errors.EntityExistsError):
        experiment_repo.create_snapshot(experiment)


def test_experiment_create_snapshot_user_not_exist(
    db, fake_data, account, experiment_repo
):

    exp_snap1 = fake_data.experiment(account.user, account.group)
    db.session.add(exp_snap1)
    db.session.commit()

    user2 = models.User("user2", "pass2", "user2@example.org")
    exp_snap2 = models.Experiment("", exp_snap1.resource, user2, "exp_snap2")

    with pytest.raises(errors.EntityDoesNotExistError):
        experiment_repo.create_snapshot(exp_snap2)


def test_experiment_create_snapshot_user_deleted(
    db, fake_data, account, experiment_repo
):

    exp_snap1 = fake_data.experiment(account.user, account.group)
    db.session.add(exp_snap1)
    db.session.commit()

    lock = models.UserLock(user_lock_types.DELETE, account.user)
    db.session.add(lock)
    db.session.commit()

    exp_snap2 = models.Experiment("", exp_snap1.resource, account.user, "exp_snap2")

    with pytest.raises(errors.EntityDeletedError):
        experiment_repo.create_snapshot(exp_snap2)


def test_experiment_create_snapshot_user_not_member(
    db, fake_data, account, experiment_repo
):

    exp_snap1 = fake_data.experiment(account.user, account.group)
    db.session.add(exp_snap1)
    db.session.commit()

    acct2 = fake_data.account()
    db.session.add_all((acct2.user, acct2.group))
    db.session.commit()

    exp_snap2 = models.Experiment("", exp_snap1.resource, acct2.user, "exp_snap2")

    with pytest.raises(errors.UserNotInGroupError):
        experiment_repo.create_snapshot(exp_snap2)


def test_experiment_create_snapshot_name_collision(
    db, fake_data, account, experiment_repo
):

    exp1 = fake_data.experiment(account.user, account.group)
    exp2 = fake_data.experiment(account.user, account.group)
    db.session.add_all((exp1, exp2))
    db.session.commit()

    # Creating another snapshot of the same resource with the same name should
    # be ok.
    exp1_snap2 = models.Experiment("", exp1.resource, exp1.creator, exp1.name)
    experiment_repo.create_snapshot(exp1_snap2)
    db.session.commit()

    # Creating another snapshot of the same resource with another resource's
    # name should cause an error.
    exp2_snap2 = models.Experiment("", exp2.resource, exp2.creator, exp1.name)
    with pytest.raises(errors.EntityExistsError):
        experiment_repo.create_snapshot(exp2_snap2)


def test_experiment_get_by_name_exists(
    db, fake_data, account, experiment_repo, deletion_policy
):
    exp1 = fake_data.experiment(account.user, account.group)
    exp2 = models.Experiment(exp1.description, exp1.resource, exp1.creator, exp1.name)

    if exp1.created_on == exp2.created_on:
        exp2.created_on = exp2.created_on + datetime.timedelta(hours=1)

    db.session.add_all((exp1, exp2))
    db.session.commit()

    snap = experiment_repo.get_by_name(exp1.name, exp1.resource.owner, deletion_policy)

    expected_snaps = helpers.find_expected_snaps_for_deletion_policy(
        [exp2], deletion_policy
    )
    expected_snap = expected_snaps[0] if expected_snaps else None

    assert snap == expected_snap


def test_experiment_get_by_name_deleted(
    db, fake_data, account, experiment_repo, deletion_policy
):
    exp1 = fake_data.experiment(account.user, account.group)
    exp2 = models.Experiment(exp1.description, exp1.resource, exp1.creator, exp1.name)

    if exp1.created_on == exp2.created_on:
        exp2.created_on = exp2.created_on + datetime.timedelta(hours=1)

    lock = models.ResourceLock(resource_lock_types.DELETE, exp1.resource)

    db.session.add_all((exp1, exp2, lock))
    db.session.commit()

    snap = experiment_repo.get_by_name(exp1.name, exp1.resource.owner, deletion_policy)

    expected_snaps = helpers.find_expected_snaps_for_deletion_policy(
        [exp2], deletion_policy
    )
    expected_snap = expected_snaps[0] if expected_snaps else None

    assert snap == expected_snap


def test_experiment_get_by_name_not_exist(
    db, fake_data, account, experiment_repo, deletion_policy
):
    exp1 = fake_data.experiment(account.user, account.group)

    snap = experiment_repo.get_by_name(exp1.name, exp1.resource.owner, deletion_policy)

    expected_snaps = helpers.find_expected_snaps_for_deletion_policy(
        [exp1], deletion_policy
    )
    expected_snap = expected_snaps[0] if expected_snaps else None

    assert snap == expected_snap


def test_experiment_get_by_name_group_not_exist(
    db, fake_data, account, experiment_repo, deletion_policy
):
    exp1 = fake_data.experiment(account.user, account.group)
    exp2 = models.Experiment(exp1.description, exp1.resource, exp1.creator, exp1.name)

    if exp1.created_on == exp2.created_on:
        exp2.created_on = exp2.created_on + datetime.timedelta(hours=1)

    db.session.add_all((exp1, exp2))
    db.session.commit()

    group2 = models.Group("group2", account.user)

    with pytest.raises(errors.EntityDoesNotExistError):
        experiment_repo.get_by_name(exp1.name, group2, deletion_policy)


def test_experiment_get_by_name_group_deleted(
    db, fake_data, account, experiment_repo, deletion_policy
):
    exp1 = fake_data.experiment(account.user, account.group)
    exp2 = models.Experiment(exp1.description, exp1.resource, exp1.creator, exp1.name)

    if exp1.created_on == exp2.created_on:
        exp2.created_on = exp2.created_on + datetime.timedelta(hours=1)

    lock = models.GroupLock(group_lock_types.DELETE, account.group)

    db.session.add_all((exp1, exp2, lock))
    db.session.commit()

    with pytest.raises(errors.EntityDeletedError):
        experiment_repo.get_by_name(exp1.name, account.group, deletion_policy)
