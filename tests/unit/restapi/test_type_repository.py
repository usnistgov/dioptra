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
import dioptra.restapi.errors as errors
import tests.unit.restapi.lib.helpers as helpers
from dioptra.restapi.db.models.constants import (
    group_lock_types,
    resource_lock_types,
    user_lock_types,
)


@pytest.fixture
def point_type(db, account):
    """
    Fixture for creating a simple made-up type for use in testing snapshot
    creation (or anything else).
    """
    res = models.Resource("plugin_task_parameter_type", account.group)
    point_t = models.PluginTaskParameterType(
        "a point", res, account.user, "point", None
    )
    db.session.add(point_t)
    db.session.commit()

    return point_t


def test_type_create_not_exist(db, account, type_repo):

    res = models.Resource("plugin_task_parameter_type", account.group)
    type_ = models.PluginTaskParameterType(
        "a type", res, account.user, "test_type", {"some": "structure"}
    )

    type_repo.create(type_)
    db.session.commit()

    check_type = db.session.get(
        models.PluginTaskParameterType, type_.resource_snapshot_id
    )
    assert check_type == type_


def test_type_create_exists(db, fake_data, account, type_repo):
    type_ = fake_data.plugin_task_parameter_type(
        account.user, account.group, "test_type"
    )

    type_repo.create(type_)
    db.session.commit()

    with pytest.raises(errors.EntityExistsError):
        type_repo.create(type_)


def test_type_create_deleted(db, fake_data, account, type_repo):
    type_ = fake_data.plugin_task_parameter_type(
        account.user, account.group, "test_type"
    )

    lock = models.ResourceLock(resource_lock_types.DELETE, type_.resource)
    db.session.add_all((type_, lock))
    db.session.commit()

    with pytest.raises(errors.EntityDeletedError):
        type_repo.create(type_)


def test_type_create_user_not_exist(fake_data, account, type_repo):
    type_ = fake_data.plugin_task_parameter_type(
        account.user, account.group, "test_type"
    )

    user2 = models.User("user2", "pass2", "user2@example.org")
    type_.creator = user2

    with pytest.raises(errors.EntityDoesNotExistError):
        type_repo.create(type_)


def test_type_create_user_deleted(db, fake_data, account, type_repo):
    type_ = fake_data.plugin_task_parameter_type(
        account.user, account.group, "test_type"
    )

    lock = models.UserLock(user_lock_types.DELETE, account.user)
    db.session.add(lock)
    db.session.commit()

    with pytest.raises(errors.EntityDeletedError):
        type_repo.create(type_)


def test_type_create_group_not_exists(fake_data, account, type_repo):
    type_ = fake_data.plugin_task_parameter_type(
        account.user, account.group, "test_type"
    )

    group2 = models.Group("group2", account.user)
    type_.resource.owner = group2

    with pytest.raises(errors.EntityDoesNotExistError):
        type_repo.create(type_)


def test_type_create_group_deleted(db, fake_data, account, type_repo):
    type_ = fake_data.plugin_task_parameter_type(
        account.user, account.group, "test_type"
    )

    lock = models.GroupLock(group_lock_types.DELETE, type_.resource.owner)
    db.session.add(lock)
    db.session.commit()

    with pytest.raises(errors.EntityDeletedError):
        type_repo.create(type_)


def test_type_create_user_not_member(db, fake_data, account, type_repo):
    user2 = models.User("user2", "pass2", "user2@example.org")
    group2 = models.Group("group2", user2)
    db.session.add_all((user2, group2))
    db.session.commit()

    type_ = fake_data.plugin_task_parameter_type(account.user, group2, "test_type")

    with pytest.raises(errors.UserNotInGroupError):
        type_repo.create(type_)


def test_type_create_wrong_resource_type(db, fake_data, account, type_repo):

    res = models.Resource("queue", account.group)
    type_ = models.PluginTaskParameterType(
        "a type", res, account.user, "test_type", {"some": "structure"}
    )

    with pytest.raises(errors.MismatchedResourceTypeError):
        type_repo.create(type_)

    queue = fake_data.queue(account.user, account.group)
    with pytest.raises(errors.MismatchedResourceTypeError):
        type_repo.create(queue)


def test_type_create_name_collision(account, type_repo, point_type):

    res = models.Resource("plugin_task_parameter_type", account.group)
    type_ = models.PluginTaskParameterType(
        "a type", res, account.user, "point", {"some": "structure"}
    )

    with pytest.raises(errors.EntityExistsError):
        type_repo.create(type_)


def test_type_create_name_reuse(db, account, type_repo, point_type):

    lock = models.ResourceLock(resource_lock_types.DELETE, point_type.resource)
    db.session.add(lock)
    db.session.commit()

    # Once a resource is deleted, creating a new resource with that name is allowed.
    res = models.Resource("plugin_task_parameter_type", account.group)
    type_ = models.PluginTaskParameterType(
        "a type", res, account.user, "point", {"some": "structure"}
    )
    type_repo.create(type_)
    db.session.commit()

    check_type = db.session.get(
        models.PluginTaskParameterType, type_.resource_snapshot_id
    )
    assert check_type == type_


