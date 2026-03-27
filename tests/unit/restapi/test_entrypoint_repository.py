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


class TestEntrypointCreate:
    """Tests for EntrypointRepository.create()"""

    def test_entrypoint_create_success(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep_resource = models.Resource("entry_point", account.group)
        entrypoint = models.EntryPoint(
            "",
            ep_resource,
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )

        entrypoint_repo.create(entrypoint)
        db_session.commit()

        result = entrypoint_repo.get_one(
            entrypoint.resource_id, utils.DeletionPolicy.NOT_DELETED
        )
        assert result == entrypoint

    def test_entrypoint_create_exists(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep_resource = models.Resource("entry_point", account.group)
        entrypoint = models.EntryPoint(
            "",
            ep_resource,
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
        entrypoint_repo.create(entrypoint)
        db_session.commit()

        with pytest.raises(errors.EntityExistsError):
            entrypoint_repo.create(entrypoint)

    def test_entrypoint_create_exists_deleted(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep_resource = models.Resource("entry_point", account.group)
        entrypoint = models.EntryPoint(
            "",
            ep_resource,
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
        entrypoint_repo.create(entrypoint)
        db_session.commit()

        lock = models.ResourceLock(resource_lock_types.DELETE, ep_resource)
        db_session.add(lock)
        db_session.commit()

        with pytest.raises(errors.EntityDeletedError):
            entrypoint_repo.create(entrypoint)

    def test_entrypoint_create_user_not_exist(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep_resource = models.Resource("entry_point", account.group)
        entrypoint = models.EntryPoint(
            "",
            ep_resource,
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
        entrypoint.creator = models.User("user2", "pass2", "user2@example.org")

        with pytest.raises(errors.EntityDoesNotExistError):
            entrypoint_repo.create(entrypoint)

    def test_entrypoint_create_user_deleted(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep_resource = models.Resource("entry_point", account.group)
        entrypoint = models.EntryPoint(
            "",
            ep_resource,
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )

        lock = models.UserLock(user_lock_types.DELETE, account.user)
        db_session.add(lock)
        db_session.commit()

        with pytest.raises(errors.EntityDeletedError):
            entrypoint_repo.create(entrypoint)

    def test_entrypoint_create_group_not_exist(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep_resource = models.Resource("entry_point", account.group)
        entrypoint = models.EntryPoint(
            "",
            ep_resource,
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )

        user2 = models.User("user2", "pass2", "user2@example.org")
        group2 = models.Group("group2", user2)
        entrypoint.resource.owner = group2

        with pytest.raises(errors.EntityDoesNotExistError):
            entrypoint_repo.create(entrypoint)

    def test_entrypoint_create_group_deleted(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep_resource = models.Resource("entry_point", account.group)
        entrypoint = models.EntryPoint(
            "",
            ep_resource,
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )

        lock = models.GroupLock(group_lock_types.DELETE, account.group)
        db_session.add(lock)
        db_session.commit()

        with pytest.raises(errors.EntityDeletedError):
            entrypoint_repo.create(entrypoint)

    def test_entrypoint_create_user_not_member(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep_resource = models.Resource("entry_point", account.group)
        entrypoint = models.EntryPoint(
            "",
            ep_resource,
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )

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
        ep_resource1 = models.Resource("entry_point", account.group)
        ep1 = models.EntryPoint(
            "",
            ep_resource1,
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
        entrypoint_repo.create(ep1)
        db_session.commit()

        ep_resource2 = models.Resource("entry_point", account.group)
        ep2 = models.EntryPoint(
            "",
            ep_resource2,
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
        with pytest.raises(errors.EntityExistsError):
            entrypoint_repo.create(ep2)

    def test_entrypoint_create_name_reuse(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep_resource1 = models.Resource("entry_point", account.group)
        ep1 = models.EntryPoint(
            "",
            ep_resource1,
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
        entrypoint_repo.create(ep1)
        db_session.commit()

        lock = models.ResourceLock(resource_lock_types.DELETE, ep1.resource)
        db_session.add(lock)
        db_session.commit()

        ep_resource2 = models.Resource("entry_point", account.group)
        ep2 = models.EntryPoint(
            "",
            ep_resource2,
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
        entrypoint_repo.create(ep2)
        db_session.commit()

        check_ep = db_session.get(models.EntryPoint, ep2.resource_snapshot_id)
        assert check_ep == ep2

    def test_entrypoint_create_wrong_resource_type(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep_resource = models.Resource("entry_point", account.group)
        entrypoint = models.EntryPoint(
            "",
            ep_resource,
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
        entrypoint.resource_type = "queue"

        with pytest.raises(errors.MismatchedResourceTypeError):
            entrypoint_repo.create(entrypoint)

        entrypoint.resource_type = "entry_point"
        entrypoint.resource.resource_type = "queue"

        with pytest.raises(errors.MismatchedResourceTypeError):
            entrypoint_repo.create(entrypoint)


class TestEntrypointCreateSnapshot:
    """Tests for EntrypointRepository.create_snapshot()"""

    def test_entrypoint_create_snapshot_success(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep_resource = models.Resource("entry_point", account.group)
        ep1 = models.EntryPoint(
            "",
            ep_resource,
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
        entrypoint_repo.create(ep1)
        db_session.commit()

        ep2 = models.EntryPoint(
            ep1.description,
            ep1.resource,
            ep1.creator,
            ep1.name,
            ep1.task_graph,
            ep1.artifact_graph,
            ep1.parameters,
            ep1.artifact_parameters,
        )
        ep2.created_on = ep1.created_on + datetime.timedelta(hours=1)

        entrypoint_repo.create_snapshot(ep2)
        db_session.commit()

        check_resource = db_session.get(models.Resource, ep2.resource_id)
        assert check_resource is not None
        assert len(check_resource.versions) == 2

    def test_entrypoint_create_snapshot_resource_not_exist(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep_resource = models.Resource("entry_point", account.group)
        entrypoint = models.EntryPoint(
            "",
            ep_resource,
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )

        with pytest.raises(errors.EntityDoesNotExistError):
            entrypoint_repo.create_snapshot(entrypoint)

    def test_entrypoint_create_snapshot_resource_deleted(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep_resource = models.Resource("entry_point", account.group)
        entrypoint = models.EntryPoint(
            "",
            ep_resource,
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
        lock = models.ResourceLock(resource_lock_types.DELETE, ep_resource)
        db_session.add_all((entrypoint, lock))
        db_session.commit()

        ep2 = models.EntryPoint(
            entrypoint.description,
            entrypoint.resource,
            entrypoint.creator,
            entrypoint.name,
            entrypoint.task_graph,
            entrypoint.artifact_graph,
            entrypoint.parameters,
            entrypoint.artifact_parameters,
        )
        ep2.created_on = entrypoint.created_on + datetime.timedelta(hours=1)

        with pytest.raises(errors.EntityDeletedError):
            entrypoint_repo.create_snapshot(ep2)

    def test_entrypoint_create_snapshot_snapshot_exists(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep_resource = models.Resource("entry_point", account.group)
        entrypoint = models.EntryPoint(
            "",
            ep_resource,
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
        entrypoint_repo.create(entrypoint)
        db_session.commit()

        with pytest.raises(errors.EntityExistsError):
            entrypoint_repo.create_snapshot(entrypoint)

    def test_entrypoint_create_snapshot_name_collision(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep_resource1 = models.Resource("entry_point", account.group)
        ep1 = models.EntryPoint(
            "",
            ep_resource1,
            account.user,
            "test_ep1",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
        ep_resource2 = models.Resource("entry_point", account.group)
        ep2 = models.EntryPoint(
            "",
            ep_resource2,
            account.user,
            "test_ep2",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
        db_session.add_all((ep1, ep2))
        db_session.commit()

        ep1_snap2 = models.EntryPoint(
            ep1.description,
            ep1.resource,
            ep1.creator,
            ep1.name,
            ep1.task_graph,
            ep1.artifact_graph,
            ep1.parameters,
            ep1.artifact_parameters,
        )
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
        ep_resource = models.Resource("entry_point", account.group)
        ep1 = models.EntryPoint(
            "description",
            ep_resource,
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
        ep2 = models.EntryPoint(
            ep1.description,
            ep1.resource,
            ep1.creator,
            ep1.name,
            ep1.task_graph,
            ep1.artifact_graph,
            ep1.parameters,
            ep1.artifact_parameters,
        )
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
        ep_resource = models.Resource("entry_point", account.group)
        ep1 = models.EntryPoint(
            "description",
            ep_resource,
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
        ep2 = models.EntryPoint(
            ep1.description,
            ep1.resource,
            ep1.creator,
            ep1.name,
            ep1.task_graph,
            ep1.artifact_graph,
            ep1.parameters,
            ep1.artifact_parameters,
        )
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
        ep_resource = models.Resource("entry_point", account.group)
        ep1 = models.EntryPoint(
            "description",
            ep_resource,
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )

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
        ep_resource = models.Resource("entry_point", account.group)
        ep1 = models.EntryPoint(
            "description",
            ep_resource,
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
        db_session.add(ep1)
        db_session.commit()

        group2 = models.Group("group2", account.user)

        with pytest.raises(errors.EntityDoesNotExistError):
            entrypoint_repo.get_by_name(ep1.name, group2, deletion_policy)

    def test_entrypoint_get_by_name_group_deleted(
        self, db_session: DBSession, account, entrypoint_repo, deletion_policy
    ):
        ep_resource = models.Resource("entry_point", account.group)
        ep1 = models.EntryPoint(
            "description",
            ep_resource,
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
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
        ep = models.EntryPoint(
            "description",
            models.Resource("entry_point", account.group),
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
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
        ep = models.EntryPoint(
            "description",
            models.Resource("entry_point", account.group),
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
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
        ep1 = models.EntryPoint(
            "description",
            models.Resource("entry_point", account.group),
            account.user,
            "test_ep1",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
        ep2 = models.EntryPoint(
            "description",
            models.Resource("entry_point", account.group),
            account.user,
            "test_ep2",
            "graph:",
            "artifact_output:",
            [],
            [],
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
        ep = models.EntryPoint(
            "description",
            models.Resource("entry_point", account.group),
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
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
        ep = models.EntryPoint(
            "description",
            models.Resource("entry_point", account.group),
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
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
        ep = models.EntryPoint(
            "description",
            models.Resource("entry_point", account.group),
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
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
        ep = models.EntryPoint(
            "description",
            models.Resource("entry_point", account.group),
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
        entrypoint_repo.create(ep)
        db_session.commit()

        lock = models.ResourceLock(resource_lock_types.DELETE, ep.resource)
        db_session.add(lock)
        db_session.commit()

        entrypoint_repo.delete(ep)


class TestEntrypointGetQueues:
    """Tests for EntrypointRepository.get_queues()"""

    def test_entrypoint_get_queues_with_children(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        queue_resource = models.Resource("queue", account.group)
        queue1 = models.Queue(
            description="", resource=queue_resource, creator=account.user, name="queue1"
        )
        db_session.add(queue1)
        db_session.commit()

        ep_resource = models.Resource("entry_point", account.group)
        ep = models.EntryPoint(
            "description",
            ep_resource,
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
        entrypoint_repo.create(ep)
        db_session.flush()

        ep.children.append(queue1.resource)
        db_session.commit()

        result = entrypoint_repo.get_queues(ep, utils.DeletionPolicy.NOT_DELETED)
        assert len(result) == 1
        assert queue1 in result

    def test_entrypoint_get_queues_no_children(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep_resource = models.Resource("entry_point", account.group)
        ep = models.EntryPoint(
            "description",
            ep_resource,
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
        entrypoint_repo.create(ep)
        db_session.commit()

        result = entrypoint_repo.get_queues(ep, utils.DeletionPolicy.NOT_DELETED)
        assert len(result) == 0


class TestEntrypointCreateQueues:
    """Tests for EntrypointRepository.create_queues()"""

    def test_entrypoint_create_queues_success(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        queue_resource = models.Resource("queue", account.group)
        queue1 = models.Queue(
            description="", resource=queue_resource, creator=account.user, name="queue1"
        )
        db_session.add(queue1)
        db_session.commit()

        ep_resource = models.Resource("entry_point", account.group)
        ep = models.EntryPoint(
            "description",
            ep_resource,
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )

        result = entrypoint_repo.create_queues(ep, [queue1])
        assert len(result) == 1


class TestEntrypointAddQueues:
    """Tests for EntrypointRepository.add_queues()"""

    def test_entrypoint_add_queues_success(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        queue1_resource = models.Resource("queue", account.group)
        queue1 = models.Queue(
            description="",
            resource=queue1_resource,
            creator=account.user,
            name="queue1",
        )
        queue2_resource = models.Resource("queue", account.group)
        queue2 = models.Queue(
            description="",
            resource=queue2_resource,
            creator=account.user,
            name="queue2",
        )
        db_session.add_all((queue1, queue2))
        db_session.commit()

        ep_resource = models.Resource("entry_point", account.group)
        ep = models.EntryPoint(
            "description",
            ep_resource,
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
        entrypoint_repo.create(ep)
        db_session.flush()

        ep.children.append(queue1.resource)
        db_session.commit()

        result = entrypoint_repo.add_queues(ep, [queue2])
        assert len(result) == 2
        assert queue1 in result
        assert queue2 in result


class TestEntrypointSetQueues:
    """Tests for EntrypointRepository.set_queues()"""

    def test_entrypoint_set_queues_success(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        queue1_resource = models.Resource("queue", account.group)
        queue1 = models.Queue(
            description="",
            resource=queue1_resource,
            creator=account.user,
            name="queue1",
        )
        queue2_resource = models.Resource("queue", account.group)
        queue2 = models.Queue(
            description="",
            resource=queue2_resource,
            creator=account.user,
            name="queue2",
        )
        db_session.add_all((queue1, queue2))
        db_session.commit()

        ep_resource = models.Resource("entry_point", account.group)
        ep = models.EntryPoint(
            "description",
            ep_resource,
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
        entrypoint_repo.create(ep)
        db_session.flush()

        ep.children.append(queue1.resource)
        db_session.flush()

        result = entrypoint_repo.set_queues(ep.resource_id, [queue2])
        assert len(result) == 1
        assert queue2 in result


class TestEntrypointUnlinkQueues:
    """Tests for EntrypointRepository.unlink_queue() and unlink_queues()"""

    def test_entrypoint_unlink_queue_success(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        queue1_resource = models.Resource("queue", account.group)
        queue1 = models.Queue(
            description="",
            resource=queue1_resource,
            creator=account.user,
            name="queue1",
        )
        db_session.add(queue1)
        db_session.commit()

        ep_resource = models.Resource("entry_point", account.group)
        ep = models.EntryPoint(
            "description",
            ep_resource,
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
        entrypoint_repo.create(ep)
        db_session.flush()

        ep.children.append(queue1.resource)
        db_session.commit()

        entrypoint_repo.unlink_queue(ep, queue1)

        db_session.refresh(ep)
        children = [c for c in ep.children if c.resource_type == "queue"]
        assert len(children) == 0

    def test_entrypoint_unlink_queues_success(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        queue1_resource = models.Resource("queue", account.group)
        queue1 = models.Queue(
            description="",
            resource=queue1_resource,
            creator=account.user,
            name="queue1",
        )
        queue2_resource = models.Resource("queue", account.group)
        queue2 = models.Queue(
            description="",
            resource=queue2_resource,
            creator=account.user,
            name="queue2",
        )
        db_session.add_all((queue1, queue2))
        db_session.commit()

        ep_resource = models.Resource("entry_point", account.group)
        ep = models.EntryPoint(
            "description",
            ep_resource,
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
        entrypoint_repo.create(ep)
        db_session.flush()

        ep.children.append(queue1.resource)
        ep.children.append(queue2.resource)
        db_session.commit()

        result = entrypoint_repo.unlink_queues(ep)
        assert len(result) == 2


class TestEntrypointGetPlugins:
    """Tests for EntrypointRepository.get_plugins()"""

    def test_entrypoint_get_plugins_no_children(
        self, db_session: DBSession, account, entrypoint_repo
    ):
        ep_resource = models.Resource("entry_point", account.group)
        ep = models.EntryPoint(
            "description",
            ep_resource,
            account.user,
            "test_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
        entrypoint_repo.create(ep)
        db_session.commit()

        result = entrypoint_repo.get_plugins(ep, utils.DeletionPolicy.NOT_DELETED)
        assert len(result) == 0


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
        ep1 = models.EntryPoint(
            "description1",
            models.Resource("entry_point", account.group),
            account.user,
            "test_ep1",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
        ep2 = models.EntryPoint(
            "description2",
            models.Resource("entry_point", account.group),
            account.user,
            "test_ep2",
            "graph:",
            "artifact_output:",
            [],
            [],
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
        ep1 = models.EntryPoint(
            "description1",
            models.Resource("entry_point", account.group),
            account.user,
            "foo_bar",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
        ep2 = models.EntryPoint(
            "description2",
            models.Resource("entry_point", account.group),
            account.user,
            "baz_qux",
            "graph:",
            "artifact_output:",
            [],
            [],
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
        ep1 = models.EntryPoint(
            "description1",
            models.Resource("entry_point", account.group),
            account.user,
            "aaa_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
        )
        ep2 = models.EntryPoint(
            "description2",
            models.Resource("entry_point", account.group),
            account.user,
            "zzz_ep",
            "graph:",
            "artifact_output:",
            [],
            [],
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
            ep = models.EntryPoint(
                f"description{i}",
                models.Resource("entry_point", account.group),
                account.user,
                f"test_ep{i}",
                "graph:",
                "artifact_output:",
                [],
                [],
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
            ep = models.EntryPoint(
                f"description{i}",
                models.Resource("entry_point", account.group),
                account.user,
                f"test_ep{i}",
                "graph:",
                "artifact_output:",
                [],
                [],
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
