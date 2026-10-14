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
from dioptra.restapi.v1.entity_types import EntityType
from dioptra.restapi.v1.shared.search_parser import parse_search_text


def make_plugin(creator, group, name="test_plugin", description=""):
    resource = models.Resource("plugin", group)
    return models.Plugin(
        name=name,
        description=description,
        resource=resource,
        creator=creator,
    )


def make_plugin_snapshot(source_plugin, name=None, description=None, hours_offset=1):
    plugin = models.Plugin(
        name=name if name is not None else source_plugin.name,
        description=description
        if description is not None
        else source_plugin.description,
        resource=source_plugin.resource,
        creator=source_plugin.creator,
    )
    plugin.created_on = source_plugin.created_on + datetime.timedelta(
        hours=hours_offset
    )
    return plugin


def make_plugin_file(
    creator,
    group,
    filename="test_plugin.py",
    contents="# test plugin",
    description="",
):
    resource = models.Resource("plugin_file", group)
    return models.PluginFile(
        filename=filename,
        contents=contents,
        description=description,
        resource=resource,
        creator=creator,
    )


def make_plugin_file_snapshot(
    source_plugin_file,
    filename=None,
    contents=None,
    description=None,
    hours_offset=1,
):
    plugin_file = models.PluginFile(
        filename=filename if filename is not None else source_plugin_file.filename,
        contents=contents if contents is not None else source_plugin_file.contents,
        description=(
            description if description is not None else source_plugin_file.description
        ),
        resource=source_plugin_file.resource,
        creator=source_plugin_file.creator,
    )
    plugin_file.created_on = source_plugin_file.created_on + datetime.timedelta(
        hours=hours_offset
    )
    return plugin_file


def make_parameter_type(creator, group, name="string"):
    resource = models.Resource("plugin_task_parameter_type", group)
    return models.PluginTaskParameterType(
        name=name,
        structure=None,
        description=None,
        resource=resource,
        creator=creator,
    )


def create_plugin_with_files(
    db_session: DBSession,
    plugin_repo,
    account,
    plugin_name="test_plugin",
    filenames=("__init__.py", "test_plugin.py"),
):
    plugin = make_plugin(account.user, account.group, name=plugin_name)
    plugin_repo.create(plugin)
    db_session.commit()

    plugin_files = []
    for filename in filenames:
        plugin_file = make_plugin_file(account.user, account.group, filename=filename)
        plugin_repo.create_file(plugin_file, plugin.resource_id)
        plugin_files.append(plugin_file)
    db_session.commit()

    plugin_repo.associate_plugin_files(plugin, plugin_files)
    db_session.commit()

    return plugin_repo.get_one(plugin.resource_id, utils.DeletionPolicy.NOT_DELETED)


# ============================================================================
# region PluginRepository.create() tests
# ============================================================================


def test_plugin_create_success(db_session: DBSession, account, plugin_repo):
    plugin = make_plugin(account.user, account.group)

    plugin_repo.create(plugin)
    db_session.commit()

    result = plugin_repo.get_one(plugin.resource_id, utils.DeletionPolicy.NOT_DELETED)
    assert result == plugin


def test_plugin_create_exists(db_session: DBSession, account, plugin_repo):
    plugin = make_plugin(account.user, account.group)
    plugin_repo.create(plugin)
    db_session.commit()

    with pytest.raises(errors.EntityExistsError):
        plugin_repo.create(plugin)


def test_plugin_create_exists_deleted(db_session: DBSession, account, plugin_repo):
    plugin = make_plugin(account.user, account.group)
    plugin_repo.create(plugin)
    db_session.commit()

    db_session.add(models.ResourceLock(resource_lock_types.DELETE, plugin.resource))
    db_session.commit()

    with pytest.raises(errors.EntityDeletedError):
        plugin_repo.create(plugin)


def test_plugin_create_user_not_exist(account, plugin_repo):
    plugin = make_plugin(account.user, account.group)
    plugin.creator = models.User("user2", "pass2", "user2@example.org")

    with pytest.raises(errors.EntityDoesNotExistError):
        plugin_repo.create(plugin)


def test_plugin_create_user_deleted(db_session: DBSession, account, plugin_repo):
    plugin = make_plugin(account.user, account.group)

    db_session.add(models.UserLock(user_lock_types.DELETE, account.user))
    db_session.commit()

    with pytest.raises(errors.EntityDeletedError):
        plugin_repo.create(plugin)


def test_plugin_create_group_not_exist(account, plugin_repo):
    plugin = make_plugin(account.user, account.group)
    plugin.resource.owner = models.Group("group2", account.user)

    with pytest.raises(errors.EntityDoesNotExistError):
        plugin_repo.create(plugin)


def test_plugin_create_group_deleted(db_session: DBSession, account, plugin_repo):
    plugin = make_plugin(account.user, account.group)

    db_session.add(models.GroupLock(group_lock_types.DELETE, account.group))
    db_session.commit()

    with pytest.raises(errors.EntityDeletedError):
        plugin_repo.create(plugin)


def test_plugin_create_name_collision(db_session: DBSession, account, plugin_repo):
    plugin = make_plugin(account.user, account.group, name="duplicate")
    plugin_repo.create(plugin)
    db_session.commit()

    duplicate = make_plugin(account.user, account.group, name="duplicate")
    with pytest.raises(errors.EntityExistsError):
        plugin_repo.create(duplicate)


