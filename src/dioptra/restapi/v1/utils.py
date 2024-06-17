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
"""Utility functions to help in building responses from ORM models"""
from typing import Any, Callable, Final
from urllib.parse import urlencode, urlunparse

from dioptra.restapi.db import models
from dioptra.restapi.routes import V1_ROOT

USERS: Final[str] = "users"
GROUPS: Final[str] = "groups"
PLUGIN_PARAMETER_TYPES: Final[str] = "pluginParameterTypes"
QUEUES: Final[str] = "queues"
TAGS: Final[str] = "tags"

# -- Ref Types -----------------------------------------------------------------


def build_user_ref(user: models.User) -> dict[str, Any]:
    """Build a UserRef dictionary.

    Args:
        user: The User object to convert into a UserRef dictionary.

    Returns:
        The UserRef dictionary.
    """
    return {
        "id": user.user_id,
        "username": user.username,
        "url": build_url(f"{USERS}/{user.user_id}"),
    }


def build_group_ref(group: models.Group) -> dict[str, Any]:
    """Build a GroupRef dictionary.

    Args:
        group: The Group object to convert into a GroupRef dictionary.

    Returns:
        The GroupRef dictionary.
    """
    return {
        "id": group.group_id,
        "name": group.name,
        "url": build_url(f"{GROUPS}/{group.group_id}"),
    }


def build_tag_ref(tag: models.Tag) -> dict[str, Any]:
    """Build a TagRef dictionary.

    Args:
        tag: The Tag object to convert into a TagRef dictionary.

    Returns:
        The TagRef dictionary.
    """
    return {
        "id": tag.tag_id,
        "name": tag.name,
        "url": build_url(f"{TAGS}/{tag.tag_id}"),
    }


def build_queue_ref(queue: models.Queue) -> dict[str, Any]:
    """Build a QueueRef dictionary.

    Args:
        queue: The Queue object to convert into a QueueRef dictionary.

    Returns:
        The QueueRef dictionary.
    """
    return {
        "id": queue.queue_id,
        "name": queue.name,
        "url": build_url(f"{QUEUES}/{queue.queue_id}"),
    }


def build_plugin_parameter_type_ref(
    plugin_param_type: models.PluginTaskParameterType,
) -> dict[str, Any]:
    """Build a PluginParameterTypeRef dictionary.

    Args:
        plugin_param_type: The Plugin Parameter Type object to convert into a
            PluginParameterTypeRef dictionary.

    Returns:
        The PluginParameterTypeRef dictionary.
    """
    return {
        "id": plugin_param_type.plugin_parameter_type_id,
        "name": plugin_param_type.name,
        "url": build_url(
            f"{PLUGIN_PARAMETER_TYPES}/{plugin_param_type.plugin_parameter_type_id}"
        ),
    }


# -- Full Types ----------------------------------------------------------------


def build_user(user: models.User) -> dict[str, Any]:
    """Build a User response dictionary.

    Args:
        user: The User object to convert into a User response dictionary.

    Returns:
        The User response dictionary.
    """
    return {
        "id": user.user_id,
        "username": user.username,
        "email": user.email_address,
    }


def build_current_user(user: models.User) -> dict[str, Any]:
    """Build a response dictionary for the current user.

    Args:
        user: The User object representing the current user to convert into a response
            dictionary.

    Returns:
        The response dictionary for the current user.
    """
    return {
        "id": user.user_id,
        "username": user.username,
        "email": user.email_address,
        "groups": [
            build_group_ref(membership.group) for membership in user.group_memberships
        ],
        "created_on": user.created_on,
        "last_modified_on": user.last_modified_on,
        "last_login_on": user.last_login_on,
        "password_expires_on": user.password_expire_on,
    }


def build_group(group: models.Group) -> dict[str, Any]:
    """Build a Group response dictionary.

    Args:
        group: The Group object to convert into a Group response dictionary.

    Returns:
        The Group response dictionary.
    """
    members: dict[int, dict[str, Any]] = {}

    for member in group.members:
        members[member.user_id] = {
            "user": build_user_ref(member.user),
            "group": build_group_ref(group),
            "permissions": {
                "read": member.read,
                "write": member.write,
                "share_read": member.share_read,
                "share_write": member.share_write,
                "owner": False,
                "admin": False,
            },
        }

    for manager in group.managers:
        members[manager.user_id]["permissions"]["owner"] = manager.owner
        members[manager.user_id]["permissions"]["admin"] = manager.admin

    return {
        "id": group.group_id,
        "name": group.name,
        "user": build_user_ref(group.creator),
        "members": list(members.values()),
        "created_on": group.created_on,
        "last_modified_on": group.last_modified_on,
    }


def build_queue(queue: models.Queue) -> dict[str, Any]:
    """Build a Queue response dictionary.

    Args:
        queue: The Queue object to convert into a Queue response dictionary.

    Returns:
        The Queue response dictionary.
    """
    return {
        "id": queue.resource_id,
        "snapshot_id": queue.resource_snapshot_id,
        "name": queue.name,
        "description": queue.description,
        "user": build_user_ref(queue.creator),
        "group": build_group_ref(queue.resource.owner),
        "created_on": queue.created_on,
        "last_modified_on": queue.resource.last_modified_on,
        "latest_snapshot": queue.resource.latest_snapshot_id
        == queue.resource_snapshot_id,
        "tags": [build_tag_ref(tag) for tag in queue.tags],
    }


