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
from sqlalchemy.orm.session import Session as DBSession

import dioptra.restapi.db.models as models
import dioptra.restapi.db.repository.utils as utils
import dioptra.restapi.errors as errors
import tests.unit.restapi.lib.helpers as helpers
from dioptra.restapi.db.models.constants import (
    group_lock_types,
    resource_lock_types,
    user_lock_types,
)


def make_entrypoint(
    creator,
    group,
    name="test_ep",
    description="",
    task_graph="graph:",
    artifact_graph="artifact_output:",
):
    """Create a basic EntryPoint without children."""
    ep_resource = models.Resource("entry_point", group)
    return models.EntryPoint(
        description=description,
        resource=ep_resource,
        creator=creator,
        name=name,
        task_graph=task_graph,
        artifact_graph=artifact_graph,
        parameters=[],
        artifact_parameters=[],
    )


def make_plugin(creator, group, name="test_plugin", description=""):
    """Create a basic Plugin without dependencies."""
    plugin_resource = models.Resource("plugin", group)
    return models.Plugin(
        description=description,
        resource=plugin_resource,
        creator=creator,
        name=name,
    )


def make_entrypoint_snapshot(source_ep, hours_offset=1):
    """Create a new EntryPoint snapshot based on an existing entrypoint.

    Args:
        source_ep: The source EntryPoint to create snapshot from
        hours_offset: Hours to add to source_ep's created_on timestamp
    """
    ep = models.EntryPoint(
        description=source_ep.description,
        resource=source_ep.resource,
        creator=source_ep.creator,
        name=source_ep.name,
        task_graph=source_ep.task_graph,
        artifact_graph=source_ep.artifact_graph,
        parameters=source_ep.parameters,
        artifact_parameters=source_ep.artifact_parameters,
    )
    ep.created_on = source_ep.created_on + datetime.timedelta(hours=hours_offset)
    return ep


_CHILD_COUNT_COMBOS = [0, 1, 2]


@pytest.fixture(params=_CHILD_COUNT_COMBOS)
def entrypoint_with_queues(request, db_session, account, fake_data):
    """EntryPoint with 0/1/2 queues as children."""
    ep = make_entrypoint(account.user, account.group)
    db_session.add(ep)

    queues = []
    for i in range(request.param):
        queue = fake_data.queue(account.user, account.group)
        db_session.add(queue)
        ep.children.append(queue.resource)
        queues.append(queue)

    db_session.commit()
    return ep, queues


@pytest.fixture(params=_CHILD_COUNT_COMBOS)
def entrypoint_with_plugins(request, db_session, account):
    """EntryPoint with 0/1/2 plugins as children."""
    ep = make_entrypoint(account.user, account.group)
    db_session.add(ep)

    plugins = []
    for i in range(request.param):
        plugin = make_plugin(account.user, account.group, name=f"plugin{i}")
        db_session.add(plugin)
        ep.children.append(plugin.resource)
        plugins.append(plugin)

    db_session.commit()
    return ep, plugins


@pytest.fixture(params=_CHILD_COUNT_COMBOS)
def entrypoint_with_both_children(request, db_session, account, fake_data):
    """EntryPoint with equal numbers of queues and plugins as children."""
    ep = make_entrypoint(account.user, account.group)
    db_session.add(ep)

    queues = []
    plugins = []
    for i in range(request.param):
        queue = fake_data.queue(account.user, account.group)
        plugin = make_plugin(account.user, account.group, name=f"plugin{i}")
        db_session.add(queue)
        db_session.add(plugin)
        ep.children.append(queue.resource)
        ep.children.append(plugin.resource)
        queues.append(queue)
        plugins.append(plugin)

    db_session.commit()
    return ep, queues, plugins


@pytest.fixture(params=_CHILD_COUNT_COMBOS)
def entrypoint_with_queues_no_commit(request, db_session, account, fake_data):
    """EntryPoint with 0/1/2 queues as children - does NOT add to session.

    Returns (ep, queues) without adding to session - allows test to call
    entrypoint_repo.create() and verify children are correctly persisted.
    """
    ep = make_entrypoint(account.user, account.group)

    queues = []
    for i in range(request.param):
        queue = fake_data.queue(account.user, account.group)
        db_session.add(queue)
        ep.children.append(queue.resource)
        queues.append(queue)

    return ep, queues


