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
"""Shared actions for REST API unit tests.

This module contains shared actions used across test suites for each of the REST
API endpoints.
"""
from typing import Any
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from dioptra.restapi.routes import (
    V1_AUTH_ROUTE,
    V1_GROUPS_ROUTE,
    V1_PLUGINS_ROUTE,
    V1_QUEUES_ROUTE,
    V1_ROOT,
    V1_USERS_ROUTE,
)


def login(client: FlaskClient, username: str, password: str) -> TestResponse:
    """Login a user using the API.

    Args:
        client: The Flask test client.
        username: The username of the user to be logged in.
        password: The password of the user to be logged in.

    Returns:
        The response from the API.
    """
    return client.post(
        f"/{V1_ROOT}/{V1_AUTH_ROUTE}/login",
        json={"username": username, "password": password},
    )


def register_user(
    client: FlaskClient, username: str, email: str, password: str
) -> TestResponse:
    """Register a user using the API.

    Args:
        client: The Flask test client.
        username: The username to assign to the new user.
        email: The email to assign to the new user.
        password: The password to set for the new user.

    Returns:
        The response from the API.
    """
    return client.post(
        f"/{V1_ROOT}/{V1_USERS_ROUTE}",
        json={
            "username": username,
            "email": email,
            "password": password,
            "confirmPassword": password,
        },
        follow_redirects=True,
    )


def register_plugin(
    client: FlaskClient,
    name: str,
    description: str,
    group_id: int,
) -> TestResponse:
    """Register a plugin using the API.

    Args:
        client: The Flask test client.
        name: The name to assign to the new plugin.
        description: The description of the new plugin.
        group_id: The group to create the new plugin in.

    Returns:
        The response from the API.
    """
    payload = {"name": name, "description": description, "group": group_id}

    return client.post(
        f"/{V1_ROOT}/{V1_PLUGINS_ROUTE}/",
        json=payload,
        follow_redirects=True,
    )


def register_queue(
    client: FlaskClient,
    name: str,
    description: str,
    group_id: int,
) -> TestResponse:
    """Register a queue using the API.

    Args:
        client: The Flask test client.
        name: The name to assign to the new queue.
        group_id: The group to create the new queue in.
        description: The description of the new queue.

    Returns:
        The response from the API.
    """
    payload = {"name": name, "description": description, "group": group_id}

    return client.post(
        f"/{V1_ROOT}/{V1_QUEUES_ROUTE}/",
        json=payload,
        follow_redirects=True,
    )


def register_group(
    client: FlaskClient,
    name: str,
) -> TestResponse:
    """Register a group using the API.

    Args:
        client: The Flask test client.
        name: The name to assign to the new group.

    Returns:
        The response from the API.
    """
    payload: dict[str, Any] = {"name": name}

    return client.post(
        f"/{V1_ROOT}/{V1_GROUPS_ROUTE}/",
        json=payload,
        follow_redirects=True,
    )

def get_public_group(client: FlaskClient) -> TestResponse:
    """Get the public group.

    Args:
        client: The Flask test client.

    Returns:
        The response from the API.
    """
    return client.get(
        f"/{V1_ROOT}/{V1_GROUPS_ROUTE}/1", follow_redirects=True
    )
