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
from __future__ import annotations

from typing import Any, Callable

from dioptra.restapi.db import models


# -- Ref Types -----------------------------------------------------------------

def build_user_ref(user: models.User) -> dict[str, Any]:
    return {
        "id": user.user_id,
        "username": user.username,
        "url": f"/users/{user.user_id}",
    }

def build_group_ref(group: models.Group) -> dict[str, Any]:
    return {
        "id": group.group_id,
        "name": group.name,
        "url": f"/groups/{group.group_id}",
    }

def build_tag_ref(tag: models.Group) -> dict[str, Any]:
    return {
        "id": tag.tag_id,
        "name": tag.name,
        "url": f"/tags/{tag.tag_id}",
    }


def build_user(user: models.User) -> dict[str, Any]:
    return {
        "id": user.user_id,
        "username": user.username,
        "email": user.email_address,
    }


def build_current_user(user: models.User) -> dict[str, Any]:
    member_of = {x.group.group_id: x.group for x in user.group_memberships}
    manager_of = {x.group.group_id: x.group for x in user.group_managerships}
    groups = {**member_of, **manager_of}.values()

    return {
        "id": user.user_id,
        "username": user.username,
        "email": user.email_address,
        "groups": [build_group_ref(group) for group in groups],
        "created_on": user.created_on,
        "last_modified_on": user.last_modified_on,
        "last_login_on": user.last_login_on,
        "password_expires_on": user.password_expire_on,
    }


def build_group(group: models.Group) -> dict[str, Any]:
    permissions = {
        x.user.user_id: {
            "user": build_user_ref(x.user),
            "group": build_group_ref(x.group),
            "permissions": {
                "read": False,
                "write": False,
                "share_read": False,
                "share_write": False,
                "owner": False,
                "admin": False,
            },
        }
        for x in group.members + group.managers
    }
    for member in group.members:
        permissions[member.user.user_id]["permissions"].update(
            {
                "read": member.read,
                "write": member.write,
                "share_read": member.share_read,
                "share_write": member.share_write,
            }
        )
    for manager in group.manager:
        permissions[manager.user.user_id]["permissions"].update(
            {"owner": manager.owner, "admin": manager.admin}
        )
    return {
        "id": group.group_ud,
        "name": group.name,
        "user": build_user_ref(group.creator),
        "members": list(permissions.values()),
        "created_on": group.created_on,
        "last_modified_on": group.last_modified_on,
    }



# -- Paging --------------------------------------------------------------------

def build_paging_envelope(
    resource_type: str,
    build_fn: Callable[[Any], dict[str, Any]],
    data: list[Any],
    query: str,
    index: int,
    length: int,
    total_num_elements: bool,
):
    has_prev = index > 0
    has_next = total_num_elements > index + length
    is_complete = len(data) == total_num_elements

    paged_data = {
        "index": index,
        "page_langth": length,
        "is_complete": is_complete,
        "first": build_paging_url(resource_type, query, 0, length),
        "data": [build_fn(x) for x in data[:length]],
    }

    if has_prev:
        prev_index = max(index - length, 0)
        prev_url = build_paging_url(resource_type, query, prev_index, length)
        paged_data.update({"prev": prev_url})

    if has_next:
        next_index = index + length
        next_url = build_paging_url(resource_type, query, next_index, length)
        paged_data.update({"next": next_url})

    return paged_data


def build_paging_url(resource_type: str, search: str, index: int, length: int) -> str:
    return f"/{resource_type}/?query={search}&index={index}&pageLength={length}"