@pytest.fixture(params=_CHILD_COUNT_COMBOS)
def entrypoint_with_plugins_no_commit(request, db_session, account):
    """EntryPoint with 0/1/2 plugins as children - does NOT add to session."""
    ep = make_entrypoint(account.user, account.group)

    plugins = []
    for i in range(request.param):
        plugin = make_plugin(account.user, account.group, name=f"plugin{i}")
        db_session.add(plugin)
        ep.children.append(plugin.resource)
        plugins.append(plugin)

    return ep, plugins


@pytest.fixture(params=_CHILD_COUNT_COMBOS)
def entrypoint_with_both_children_no_commit(request, db_session, account, fake_data):
    """EntryPoint with equal queues and plugins - does NOT add to session."""
    ep = make_entrypoint(account.user, account.group)

    queues = []
    plugins = []
    for i in range(request.param):
        queue = fake_data.queue(account.user, account.group)
        plugin = make_plugin(account.user, account.group, name=f"plugin{i}")
        db_session.add(queue)
        db_session.add(plugin)
        ep.children.append(queue.resource)
        ep.children.append(plugin.resource)
        queues.append(queue)
        plugins.append(plugin)

    return ep, queues, plugins


class TestEntrypointCreate:
    """Tests for EntrypointRepository.create()"""

    def test_entrypoint_create_success(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        entrypoint = make_entrypoint(account.user, account.group)

        entrypoint_repo.create(entrypoint)
        db_session.commit()

        result = entrypoint_repo.get_one(
            entrypoint.resource_id, utils.DeletionPolicy.NOT_DELETED
        )
        assert result == entrypoint

    def test_entrypoint_create_exists(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        entrypoint = make_entrypoint(account.user, account.group)
        entrypoint_repo.create(entrypoint)
        db_session.commit()

        with pytest.raises(errors.EntityExistsError):
            entrypoint_repo.create(entrypoint)

    def test_entrypoint_create_exists_deleted(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        entrypoint = make_entrypoint(account.user, account.group)
        entrypoint_repo.create(entrypoint)
        db_session.commit()

        lock = models.ResourceLock(resource_lock_types.DELETE, entrypoint.resource)
        db_session.add(lock)
        db_session.commit()

        with pytest.raises(errors.EntityDeletedError):
            entrypoint_repo.create(entrypoint)

    def test_entrypoint_create_user_not_exist(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        entrypoint = make_entrypoint(account.user, account.group)
        entrypoint.creator = models.User("user2", "pass2", "user2@example.org")

        with pytest.raises(errors.EntityDoesNotExistError):
            entrypoint_repo.create(entrypoint)

    def test_entrypoint_create_user_deleted(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        entrypoint = make_entrypoint(account.user, account.group)

        lock = models.UserLock(user_lock_types.DELETE, account.user)
        db_session.add(lock)
        db_session.commit()

        with pytest.raises(errors.EntityDeletedError):
            entrypoint_repo.create(entrypoint)

    def test_entrypoint_create_group_not_exist(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        entrypoint = make_entrypoint(account.user, account.group)

        user2 = models.User("user2", "pass2", "user2@example.org")
        group2 = models.Group("group2", user2)
        entrypoint.resource.owner = group2

        with pytest.raises(errors.EntityDoesNotExistError):
            entrypoint_repo.create(entrypoint)

    def test_entrypoint_create_group_deleted(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        entrypoint = make_entrypoint(account.user, account.group)

        lock = models.GroupLock(group_lock_types.DELETE, account.group)
        db_session.add(lock)
        db_session.commit()

        with pytest.raises(errors.EntityDeletedError):
            entrypoint_repo.create(entrypoint)

    def test_entrypoint_create_user_not_member(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        entrypoint = make_entrypoint(account.user, account.group)

        user2 = models.User("user2", "pass2", "user2@example.org")
        group2 = models.Group("group2", user2)
        db_session.add(group2)
        db_session.commit()

        entrypoint.resource.owner = group2
        with pytest.raises(errors.UserNotInGroupError):
            entrypoint_repo.create(entrypoint)

    def test_entrypoint_create_name_collision(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep1 = make_entrypoint(account.user, account.group)
        entrypoint_repo.create(ep1)
        db_session.commit()

        ep2 = make_entrypoint(account.user, account.group, name=ep1.name)
        with pytest.raises(errors.EntityExistsError):
            entrypoint_repo.create(ep2)

    def test_entrypoint_create_name_reuse(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep1 = make_entrypoint(account.user, account.group)
        entrypoint_repo.create(ep1)
        db_session.commit()

        lock = models.ResourceLock(resource_lock_types.DELETE, ep1.resource)
        db_session.add(lock)
        db_session.commit()

        ep2 = make_entrypoint(account.user, account.group, name=ep1.name)
        entrypoint_repo.create(ep2)
        db_session.commit()

        check_ep = db_session.get(models.EntryPoint, ep2.resource_snapshot_id)
        assert check_ep == ep2

    def test_entrypoint_create_wrong_resource_type(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        entrypoint = make_entrypoint(account.user, account.group)
        entrypoint.resource_type = "queue"

        with pytest.raises(errors.MismatchedResourceTypeError):
            entrypoint_repo.create(entrypoint)

        entrypoint.resource_type = "entry_point"
        entrypoint.resource.resource_type = "queue"

        with pytest.raises(errors.MismatchedResourceTypeError):
            entrypoint_repo.create(entrypoint)

    def test_entrypoint_create_with_queues(
        self,
        db_session,
        account,
        entrypoint_repo,
        entrypoint_with_queues_no_commit,
    ):
        """Test creating entrypoint with queues preserves them."""
        ep, queues = entrypoint_with_queues_no_commit

        entrypoint_repo.create(ep)
        db_session.commit()

        result = entrypoint_repo.get_one(
            ep.resource_id, utils.DeletionPolicy.NOT_DELETED
        )
        assert result == ep

        stored_queues = entrypoint_repo.get_queues(ep, utils.DeletionPolicy.NOT_DELETED)
        assert len(stored_queues) == len(queues)

    def test_entrypoint_create_with_plugins(
        self,
        db_session,
        account,
        entrypoint_repo,
        entrypoint_with_plugins_no_commit,
    ):
        """Test creating entrypoint with plugins preserves them."""
        ep, plugins = entrypoint_with_plugins_no_commit

        entrypoint_repo.create(ep)
        db_session.commit()

        result = entrypoint_repo.get_one(
            ep.resource_id, utils.DeletionPolicy.NOT_DELETED
        )
        assert result == ep

        stored_plugins = entrypoint_repo.get_plugins(
            ep, utils.DeletionPolicy.NOT_DELETED
        )
        assert len(stored_plugins) == len(plugins)

    def test_entrypoint_create_with_both_children(
        self,
        db_session,
        account,
        entrypoint_repo,
        entrypoint_with_both_children_no_commit,
    ):
        """Test creating entrypoint with both queues and plugins preserves them."""
        ep, queues, plugins = entrypoint_with_both_children_no_commit

        entrypoint_repo.create(ep)
        db_session.commit()

        result = entrypoint_repo.get_one(
            ep.resource_id, utils.DeletionPolicy.NOT_DELETED
        )
        assert result == ep

        stored_queues = entrypoint_repo.get_queues(ep, utils.DeletionPolicy.NOT_DELETED)
        stored_plugins = entrypoint_repo.get_plugins(
            ep, utils.DeletionPolicy.NOT_DELETED
        )

        assert len(stored_queues) == len(queues)
        assert len(stored_plugins) == len(plugins)


class TestEntrypointCreateSnapshot:
    """Tests for EntrypointRepository.create_snapshot()"""

    def test_entrypoint_create_snapshot_success(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep1 = make_entrypoint(account.user, account.group)
        entrypoint_repo.create(ep1)
        db_session.commit()

        ep2 = make_entrypoint_snapshot(ep1)

        entrypoint_repo.create_snapshot(ep2)
        db_session.commit()

        check_resource = db_session.get(models.Resource, ep2.resource_id)
        assert check_resource is not None
        assert len(check_resource.versions) == 2

    def test_entrypoint_create_snapshot_resource_not_exist(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        entrypoint = make_entrypoint(account.user, account.group)

        with pytest.raises(errors.EntityDoesNotExistError):
            entrypoint_repo.create_snapshot(entrypoint)

    def test_entrypoint_create_snapshot_resource_deleted(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        entrypoint = make_entrypoint(account.user, account.group)
        lock = models.ResourceLock(resource_lock_types.DELETE, entrypoint.resource)
        db_session.add_all((entrypoint, lock))
        db_session.commit()

        ep2 = make_entrypoint_snapshot(entrypoint)

        with pytest.raises(errors.EntityDeletedError):
            entrypoint_repo.create_snapshot(ep2)

    def test_entrypoint_create_snapshot_snapshot_exists(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        entrypoint = make_entrypoint(account.user, account.group)
        entrypoint_repo.create(entrypoint)
        db_session.commit()

        with pytest.raises(errors.EntityExistsError):
            entrypoint_repo.create_snapshot(entrypoint)

    def test_entrypoint_create_snapshot_name_collision(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep1 = make_entrypoint(account.user, account.group, name="test_ep1")
        ep2 = make_entrypoint(account.user, account.group, name="test_ep2")
        db_session.add_all((ep1, ep2))
        db_session.commit()

        ep1_snap2 = make_entrypoint_snapshot(ep1)
        entrypoint_repo.create_snapshot(ep1_snap2)
        db_session.commit()

        ep2_snap2 = models.EntryPoint(
            ep2.description,
            ep2.resource,
            ep2.creator,
            ep1.name,
            ep2.task_graph,
            ep2.artifact_graph,
            ep2.parameters,
            ep2.artifact_parameters,
        )
        with pytest.raises(errors.EntityExistsError):
            entrypoint_repo.create_snapshot(ep2_snap2)


class TestEntrypointGetByName:
    """Tests for EntrypointRepository.get_by_name()"""

    def test_entrypoint_get_by_name_exists(
        self, db_session: DBSession, account, entrypoint_repo, deletion_policy
    ):
        ep1 = make_entrypoint(account.user, account.group, description="description")
        ep2 = make_entrypoint_snapshot(ep1)
        if ep1.created_on == ep2.created_on:
            ep2.created_on = ep2.created_on + datetime.timedelta(hours=1)
        db_session.add_all((ep1, ep2))
        db_session.commit()

        snap = entrypoint_repo.get_by_name(
            ep1.name, ep1.resource.owner, deletion_policy
        )

        expected_snaps = helpers.find_expected_snaps_for_deletion_policy(
            [ep2], deletion_policy
        )
        expected_snap = expected_snaps[0] if expected_snaps else None
        assert snap == expected_snap

    def test_entrypoint_get_by_name_deleted(
        self, db_session: DBSession, account, entrypoint_repo, deletion_policy
    ):
        ep1 = make_entrypoint(account.user, account.group, description="description")
        ep2 = make_entrypoint_snapshot(ep1)
        if ep1.created_on == ep2.created_on:
            ep2.created_on = ep2.created_on + datetime.timedelta(hours=1)
        lock = models.ResourceLock(resource_lock_types.DELETE, ep1.resource)
        db_session.add_all((ep1, ep2, lock))
        db_session.commit()

        snap = entrypoint_repo.get_by_name(
            ep1.name, ep1.resource.owner, deletion_policy
        )

        expected_snaps = helpers.find_expected_snaps_for_deletion_policy(
            [ep2], deletion_policy
        )
        expected_snap = expected_snaps[0] if expected_snaps else None
        assert snap == expected_snap

    def test_entrypoint_get_by_name_not_exist(
        self, db_session: DBSession, account, entrypoint_repo, deletion_policy
    ):
        ep1 = make_entrypoint(account.user, account.group, description="description")

        snap = entrypoint_repo.get_by_name(
            ep1.name, ep1.resource.owner, deletion_policy
        )

        expected_snaps = helpers.find_expected_snaps_for_deletion_policy(
            [ep1], deletion_policy
        )
        expected_snap = expected_snaps[0] if expected_snaps else None
        assert snap == expected_snap

    def test_entrypoint_get_by_name_group_not_exist(
        self, db_session: DBSession, account, entrypoint_repo, deletion_policy
    ):
        ep1 = make_entrypoint(account.user, account.group, description="description")
        db_session.add(ep1)
        db_session.commit()

        group2 = models.Group("group2", account.user)

        with pytest.raises(errors.EntityDoesNotExistError):
            entrypoint_repo.get_by_name(ep1.name, group2, deletion_policy)

    def test_entrypoint_get_by_name_group_deleted(
        self, db_session: DBSession, account, entrypoint_repo, deletion_policy
    ):
        ep1 = make_entrypoint(account.user, account.group, description="description")
        db_session.add(ep1)
        db_session.commit()

        lock = models.GroupLock(group_lock_types.DELETE, account.group)
        db_session.add(lock)
        db_session.commit()

        with pytest.raises(errors.EntityDeletedError):
            entrypoint_repo.get_by_name(ep1.name, account.group, deletion_policy)


class TestEntrypointGet:
    """Tests for EntrypointRepository.get()"""

    def test_entrypoint_get_single_exists(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep = make_entrypoint(account.user, account.group, description="description")
        entrypoint_repo.create(ep)
        db_session.commit()

        result = entrypoint_repo.get(ep.resource_id, utils.DeletionPolicy.NOT_DELETED)
        assert result == ep

    def test_entrypoint_get_single_not_exists(
        self, db_session: DBSession, entrypoint_repo
    ):
        result = entrypoint_repo.get(99999, utils.DeletionPolicy.NOT_DELETED)
        assert result is None

    def test_entrypoint_get_single_deleted(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep = make_entrypoint(account.user, account.group, description="description")
        entrypoint_repo.create(ep)
        db_session.commit()

        lock = models.ResourceLock(resource_lock_types.DELETE, ep.resource)
        db_session.add(lock)
        db_session.commit()

        result = entrypoint_repo.get(ep.resource_id, utils.DeletionPolicy.NOT_DELETED)
        assert result is None

    def test_entrypoint_get_multiple(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep1 = make_entrypoint(
            account.user, account.group, name="test_ep1", description="description"
        )
        ep2 = make_entrypoint(
            account.user, account.group, name="test_ep2", description="description"
        )
        entrypoint_repo.create(ep1)
        entrypoint_repo.create(ep2)
        db_session.commit()

        result = entrypoint_repo.get(
            [ep1.resource_id, ep2.resource_id], utils.DeletionPolicy.NOT_DELETED
        )
        assert len(result) == 2
        assert ep1 in result
        assert ep2 in result


class TestEntrypointGetOne:
    """Tests for EntrypointRepository.get_one()"""

    def test_entrypoint_get_one_exists(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep = make_entrypoint(account.user, account.group, description="description")
        entrypoint_repo.create(ep)
        db_session.commit()

        result = entrypoint_repo.get_one(
            ep.resource_id, utils.DeletionPolicy.NOT_DELETED
        )
        assert result == ep

    def test_entrypoint_get_one_not_exists(
        self, db_session: DBSession, entrypoint_repo
    ):
        with pytest.raises(errors.EntityDoesNotExistError):
            entrypoint_repo.get_one(99999, utils.DeletionPolicy.NOT_DELETED)

    def test_entrypoint_get_one_deleted(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep = make_entrypoint(account.user, account.group, description="description")
        entrypoint_repo.create(ep)
        db_session.commit()

        lock = models.ResourceLock(resource_lock_types.DELETE, ep.resource)
        db_session.add(lock)
        db_session.commit()

        with pytest.raises(errors.EntityDeletedError):
            entrypoint_repo.get_one(ep.resource_id, utils.DeletionPolicy.NOT_DELETED)


class TestEntrypointDelete:
    """Tests for EntrypointRepository.delete()"""

    def test_entrypoint_delete_exists(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep = make_entrypoint(account.user, account.group, description="description")
        entrypoint_repo.create(ep)
        db_session.commit()

        entrypoint_repo.delete(ep)
        db_session.commit()

        assert ep.resource.is_deleted is True

    def test_entrypoint_delete_not_exists(self, db_session: DBSession, entrypoint_repo):
        with pytest.raises(errors.EntityDoesNotExistError):
            entrypoint_repo.delete(99999)

    def test_entrypoint_delete_already_deleted(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep = make_entrypoint(account.user, account.group, description="description")
        entrypoint_repo.create(ep)
        db_session.commit()

        lock = models.ResourceLock(resource_lock_types.DELETE, ep.resource)
        db_session.add(lock)
        db_session.commit()

        entrypoint_repo.delete(ep)


class TestEntrypointGetQueues:
    """Tests for EntrypointRepository.get_queues()"""

    def test_entrypoint_get_queues(self, entrypoint_with_queues, entrypoint_repo):
        ep, queues = entrypoint_with_queues
        result = entrypoint_repo.get_queues(ep, utils.DeletionPolicy.NOT_DELETED)
        assert len(result) == len(queues)


class TestEntrypointCreateQueues:
    """Tests for EntrypointRepository.create_queues()"""

    def test_entrypoint_create_queues_success(
        self, db_session: DBSession, account, entrypoint_repo, fake_data
    ):
        queue1 = fake_data.queue(account.user, account.group)
        db_session.add(queue1)
        db_session.commit()

        ep = make_entrypoint(account.user, account.group)
        entrypoint_repo.create(ep)
        db_session.commit()

        result = entrypoint_repo.create_queues(ep, [queue1])
        assert len(result) == 1

        stored_queues = entrypoint_repo.get_queues(ep, utils.DeletionPolicy.NOT_DELETED)
        assert len(stored_queues) == 1
        assert queue1 in stored_queues


class TestEntrypointAddQueues:
    """Tests for EntrypointRepository.add_queues()"""

    def test_entrypoint_add_queues_success(
        self, db_session: DBSession, account, entrypoint_repo, fake_data
    ):
        queue1 = fake_data.queue(account.user, account.group)
        queue2 = fake_data.queue(account.user, account.group)
        db_session.add_all((queue1, queue2))
        db_session.commit()

        ep = make_entrypoint(account.user, account.group)
        entrypoint_repo.create(ep)

        ep.children.append(queue1.resource)
        db_session.commit()

        result = entrypoint_repo.add_queues(ep, [queue2])
        assert len(result) == 2
        assert queue1 in result
        assert queue2 in result


class TestEntrypointSetQueues:
    """Tests for EntrypointRepository.set_queues()"""

    def test_entrypoint_set_queues_success(
        self, db_session: DBSession, account, entrypoint_repo, fake_data
    ):
        queue1 = fake_data.queue(account.user, account.group)
        queue2 = fake_data.queue(account.user, account.group)
        db_session.add_all((queue1, queue2))
        db_session.commit()

        ep = make_entrypoint(account.user, account.group)
        entrypoint_repo.create(ep)

        ep.children.append(queue1.resource)

        result = entrypoint_repo.set_queues(ep.resource_id, [queue2])
        assert len(result) == 1
        assert queue2 in result


class TestEntrypointUnlinkQueues:
    """Tests for EntrypointRepository.unlink_queue() and unlink_queues()"""

    def test_entrypoint_unlink_queue_success(
        self, db_session: DBSession, account, entrypoint_repo, fake_data
    ):
        queue1 = fake_data.queue(account.user, account.group)
        db_session.add(queue1)
        db_session.commit()

        ep = make_entrypoint(account.user, account.group)
        entrypoint_repo.create(ep)

        ep.children.append(queue1.resource)
        db_session.commit()

        entrypoint_repo.unlink_queue(ep, queue1)

        result = entrypoint_repo.get_queues(ep, utils.DeletionPolicy.NOT_DELETED)
        assert len(result) == 0

    def test_entrypoint_unlink_queues_success(
        self, db_session: DBSession, account, entrypoint_repo, fake_data
    ):
        queue1 = fake_data.queue(account.user, account.group)
        queue2 = fake_data.queue(account.user, account.group)
        db_session.add_all((queue1, queue2))
        db_session.commit()

        ep = make_entrypoint(account.user, account.group)
        entrypoint_repo.create(ep)

        ep.children.append(queue1.resource)
        ep.children.append(queue2.resource)
        db_session.commit()

        result = entrypoint_repo.unlink_queues(ep)
        assert len(result) == 2
        assert queue1.resource_id in result
        assert queue2.resource_id in result

        stored_queues = entrypoint_repo.get_queues(ep, utils.DeletionPolicy.NOT_DELETED)
        assert len(stored_queues) == 0


class TestEntrypointGetByFiltersPaged:
    """Tests for EntrypointRepository.get_by_filters_paged()"""

    def test_entrypoint_get_by_filters_paged_empty(
        self, db_session: DBSession, entrypoint_repo
    ):
        result, count = entrypoint_repo.get_by_filters_paged(
            group=None,
            filters=[],
            page_start=0,
            page_length=10,
            sort_by=None,
            descending=False,
        )
        assert count == 0
        assert len(result) == 0

    def test_entrypoint_get_by_filters_paged_with_results(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep1 = make_entrypoint(
            account.user, account.group, name="test_ep1", description="description1"
        )
        ep2 = make_entrypoint(
            account.user, account.group, name="test_ep2", description="description2"
        )
        entrypoint_repo.create(ep1)
        entrypoint_repo.create(ep2)
        db_session.commit()

        result, count = entrypoint_repo.get_by_filters_paged(
            group=account.group,
            filters=[],
            page_start=0,
            page_length=10,
            sort_by=None,
            descending=False,
        )
        assert count == 2
        assert len(result) == 2

    def test_entrypoint_get_by_filters_paged_with_filters(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep1 = make_entrypoint(
            account.user, account.group, name="foo_bar", description="description1"
        )
        ep2 = make_entrypoint(
            account.user, account.group, name="baz_qux", description="description2"
        )
        entrypoint_repo.create(ep1)
        entrypoint_repo.create(ep2)
        db_session.commit()

        result, count = entrypoint_repo.get_by_filters_paged(
            group=account.group,
            filters=[{"field": "name", "value": ["foo_bar"]}],
            page_start=0,
            page_length=10,
            sort_by=None,
            descending=False,
        )
        assert count == 1
        assert result[0] == ep1

    def test_entrypoint_get_by_filters_paged_with_sort(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep1 = make_entrypoint(
            account.user, account.group, name="aaa_ep", description="description1"
        )
        ep2 = make_entrypoint(
            account.user, account.group, name="zzz_ep", description="description2"
        )
        entrypoint_repo.create(ep1)
        entrypoint_repo.create(ep2)
        db_session.commit()

        result, count = entrypoint_repo.get_by_filters_paged(
            group=account.group,
            filters=[],
            page_start=0,
            page_length=10,
            sort_by="name",
            descending=True,
        )
        assert count == 2
        assert result[0] == ep2
        assert result[1] == ep1

    def test_entrypoint_get_by_filters_paged_with_pagination(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        for i in range(5):
            ep = make_entrypoint(
                account.user,
                account.group,
                name=f"test_ep{i}",
                description=f"description{i}",
            )
            entrypoint_repo.create(ep)
        db_session.commit()

        result, count = entrypoint_repo.get_by_filters_paged(
            group=account.group,
            filters=[],
            page_start=0,
            page_length=2,
            sort_by="name",
            descending=False,
        )
        assert count == 5
        assert len(result) == 2

    def test_entrypoint_get_by_filters_paged_with_invalid_sort(
        self, db_session: DBSession, entrypoint_repo
    ):
        with pytest.raises(errors.SortParameterValidationError):
            entrypoint_repo.get_by_filters_paged(
                group=None,
                filters=[],
                page_start=0,
                page_length=10,
                sort_by="invalid_field",
                descending=False,
            )

    def test_entrypoint_get_by_filters_paged_with_unlimited_length(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        for i in range(15):
            ep = make_entrypoint(
                account.user,
                account.group,
                name=f"test_ep{i}",
                description=f"description{i}",
            )
            entrypoint_repo.create(ep)
        db_session.commit()

        result, count = entrypoint_repo.get_by_filters_paged(
            group=account.group,
            filters=[],
            page_start=0,
            page_length=0,
            sort_by="name",
            descending=False,
        )
        assert count == 15
        assert len(result) == 15


class TestEntrypointGetExact:
    """Tests for EntrypointRepository.get_exact()"""

    def test_entrypoint_get_exact_single_exists(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep = make_entrypoint(account.user, account.group, description="description")
        entrypoint_repo.create(ep)
        db_session.commit()

        result = entrypoint_repo.get_exact(
            [ep.resource_id], utils.DeletionPolicy.NOT_DELETED
        )
        assert len(result) == 1
        assert result[0] == ep

    def test_entrypoint_get_exact_multiple(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep1 = make_entrypoint(
            account.user, account.group, name="test_ep1", description="description"
        )
        ep2 = make_entrypoint(
            account.user, account.group, name="test_ep2", description="description"
        )
        entrypoint_repo.create(ep1)
        entrypoint_repo.create(ep2)
        db_session.commit()

        result = entrypoint_repo.get_exact(
            [ep1.resource_id, ep2.resource_id], utils.DeletionPolicy.NOT_DELETED
        )
        assert len(result) == 2
        assert ep1 in result
        assert ep2 in result

    def test_entrypoint_get_exact_not_exists(
        self, db_session: DBSession, entrypoint_repo
    ):
        with pytest.raises(errors.EntityDoesNotExistError):
            entrypoint_repo.get_exact([99999], utils.DeletionPolicy.NOT_DELETED)

    def test_entrypoint_get_exact_deleted(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep = make_entrypoint(account.user, account.group, description="description")
        entrypoint_repo.create(ep)
        db_session.commit()

        lock = models.ResourceLock(resource_lock_types.DELETE, ep.resource)
        db_session.add(lock)
        db_session.commit()

        with pytest.raises(errors.EntityDoesNotExistError):
            entrypoint_repo.get_exact(
                [ep.resource_id], utils.DeletionPolicy.NOT_DELETED
            )


class TestEntrypointGetOneSnapshot:
    """Tests for EntrypointRepository.get_one_snapshot()"""

    def test_entrypoint_get_one_snapshot_exists(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep1 = make_entrypoint(account.user, account.group, description="description")
        entrypoint_repo.create(ep1)
        db_session.commit()

        ep2 = make_entrypoint_snapshot(ep1)
        entrypoint_repo.create_snapshot(ep2)
        db_session.commit()

        result = entrypoint_repo.get_one_snapshot(
            ep1.resource_id, ep2.resource_snapshot_id, utils.DeletionPolicy.ANY
        )
        assert result == ep2

    def test_entrypoint_get_one_snapshot_not_exists(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep = make_entrypoint(account.user, account.group, description="description")
        entrypoint_repo.create(ep)
        db_session.commit()

        with pytest.raises(errors.EntityDoesNotExistError):
            entrypoint_repo.get_one_snapshot(
                ep.resource_id, 99999, utils.DeletionPolicy.ANY
            )

    def test_entrypoint_get_one_snapshot_deleted(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep = make_entrypoint(account.user, account.group, description="description")
        entrypoint_repo.create(ep)
        db_session.commit()

        lock = models.ResourceLock(resource_lock_types.DELETE, ep.resource)
        db_session.add(lock)
        db_session.commit()

        with pytest.raises(errors.EntityDeletedError):
            entrypoint_repo.get_one_snapshot(
                ep.resource_id,
                ep.resource_snapshot_id,
                utils.DeletionPolicy.NOT_DELETED,
            )


class TestEntrypointGetPlugins:
    """Tests for EntrypointRepository.get_plugins()"""

    def test_entrypoint_get_plugins(self, entrypoint_with_plugins, entrypoint_repo):
        ep, plugins = entrypoint_with_plugins
        result = entrypoint_repo.get_plugins(ep, utils.DeletionPolicy.NOT_DELETED)
        assert len(result) == len(plugins)


class TestEntrypointCreatePlugins:
    """Tests for EntrypointRepository.create_plugins()"""

    def test_entrypoint_create_plugins_success(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        plugin1 = make_plugin(account.user, account.group, name="plugin1")
        db_session.add(plugin1)
        db_session.commit()

        ep = make_entrypoint(account.user, account.group)
        entrypoint_repo.create(ep)
        db_session.commit()

        result = entrypoint_repo.create_plugins(ep, [plugin1])
        assert len(result) == 1

        stored_plugins = entrypoint_repo.get_plugins(
            ep, utils.DeletionPolicy.NOT_DELETED
        )
        assert len(stored_plugins) == 1
        assert plugin1 in stored_plugins


class TestEntrypointAddPlugins:
    """Tests for EntrypointRepository.add_plugins()"""

    def test_entrypoint_add_plugins_success(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        plugin1 = make_plugin(account.user, account.group, name="plugin1")
        plugin2 = make_plugin(account.user, account.group, name="plugin2")
        db_session.add_all((plugin1, plugin2))
        db_session.commit()

        ep = make_entrypoint(account.user, account.group)
        entrypoint_repo.create(ep)

        ep.children.append(plugin1.resource)
        db_session.commit()

        result = entrypoint_repo.add_plugins(ep, [plugin2])
        assert len(result) == 2
        assert plugin1 in result
        assert plugin2 in result


class TestEntrypointSetPlugins:
    """Tests for EntrypointRepository.set_plugins()"""

    def test_entrypoint_set_plugins_success(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        plugin1 = make_plugin(account.user, account.group, name="plugin1")
        plugin2 = make_plugin(account.user, account.group, name="plugin2")
        db_session.add_all((plugin1, plugin2))
        db_session.commit()

        ep = make_entrypoint(account.user, account.group)
        entrypoint_repo.create(ep)

        ep.children.append(plugin1.resource)

        result = entrypoint_repo.set_plugins(ep.resource_id, [plugin2])
        assert len(result) == 1
        assert plugin2 in result


class TestEntrypointUnlinkPlugin:
    """Tests for EntrypointRepository.unlink_plugin()"""

    def test_entrypoint_unlink_plugin_success(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        plugin1 = make_plugin(account.user, account.group, name="plugin1")
        db_session.add(plugin1)
        db_session.commit()

        ep = make_entrypoint(account.user, account.group)
        entrypoint_repo.create(ep)

        ep.children.append(plugin1.resource)
        db_session.commit()

        entrypoint_repo.unlink_plugin(ep, plugin1)

        result = entrypoint_repo.get_plugins(ep, utils.DeletionPolicy.NOT_DELETED)
        assert len(result) == 0
