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
    V1_ARTIFACTS_ROUTE,
    V1_AUTH_ROUTE,
    V1_ENTRYPOINTS_ROUTE,
    V1_EXPERIMENTS_ROUTE,
    V1_GROUPS_ROUTE,
    V1_JOBS_ROUTE,
    V1_MODELS_ROUTE,
    V1_PLUGIN_PARAMETER_TYPES_ROUTE,
    V1_PLUGINS_ROUTE,
    V1_QUEUES_ROUTE,
    V1_ROOT,
    V1_TAGS_ROUTE,
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


def register_entrypoint(
    client: FlaskClient,
    name: str,
    description: str,
    group_id: int,
    task_graph: str,
    parameters: list[dict[str, Any]],
    plugin_ids: list[int],
    queue_ids: list[int],
) -> TestResponse:
    """Register an entrypoint using the API.

    Args:
        client: The Flask test client.
        name: The name to assign to the new entrypoint.
        description: The description for the new entrypoint.
        group_id: The group to create the new entrypoint in.
        task_graph: A graph of the tasks to perform in a entry point.
        parameters: A list of entrypoint parameters.

    Returns:
        The response from the API.
    """
    payload: dict[str, Any] = {
        "name": name,
        "group": group_id,
        "taskGraph": task_graph,
        "parameters": parameters,
        "plugins": plugin_ids,
        "queues": queue_ids,
    }

    if description:
        payload["description"] = description

    return client.post(
        f"/{V1_ROOT}/{V1_ENTRYPOINTS_ROUTE}/",
        json=payload,
        follow_redirects=True,
    )


def register_experiment(
    client: FlaskClient,
    name: str,
    group_id: int,
    entrypoint_ids: list[int] | None = None,
    description: str | None = None,
) -> TestResponse:
    """Register an experiment using the API.

    Args:
        client: The Flask test client.
        name: The name to assign to the new experiment.
        group_id: The group to create the new experiment in.
        entrypoints: The entrypoint IDs for the new experiment.
        description: The description of the new experiment.

    Returns:
        The response from the API.
    """

    payload = {"name": name, "group": group_id}

    if description is not None:
        payload["description"] = description
    if entrypoint_ids is not None:
        payload["entrypoints"] = entrypoint_ids

    return client.post(
        f"/{V1_ROOT}/{V1_EXPERIMENTS_ROUTE}/",
        json=payload,
        follow_redirects=True,
    )


