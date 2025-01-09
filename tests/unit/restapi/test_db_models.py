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
"""Test suite for using the v1 ORM models to insert data in the database.

These tests exercise all of the v1 tables to ensure that the ORM models are configured
correctly and respect the data integrity constraints defined in the database schema.
These tests are a temporary measure that should eventually be replaced by integration
tests for the REST API.
"""
import uuid

import pytest
from faker import Faker
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

from dioptra.restapi.db import models
from dioptra.restapi.db.models.constants import (
    group_lock_types,
    resource_lock_types,
    user_lock_types,
)

from .lib import db as libdb
from .lib.db import views as viewsdb

# -- Fixtures --------------------------------------------------------------------------


@pytest.fixture
def fake_data(faker: Faker) -> libdb.FakeData:
    return libdb.FakeData(faker)


@pytest.fixture
def account(db: SQLAlchemy, fake_data: libdb.FakeData) -> libdb.FakeAccount:
    new_account = fake_data.account()
    db.session.add(new_account.user)
    db.session.add(new_account.group)
    db.session.commit()
    return new_account


@pytest.fixture
def second_account(
    db: SQLAlchemy, account: libdb.FakeData, fake_data: libdb.FakeData
) -> libdb.FakeAccount:
    new_account = fake_data.account()
    db.session.add(new_account.user)
    db.session.add(new_account.group)
    db.session.commit()
    return new_account


@pytest.fixture
def deleted_user_id(
    db: SQLAlchemy,
    account: libdb.FakeAccount,
) -> int:
    deleted_user_id = account.user.user_id
    deleted_user_lock = models.UserLock(
        user_lock_type=user_lock_types.DELETE,
        user=account.user,
    )
    db.session.add(deleted_user_lock)
    db.session.commit()
    return deleted_user_id


@pytest.fixture
def deleted_group_id(
    db: SQLAlchemy,
    account: libdb.FakeAccount,
) -> int:
    deleted_group_id = account.group.group_id
    deleted_group_lock = models.GroupLock(
        group_lock_type=group_lock_types.DELETE,
        group=account.group,
    )
    db.session.add(deleted_group_lock)
    db.session.commit()
    return deleted_group_id


@pytest.fixture
def tag_id(
    db: SQLAlchemy,
    account: libdb.FakeAccount,
    fake_data: libdb.FakeData,
) -> int:
    new_tag = fake_data.tag(creator=account.user, group=account.group)
    db.session.add(new_tag)
    db.session.commit()
    return new_tag.tag_id


@pytest.fixture
def registered_queue_id(
    db: SQLAlchemy,
    account: libdb.FakeAccount,
    fake_data: libdb.FakeData,
) -> int:
    new_queue = fake_data.queue(creator=account.user, group=account.group)
    db.session.add(new_queue)
    db.session.commit()
    return new_queue.resource_id


@pytest.fixture
def registered_queue_id_with_description(
    db: SQLAlchemy,
    account: libdb.FakeAccount,
    fake_data: libdb.FakeData,
) -> int:
    new_queue = fake_data.queue(
        creator=account.user, group=account.group, include_description=True
    )
    db.session.add(new_queue)
    db.session.commit()
    return new_queue.resource_id


@pytest.fixture
def draft_resource_id_for_new_queue_resource(
    db: SQLAlchemy,
    account: libdb.FakeAccount,
    fake_data: libdb.FakeData,
) -> int:
    new_queue = fake_data.queue(
        creator=account.user, group=account.group, include_description=True
    )
    draft_payload = {
        "name": new_queue.name,
        "description": new_queue.description,
        # If doing an update, this is the ID for snapshot being modified.
        # If None, then a new resource will be created.
        "resource_snapshot_id": None,
        # If doing an update, this is the ID for the resource being modified.
        # If None, then a new resource will be created.
        "resource_id": None,
    }
    draft_resource = models.DraftResource(
        resource_type="queue",
        target_owner=account.group,
        payload=draft_payload,
        creator=account.user,
    )
    db.session.add(draft_resource)
    db.session.commit()
    return draft_resource.draft_resource_id