def test_plugin_create_name_reuse_after_delete(
    db_session: DBSession, account, plugin_repo
):
    plugin = make_plugin(account.user, account.group, name="reusable")
    plugin_repo.create(plugin)
    db_session.commit()

    db_session.add(models.ResourceLock(resource_lock_types.DELETE, plugin.resource))
    db_session.commit()

    replacement = make_plugin(account.user, account.group, name="reusable")
    plugin_repo.create(replacement)
    db_session.commit()

    assert replacement.resource_id != plugin.resource_id
    assert (
        plugin_repo.get_one(replacement.resource_id, utils.DeletionPolicy.NOT_DELETED)
        == replacement
    )


def test_plugin_create_user_not_member(db_session: DBSession, account, plugin_repo):
    user = models.User("other", "password", "other@example.org")
    db_session.add(user)
    db_session.commit()

    plugin = make_plugin(user, account.group)
    with pytest.raises(errors.UserNotInGroupError):
        plugin_repo.create(plugin)


def test_plugin_create_wrong_resource_type(account, plugin_repo):
    plugin = make_plugin(account.user, account.group)
    plugin.resource_type = "queue"

    with pytest.raises(errors.MismatchedResourceTypeError):
        plugin_repo.create(plugin)

    plugin.resource_type = "plugin"
    plugin.resource.resource_type = "queue"

    with pytest.raises(errors.MismatchedResourceTypeError):
        plugin_repo.create(plugin)


# endregion

# ============================================================================
# region PluginRepository.create_snapshot() tests
# ============================================================================


def test_plugin_create_snapshot_success(db_session: DBSession, account, plugin_repo):
    plugin = make_plugin(account.user, account.group, name="versioned")
    plugin_repo.create(plugin)
    db_session.commit()

    snapshot = make_plugin_snapshot(plugin, description="updated")
    plugin_repo.create_snapshot(snapshot)
    db_session.commit()

    latest = plugin_repo.get_one(plugin.resource_id, utils.DeletionPolicy.NOT_DELETED)
    assert latest == snapshot
    assert plugin.resource.latest_snapshot_id == snapshot.resource_snapshot_id
    assert len(plugin.resource.versions) == 2


def test_plugin_create_snapshot_name_collision(
    db_session: DBSession, account, plugin_repo
):
    plugin1 = make_plugin(account.user, account.group, name="plugin1")
    plugin2 = make_plugin(account.user, account.group, name="plugin2")
    plugin_repo.create(plugin1)
    plugin_repo.create(plugin2)
    db_session.commit()

    snapshot = make_plugin_snapshot(plugin2, name="plugin1")
    with pytest.raises(errors.EntityExistsError):
        plugin_repo.create_snapshot(snapshot)


def test_plugin_create_snapshot_resource_not_exist(account, plugin_repo):
    plugin = make_plugin(account.user, account.group)

    with pytest.raises(errors.EntityDoesNotExistError):
        plugin_repo.create_snapshot(plugin)


def test_plugin_create_snapshot_resource_deleted(
    db_session: DBSession, account, plugin_repo
):
    plugin = make_plugin(account.user, account.group)
    plugin_repo.create(plugin)
    db_session.commit()

    db_session.add(models.ResourceLock(resource_lock_types.DELETE, plugin.resource))
    db_session.commit()

    snapshot = make_plugin_snapshot(plugin)
    with pytest.raises(errors.EntityDeletedError):
        plugin_repo.create_snapshot(snapshot)


def test_plugin_create_snapshot_snapshot_exists(
    db_session: DBSession, account, plugin_repo
):
    plugin = make_plugin(account.user, account.group)
    plugin_repo.create(plugin)
    db_session.commit()

    with pytest.raises(errors.EntityExistsError):
        plugin_repo.create_snapshot(plugin)


def test_plugin_create_snapshot_user_not_exist(
    db_session: DBSession, account, plugin_repo
):
    plugin = make_plugin(account.user, account.group)
    plugin_repo.create(plugin)
    db_session.commit()
    snapshot = make_plugin_snapshot(plugin)
    snapshot.creator = models.User("user2", "pass2", "user2@example.org")

    with pytest.raises(errors.EntityDoesNotExistError):
        plugin_repo.create_snapshot(snapshot)


def test_plugin_create_snapshot_user_deleted(
    db_session: DBSession, account, plugin_repo
):
    plugin = make_plugin(account.user, account.group)
    plugin_repo.create(plugin)
    db_session.commit()
    snapshot = make_plugin_snapshot(plugin)

    db_session.add(models.UserLock(user_lock_types.DELETE, account.user))
    db_session.commit()

    with pytest.raises(errors.EntityDeletedError):
        plugin_repo.create_snapshot(snapshot)


def test_plugin_create_snapshot_user_not_member(
    db_session: DBSession, account, plugin_repo
):
    plugin = make_plugin(account.user, account.group)
    plugin_repo.create(plugin)
    db_session.commit()
    user = models.User("other", "password", "other@example.org")
    db_session.add(user)
    db_session.commit()
    snapshot = make_plugin_snapshot(plugin)
    snapshot.creator = user

    with pytest.raises(errors.UserNotInGroupError):
        plugin_repo.create_snapshot(snapshot)


def test_plugin_create_snapshot_wrong_resource_type(
    db_session: DBSession, account, plugin_repo
):
    plugin = make_plugin(account.user, account.group)
    plugin_repo.create(plugin)
    db_session.commit()

    snapshot = make_plugin_snapshot(plugin)
    snapshot.resource.resource_type = "queue"

    with db_session.no_autoflush, pytest.raises(errors.MismatchedResourceTypeError):
        plugin_repo.create_snapshot(snapshot)