def build_plugin(plugin: models.Plugin) -> dict[str, Any]:
    return {
        "id": plugin.resource_id,
        "snapshot_id": plugin.resource_snapshot_id,
        "name": plugin.name,
        "description": plugin.description,
        "user": build_user_ref(plugin.creator),
        "group": build_group_ref(plugin.resource.owner),
        "created_on": plugin.created_on,
        "last_modified_on": plugin.resource.last_modified_on,
        "latest_snapshot": plugin.resource.latest_snapshot_id
        == plugin.resource_snapshot_id,
        "tags": [build_tag_ref(tag) for tag in plugin.tags],
        "files": [],
    }


def build_plugin_parameter_type(
    plugin_parameter_type: models.PluginTaskParameterType,
) -> dict[str, Any]:
    """Build a Plugin Parameter Type response dictionary.

    Args:
        plugin_parameter_type: The Plugin Parameter Type object to convert
            into a Plugin Parameter Type response dictionary.

    Returns:
        The Plugin Parameter Type response dictionary.
    """
    return {
        "id": plugin_parameter_type.resource_id,
        "snapshot_id": plugin_parameter_type.resource_snapshot_id,
        "name": plugin_parameter_type.name,
        "structure": plugin_parameter_type.structure,
        "description": plugin_parameter_type.description,
        "user": build_user_ref(plugin_parameter_type.creator),
        "group": build_group_ref(plugin_parameter_type.resource.owner),
        "created_on": plugin_parameter_type.created_on,
        "last_modified_on": plugin_parameter_type.resource.last_modified_on,
        "latest_snapshot": plugin_parameter_type.resource.latest_snapshot_id
        == plugin_parameter_type.resource_snapshot_id,
        "tags": [build_tag_ref(tag) for tag in plugin_parameter_type.tags],
    }


def build_existing_resource_draft(
    draft: models.DraftResource, num_other_drafts: int
) -> dict[str, Any]:
    """Build a Draft response dictionary for a modification of an existing resource.

    Args:
        queue: The Draft object to convert into a Draft response dictionary.

    Returns:
        The Draft response dictionary.
    """
    return {
        "id": draft.draft_resource_id,
        "resource_id": draft.payload["resource_id"],
        "resource_snapshot_id": draft.payload["resource_snapshot_id"],
        "payload": draft.payload["resource_data"],
        "resource_type": draft.resource_type,
        "user": build_user_ref(draft.creator),
        "group": build_group_ref(draft.target_owner),
        "created_on": draft.created_on,
        "last_modified_on": draft.last_modified_on,
        "num_other_drafts": num_other_drafts,
    }


def build_new_resource_draft(draft: models.DraftResource) -> dict[str, Any]:
    """Build a Draft response dictionary for a new resource.

    Args:
        queue: The Draft object to convert into a Draft response dictionary.

    Returns:
        The Draft response dictionary.
    """
    return {
        "id": draft.draft_resource_id,
        "payload": draft.payload["resource_data"],
        "resource_type": draft.resource_type,
        "user": build_user_ref(draft.creator),
        "group": build_group_ref(draft.target_owner),
        "created_on": draft.created_on,
        "last_modified_on": draft.last_modified_on,
    }


# -- Paging --------------------------------------------------------------------


def build_paging_envelope(
    resource_type: str,
    build_fn: Callable[[Any], dict[str, Any]],
    data: list[Any],
    query: str | None,
    index: int,
    length: int,
    total_num_elements: bool,
) -> dict[str, Any]:
    """Build the paging envelope for a response.

    Args:
        resource_type: The type of resource to paginate, forms the URL path in the
            paging url.
        build_fn: The function for converting an ORM object into a response dictionary.
            This dictionary is then wrapped in the paging envelope and set as the "data"
            field.
        data: The list of ORM objects to wrap in the paging envelope.
        query: The optional search query string.
        index: The index of the current page.
        length: The number of results to return per page.
        total_num_elements: The total number of elements in the collection.

    Returns:
        The paging envelope for the response.
    """
    has_prev = index > 0
    has_next = total_num_elements > index + length
    is_complete = not has_next

    paged_data = {
        "index": index,
        "is_complete": is_complete,
        "total_num_results": total_num_elements,
        "first": build_paging_url(resource_type, search=query, index=0, length=length),
        "data": [build_fn(x) for x in data],
    }

    if has_prev:
        prev_index = max(index - length, 0)
        prev_url = build_paging_url(
            resource_type, search=query, index=prev_index, length=length
        )
        paged_data["prev"] = prev_url

    if has_next:
        next_index = index + length
        next_url = build_paging_url(
            resource_type, search=query, index=next_index, length=length
        )
        paged_data["next"] = next_url

    return paged_data


def build_paging_url(
    resource_type: str, search: str | None, index: int, length: int
) -> str:
    """Build a URL for a paged resource endpoint.

    Args:
        resource_type: The type of resource to paginate, forms the URL path.
        search: The optional search query string.
        index: The index of the current page.
        length: The number of results to return per page.

    Returns:
        A quoted URL string for the paged resource endpoint.
    """
    query_params: dict[str, Any] = {"index": index, "pageLength": length}

    if search:
        query_params["search"] = search

    return build_url(resource_type, query_params)


def build_url(resource_type: str, query_params: dict[str, str] | None = None) -> str:
    query_params = query_params or {}

    return urlunparse(
        ("", "", f"/{V1_ROOT}/{resource_type}", "", urlencode(query_params), "")
    )