def test_type_create_snapshot_exists(db, fake_data, account, type_repo):
    type_ = fake_data.plugin_task_parameter_type(
        account.user, account.group, "test_type"
    )

    db.session.add(type_)
    db.session.commit()

    with pytest.raises(errors.EntityExistsError):
        type_repo.create_snapshot(type_)


def test_type_create_snapshot_not_exist(db, fake_data, account, type_repo):
    type_ = fake_data.plugin_task_parameter_type(
        account.user, account.group, "test_type"
    )

    db.session.add(type_)
    db.session.commit()

    type2 = models.PluginTaskParameterType(
        "snap2", type_.resource, type_.creator, "test_type", {"some": "structure"}
    )

    type_repo.create_snapshot(type2)
    db.session.commit()

    check_resource = db.session.get(models.Resource, type2.resource_id)
    assert check_resource is not None
    assert len(check_resource.versions) == 2
    assert type_ in check_resource.versions
    assert type2 in check_resource.versions
    assert type_.created_on < type2.created_on


def test_type_create_snapshot_resource_not_exist(fake_data, account, type_repo):
    type_ = fake_data.plugin_task_parameter_type(
        account.user, account.group, "test_type"
    )

    with pytest.raises(errors.EntityDoesNotExistError):
        type_repo.create_snapshot(type_)


def test_type_create_snapshot_user_not_exist(type_repo, point_type):

    user2 = models.User("user2", "pass2", "user2@example.org")
    point_type_v2 = models.PluginTaskParameterType(
        point_type.description, point_type.resource, user2, "point2", None
    )

    with pytest.raises(errors.EntityDoesNotExistError):
        type_repo.create_snapshot(point_type_v2)


def test_type_create_snapshot_user_deleted(db, type_repo, point_type):

    lock = models.UserLock(user_lock_types.DELETE, point_type.creator)
    db.session.add(lock)
    db.session.commit()

    point_type_v2 = models.PluginTaskParameterType(
        point_type.description, point_type.resource, point_type.creator, "point2", None
    )

    with pytest.raises(errors.EntityDeletedError):
        type_repo.create_snapshot(point_type_v2)


def test_type_create_snapshot_user_not_member(db, type_repo, point_type):

    user2 = models.User("user2", "pass2", "user2@example.org")
    group2 = models.Group("group2", user2)
    db.session.add_all((user2, group2))
    db.session.commit()

    point_type_v2 = models.PluginTaskParameterType(
        point_type.description, point_type.resource, user2, "point2", None
    )

    with pytest.raises(errors.UserNotInGroupError):
        type_repo.create_snapshot(point_type_v2)


# Fails: the queue's resource_type gets changed to
# "plugin_task_parameter_type" for some reason, which prevents the expected
# exception from being raised.
#
# def test_type_create_snapshot_wrong_resource_type(db, fake_data, account, type_repo, point_type):
#
#     queue = models.Queue("a queue", point_type.resource, point_type.creator, "my_queue")
#
#     with pytest.raises(errors.MismatchedResourceTypeError):
#         type_repo.create_snapshot(queue)


def test_type_create_snapshot_name_collision(
    db, fake_data, account, type_repo, point_type
):

    type_ = fake_data.plugin_task_parameter_type(account.user, account.group, "my_type")
    db.session.add(type_)
    db.session.commit()

    type2 = models.PluginTaskParameterType(
        type_.description,
        type_.resource,
        type_.creator,
        "point",  # already taken by point_type
        {"some": "structure"},
    )

    with pytest.raises(errors.EntityExistsError):
        type_repo.create_snapshot(type2)


def test_type_get_by_name_exists(type_repo, point_type, deletion_policy):

    found = type_repo.get_by_name("point", point_type.resource.owner, deletion_policy)
    expected_list = helpers.find_expected_snaps_for_deletion_policy(
        (point_type,), deletion_policy
    )

    if len(expected_list) == 0:
        assert not found
    else:
        assert found == expected_list[0]


def test_type_get_by_name_not_exist(type_repo, account, deletion_policy):
    found = type_repo.get_by_name("doesntexist", account.group, deletion_policy)

    assert not found


def test_type_get_by_name_deleted(db, type_repo, point_type, deletion_policy):

    lock = models.ResourceLock(resource_lock_types.DELETE, point_type.resource)
    db.session.add(lock)
    db.session.commit()

    found = type_repo.get_by_name("point", point_type.resource.owner, deletion_policy)
    expected_list = helpers.find_expected_snaps_for_deletion_policy(
        (point_type,), deletion_policy
    )

    if len(expected_list) == 0:
        assert not found
    else:
        assert found == expected_list[0]
