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
    V1_PLUGIN_PARAMETER_TYPES_ROUTE,
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


def register_plugin_file(
    client: FlaskClient,
    plugin_id: int,
    group_id: int,
    filename: str,
    contents: str,
    description: str | None = None,  
) -> TestResponse:
    """Register a plugin file using the API.

    Args:
        client: The Flask test client.
        group_id: The group that owns the plugin.
        plugin_id: The plugin resource to create the file in.
        filename: The name of the plugin file.
        contents: The contents of the file containing imports, 
          functions, structures, etc.
        tasks: Tasks associated with the plugin file resource.
        description: The description of the plugin file.

    Returns:
        The response from the API.
    """
    payload: dict[str, Any] = {
        "group_id": group_id,
        "filename": filename,
        "contents": contents,
    }

    if description is not None:
        payload["description"] = description

    return client.post(
        f"/{V1_ROOT}/{V1_PLUGINS_ROUTE}/{plugin_id}/files",
        json=payload,
        follow_redirects=True,
    )


def register_plugin_parameter_type(
    client: FlaskClient,
    name: str,
    group_id: int,
    structure: dict[str, Any] | None = None,
    description: str | None = None,
) -> TestResponse:
    """Create a Plugin Parameter Type using the API.

    Args:
        client: The Flask test client.
        name: The name of the plugin parameter type to be created.
        group_id: The group to create the new plugin parameter type in.
        structure: Optional JSON-type field for further constraining a type's structure.

    Returns:
        The response from the API.
    """
    payload = {"name": name, "group_id": group_id}

    if structure:
        payload["structure"] = structure
        
    if description:
        payload["description"] = description

    return client.post(
        f"/{V1_ROOT}/{V1_PLUGIN_PARAMETER_TYPES_ROUTE}",
        json=payload,
        follow_redirects=True,
    )


def register_plugin_task(
    client: FlaskClient,
    plugin_id: int,
    plugin_file_id: int,
    name: str,
    parameter_type_id: int,
) -> TestResponse:
    """Register a plugin task using the API.

    Args:
        client: The Flask test client.
        plugin_id: The plugin ID with a file.
        plugin_file_id: The plugin file ID to append the task.
        name: The name of the plugin task.
        parameter_type_id: The ID of the parameter type.
    Returns:
        The response from the API.
    """
    payload: dict[str, Any] = {
        "name": name,
        "parameter_type_id": parameter_type_id,
    }

    return client.post(
        f"/{V1_ROOT}/{V1_PLUGINS_ROUTE}/{plugin_id}/files/{plugin_file_id}/tasks",
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