# endregion

# ============================================================================
# region PluginRepository.get_by_name() tests
# ============================================================================


def test_plugin_get_by_name_exists(
    db_session: DBSession, account, plugin_repo, deletion_policy
):
    plugin1 = make_plugin(account.user, account.group, description="description")
    plugin_repo.create(plugin1)
    db_session.commit()
    plugin2 = make_plugin_snapshot(plugin1)
    if plugin1.created_on == plugin2.created_on:
        plugin2.created_on = plugin2.created_on + datetime.timedelta(hours=1)
    plugin_repo.create_snapshot(plugin2)
    db_session.commit()

    snap = plugin_repo.get_by_name(
        plugin1.name, plugin1.resource.owner, deletion_policy
    )

    expected_snaps = helpers.find_expected_snaps_for_deletion_policy(
        [plugin2], deletion_policy
    )
    expected_snap = expected_snaps[0] if expected_snaps else None
    assert snap == expected_snap


def test_plugin_get_by_name_deleted(
    db_session: DBSession, account, plugin_repo, deletion_policy
):
    plugin1 = make_plugin(account.user, account.group, description="description")
    plugin_repo.create(plugin1)
    db_session.commit()
    plugin2 = make_plugin_snapshot(plugin1)
    if plugin1.created_on == plugin2.created_on:
        plugin2.created_on = plugin2.created_on + datetime.timedelta(hours=1)
    plugin_repo.create_snapshot(plugin2)
    db_session.add(models.ResourceLock(resource_lock_types.DELETE, plugin1.resource))
    db_session.commit()

    snap = plugin_repo.get_by_name(
        plugin1.name, plugin1.resource.owner, deletion_policy
    )

    expected_snaps = helpers.find_expected_snaps_for_deletion_policy(
        [plugin2], deletion_policy
    )
    expected_snap = expected_snaps[0] if expected_snaps else None
    assert snap == expected_snap


def test_plugin_get_by_name_not_exist(
    db_session: DBSession, account, plugin_repo, deletion_policy
):
    plugin = make_plugin(account.user, account.group, description="description")

    snap = plugin_repo.get_by_name(plugin.name, plugin.resource.owner, deletion_policy)

    expected_snaps = helpers.find_expected_snaps_for_deletion_policy(
        [plugin], deletion_policy
    )
    expected_snap = expected_snaps[0] if expected_snaps else None
    assert snap == expected_snap


def test_plugin_get_by_name_group_not_exist(
    db_session: DBSession, account, plugin_repo, deletion_policy
):
    plugin = make_plugin(account.user, account.group, description="description")
    plugin_repo.create(plugin)
    db_session.commit()

    group2 = models.Group("group2", account.user)

    with pytest.raises(errors.EntityDoesNotExistError):
        plugin_repo.get_by_name(plugin.name, group2, deletion_policy)


def test_plugin_get_by_name_group_deleted(
    db_session: DBSession, account, plugin_repo, deletion_policy
):
    plugin = make_plugin(account.user, account.group, description="description")
    plugin_repo.create(plugin)
    db_session.commit()

    db_session.add(models.GroupLock(group_lock_types.DELETE, account.group))
    db_session.commit()

    with pytest.raises(errors.EntityDeletedError):
        plugin_repo.get_by_name(plugin.name, account.group, deletion_policy)


# endregion

# ============================================================================
# region PluginRepository.get() tests
# ============================================================================


def test_plugin_get_single_exists(db_session: DBSession, account, plugin_repo):
    plugin = make_plugin(account.user, account.group, description="description")
    plugin_repo.create(plugin)
    db_session.commit()

    result = plugin_repo.get(plugin.resource_id, utils.DeletionPolicy.NOT_DELETED)
    assert result == plugin


def test_plugin_get_single_not_exists(db_session: DBSession, plugin_repo):
    result = plugin_repo.get(99999, utils.DeletionPolicy.NOT_DELETED)
    assert result is None


def test_plugin_get_single_deleted(db_session: DBSession, account, plugin_repo):
    plugin = make_plugin(account.user, account.group, description="description")
    plugin_repo.create(plugin)
    db_session.commit()

    db_session.add(models.ResourceLock(resource_lock_types.DELETE, plugin.resource))
    db_session.commit()

    result = plugin_repo.get(plugin.resource_id, utils.DeletionPolicy.NOT_DELETED)
    assert result is None


def test_plugin_get_multiple(db_session: DBSession, account, plugin_repo):
    plugin1 = make_plugin(account.user, account.group, name="plugin1")
    plugin2 = make_plugin(account.user, account.group, name="plugin2")
    plugin_repo.create(plugin1)
    plugin_repo.create(plugin2)
    db_session.commit()

    result = plugin_repo.get(
        [plugin1.resource_id, plugin2.resource_id], utils.DeletionPolicy.NOT_DELETED
    )
    assert len(result) == 2
    assert plugin1 in result
    assert plugin2 in result


# endregion

# ============================================================================
# region PluginRepository.get_one() tests
# ============================================================================


def test_plugin_get_one_exists(db_session: DBSession, account, plugin_repo):
    plugin = make_plugin(account.user, account.group, description="description")
    plugin_repo.create(plugin)
    db_session.commit()

    result = plugin_repo.get_one(plugin.resource_id, utils.DeletionPolicy.NOT_DELETED)
    assert result == plugin