def register_job(
    client: FlaskClient,
    queue_id: int,
    experiment_id: int,
    entrypoint_id: int,
    values: dict[str, str],
    description: str | None = None,
    timeout: str | None = None,
) -> TestResponse:
    """Register a job using the API.

    Args:
        client:
        queue_id:
        experiment_id:
        entrypoint_id:
        description:
        values:
        timeout:

    Returns:
        The response from the API.
    """
    payload: dict[str, Any] = {
        "queue": queue_id,
        "entrypoint": entrypoint_id,
        "values": values,
    }

    if description:
        payload["description"] = description

    if timeout:
        payload["timeout"] = timeout

    return client.post(
        f"/{V1_ROOT}/{V1_EXPERIMENTS_ROUTE}/{experiment_id}/{V1_JOBS_ROUTE}",
        json=payload,
        follow_redirects=True,
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


def register_tag(
    client: FlaskClient,
    name: str,
    group_id: int,
) -> TestResponse:
    """Register a tag using the API.
    Args:
        client: The Flask test client.
        name: The name to assign to the new tag.
        group_id: The group to create the new tag in.
    Returns:
        The response from the API.
    """

    payload = {"name": name, "group": group_id}

    return client.post(
        f"/{V1_ROOT}/{V1_TAGS_ROUTE}/",
        json=payload,
        follow_redirects=True,
    )


def register_artifact(
    client: FlaskClient,
    uri: int,
    job_id: int,
    group_id: int,
    description: str | None = None,
) -> TestResponse:
    """Register an artifact using the API.

    Args:
        client: The Flask test client.
        uri: The URI of the artifact
        job_id: The job to create the new artifact.
        group_id: The group to create the new artifact in.
        description: The description of the new artifact.

    Returns:
        The response from the API.
    """
    payload = {"uri": uri, "job": job_id, "group": group_id}

    if description is not None:
        payload["description"] = description

    return client.post(
        f"/{V1_ROOT}/{V1_ARTIFACTS_ROUTE}/",
        json=payload,
        follow_redirects=True,
    )


def register_model(
    client: FlaskClient,
    name: str,
    group_id: int,
    description: str | None = None,
) -> TestResponse:
    """Register a model using the API.

    Args:
        client: The Flask test client.
        name: The name to assign to the new model.
        group_id: The group to create the new model in.
        description: The description of the new model.

    Returns:
        The response from the API.
    """
    payload = {"name": name, "group": group_id, "description": description}

    return client.post(
        f"/{V1_ROOT}/{V1_MODELS_ROUTE}/",
        json=payload,
        follow_redirects=True,
    )


def register_model_version(
    client: FlaskClient,
    model_id: int,
    artifact_id: int,
    description: str | None = None,
) -> TestResponse:
    """Register a model version using the API.

    Args:
        client: The Flask test client.
        model_id: The id of the model to create a new version of.
        artifact_id: The id of artifact representing the new model version.
        description: The description of the new model version.

    Returns:
        The response from the API.
    """
    payload = {"artifact": artifact_id, "description": description}

    return client.post(
        f"/{V1_ROOT}/{V1_MODELS_ROUTE}/{model_id}/versions",
        json=payload,
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
    description: str,
    filename: str,
    contents: str,
    tasks: list[dict[str, Any]] | None = None,
) -> TestResponse:
    """Register a plugin file using the API.

    Args:
        client: The Flask test client.
        plugin_id: The plugin resource to create the file in.
        filename: The name of the plugin file.
        contents: The contents of the file containing imports, functions,
            structures, etc.
        tasks: Tasks associated with the plugin file resource.
        description: The description of the plugin file.

    Returns:
        The response from the API.
    """
    payload: dict[str, Any] = {
        "filename": filename,
        "contents": contents,
        "description": description,
        "tasks": tasks or [],
    }

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
    payload = {"name": name, "group": group_id}

    if structure:
        payload["structure"] = structure

    if description:
        payload["description"] = description

    return client.post(
        f"/{V1_ROOT}/{V1_PLUGIN_PARAMETER_TYPES_ROUTE}",
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
    return client.get(f"/{V1_ROOT}/{V1_GROUPS_ROUTE}/1", follow_redirects=True)


def get_model(client: FlaskClient, model_id: int) -> TestResponse:
    response = client.get(
        f"/{V1_ROOT}/{V1_MODELS_ROUTE}/{model_id}",
        follow_redirects=True,
    )
    return response


def get_plugin_parameter_types(client: FlaskClient) -> TestResponse:
    response = client.get(
        f"/{V1_ROOT}/{V1_PLUGIN_PARAMETER_TYPES_ROUTE}",
        follow_redirects=True,
    )
    return response


def get_draft(
    client: FlaskClient,
    resource_route: str,
    resource_id: int,
) -> TestResponse:
    """Get the draft of the resource with the provided unique ID.

    Args:
        client: The Flask test client.
        resource_route: The route of the resource type for the draft.
        resource_id: The id of the queue to rename.

    Returns:
        The response from the API.
    """

    return client.get(f"/{V1_ROOT}/{resource_route}/{resource_id}/draft")


def create_existing_resource_draft(
    client: FlaskClient,
    resource_route: str,
    resource_id: int,
    payload: dict[str, Any],
) -> TestResponse:
    """Create a draft of the resource with the provided unique ID.

    Args:
        client: The Flask test client.
        resource_route: The route of the resource type for the draft.
        resource_id: The id of the resource to create draft of.
        payload: The contents of the draft resource.

    Returns:
        The response from the API.
    """
    return client.post(
        f"/{V1_ROOT}/{resource_route}/{resource_id}/draft",
        json=payload,
        follow_redirects=True,
    )


def modify_existing_resource_draft(
    client: FlaskClient,
    resource_route: str,
    resource_id: int,
    payload: dict[str, Any],
) -> TestResponse:
    """Modify the draft of the resource with the provided unique ID.

    Args:
        client: The Flask test client.
        resource_route: The route of the resource type for the draft.
        resource_id: The id of the resource to modify.
        payload: The new contents of the draft resource.

    Returns:
        The response from the API.
    """
    return client.put(
        f"/{V1_ROOT}/{resource_route}/{resource_id}/draft",
        json=payload,
        follow_redirects=True,
    )


def delete_existing_resource_draft(
    client: FlaskClient,
    resource_route: str,
    resource_id: int,
) -> TestResponse:
    """Delete the draft of the resource with the provided unique ID.

    Args:
        client: The Flask test client.
        resource_route: The route of the resource type for the draft.
        resource_id: The id of the resource draft to delete.

    Returns:
        The response from the API.
    """

    return client.delete(
        f"/{V1_ROOT}/{resource_route}/{resource_id}/draft",
        follow_redirects=True,
    )


def get_drafts(
    client: FlaskClient,
    resource_route: str,
) -> TestResponse:
    """Get a list of drafts for the resource type

    Args:
        client: The Flask test client.
        resource_route: The route of the resource type for the draft.

    Returns:
        The response from the API.
    """

    return client.get(f"/{V1_ROOT}/{resource_route}/drafts")


def create_new_resource_draft(
    client: FlaskClient,
    resource_route: str,
    group_id: int | None,
    payload: dict[str, Any],
) -> TestResponse:
    """Create a draft resource using the API.

    Args:
        client: The Flask test client.
        resource_route: The route of the resource type for the draft.
        payload: The contents of the draft resource.

    Returns:
        The response from the API.
    """
    if group_id is not None:
        payload = {**payload, "group": group_id}

    return client.post(
        f"/{V1_ROOT}/{resource_route}/drafts",
        json=payload,
        follow_redirects=True,
    )


def modify_new_resource_draft(
    client: FlaskClient,
    resource_route: str,
    draft_id: int,
    payload: dict[str, Any],
) -> TestResponse:
    """Modify a draft resource using the API.

    Args:
        client: The Flask test client.
        draft_id: The id of the draft to modify.
        payload: The new contents of the draft resource.

    Returns:
        The response from the API.
    """
    return client.put(
        f"/{V1_ROOT}/{resource_route}/drafts/{draft_id}",
        json=payload,
        follow_redirects=True,
    )


def delete_new_resource_draft(
    client: FlaskClient,
    resource_route: str,
    draft_id: int,
) -> TestResponse:
    """Delete a draft resource using the API.

    Args:
        client: The Flask test client.
        resource_id: The id of the resource to modify.
        draft_id: The id of the draft to modify.

    Returns:
        The response from the API.
    """
    return client.delete(
        f"/{V1_ROOT}/{resource_route}/drafts/{draft_id}",
        follow_redirects=True,
    )


def get_tags(
    client: FlaskClient,
    resource_route: str,
    resource_id: int,
) -> TestResponse:
    """Get a list of tags for the resource type

    Args:
        client: The Flask test client.
        resource_route: The route of the resource type.
        resource_id: The id of the resource to append tags to.

    Returns:
        The response from the API.
    """

    return client.get(
        f"/{V1_ROOT}/{resource_route}/{resource_id}/tags", follow_redirects=True
    )


def append_tags(
    client: FlaskClient,
    resource_route: str,
    resource_id: int,
    tag_ids: list[int],
) -> TestResponse:
    """Append tags to the resource with the provided unique ID.

    Args:
        client: The Flask test client.
        resource_route: The route of the resource type.
        resource_id: The id of the resource to append tags to.
        payload: The contents of the tags resource.

    Returns:
        The response from the API.
    """
    return client.post(
        f"/{V1_ROOT}/{resource_route}/{resource_id}/tags",
        json={"ids": tag_ids},
        follow_redirects=True,
    )


def modify_tags(
    client: FlaskClient,
    resource_route: str,
    resource_id: int,
    tag_ids: list[int],
) -> TestResponse:
    """Modify the tags of the resource with the provided unique ID.

    Args:
        client: The Flask test client.
        resource_route: The route of the resource type.
        resource_id: The id of the resource to modify.
        tag_ids: The new tag_ids for the resource

    Returns:
        The response from the API.
    """
    return client.put(
        f"/{V1_ROOT}/{resource_route}/{resource_id}/tags",
        json={"ids": tag_ids},
        follow_redirects=True,
    )


def remove_tags(
    client: FlaskClient,
    resource_route: str,
    resource_id: int,
) -> TestResponse:
    """Remove the tags of the resource with the provided unique ID.

    Args:
        client: The Flask test client.
        resource_route: The route of the resource type.
        resource_id: The id of the resource to remove tags from.

    Returns:
        The response from the API.
    """

    return client.delete(
        f"/{V1_ROOT}/{resource_route}/{resource_id}/tags",
        follow_redirects=True,
    )


def remove_tag(
    client: FlaskClient,
    resource_route: str,
    resource_id: int,
    tag_id: int,
) -> TestResponse:
    """Remove tag from the resource with the provided unique ID.

    Args:
        client: The Flask test client.
        resource_route: The route of the resource type.
        resource_id: The id of the resource to remove a tag from.
        tag_id: The id of the tag to delete.

    Returns:
        The response from the API.
    """

    return client.delete(
        f"/{V1_ROOT}/{resource_route}/{resource_id}/tags/{tag_id}",
        follow_redirects=True,
    )