@pytest.fixture
def edited_queue_id(
    db: SQLAlchemy,
    faker: Faker,
    registered_queue_id: int,
) -> int:
    queue_v1 = viewsdb.get_latest_queue(db, resource_id=registered_queue_id)

    if queue_v1 is None:
        raise ValueError("Failed to retrieve the latest queue for test.")

    queue_v2 = models.Queue(
        name=faker.sentence(nb_words=3, variable_nb_words=True),
        description=queue_v1.description,
        resource=queue_v1.resource,
        creator=queue_v1.creator,
    )
    db.session.add(queue_v2)
    db.session.commit()

    queue_v2 = viewsdb.get_latest_queue(db, resource_id=registered_queue_id)

    if queue_v2 is None:
        raise ValueError("Failed to retrieve the latest queue for test.")

    queue_v3 = models.Queue(
        name=queue_v2.name,
        description=faker.sentence(),
        resource=queue_v2.resource,
        creator=queue_v2.creator,
    )
    db.session.add(queue_v3)
    db.session.commit()

    return registered_queue_id


@pytest.fixture
def deleted_queue_id(
    db: SQLAlchemy,
    registered_queue_id: int,
) -> int:
    queue = viewsdb.get_latest_queue(db, resource_id=registered_queue_id)

    if queue is None:
        raise ValueError("Failed to retrieve the latest queue for test.")

    deleted_resource_lock = models.ResourceLock(
        resource_lock_type=resource_lock_types.DELETE,
        resource=queue.resource,
    )
    db.session.add(deleted_resource_lock)
    db.session.commit()
    return registered_queue_id


@pytest.fixture
def registered_and_tagged_queue_id(
    db: SQLAlchemy,
    registered_queue_id: int,
    tag_id: int,
) -> int:
    tag = db.session.get_one(models.Tag, tag_id)
    queue = viewsdb.get_latest_queue(db, resource_id=registered_queue_id)

    if queue is None:
        raise ValueError("Failed to retrieve the latest queue for test.")

    tag.resources.append(queue.resource)
    db.session.commit()

    return queue.resource_id


@pytest.fixture
def shared_resource_id_for_queue(
    db: SQLAlchemy,
    account: libdb.FakeAccount,
    second_account: libdb.FakeAccount,
    registered_queue_id: int,
) -> int:
    queue = viewsdb.get_latest_queue(db, resource_id=registered_queue_id)

    if queue is None:
        raise ValueError("Failed to retrieve the latest queue for test.")

    # The first user creates a read-only share of a queue resource for the second user's
    # default group.
    shared_resource = models.SharedResource(
        read=True,
        write=False,
        recipient=second_account.group,
        resource=queue.resource,
        creator=account.user,
    )
    db.session.add(shared_resource)
    db.session.commit()

    return shared_resource.shared_resource_id


@pytest.fixture
def registered_experiment_id(
    db: SQLAlchemy,
    account: libdb.FakeAccount,
    fake_data: libdb.FakeData,
) -> int:
    new_experiment = fake_data.experiment(creator=account.user, group=account.group)
    db.session.add(new_experiment)
    db.session.commit()
    return new_experiment.resource_id


@pytest.fixture
def registered_experiment_id_with_description(
    db: SQLAlchemy,
    account: libdb.FakeAccount,
    fake_data: libdb.FakeData,
) -> int:
    new_experiment = fake_data.experiment(
        creator=account.user, group=account.group, include_description=True
    )
    db.session.add(new_experiment)
    db.session.commit()
    return new_experiment.resource_id


@pytest.fixture
def registered_and_tagged_experiment_id(
    db: SQLAlchemy,
    registered_experiment_id: int,
    tag_id: int,
) -> int:
    tag = db.session.get_one(models.Tag, tag_id)
    experiment = viewsdb.get_latest_experiment(db, resource_id=registered_experiment_id)

    if experiment is None:
        raise ValueError("Failed to retrieve the latest queue for test.")

    tag.resources.append(experiment.resource)
    db.session.commit()

    return experiment.resource_id


@pytest.fixture
def registered_str_parameter_type_id(
    db: SQLAlchemy,
    account: libdb.FakeAccount,
    fake_data: libdb.FakeData,
) -> int:
    new_plugin_task_parameter_type = fake_data.plugin_task_parameter_type(
        creator=account.user, group=account.group, name="str"
    )
    db.session.add(new_plugin_task_parameter_type)
    db.session.commit()
    return new_plugin_task_parameter_type.resource_id