def test_plugin_get_one_not_exists(db_session: DBSession, plugin_repo):
    with pytest.raises(errors.EntityDoesNotExistError):
        plugin_repo.get_one(99999, utils.DeletionPolicy.NOT_DELETED)


def test_plugin_get_one_deleted(db_session: DBSession, account, plugin_repo):
    plugin = make_plugin(account.user, account.group, description="description")
    plugin_repo.create(plugin)
    db_session.commit()

    db_session.add(models.ResourceLock(resource_lock_types.DELETE, plugin.resource))
    db_session.commit()

    with pytest.raises(errors.EntityDeletedError):
        plugin_repo.get_one(plugin.resource_id, utils.DeletionPolicy.NOT_DELETED)


# endregion

# ============================================================================
# region PluginRepository.get_exact() tests
# ============================================================================


def test_plugin_get_exact_single_exists(db_session: DBSession, account, plugin_repo):
    plugin = make_plugin(account.user, account.group, description="description")
    plugin_repo.create(plugin)
    db_session.commit()

    result = plugin_repo.get_exact(
        [plugin.resource_id], utils.DeletionPolicy.NOT_DELETED
    )
    assert len(result) == 1
    assert result[0] == plugin


def test_plugin_get_exact_multiple(db_session: DBSession, account, plugin_repo):
    plugin1 = make_plugin(account.user, account.group, name="plugin1")
    plugin2 = make_plugin(account.user, account.group, name="plugin2")
    plugin_repo.create(plugin1)
    plugin_repo.create(plugin2)
    db_session.commit()

    result = plugin_repo.get_exact(
        [plugin1.resource_id, plugin2.resource_id], utils.DeletionPolicy.NOT_DELETED
    )
    assert len(result) == 2
    assert plugin1 in result
    assert plugin2 in result


def test_plugin_get_exact_not_exists(db_session: DBSession, plugin_repo):
    with pytest.raises(errors.EntityDoesNotExistError):
        plugin_repo.get_exact([99999], utils.DeletionPolicy.NOT_DELETED)


def test_plugin_get_exact_deleted(db_session: DBSession, account, plugin_repo):
    plugin = make_plugin(account.user, account.group, description="description")
    plugin_repo.create(plugin)
    db_session.commit()

    db_session.add(models.ResourceLock(resource_lock_types.DELETE, plugin.resource))
    db_session.commit()

    with pytest.raises(errors.EntityDoesNotExistError):
        plugin_repo.get_exact([plugin.resource_id], utils.DeletionPolicy.NOT_DELETED)


# endregion

# ============================================================================
# region PluginRepository.get_one_snapshot() tests
# ============================================================================


def test_plugin_get_one_snapshot_exists(db_session: DBSession, account, plugin_repo):
    plugin = make_plugin(account.user, account.group)
    plugin_repo.create(plugin)
    db_session.commit()
    snapshot = make_plugin_snapshot(plugin, description="updated")
    plugin_repo.create_snapshot(snapshot)
    db_session.commit()

    result = plugin_repo.get_one_snapshot(
        plugin.resource_id,
        snapshot.resource_snapshot_id,
        utils.DeletionPolicy.NOT_DELETED,
    )
    assert result == snapshot


# endregion

# ============================================================================
# region PluginRepository.get_by_filters_paged() tests
# ============================================================================


def test_plugin_get_by_filters_paged_empty(plugin_repo):
    result, count = plugin_repo.get_by_filters_paged(
        None,
        [],
        0,
        10,
        None,
        False,
    )

    assert result == []
    assert count == 0


def test_plugin_get_by_filters_paged_with_results(
    db_session: DBSession, account, plugin_repo
):
    plugin1 = make_plugin(account.user, account.group, name="alpha")
    plugin2 = make_plugin(account.user, account.group, name="beta")
    plugin_repo.create(plugin1)
    plugin_repo.create(plugin2)
    db_session.commit()

    result, count = plugin_repo.get_by_filters_paged(
        account.group.group_id,
        [],
        0,
        10,
        "name",
        False,
    )

    assert result == [plugin1, plugin2]
    assert count == 2


def test_plugin_get_by_filters_paged_with_filter(
    db_session: DBSession, account, plugin_repo
):
    plugin1 = make_plugin(account.user, account.group, name="alpha")
    plugin2 = make_plugin(account.user, account.group, name="beta")
    plugin_repo.create(plugin1)
    plugin_repo.create(plugin2)
    db_session.commit()

    result, count = plugin_repo.get_by_filters_paged(
        account.group,
        parse_search_text("name:alpha"),
        0,
        10,
        None,
        False,
    )

    assert result == [plugin1]
    assert count == 1


def test_plugin_get_by_filters_paged_with_sort(
    db_session: DBSession, account, plugin_repo
):
    plugin1 = make_plugin(account.user, account.group, name="aaa_plugin")
    plugin2 = make_plugin(account.user, account.group, name="zzz_plugin")
    plugin_repo.create(plugin1)
    plugin_repo.create(plugin2)
    db_session.commit()

    result, count = plugin_repo.get_by_filters_paged(
        account.group,
        [],
        0,
        10,
        "name",
        True,
    )

    assert count == 2
    assert result[0] == plugin2
    assert result[1] == plugin1


