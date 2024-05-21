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
"""Shared utilities for REST API unit tests.

This module contains shared functionality used across test suites for each of the REST
API endpoints.
"""

import datetime
from typing import Any


def is_iso_format(date_string: str) -> bool:
    try:
        datetime.datetime.fromisoformat(date_string)
        return True

    except ValueError:
        return False


def validate_non_ref_feilds(
    expected_keys: set[str],
    response: dict[str, Any], 
    expected_contents: dict[str, Any],
) -> bool:
    try:
        base_resource_keys: set[str] = {
            "id",
            "snapshotId",
            "createdOn",
            "lastModifiedOn",
            "latestSnapshot",
        }
        for key in base_resource_keys:
            assert key in expected_keys
    except ValueError("Base resource keys are missing"):
        return False
    
    try:
        assert isinstance(response["id"], int)
        assert isinstance(response["snapshotId"], int)
        assert isinstance(response["createdOn"], str)
        assert isinstance(response["lastModifiedOn"], str)
        assert isinstance(response["latestSnapshot"], bool)
    except ValueError("Response keys do not match expected keys types"):
        return False
    
    try:
        assert is_iso_format(response["createdOn"])
        assert is_iso_format(response["lastModifiedOn"])
    except ValueError("Required response keys are not in iso format"):
        return False
    
    try:
        if "name" in expected_keys:
            assert isinstance(response["name"], str)
            assert response["name"] == expected_contents["name"]
        if "description" in expected_keys:
            assert isinstance(response["description"], str)
            assert response["description"] == expected_contents["description"]
    except ValueError("Mutable fields keys do not match expected key types or values"):
        return False
    
    return True


def validate_group_ref(
    group_ref: dict[str, Any], expected_contents: dict[str, Any]
) -> bool:
    try:
        assert isinstance(group_ref["id"], int)
        assert isinstance(group_ref["group"]["name"], str)
        assert isinstance(group_ref["group"]["url"], str)
        assert group_ref["id"] == expected_contents["group"]["id"]
        return True
    except ValueError:
        return False


def validate_user_ref(
    user_ref: dict[str, Any], expected_contents: dict[str, Any]
) -> bool:
    try:
        assert isinstance(user_ref["id"], int)
        assert isinstance(user_ref["username"], str)
        assert isinstance(user_ref["url"], str)
        assert user_ref["id"] == expected_contents["user_id"]
        return True
    except ValueError:
        return False


def validate_tag_ref(tags_ref: dict[str, Any]) -> bool:
    try:
        for tag in tags_ref:
            assert isinstance(tag["id"], int)
            assert isinstance(tag["name"], str)
            assert isinstance(tag["url"], str)
        return True
    except ValueError:
        return False