@pytest.fixture
def registered_plugin_id(
    db: SQLAlchemy,
    account: libdb.FakeAccount,
    fake_data: libdb.FakeData,
    registered_str_parameter_type_id: int,
) -> int:
    registered_str_parameter_type = viewsdb.get_latest_plugin_task_parameter_type(
        db, resource_id=registered_str_parameter_type_id
    )

    if registered_str_parameter_type is None:
        raise ValueError(
            "Failed to retrieve the latest plugin task parameter type for test."
        )

    new_plugin = fake_data.plugin(
        creator=account.user,
        group=account.group,
        str_parameter_type=registered_str_parameter_type,
    )
    db.session.add(new_plugin.plugin)
    db.session.add(new_plugin.init_plugin_file)
    db.session.add(new_plugin.plugin_file)
    db.session.add(new_plugin.plugin_task)
    db.session.commit()
    return new_plugin.plugin.resource_id


@pytest.fixture
def registered_entry_point_id(
    db: SQLAlchemy,
    account: libdb.FakeAccount,
    fake_data: libdb.FakeData,
    registered_queue_id: int,
    registered_plugin_id: int,
) -> int:
    registered_queue = viewsdb.get_latest_queue(db, resource_id=registered_queue_id)

    if registered_queue is None:
        raise ValueError("Failed to retrieve the latest queue for test.")

    registered_plugin = viewsdb.get_latest_plugin(db, resource_id=registered_plugin_id)

    if registered_plugin is None:
        raise ValueError("Failed to retrieve the latest plugin for test.")

    latest_plugin_files = viewsdb.get_latest_plugin_files(
        db,
        plugin_resource_id=registered_plugin_id,
    )
    new_entry_point = fake_data.entry_point(
        creator=account.user,
        group=account.group,
        plugin=registered_plugin,
        plugin_files=latest_plugin_files,
        queue=registered_queue,
    )
    db.session.add(new_entry_point)
    db.session.commit()

    return new_entry_point.resource_id


@pytest.fixture
def registered_experiment_entry_point_id(
    db: SQLAlchemy,
    registered_experiment_id: int,
    registered_entry_point_id: int,
) -> int:
    registered_experiment = viewsdb.get_latest_experiment(
        db, resource_id=registered_experiment_id
    )

    if registered_experiment is None:
        raise ValueError("Failed to retrieve the latest experiment for test.")

    registered_entry_point = viewsdb.get_latest_entry_point(
        db, resource_id=registered_entry_point_id
    )

    if registered_entry_point is None:
        raise ValueError("Failed to retrieve the latest entry point for test.")

    registered_experiment.children.append(registered_entry_point.resource)
    db.session.commit()

    return registered_experiment.resource_id


@pytest.fixture
def registered_job_id(
    db: SQLAlchemy,
    account: libdb.FakeAccount,
    fake_data: libdb.FakeData,
    registered_experiment_entry_point_id: int,
) -> int:
    registered_experiment = viewsdb.get_latest_experiment(
        db, resource_id=registered_experiment_entry_point_id
    )

    if registered_experiment is None:
        raise ValueError("Failed to retrieve the latest experiment for test.")

    experiment_entry_points = viewsdb.get_latest_experiment_entry_points(
        db, experiment_resource_id=registered_experiment_entry_point_id
    )

    if not experiment_entry_points:
        raise ValueError("No entry points associated with experiment resource.")

    entry_point_queues = viewsdb.get_latest_entry_point_queues(
        db, entry_point_resource_id=experiment_entry_points[0].resource_id
    )

    if not entry_point_queues:
        raise ValueError("No queues associated with entry point resource.")

    new_job = fake_data.job(
        creator=account.user,
        group=account.group,
        entry_point=experiment_entry_points[0],
        experiment=registered_experiment,
        queue=entry_point_queues[0],
    )
    db.session.add(new_job)
    db.session.commit()

    return new_job.resource_id