def test_plugin_get_by_filters_paged_with_pagination(
    db_session: DBSession, account, plugin_repo
):
    for i in range(3):
        plugin_repo.create(make_plugin(account.user, account.group, name=f"p{i}"))
    db_session.commit()

    result, count = plugin_repo.get_by_filters_paged(
        account.group,
        [],
        1,
        1,
        "name",
        False,
    )

    assert [plugin.name for plugin in result] == ["p1"]
    assert count == 3


def test_plugin_get_by_filters_paged_with_invalid_sort(account, plugin_repo):
    with pytest.raises(errors.SortParameterValidationError):
        plugin_repo.get_by_filters_paged(
            account.group,
            [],
            0,
            10,
            "invalid",
            False,
        )


def test_plugin_get_by_filters_paged_with_unlimited_length(
    db_session: DBSession, account, plugin_repo
):
    for i in range(15):
        plugin_repo.create(
            make_plugin(
                account.user,
                account.group,
                name=f"plugin{i}",
                description=f"description{i}",
            )
        )
    db_session.commit()

    result, count = plugin_repo.get_by_filters_paged(
        account.group,
        [],
        0,
        0,
        "name",
        False,
    )

    assert count == 15
    assert len(result) == 15


# endregion

# ============================================================================
# region PluginRepository.delete() tests
# ============================================================================


def test_plugin_delete_success(db_session: DBSession, account, plugin_repo):
    plugin = make_plugin(account.user, account.group)
    plugin_repo.create(plugin)
    db_session.commit()

    plugin_repo.delete(plugin)
    db_session.commit()

    assert plugin.resource.is_deleted


def test_plugin_delete_missing(plugin_repo):
    with pytest.raises(errors.EntityDoesNotExistError):
        plugin_repo.delete(12345)


# endregion

# ============================================================================
# region PluginRepository.create_file() tests
# ============================================================================


def test_plugin_create_file_and_associate(db_session: DBSession, account, plugin_repo):
    plugin = make_plugin(account.user, account.group)
    plugin_repo.create(plugin)
    db_session.commit()
    plugin_file = make_plugin_file(account.user, account.group)

    plugin_repo.create_file(plugin_file, plugin.resource_id)
    db_session.commit()
    plugin_repo.associate_plugin_files(plugin, [plugin_file])
    db_session.commit()

    result = plugin_repo.get_one_file(
        plugin.resource_id,
        plugin_file.resource_id,
        utils.DeletionPolicy.NOT_DELETED,
    )
    assert result == plugin_file


def test_plugin_create_file_exists(db_session: DBSession, account, plugin_repo):
    plugin_file = make_plugin_file(account.user, account.group)
    plugin_repo.create_file(plugin_file)
    db_session.commit()

    with pytest.raises(errors.EntityExistsError):
        plugin_repo.create_file(plugin_file)


def test_plugin_create_file_exists_deleted(db_session: DBSession, account, plugin_repo):
    plugin_file = make_plugin_file(account.user, account.group)
    plugin_repo.create_file(plugin_file)
    db_session.commit()

    db_session.add(
        models.ResourceLock(resource_lock_types.DELETE, plugin_file.resource)
    )
    db_session.commit()

    with pytest.raises(errors.EntityDeletedError):
        plugin_repo.create_file(plugin_file)


def test_plugin_create_file_user_not_exist(account, plugin_repo):
    plugin_file = make_plugin_file(account.user, account.group)
    plugin_file.creator = models.User("user2", "pass2", "user2@example.org")

    with pytest.raises(errors.EntityDoesNotExistError):
        plugin_repo.create_file(plugin_file)


def test_plugin_create_file_user_deleted(db_session: DBSession, account, plugin_repo):
    plugin_file = make_plugin_file(account.user, account.group)

    db_session.add(models.UserLock(user_lock_types.DELETE, account.user))
    db_session.commit()

    with pytest.raises(errors.EntityDeletedError):
        plugin_repo.create_file(plugin_file)


def test_plugin_create_file_group_not_exist(account, plugin_repo):
    plugin_file = make_plugin_file(account.user, account.group)
    plugin_file.resource.owner = models.Group("group2", account.user)

    with pytest.raises(errors.EntityDoesNotExistError):
        plugin_repo.create_file(plugin_file)


def test_plugin_create_file_group_deleted(db_session: DBSession, account, plugin_repo):
    plugin_file = make_plugin_file(account.user, account.group)

    db_session.add(models.GroupLock(group_lock_types.DELETE, account.group))
    db_session.commit()

    with pytest.raises(errors.EntityDeletedError):
        plugin_repo.create_file(plugin_file)


def test_plugin_create_file_user_not_member(
    db_session: DBSession, account, plugin_repo
):
    user = models.User("other", "password", "other@example.org")
    db_session.add(user)
    db_session.commit()

    plugin_file = make_plugin_file(user, account.group)

    with pytest.raises(errors.UserNotInGroupError):
        plugin_repo.create_file(plugin_file)


def test_plugin_create_file_wrong_resource_type(account, plugin_repo):
    plugin_file = make_plugin_file(account.user, account.group)
    plugin_file.resource_type = "queue"

    with pytest.raises(errors.MismatchedResourceTypeError):
        plugin_repo.create_file(plugin_file)

    plugin_file.resource_type = "plugin_file"
    plugin_file.resource.resource_type = "queue"

    with pytest.raises(errors.MismatchedResourceTypeError):
        plugin_repo.create_file(plugin_file)


