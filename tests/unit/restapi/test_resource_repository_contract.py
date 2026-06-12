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
from sqlalchemy.orm.session import Session as DBSession

import dioptra.restapi.db.repository.utils as utils
import dioptra.restapi.errors as errors
from tests.unit.restapi.lib.repository_contracts import (
    RESOURCE_REPOSITORY_CASES,
    ResourceRepositoryCase,
)


@pytest.fixture(params=RESOURCE_REPOSITORY_CASES, ids=lambda case: case.id)
def repository_case(request) -> ResourceRepositoryCase:
    return request.param


def test_create_persists_initial_snapshot(
    request,
    repository_case: ResourceRepositoryCase,
    account,
    fake_data,
    db_session: DBSession,
):
    repo = request.getfixturevalue(repository_case.repo_fixture)
    snapshot = repository_case.make_initial_snapshot(account, fake_data, db_session)

    repo.create(snapshot)
    db_session.commit()

    persisted = db_session.get(
        repository_case.snapshot_class, snapshot.resource_snapshot_id
    )
    assert persisted == snapshot


def test_create_snapshot_becomes_latest(
    request,
    repository_case: ResourceRepositoryCase,
    account,
    fake_data,
    db_session: DBSession,
):
    repo = request.getfixturevalue(repository_case.repo_fixture)
    snapshot = repository_case.make_initial_snapshot(account, fake_data, db_session)
    repo.create(snapshot)
    db_session.commit()

    next_snapshot = repository_case.make_next_snapshot(snapshot)
    repo.create_snapshot(next_snapshot)
    db_session.commit()

    latest = repo.get_one(snapshot.resource_id, utils.DeletionPolicy.NOT_DELETED)
    assert latest == next_snapshot


def test_get_returns_latest_snapshot(
    request,
    repository_case: ResourceRepositoryCase,
    account,
    fake_data,
    db_session: DBSession,
):
    repo = request.getfixturevalue(repository_case.repo_fixture)
    snapshot = repository_case.make_initial_snapshot(account, fake_data, db_session)
    repo.create(snapshot)
    db_session.commit()

    next_snapshot = repository_case.make_next_snapshot(snapshot)
    repo.create_snapshot(next_snapshot)
    db_session.commit()

    latest = repo.get(snapshot.resource_id, utils.DeletionPolicy.NOT_DELETED)
    assert latest == next_snapshot


def test_get_one_returns_latest_snapshot(
    request,
    repository_case: ResourceRepositoryCase,
    account,
    fake_data,
    db_session: DBSession,
):
    repo = request.getfixturevalue(repository_case.repo_fixture)
    snapshot = repository_case.make_initial_snapshot(account, fake_data, db_session)
    repo.create(snapshot)
    db_session.commit()

    next_snapshot = repository_case.make_next_snapshot(snapshot)
    repo.create_snapshot(next_snapshot)
    db_session.commit()

    latest = repo.get_one(snapshot.resource_id, utils.DeletionPolicy.NOT_DELETED)
    assert latest == next_snapshot


def test_delete_marks_resource_deleted(
    request,
    repository_case: ResourceRepositoryCase,
    account,
    fake_data,
    db_session: DBSession,
):
    repo = request.getfixturevalue(repository_case.repo_fixture)
    snapshot = repository_case.make_initial_snapshot(account, fake_data, db_session)
    repo.create(snapshot)
    db_session.commit()

    repo.delete(snapshot.resource_id)
    db_session.commit()

    assert repo.get(snapshot.resource_id, utils.DeletionPolicy.NOT_DELETED) is None
    assert repo.get_one(snapshot.resource_id, utils.DeletionPolicy.DELETED) == snapshot


def test_get_by_name_returns_latest_snapshot(
    request,
    repository_case: ResourceRepositoryCase,
    account,
    fake_data,
    db_session: DBSession,
):
    repo = request.getfixturevalue(repository_case.repo_fixture)
    snapshot = repository_case.make_initial_snapshot(account, fake_data, db_session)
    repo.create(snapshot)
    db_session.commit()

    next_snapshot = repository_case.make_next_snapshot(snapshot)
    repo.create_snapshot(next_snapshot)
    db_session.commit()

    result = repo.get_by_name(
        next_snapshot.name,
        account.group,
        utils.DeletionPolicy.NOT_DELETED,
    )
    assert result == next_snapshot


def test_create_rejects_wrong_resource_type(
    request,
    repository_case: ResourceRepositoryCase,
    account,
    fake_data,
    db_session: DBSession,
):
    repo = request.getfixturevalue(repository_case.repo_fixture)
    snapshot = repository_case.make_wrong_resource_type_snapshot(
        account, fake_data, db_session
    )

    with pytest.raises(errors.MismatchedResourceTypeError):
        repo.create(snapshot)