@pytest.fixture
def registered_child_job_id(
    db: SQLAlchemy,
    account: libdb.FakeAccount,
    fake_data: libdb.FakeData,
    registered_experiment_entry_point_id: int,
    registered_job_id: int,
) -> int:
    registered_experiment = viewsdb.get_latest_experiment(
        db, resource_id=registered_experiment_entry_point_id
    )

    if registered_experiment is None:
        raise ValueError("Failed to retrieve the latest experiment for test.")

    experiment_entry_points = viewsdb.get_latest_experiment_entry_points(
        db, experiment_resource_id=registered_experiment_entry_point_id
    )

    if not experiment_entry_points:
        raise ValueError("No entry points associated with experiment resource.")

    entry_point_queues = viewsdb.get_latest_entry_point_queues(
        db, entry_point_resource_id=experiment_entry_points[0].resource_id
    )

    if not entry_point_queues:
        raise ValueError("No queues associated with entry point resource.")

    parent_job = viewsdb.get_latest_job(db, resource_id=registered_job_id)

    if parent_job is None:
        raise ValueError("Failed to retrieve the parent job for test.")

    new_child_job = fake_data.job(
        creator=account.user,
        group=account.group,
        entry_point=experiment_entry_points[0],
        experiment=registered_experiment,
        queue=entry_point_queues[0],
    )

    # Make new_child_job depend on parent_job, meaning it should not start until
    # parent_job ends.
    new_child_job.parents.append(parent_job.resource)

    db.session.add(new_child_job)
    db.session.commit()

    return new_child_job.resource_id


@pytest.fixture
def registered_mlflow_run_job_resource_id(
    db: SQLAlchemy,
    account: libdb.FakeAccount,
    fake_data: libdb.FakeData,
    registered_job_id: int,
) -> int:
    job = viewsdb.get_latest_job(db, resource_id=registered_job_id)

    if job is None:
        raise ValueError("Failed to retrieve the latest job for test.")

    job_mlflow_run = fake_data.job_mlflow_run(job=job)
    db.session.add(job_mlflow_run)
    db.session.commit()

    return job_mlflow_run.job_resource_id


@pytest.fixture
def registered_artifact_id(
    db: SQLAlchemy,
    account: libdb.FakeAccount,
    fake_data: libdb.FakeData,
    registered_job_id: int,
) -> int:
    job = viewsdb.get_latest_job(db, resource_id=registered_job_id)

    if job is None:
        raise ValueError("Failed to retrieve the latest job for test.")

    artifact = fake_data.artifact(creator=account.user, group=account.group, job=job)
    db.session.add(artifact)
    db.session.commit()

    return artifact.resource_id


@pytest.fixture
def registered_ml_model_id(
    db: SQLAlchemy,
    account: libdb.FakeAccount,
    fake_data: libdb.FakeData,
    registered_artifact_id: int,
) -> int:
    artifact = viewsdb.get_latest_artifact(db, resource_id=registered_artifact_id)

    if artifact is None:
        raise ValueError("Failed to retrieve the latest artifact for test.")

    ml_model = fake_data.ml_model(
        creator=account.user, group=account.group, artifact=artifact
    )
    db.session.add(ml_model)
    db.session.commit()

    return ml_model.resource_id


# -- Tests -----------------------------------------------------------------------------


def test_db_user_not_deleted(db: SQLAlchemy, account: libdb.FakeAccount) -> None:
    user = db.session.get_one(models.User, account.user.user_id)
    delete_lock = [x for x in user.locks if x.user_lock_type == user_lock_types.DELETE]
    assert len(delete_lock) == 0
    assert isinstance(user.is_deleted, bool)
    assert not user.is_deleted


def test_db_delete_user(db: SQLAlchemy, deleted_user_id: int) -> None:
    deleted_user = db.session.get_one(models.User, deleted_user_id)
    delete_lock = [
        x for x in deleted_user.locks if x.user_lock_type == user_lock_types.DELETE
    ]
    assert len(delete_lock) == 1
    assert isinstance(deleted_user.is_deleted, bool)
    assert deleted_user.is_deleted