def test_plugin_create_file_duplicate_filename_same_plugin(
    db_session: DBSession, account, plugin_repo
):
    plugin = create_plugin_with_files(
        db_session, plugin_repo, account, filenames=("duplicate.py",)
    )
    duplicate = make_plugin_file(account.user, account.group, filename="duplicate.py")

    with pytest.raises(errors.EntityExistsError):
        plugin_repo.create_file(duplicate, plugin.resource_id)


def test_plugin_create_file_duplicate_filename_different_plugin(
    db_session: DBSession, account, plugin_repo
):
    plugin1 = create_plugin_with_files(
        db_session,
        plugin_repo,
        account,
        plugin_name="plugin1",
        filenames=("shared.py",),
    )
    plugin1_file_id = plugin1.plugin_files[0].resource_id

    plugin2 = make_plugin(account.user, account.group, name="plugin2")
    plugin_repo.create(plugin2)
    db_session.commit()
    plugin2_resource_id = plugin2.resource_id

    plugin2_file = make_plugin_file(
        account.user,
        account.group,
        filename="shared.py",
    )
    plugin_repo.create_file(plugin2_file, plugin2_resource_id)
    db_session.commit()
    plugin_repo.associate_plugin_files(plugin2, [plugin2_file])
    db_session.commit()
    plugin2_file_id = plugin2_file.resource_id

    db_session.expire_all()

    result = plugin_repo.get_one_file(
        plugin2_resource_id,
        plugin2_file_id,
        utils.DeletionPolicy.NOT_DELETED,
    )

    assert result.filename == "shared.py"
    assert result.resource_id == plugin2_file_id
    assert result.resource_id != plugin1_file_id


# endregion

# ============================================================================
# region PluginRepository.get_one_file() tests
# ============================================================================


def test_plugin_get_one_file_exists(db_session: DBSession, account, plugin_repo):
    plugin = create_plugin_with_files(db_session, plugin_repo, account)
    plugin_file = plugin.plugin_files[0]

    result = plugin_repo.get_one_file(
        plugin.resource_id,
        plugin_file.resource_id,
        utils.DeletionPolicy.NOT_DELETED,
    )

    assert result == plugin_file


def test_plugin_get_one_file_not_exists(db_session: DBSession, account, plugin_repo):
    plugin = create_plugin_with_files(db_session, plugin_repo, account)

    with pytest.raises(errors.EntityDoesNotExistError):
        plugin_repo.get_one_file(
            plugin.resource_id,
            99999,
            utils.DeletionPolicy.NOT_DELETED,
        )


def test_plugin_get_one_file_wrong_parent(db_session: DBSession, account, plugin_repo):
    plugin1 = create_plugin_with_files(
        db_session,
        plugin_repo,
        account,
        plugin_name="plugin1",
    )
    plugin2 = make_plugin(account.user, account.group, name="plugin2")
    plugin_repo.create(plugin2)
    db_session.commit()
    plugin_file = plugin1.plugin_files[0]

    with pytest.raises(errors.EntityDoesNotExistError):
        plugin_repo.get_one_file(
            plugin2.resource_id,
            plugin_file.resource_id,
            utils.DeletionPolicy.NOT_DELETED,
        )


def test_plugin_get_one_file_rejects_non_plugin_parent(
    db_session: DBSession, account, fake_data, plugin_repo
):
    plugin = create_plugin_with_files(db_session, plugin_repo, account)
    queue = fake_data.queue(account.user, account.group)
    db_session.add(queue)
    db_session.commit()

    with pytest.raises(errors.EntityDoesNotExistError) as exc_info:
        plugin_repo.get_one_file(
            queue.resource_id,
            plugin.plugin_files[0].resource_id,
            utils.DeletionPolicy.NOT_DELETED,
        )

    assert exc_info.value.entity_type is EntityType.PLUGIN


def test_plugin_get_one_file_deleted(db_session: DBSession, account, plugin_repo):
    plugin = create_plugin_with_files(db_session, plugin_repo, account)
    plugin_file = plugin.plugin_files[0]

    db_session.add(
        models.ResourceLock(resource_lock_types.DELETE, plugin_file.resource)
    )
    db_session.commit()

    with pytest.raises(errors.EntityDeletedError):
        plugin_repo.get_one_file(
            plugin.resource_id,
            plugin_file.resource_id,
            utils.DeletionPolicy.NOT_DELETED,
        )
    assert (
        plugin_repo.get_one_file(
            plugin.resource_id,
            plugin_file.resource_id,
            utils.DeletionPolicy.DELETED,
        )
        == plugin_file
    )


# endregion

# ============================================================================
# region PluginRepository.create_file_snapshot() tests
# ============================================================================


def test_plugin_create_file_snapshot_success(
    db_session: DBSession, account, plugin_repo
):
    plugin = create_plugin_with_files(db_session, plugin_repo, account)
    plugin_file = plugin_repo.get_one_file(
        plugin.resource_id,
        plugin.plugin_files[0].resource_id,
        utils.DeletionPolicy.NOT_DELETED,
    )
    snapshot = make_plugin_file_snapshot(plugin_file, contents="# updated")
    plugin_snapshot = make_plugin_snapshot(plugin)

    plugin_repo.create_snapshot(plugin_snapshot)
    plugin_repo.create_file_snapshot(snapshot, plugin.resource_id)
    plugin_repo.associate_plugin_files(plugin_snapshot, [snapshot])
    db_session.commit()

    latest = plugin_repo.get_one_file(
        plugin.resource_id,
        plugin_file.resource_id,
        utils.DeletionPolicy.NOT_DELETED,
    )
    assert latest == snapshot


