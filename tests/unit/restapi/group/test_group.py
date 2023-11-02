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
from dioptra.restapi.user.model import User


@pytest.fixture
def group_service() -> GroupService:
    yield GroupService()


@pytest.fixture
def group_membership_service() -> GroupMembershipService:
    yield GroupMembershipService()


def create_user(db: SQLAlchemy) -> User:
    """Create a user and add them to the database.

    Args:
        db: The SQLAlchemy database session.

    Returns:
        The newly created user object.
    """
    timestamp = datetime.datetime.now()
    user_expire_on = datetime.datetime(9999, 12, 31, 23, 59, 59)
    password_expire_on = timestamp.replace(year=timestamp.year + 1)

    new_user: User = User(
        username="test_admin",
        password="password",
        email_address="test@test.com",
        created_on=timestamp,
        last_modified_on=timestamp,
        last_login_on=timestamp,
        user_expire_on=user_expire_on,
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


def test_create_group(db: SQLAlchemy, group_service: GroupService):
    """Test the creation of a group using the database and group service.

    Args:
        db: The SQLAlchemy database session for testing.
        group_service: The group service responsible for group creation.
    """
    group = create_group(group_service, name="Test Group")

    assert group in group_service.get_all()


def test_delete_group(db: SQLAlchemy, group_service: GroupService):
    """Test the deletion of a group using the database and group service.

    Args:
        db: The SQLAlchemy database session for testing.
        group_service: The group service responsible for group operations.
    """
    group = create_group(group_service, name="Test Group")
    group_service.delete(group.group_id)
    retrieved_group = group_service.get_by_id(group.group_id)

    assert retrieved_group.deleted == True


def test_create_group_membership(
    db: SQLAlchemy,
    group_service: GroupService,
    group_membership_service: GroupMembershipService,
) -> None:
    """Test the creation of a group membership using the database and services.

    Args:
        db: The SQLAlchemy database session for testing.
        group_service: The group service responsible for group operations.
        group_membership_service: The group membership service responsible for group membership operations.
    """  # Create a user

    new_user = create_user(db)

    # Create a group
    group = create_group(group_service, name="Test Group")

    # Create a group membership
    membership = group_membership_service.submit(
        group.group_id,
        new_user.user_id,
        read=True,
        write=True,
        share_read=True,
        share_write=True,
    )

    # Assert that the group membership has been created
    assert membership.group_id == group.group_id
    assert membership.user_id == new_user.user_id
    assert membership.read is True
    assert membership.write is True
    assert membership.share_read is True
    assert membership.share_write is True

    assert new_user in group.users


def test_delete_group_membership(
    db: SQLAlchemy,
    group_service: GroupService,
    group_membership_service: GroupMembershipService,
) -> None:
    """Test the deletion of a group membership using the database and services.

    Args:
        db: The SQLAlchemy database session for testing.
        group_service: The group service responsible for group operations.
        group_membership_service: The group membership service responsible for group membership operations.
    """
    # Create a user

    new_user = create_user(db)

    # Create a group
    group = create_group(group_service, name="Test Group")

    # Create a group membership
    membership = group_membership_service.submit(
        group.group_id,
        new_user.user_id,
        read=True,
        write=True,
        share_read=True,
        share_write=True,
    )

    # get membership from db
    retrieved_membership = group_membership_service.get_by_id(
        group.group_id, new_user.user_id
    )

    # and then delete it
    group_membership_service.delete(
        retrieved_membership.group_id, retrieved_membership.user_id
    )

    assert group_membership_service.get_by_id(group.group_id, new_user.user_id) == None


def test_group_relationship(
    db: SQLAlchemy,
    group_service: GroupService,
    group_membership_service: GroupMembershipService,
) -> None:
    """Test the relationship between groups and group memberships using the database and services.

    Args:
        db: The SQLAlchemy database session for testing.
        group_service: The group service responsible for group operations.
        group_membership_service: The group membership service responsible for group membership operations.
    """
    # Create a user

    new_user = create_user(db)

    # Create a group
    group = create_group(group_service, name="Test Group")

    # Create a group membership
    membership = group_membership_service.submit(
        group.group_id,
        new_user.user_id,
        read=True,
        write=True,
        share_read=True,
        share_write=True,
    )

    # get membership from db
    retrieved_membership = group_membership_service.get_by_id(
        group.group_id, new_user.user_id
    )

    assert retrieved_membership.group == group


def test_user_relationship(
    db: SQLAlchemy,
    group_service: GroupService,
    group_membership_service: GroupMembershipService,
) -> None:
    """Test the relationship between users and group memberships using the database and services.

    Args:
        db: The SQLAlchemy database session for testing.
        group_service: The group service responsible for group operations.
        group_membership_service: The group membership service responsible for group membership operations.
    """
    # Create a user

    new_user = create_user(db)

    # Create a group
    group = create_group(group_service, name="Test Group")

    # Create a group membership
    membership = group_membership_service.submit(
        group.group_id,
        new_user.user_id,
        read=True,
        write=True,
        share_read=True,
        share_write=True,
    )

    # get membership from db
    retrieved_membership = group_membership_service.get_by_id(
        group.group_id, new_user.user_id
    )

    assert retrieved_membership.user == new_user