def test_db_group_not_deleted(db: SQLAlchemy, account: libdb.FakeAccount) -> None:
    group = db.session.get_one(models.Group, account.group.group_id)
    delete_lock = [
        x for x in group.locks if x.group_lock_type == group_lock_types.DELETE
    ]
    assert len(delete_lock) == 0
    assert isinstance(group.is_deleted, bool)
    assert not group.is_deleted


def test_db_delete_group(db: SQLAlchemy, deleted_group_id: int) -> None:
    deleted_group = db.session.get_one(models.Group, deleted_group_id)
    delete_lock = [
        x for x in deleted_group.locks if x.group_lock_type == group_lock_types.DELETE
    ]
    assert len(delete_lock) == 1
    assert isinstance(deleted_group.is_deleted, bool)
    assert deleted_group.is_deleted


def test_db_add_queue(
    db: SQLAlchemy, account: libdb.FakeAccount, registered_queue_id: int
) -> None:
    new_queue = viewsdb.get_latest_queue(db, resource_id=registered_queue_id)

    assert new_queue is not None
    assert new_queue.creator.user_id == account.user.user_id
    assert new_queue.resource.owner.group_id == account.group.group_id
    assert isinstance(new_queue.name, str)
    assert new_queue.description is None


def test_db_add_queue_with_description(
    db: SQLAlchemy,
    account: libdb.FakeAccount,
    registered_queue_id_with_description: int,
) -> None:
    new_queue = viewsdb.get_latest_queue(
        db, resource_id=registered_queue_id_with_description
    )

    assert new_queue is not None
    assert new_queue.creator.user_id == account.user.user_id
    assert new_queue.resource.owner.group_id == account.group.group_id
    assert isinstance(new_queue.name, str)
    assert new_queue.description is not None and isinstance(new_queue.description, str)


def test_db_add_queue_using_data_in_a_draft_resource(
    db: SQLAlchemy,
    account: libdb.FakeAccount,
    draft_resource_id_for_new_queue_resource: int,
) -> None:
    draft_resource = db.session.get_one(
        models.DraftResource, draft_resource_id_for_new_queue_resource
    )
    created_draft_resource_ids = {
        x.draft_resource_id for x in account.user.created_drafts
    }
    assert draft_resource_id_for_new_queue_resource in created_draft_resource_ids

    # Note: What follows assumes that we know the value of draft_resource.resource_type
    # ahead of time. In practice this will not be the case, and the appropriate ORM
    # model class will need to be retrieved based on the value of
    # draft_resource.resource_type.
    new_queue = models.Queue(
        name=draft_resource.payload["name"],
        description=draft_resource.payload["description"],
        resource=models.Resource(
            resource_type=draft_resource.resource_type,
            owner=draft_resource.target_owner,
        ),
        creator=draft_resource.creator,
    )
    db.session.add(new_queue)
    db.session.delete(draft_resource)
    db.session.commit()

    deleted_draft_resource = db.session.get(
        models.DraftResource, draft_resource_id_for_new_queue_resource
    )

    assert new_queue.resource_snapshot_id is not None
    assert new_queue.resource_id is not None
    assert new_queue.creator.user_id == account.user.user_id
    assert new_queue.resource.owner.group_id == account.group.group_id
    assert isinstance(new_queue.name, str)
    assert new_queue.description is not None and isinstance(new_queue.description, str)
    assert deleted_draft_resource is None


def test_db_share_queue_resource(
    db: SQLAlchemy,
    account: libdb.FakeAccount,
    second_account: libdb.FakeAccount,
    shared_resource_id_for_queue: int,
) -> None:
    shared_resource = db.session.get_one(
        models.SharedResource, shared_resource_id_for_queue
    )
    received_shared_resource_ids = {
        x.shared_resource_id for x in second_account.group.received_shares
    }
    created_shared_resource_ids = {
        x.shared_resource_id for x in account.user.created_shares
    }
    shared_queue = viewsdb.get_latest_queue(db, resource_id=shared_resource.resource_id)

    assert shared_resource.shared_resource_id in received_shared_resource_ids
    assert shared_resource.shared_resource_id in created_shared_resource_ids
    assert shared_queue is not None