def test_plugin_create_file_snapshot_resource_not_exist(account, plugin_repo):
    plugin_file = make_plugin_file(account.user, account.group)

    with pytest.raises(errors.EntityDoesNotExistError):
        plugin_repo.create_file_snapshot(plugin_file)


def test_plugin_create_file_snapshot_resource_deleted(
    db_session: DBSession, account, plugin_repo
):
    plugin = create_plugin_with_files(db_session, plugin_repo, account)
    plugin_file = plugin.plugin_files[0]
    snapshot = make_plugin_file_snapshot(plugin_file)

    db_session.add(
        models.ResourceLock(resource_lock_types.DELETE, plugin_file.resource)
    )
    db_session.commit()

    with pytest.raises(errors.EntityDeletedError):
        plugin_repo.create_file_snapshot(snapshot, plugin.resource_id)


def test_plugin_create_file_snapshot_snapshot_exists(
    db_session: DBSession, account, plugin_repo
):
    plugin = create_plugin_with_files(db_session, plugin_repo, account)
    plugin_file = plugin.plugin_files[0]

    with pytest.raises(errors.EntityExistsError):
        plugin_repo.create_file_snapshot(plugin_file, plugin.resource_id)


def test_plugin_create_file_snapshot_duplicate_filename(
    db_session: DBSession, account, plugin_repo
):
    plugin = create_plugin_with_files(
        db_session,
        plugin_repo,
        account,
        filenames=("alpha.py", "beta.py"),
    )
    plugin_file = plugin.plugin_files[1]
    snapshot = make_plugin_file_snapshot(plugin_file, filename="alpha.py")

    with pytest.raises(errors.EntityExistsError):
        plugin_repo.create_file_snapshot(snapshot, plugin.resource_id)


def test_plugin_create_file_snapshot_same_filename_allowed(
    db_session: DBSession, account, plugin_repo
):
    plugin = create_plugin_with_files(db_session, plugin_repo, account)
    plugin_file = plugin.plugin_files[0]
    snapshot = make_plugin_file_snapshot(plugin_file, contents="# updated")

    plugin_repo.create_file_snapshot(snapshot, plugin.resource_id)
    db_session.commit()

    result = db_session.get(models.PluginFile, snapshot.resource_snapshot_id)
    assert result == snapshot


# endregion

# ============================================================================
# region PluginRepository.get_by_filters_paged_files() tests
# ============================================================================


def test_plugin_get_by_filters_paged_files_empty(
    db_session: DBSession, account, plugin_repo
):
    plugin = make_plugin(account.user, account.group)
    plugin_repo.create(plugin)
    db_session.commit()

    result, count = plugin_repo.get_by_filters_paged_files(
        plugin,
        [],
        0,
        10,
        None,
        False,
    )

    assert count == 0
    assert len(result) == 0


def test_plugin_get_by_filters_paged_files_with_results(
    db_session: DBSession, account, plugin_repo
):
    plugin = create_plugin_with_files(
        db_session,
        plugin_repo,
        account,
        filenames=("alpha.py", "beta.py"),
    )

    result, count = plugin_repo.get_by_filters_paged_files(
        plugin,
        [],
        0,
        10,
        None,
        False,
    )

    assert count == 2
    assert len(result) == 2


def test_plugin_get_by_filters_paged_files_with_filters(
    db_session: DBSession, account, plugin_repo
):
    plugin = create_plugin_with_files(
        db_session,
        plugin_repo,
        account,
        filenames=("alpha.py", "beta.py"),
    )
    filters = parse_search_text("filename:*.py,filename:alpha*")

    result, count = plugin_repo.get_by_filters_paged_files(
        plugin,
        filters,
        0,
        10,
        "filename",
        False,
    )

    assert [plugin_file.filename for plugin_file in result] == ["alpha.py"]
    assert count == 1


def test_plugin_get_by_filters_paged_files_only_returns_parent_files(
    db_session: DBSession, account, plugin_repo
):
    plugin = create_plugin_with_files(
        db_session,
        plugin_repo,
        account,
        plugin_name="plugin1",
        filenames=("plugin1.py",),
    )
    create_plugin_with_files(
        db_session,
        plugin_repo,
        account,
        plugin_name="plugin2",
        filenames=("plugin2.py",),
    )

    result, count = plugin_repo.get_by_filters_paged_files(
        plugin,
        [],
        0,
        10,
        "filename",
        False,
    )

    assert [plugin_file.filename for plugin_file in result] == ["plugin1.py"]
    assert count == 1


def test_plugin_get_by_filters_paged_files_rejects_non_plugin_parent(
    db_session: DBSession, account, fake_data, plugin_repo
):
    queue = fake_data.queue(account.user, account.group)
    db_session.add(queue)
    db_session.commit()

    with pytest.raises(errors.EntityDoesNotExistError) as exc_info:
        plugin_repo.get_by_filters_paged_files(
            queue.resource_id,
            [],
            0,
            10,
            None,
            False,
        )

    assert exc_info.value.entity_type is EntityType.PLUGIN


def test_plugin_get_by_filters_paged_files_invalid_filter(
    db_session: DBSession, account, plugin_repo
):
    plugin = create_plugin_with_files(db_session, plugin_repo, account)

    with pytest.raises(errors.SearchParseError):
        plugin_repo.get_by_filters_paged_files(
            plugin,
            parse_search_text("invalid:value"),
            0,
            10,
            None,
            False,
        )


