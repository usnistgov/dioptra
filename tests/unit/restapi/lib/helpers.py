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


def is_timeout_format(timeout_string: str) -> bool:
    try:
        parsed_timeout_string = timeout_string.split("h")
        assert len(parsed_timeout_string) == 2
        assert parsed_timeout_string[-1] == ""
        assert parsed_timeout_string[0].isnumeric()
        return True

    except ValueError:
        return False


def assert_user_ref_contents_matches_expectations(
    response: dict[str, Any], expected_contents: dict[str, Any]
) -> None:
    assert isinstance(response["user"]["id"], int)
    assert isinstance(response["user"]["username"], str)
    assert isinstance(response["user"]["url"], str)
    assert response["user"]["id"] == expected_contents["user_id"]


def assert_group_ref_contents_matches_expectations(
    response: dict[str, Any], expected_contents: dict[str, Any]
) -> None:
    assert isinstance(response["group"]["id"], int)
    assert isinstance(response["group"]["name"], str)
    assert isinstance(response["group"]["url"], str)
    assert response["group"]["id"] == expected_contents["group_id"]


def assert_tag_ref_contents_matches_expectations(response: dict[str, Any]) -> None:
    for tag in response["tags"]:
        assert isinstance(tag["id"], int)
        assert isinstance(tag["name"], str)
        assert isinstance(tag["url"], str)


def assert_base_resource_ref_contents_matches_expectations(
    resource_type: str,
    response: dict[str, Any],
    expected_contents: dict[str, Any],
) -> None:
    assert isinstance(response[resource_type]["id"], int)
    assert isinstance(response[resource_type]["snapshotId"], int)
    assert isinstance(response[resource_type]["url"], str)
    assert_group_ref_contents_matches_expectations(
        response=response[resource_type], expected_contents=expected_contents
    )


def assert_queue_ref_contents_matches_expectations(
    response: dict[str, Any], expected_contents: dict[str, Any]
) -> None:
    assert isinstance(response["queue"]["name"], str)
    assert_base_resource_ref_contents_matches_expectations(
        resource_type="queue", response=response, expected_contents=expected_contents
    )
    assert response["queue"]["id"] == expected_contents["queue_id"]


def assert_experiment_ref_contents_matches_expectations(
    response: dict[str, Any], expected_contents: dict[str, Any]
) -> None:
    assert isinstance(response["experiment"]["name"], str)
    assert_base_resource_ref_contents_matches_expectations(
        resource_type="experiment",
        response=response,
        expected_contents=expected_contents,
    )
    assert response["experiment"]["id"] == expected_contents["experiment_id"]


def assert_entrypoint_ref_contents_matches_expectations(
    response: dict[str, Any], expected_contents: dict[str, Any]
) -> None:
    assert isinstance(response["entrypoint"]["name"], str)
    assert_base_resource_ref_contents_matches_expectations(
        resource_type="entrypoint",
        response=response,
        expected_contents=expected_contents,
    )
    assert response["entrypoint"]["id"] == expected_contents["entrypoint_id"]