def test_db_queue_resource_not_deleted(
    db: SQLAlchemy, registered_queue_id: int
) -> None:
    queue = viewsdb.get_latest_queue(db, resource_id=registered_queue_id)
    assert queue is not None

    queue_resource = db.session.get_one(models.Resource, registered_queue_id)
    assert isinstance(queue_resource.is_deleted, bool)
    assert not queue_resource.is_deleted


def test_db_delete_queue_resource(db: SQLAlchemy, deleted_queue_id: int) -> None:
    deleted_queue = viewsdb.get_latest_queue(db, resource_id=deleted_queue_id)
    assert deleted_queue is None

    deleted_queue_resource = db.session.get_one(models.Resource, deleted_queue_id)
    assert isinstance(deleted_queue_resource.is_deleted, bool)
    assert deleted_queue_resource.is_deleted


def test_db_queue_last_modified_on(db: SQLAlchemy, edited_queue_id: int) -> None:
    queue = viewsdb.get_latest_queue(db, resource_id=edited_queue_id)

    assert queue is not None
    assert len(queue.resource.versions) > 1
    assert queue.resource.last_modified_on > queue.resource.created_on
    assert queue.created_on == queue.resource.last_modified_on


def test_db_add_experiment(
    db: SQLAlchemy, account: libdb.FakeAccount, registered_experiment_id: int
) -> None:
    new_experiment = viewsdb.get_latest_experiment(
        db, resource_id=registered_experiment_id
    )

    assert new_experiment is not None
    assert new_experiment.creator.user_id == account.user.user_id
    assert new_experiment.resource.owner.group_id == account.group.group_id
    assert isinstance(new_experiment.name, str)
    assert new_experiment.description is None


def test_db_add_experiment_with_description(
    db: SQLAlchemy,
    account: libdb.FakeAccount,
    registered_experiment_id_with_description: int,
) -> None:
    new_experiment = viewsdb.get_latest_experiment(
        db, resource_id=registered_experiment_id_with_description
    )

    assert new_experiment is not None
    assert new_experiment.creator.user_id == account.user.user_id
    assert new_experiment.resource.owner.group_id == account.group.group_id
    assert isinstance(new_experiment.name, str)
    assert new_experiment.description is not None and isinstance(
        new_experiment.description, str
    )


def test_db_tag_resources(
    db: SQLAlchemy,
    account: libdb.FakeAccount,
    registered_and_tagged_queue_id: int,
    registered_and_tagged_experiment_id: int,
    tag_id: int,
) -> None:
    queue = viewsdb.get_latest_queue(db, resource_id=registered_and_tagged_queue_id)
    experiment = viewsdb.get_latest_experiment(
        db, resource_id=registered_and_tagged_experiment_id
    )

    assert queue is not None and experiment is not None
    assert tag_id in {x.tag_id for x in queue.tags}
    assert tag_id in {x.tag_id for x in experiment.tags}
    assert tag_id in {x.tag_id for x in account.user.created_tags}
    assert tag_id in {x.tag_id for x in account.group.available_tags}


def test_db_add_plugin_task_parameter_type(
    db: SQLAlchemy, account: libdb.FakeAccount, registered_str_parameter_type_id: int
) -> None:
    new_plugin_task_parameter_type = viewsdb.get_latest_plugin_task_parameter_type(
        db, resource_id=registered_str_parameter_type_id
    )

    assert new_plugin_task_parameter_type is not None
    assert new_plugin_task_parameter_type.creator.user_id == account.user.user_id
    assert (
        new_plugin_task_parameter_type.resource.owner.group_id == account.group.group_id
    )
    assert isinstance(new_plugin_task_parameter_type.name, str)


def test_db_add_plugin(
    db: SQLAlchemy, account: libdb.FakeAccount, registered_plugin_id: int
) -> None:
    new_plugin = viewsdb.get_latest_plugin(db, resource_id=registered_plugin_id)
    new_plugin_files = viewsdb.get_latest_plugin_files(
        db, plugin_resource_id=registered_plugin_id
    )

    assert new_plugin is not None
    assert new_plugin.creator.user_id == account.user.user_id
    assert new_plugin.resource.owner.group_id == account.group.group_id
    assert len(new_plugin_files) > 0

    for plugin_file in new_plugin_files:
        assert plugin_file.creator.user_id == account.user.user_id
        assert plugin_file.resource.owner.group_id == account.group.group_id