def test_plugin_get_by_filters_paged_files_with_sort(
    db_session: DBSession, account, plugin_repo
):
    plugin = create_plugin_with_files(
        db_session,
        plugin_repo,
        account,
        filenames=("aaa.py", "zzz.py"),
    )

    result, count = plugin_repo.get_by_filters_paged_files(
        plugin,
        [],
        0,
        10,
        "filename",
        True,
    )

    assert count == 2
    assert [plugin_file.filename for plugin_file in result] == ["zzz.py", "aaa.py"]


def test_plugin_get_by_filters_paged_files_with_pagination(
    db_session: DBSession, account, plugin_repo
):
    plugin = create_plugin_with_files(
        db_session,
        plugin_repo,
        account,
        filenames=tuple(f"plugin{i}.py" for i in range(5)),
    )

    result, count = plugin_repo.get_by_filters_paged_files(
        plugin,
        [],
        0,
        2,
        "filename",
        False,
    )

    assert count == 5
    assert len(result) == 2


def test_plugin_get_by_filters_paged_files_invalid_sort(
    db_session: DBSession, account, plugin_repo
):
    plugin = create_plugin_with_files(db_session, plugin_repo, account)

    with pytest.raises(errors.SortParameterValidationError):
        plugin_repo.get_by_filters_paged_files(
            plugin,
            [],
            0,
            10,
            "invalid",
            False,
        )


def test_plugin_get_by_filters_paged_files_with_unlimited_length(
    db_session: DBSession, account, plugin_repo
):
    plugin = create_plugin_with_files(
        db_session,
        plugin_repo,
        account,
        filenames=tuple(f"plugin{i}.py" for i in range(15)),
    )

    result, count = plugin_repo.get_by_filters_paged_files(
        plugin,
        [],
        0,
        0,
        "filename",
        False,
    )

    assert count == 15
    assert len(result) == 15


# endregion

# ============================================================================
# region PluginRepository.delete_file() tests
# ============================================================================


def test_plugin_delete_file_success(db_session: DBSession, account, plugin_repo):
    plugin = create_plugin_with_files(db_session, plugin_repo, account)
    plugin_file = plugin.plugin_files[0]

    plugin_repo.delete_file(plugin_file)
    db_session.commit()

    assert plugin_file.resource.is_deleted


# endregion

# ============================================================================
# region PluginRepository associations and tasks tests
# ============================================================================


def test_plugin_get_one_plugin_plugin_file(db_session: DBSession, account, plugin_repo):
    plugin = create_plugin_with_files(db_session, plugin_repo, account)
    plugin_file = plugin.plugin_files[0]
    plugin_id = plugin.resource_id
    plugin_snapshot_id = plugin.resource_snapshot_id
    plugin_file_id = plugin_file.resource_id
    plugin_file_snapshot_id = plugin_file.resource_snapshot_id

    db_session.expire_all()

    result = plugin_repo.get_one_plugin_plugin_file(
        plugin_snapshot_id,
        plugin_file_snapshot_id,
    )

    assert result.plugin_resource_snapshot_id == plugin_snapshot_id
    assert result.plugin_file_resource_snapshot_id == plugin_file_snapshot_id
    assert result.plugin.resource_id == plugin_id
    assert result.plugin_file.resource_id == plugin_file_id


def test_plugin_get_one_plugin_plugin_file_missing(plugin_repo):
    with pytest.raises(errors.EntityRelationshipDoesNotExistError):
        plugin_repo.get_one_plugin_plugin_file(123, 456)


def test_plugin_add_and_get_one_task(db_session: DBSession, account, plugin_repo):
    plugin = create_plugin_with_files(
        db_session, plugin_repo, account, filenames=("tasks.py",)
    )
    plugin_file = plugin.plugin_files[0]
    parameter_type = make_parameter_type(account.user, account.group)
    db_session.add(parameter_type)
    db_session.commit()
    function_tasks = [
        {
            "name": "hello_world",
            "input_params": [
                {
                    "name": "name",
                    "parameter_type_id": parameter_type.resource_id,
                    "required": True,
                }
            ],
            "output_params": [
                {
                    "name": "message",
                    "parameter_type_id": parameter_type.resource_id,
                }
            ],
        }
    ]
    artifact_tasks = [
        {
            "name": "save_model",
            "output_params": [
                {
                    "name": "model",
                    "parameter_type_id": parameter_type.resource_id,
                }
            ],
        }
    ]

    plugin_repo.add_plugin_tasks(
        function_tasks,
        artifact_tasks,
        plugin_file,
        [parameter_type],
    )
    db_session.commit()

    function_task = next(
        task for task in plugin_file.tasks if task.plugin_task_name == "hello_world"
    )
    artifact_task = next(
        task for task in plugin_file.tasks if task.plugin_task_name == "save_model"
    )

    assert plugin_repo.get_one_task(function_task.task_id) == function_task
    assert plugin_repo.get_one_task(artifact_task.task_id) == artifact_task
    assert len(function_task.input_parameters) == 1
    assert len(function_task.output_parameters) == 1
    assert len(artifact_task.output_parameters) == 1


def test_plugin_get_one_task_missing(plugin_repo):
    with pytest.raises(errors.PluginTaskDoesNotExistError):
        plugin_repo.get_one_task(12345)


# endregion
