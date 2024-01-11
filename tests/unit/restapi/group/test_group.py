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
from dioptra.restapi.group_membership.model import GroupMembership
from dioptra.restapi.group_membership.service import GroupMembershipService
from dioptra.restapi.queue.routes import BASE_ROUTE as QUEUE_BASE_ROUTE
from dioptra.restapi.user.model import User


@pytest.fixture
def group_service() -> GroupService:
    yield GroupService()


@pytest.fixture
def group_membership_service() -> GroupMembershipService:
    yield GroupMembershipService()


###### helpers


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
    return group_service.create(name)


def get_group(id: int, group_service: GroupService) -> Group | None:
    """Retrieve a group by its unique identifier.

    Args:
        id: The unique identifier of the group.
        group_service: The service responsible for handling group-related operations.

    Returns:
        The retrieved Group object.

    Raises:
        GroupDoesNotExistError: If no group with the specified ID is found.
    """
    return group_service.get(id)


def delete_group(id: int, group_service: GroupService) -> dict[str, Any]:
    """Delete a group by its unique identifier.

    Args:
        id: The unique identifier of the group.
        group_service: The service responsible for handling group operations.

    Returns:
        A dictionary reporting the status of the request.

    Raises:
        GroupDoesNotExistError: If the group with the specified ID does not exist.
    """
    return group_service.delete(id)


def create_group_membership(
    group_id: int,
    user_id: int,
    read: bool,
    write: bool,
    share_read: bool,
    share_write: bool,
    group_membership_service: GroupMembershipService,
) -> GroupMembershipService | None:
    """Create a group membership.

    Args:
        group_id: The unique identifier of the group.
        user_id: The unique identifier of the user.
        read: Whether the user has read permissions.
        write: Whether the user has write permissions.
        share_read: Whether the user has share-read permissions.
        share_write: Whether the user has share-write permissions.
        group_membership_service: The service responsible for handling group memberships.

    Returns:
        The created GroupMembership object representing the group membership.

    Raises:
        GroupMembershipSubmissionError: If there is an issue with the submission.
    """
    return group_membership_service.create(
        group_id,
        user_id,
        read=read,
        write=write,
        share_read=share_read,
        share_write=share_write,
    )


def get_group_membership(
    user_id: int, group_id: int, group_membership_service: GroupMembershipService
) -> GroupMembership | None:
    """Retrieve a group membership for a user in a specific group.

    Args:
        user_id: The unique identifier of the user.
        group_id: The unique identifier of the group.
        group_membership_service: The service responsible for handling group membership operations.

    Returns:
        The retrieved GroupMembership object if found, otherwise None.

    Raises:
        GroupMembershipDoesNotExistError: If no group membership with the specified user and group IDs is found.
    """
    return group_membership_service.get(group_id, user_id)


def delete_group_membership(
    group_id: int, user_id: int, group_membership_service: Any
) -> dict[str, Any]:
    """Delete a group membership.

    Args:
        group_id: The unique identifier of the group.
        user_id: The unique identifier of the user.
        group_membership_service: The service responsible for group membership operations.

    Returns:
        A dictionary reporting the status of the request.
    """
    return group_membership_service.delete(group_id, user_id)


##### asserts


def assert_group_membership_created(membership: Any, group: Any, new_user: Any) -> None:
    """Assert that the group membership has been created.

    Args:
        membership: The created group membership object.
        group: The group to which the user is added.
        new_user: The user added to the group.
    """
    assert membership.group_id == group.group_id
    assert membership.user_id == new_user.user_id
    assert membership.read is True
    assert membership.write is True
    assert membership.share_read is True
    assert membership.share_write is True

    assert new_user in group.users


def assert_group_membership_does_not_exist(
    membership: Any, group: Any, new_user: Any
) -> None:
    """Assert that the group membership has not been created.

    Args:
        membership: The created group membership object (should be None).
        group: The group to which the user should not be added.
        new_user: The user that should not be added to the group.
    """
    assert membership is None


def assert_membership_group(
    retrieved_membership: GroupMembership,
    group: Group,
) -> None:
    """Assert that the group in the retrieved membership matches the expected group.

    Args:
        retrieved_membership: The retrieved membership object.
        group: The expected group object.

    Raises:
        AssertionError: If the groups do not match.
    """
    assert retrieved_membership.group == group


def assert_group_in_list(
    group: Group,
    group_service: GroupService,
) -> None:
    """Assert that the group is in the list of all groups retrieved from the service.

    Args:
        group: The group object to check.
        group_service: The group service.

    Raises:
        AssertionError: If the group is not found in the list.
    """
    assert group in group_service.get_all()


def assert_group_is_none(retrieved_group: Group | None) -> None:
    """Assert that the retrieved group is None.

    Args:
        retrieved_group: The retrieved group object.

    Raises:
        AssertionError: If the retrieved group is not None.
    """
    assert retrieved_group is None


def assert_membership_user_equals(
    retrieved_membership: GroupMembership, new_user: User
) -> None:
    """Assert that the user in the retrieved membership equals the new user.

    Args:
        retrieved_membership: The retrieved group membership object.
        new_user: The new user object.

    Raises:
        AssertionError: If the user in the retrieved membership does not equal the new user.
    """
    assert retrieved_membership.user == new_user


###### tests


def test_create_group(db: SQLAlchemy, group_service: GroupService):
    """Test the creation of a group using the database and group service.

    Args:
        db: The SQLAlchemy database session for testing.
        group_service: The group service responsible for group creation.
    """
    group = create_group(group_service, name="Test Group")

    assert_group_in_list(group, group_service)


def test_delete_group(db: SQLAlchemy, group_service: GroupService):
    """Test the deletion of a group using the database and group service.

    Args:
        db: The SQLAlchemy database session for testing.
        group_service: The group service responsible for group operations.
    """
    group = create_group(group_service, name="Test Group")
    delete_group(group.group_id, group_service)
    retrieved_group = get_group(group.group_id, group_service)

    assert_group_is_none(retrieved_group)


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
    membership = create_group_membership(
        group.group_id,
        new_user.user_id,
        read=True,
        write=True,
        share_read=True,
        share_write=True,
        group_membership_service=group_membership_service,
    )

    assert_group_membership_created(membership, group, new_user)


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
    membership = create_group_membership(
        group.group_id,
        new_user.user_id,
        read=True,
        write=True,
        share_read=True,
        share_write=True,
        group_membership_service=group_membership_service,
    )

    # get membership from db
    retrieved_membership = get_group_membership(
        group.group_id, new_user.user_id, group_membership_service
    )

    # and then delete it
    delete_group_membership(
        retrieved_membership.group_id,
        retrieved_membership.user_id,
        group_membership_service,
    )

    # get membership from db
    retrieved_membership = get_group_membership(
        group.group_id, new_user.user_id, group_membership_service
    )

    assert_group_membership_does_not_exist(retrieved_membership, group, new_user)


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
    membership = create_group_membership(
        group.group_id,
        new_user.user_id,
        read=True,
        write=True,
        share_read=True,
        share_write=True,
        group_membership_service=group_membership_service,
    )

    # get membership from db
    retrieved_membership = get_group_membership(
        group.group_id, new_user.user_id, group_membership_service
    )

    assert_membership_group(retrieved_membership, group)


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
    membership = create_group_membership(
        group.group_id,
        new_user.user_id,
        read=True,
        write=True,
        share_read=True,
        share_write=True,
        group_membership_service=group_membership_service,
    )

    # get membership from db
    retrieved_membership = get_group_membership(
        group.group_id, new_user.user_id, group_membership_service
    )

    assert_membership_user_equals(retrieved_membership, new_user)