def test_db_add_entry_point(
    db: SQLAlchemy, account: libdb.FakeAccount, registered_entry_point_id: int
) -> None:
    new_entry_point = viewsdb.get_latest_entry_point(
        db, resource_id=registered_entry_point_id
    )

    assert new_entry_point is not None
    assert new_entry_point.creator.user_id == account.user.user_id
    assert new_entry_point.resource.owner.group_id == account.group.group_id
    assert len(new_entry_point.entry_point_plugin_files) > 0


def test_db_add_job(
    db: SQLAlchemy,
    account: libdb.FakeAccount,
    registered_job_id: int,
) -> None:
    new_job = viewsdb.get_latest_job(db, resource_id=registered_job_id)

    assert new_job is not None
    assert new_job.creator.user_id == account.user.user_id
    assert new_job.resource.owner.group_id == account.group.group_id
    assert new_job.entry_point_job.entry_point is not None
    assert new_job.experiment_job.experiment is not None
    assert new_job.queue_job.queue is not None
    assert new_job.mlflow_run is None


def test_db_add_job_that_depends_on_another_job(
    db: SQLAlchemy,
    registered_job_id: int,
    registered_child_job_id: int,
) -> None:
    child_job = viewsdb.get_latest_job(db, resource_id=registered_child_job_id)

    assert child_job is not None
    assert registered_job_id in {x.resource_id for x in child_job.parents}


def test_db_add_mlflow_run_to_job(
    db: SQLAlchemy,
    registered_mlflow_run_job_resource_id: int,
) -> None:
    job = viewsdb.get_latest_job(db, resource_id=registered_mlflow_run_job_resource_id)

    assert job is not None
    assert job.mlflow_run is not None
    assert isinstance(job.mlflow_run.mlflow_run_id, uuid.UUID)


@pytest.mark.skip(reason="Changes to the MlModel ORM object make this test incorrect.")
def test_db_add_artifact_to_job(
    db: SQLAlchemy,
    account: libdb.FakeAccount,
    registered_job_id: int,
    registered_artifact_id: int,
) -> None:
    new_artifact = viewsdb.get_latest_artifact(db, resource_id=registered_artifact_id)

    # Validate that the job/artifact association worked as expected, should be identical
    # to new_artifact
    job_artifacts = viewsdb.get_latest_job_artifacts(
        db, job_resource_id=registered_job_id
    )

    assert new_artifact is not None
    assert len(job_artifacts) == 1
    assert new_artifact.resource_snapshot_id == job_artifacts[0].resource_snapshot_id
    assert new_artifact.creator.user_id == account.user.user_id
    assert new_artifact.resource.owner.group_id == account.group.group_id
    assert new_artifact.uri.startswith("s3://")


@pytest.mark.skip(reason="Changes to the MlModel ORM object make this test incorrect.")
def test_db_add_ml_model_to_job(
    db: SQLAlchemy,
    account: libdb.FakeAccount,
    registered_ml_model_id: int,
) -> None:
    new_ml_model = viewsdb.get_latest_ml_model(db, resource_id=registered_ml_model_id)

    assert new_ml_model is not None
    assert new_ml_model.creator.user_id == account.user.user_id
    assert new_ml_model.resource.owner.group_id == account.group.group_id
    assert new_ml_model.artifact.creator.user_id == account.user.user_id
    assert new_ml_model.artifact.resource.owner.group_id == account.group.group_id
    assert isinstance(new_ml_model.name, str)


@pytest.mark.skip(reason="Changes to the MlModel ORM object make this test incorrect.")
def test_db_invalid_resource_dependency_fails(
    db: SQLAlchemy,
    registered_plugin_id: int,
    registered_ml_model_id: int,
) -> None:
    plugin = viewsdb.get_latest_plugin(db, resource_id=registered_plugin_id)
    ml_model = viewsdb.get_latest_ml_model(db, resource_id=registered_ml_model_id)

    assert plugin is not None and ml_model is not None

    with pytest.raises(IntegrityError):
        try:
            ml_model.parents.append(plugin.resource)
            db.session.commit()

        except IntegrityError as err:
            db.session.rollback()
            raise err
