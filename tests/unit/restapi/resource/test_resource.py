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
"""Test suite for queue operations.

This module contains a set of tests that validate the CRUD operations and additional
functionalities for the queue entity. The tests ensure that the queues can be
registered, renamed, deleted, and locked/unlocked as expected through the REST API.
"""
from __future__ import annotations

import datetime
from typing import Any

import pytest
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.test import TestResponse

from dioptra.restapi.group.model import Group
from dioptra.restapi.group.service import GroupService
from dioptra.restapi.group_membership.service import GroupMembershipService
from dioptra.restapi.queue.routes import BASE_ROUTE as QUEUE_BASE_ROUTE
from dioptra.restapi.resource.model import DioptraResource
from dioptra.restapi.resource.service import DioptraResourceService
from dioptra.restapi.user.model import User


@pytest.fixture
def group_service() -> GroupService:
    yield GroupService()


@pytest.fixture
def group_membership_service() -> GroupMembershipService:
    yield GroupMembershipService()


@pytest.fixture
def dioptra_resource_service() -> DioptraResourceService:
    yield DioptraResourceService()


def create_user(db: SQLAlchemy) -> User:
    """Create a user and add them to the database.

    Args:
        db: The SQLAlchemy database session.

    Returns:
        The newly created user object.
    """
    timestamp = datetime.datetime.now()
    password_expire_on = timestamp.replace(year=timestamp.year + 1)

    new_user: User = User(
        username="test_admin",
        password="password",
        email_address="test@test.com",
        created_on=timestamp,
        last_modified_on=timestamp,
        last_login_on=timestamp,
        password_expire_on=password_expire_on,
    )
    db.session.add(new_user)
    db.session.commit()
    return new_user


def create_group(group_service: GroupService, name: str = "test") -> Group:
    """Create a group using the group service.

    Args:
        group_service: The group service responsible for group creation.
        name: The name to assign to the new group (default is "test").

    Returns:
        The response from the group service representing the newly created group.
    """
    return group_service.submit(name)


def create_resource(
    dioptra_resource_service: DioptraResourceService, creator_id: int, owner_id: int
) -> DioptraResource:
    """Create a resource using the DioptraResourceService.

    Args:
        dioptra_resource_service: The DioptraResource service responsible for resource creation.
        creator_id: The id of the user who created the resource.
        owner_id: The id of the group that owns the resource.

    Returns:
        The response from the DioptraResource service representing the newly created resource.
    """
    return dioptra_resource_service.create(creator_id, owner_id)


def test_create_dioptra_resource(
    db: SQLAlchemy,
    dioptra_resource_service: DioptraResourceService,
    group_service: GroupService,
):
    """Test the creation of a DioptraResource using the database and DioptraResource service.

    Args:
        db: The SQLAlchemy database session for testing.
        dioptra_resource_service: The DioptraResource service responsible for resource creation.
    """
    # Create a user
    new_user = create_user(db)

    # Create a group
    group = create_group(group_service, name="Test Group")

    # Create a DioptraResource
    resource = create_resource(
        dioptra_resource_service, creator_id=new_user.user_id, owner_id=group.group_id
    )

    assert resource in dioptra_resource_service.get_all()


def test_delete_dioptra_resource(
    db: SQLAlchemy,
    dioptra_resource_service: DioptraResourceService,
    group_service: GroupService,
):
    """Test the deletion of a DioptraResource using the database and DioptraResource service.

    Args:
        db: The SQLAlchemy database session for testing.
        dioptra_resource_service: The DioptraResource service responsible for resource operations.
    """
    # Create a user
    new_user = create_user(db)

    # Create a group
    group = create_group(group_service, name="Test Group")

    # Create a DioptraResource
    resource = create_resource(
        dioptra_resource_service, creator_id=new_user.user_id, owner_id=group.group_id
    )

    dioptra_resource_service.delete(resource.resource_id)
    retrieved_resource = dioptra_resource_service.get(resource.resource_id)

    assert retrieved_resource.is_deleted is True


def test_user_dioptra_resource_relationship(
    db: SQLAlchemy,
    dioptra_resource_service: DioptraResourceService,
    group_service: GroupService,
):
    """Test the relationship between users and DioptraResources using the database and service.

    Args:
        db: The SQLAlchemy database session for testing.
        dioptra_resource_service: The DioptraResource service responsible for resource operations.
    """
    # Create a user
    new_user = create_user(db)

    # Create a group
    group = create_group(group_service, name="Test Group")

    # Create a DioptraResource
    resource = create_resource(
        dioptra_resource_service, creator_id=new_user.user_id, owner_id=group.group_id
    )

    retrieved_resource = dioptra_resource_service.get(resource.resource_id)

    assert retrieved_resource.creator == new_user


def test_group_dioptra_resource_relationship(
    db: SQLAlchemy,
    dioptra_resource_service: DioptraResourceService,
    group_service: GroupService,
):
    """Test the relationship between groups and DioptraResources using the database and service.

    Args:
        db: The SQLAlchemy database session for testing.
        dioptra_resource_service: The DioptraResource service responsible for resource operations.
    """
    # Create a user
    new_user = create_user(db)

    # Create a group
    group = create_group(group_service, name="Test Group")

    # Create a DioptraResource
    resource = create_resource(
        dioptra_resource_service, creator_id=new_user.user_id, owner_id=group.group_id
    )

    retrieved_resource = dioptra_resource_service.get(resource.resource_id)

    assert retrieved_resource.owner == group
