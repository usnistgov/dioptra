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
"""Shared assertions for REST API unit tests."""
from http import HTTPStatus
from typing import Any

from dioptra.client.drafts import (
    ModifyResourceDraftsSubCollectionClient,
    NewResourceDraftsSubCollectionClient,
)

from dioptra.client.snapshots import SnapshotsSubCollectionClient

from . import helpers

def assert_base_resource_contents_match_expectations(response: dict[str, Any]) -> None:
    assert isinstance(response["id"], int)
    assert isinstance(response["snapshot"], int)
    assert isinstance(response["createdOn"], str)
    assert isinstance(response["snapshotCreatedOn"], str)
    assert isinstance(response["lastModifiedOn"], str)
    assert isinstance(response["latestSnapshot"], bool)
    assert isinstance(response["hasDraft"], bool)

    assert helpers.is_iso_format(response["createdOn"])
    assert helpers.is_iso_format(response["snapshotCreatedOn"])
    assert helpers.is_iso_format(response["lastModifiedOn"])


def assert_resource_contents_match_expectations(
    response: dict[str, Any], expected: dict[str, Any]
) -> None:
    for key, value in expected.items():
        assert key in response
        if isinstance(value, (int, float, bool, str)):
            assert response[key] == value


def assert_user_ref_contents_matches_expectations(
    user: dict[str, Any], expected_user_id: int
) -> None:
    assert isinstance(user["id"], int)
    assert isinstance(user["username"], str)
    assert isinstance(user["url"], str)
    assert user["id"] == expected_user_id


def assert_group_ref_contents_matches_expectations(
    group: dict[str, Any], expected_group_id: int
) -> None:
    assert isinstance(group["id"], int)
    assert isinstance(group["name"], str)
    assert isinstance(group["url"], str)
    assert group["id"] == expected_group_id


def assert_tag_ref_contents_matches_expectations(tags: list[dict[str, Any]]) -> None:
    for tag in tags:
        assert isinstance(tag["id"], int)
        assert isinstance(tag["name"], str)
        assert isinstance(tag["url"], str)


def assert_base_resource_ref_contents_matches_expectations(
    resource: dict[str, Any], expected_group_id: int
) -> None:
    assert isinstance(resource["snapshotId"], int)
    assert isinstance(resource["url"], str)
    assert_group_ref_contents_matches_expectations(
        group=resource["group"], expected_group_id=expected_group_id
    )


def assert_queue_ref_contents_matches_expectations(
    queue: dict[str, Any],
    expected_queue_id: int,
    expected_queue_snapshot_id: int,
    expected_group_id: int,
) -> None:
    assert isinstance(queue["name"], str)
    assert_base_resource_ref_contents_matches_expectations(
        resource=queue, expected_group_id=expected_group_id
    )
    assert queue["id"] == expected_queue_id
    assert queue["snapshotId"] == expected_queue_snapshot_id


def assert_experiment_ref_contents_matches_expectations(
    experiment: dict[str, Any],
    expected_experiment_id: int,
    expected_experiment_snapshot_id: int,
    expected_group_id: int,
) -> None:
    assert isinstance(experiment["name"], str)
    assert_base_resource_ref_contents_matches_expectations(
        resource=experiment, expected_group_id=expected_group_id
    )
    assert experiment["id"] == expected_experiment_id
    assert experiment["snapshotId"] == expected_experiment_snapshot_id


def assert_entrypoint_ref_contents_matches_expectations(
    entrypoint: dict[str, Any],
    expected_entrypoint_id: int,
    expected_entrypoint_snapshot_id: int,
    expected_group_id: int,
) -> None:
    assert isinstance(entrypoint["name"], str)
    assert_base_resource_ref_contents_matches_expectations(
        resource=entrypoint, expected_group_id=expected_group_id
    )
    assert entrypoint["id"] == expected_entrypoint_id
    assert entrypoint["snapshotId"] == expected_entrypoint_snapshot_id


def assert_draft_response_contents_matches_expectations(
    response: dict[str, Any],
    expected_contents: dict[str, Any],
) -> None:
    """Assert that draft response contents is valid and matches the expected values.

    Args:
        response: The actual response from the API.
        expected_contents: The expected response from the API.

    Raises:
        AssertionError: If the API response does not match the expected response
            or if the response contents is not valid.
    """
    expected_keys = {
        "id",
        "group",
        "user",
        "createdOn",
        "lastModifiedOn",
        "resourceType",
        "payload",
        "resource",
        "resourceSnapshot",
        "metadata",
    }
    assert set(response.keys()) == expected_keys

    # Validate the non-Ref fields
    assert isinstance(response["id"], int)
    assert isinstance(response["createdOn"], str)
    assert isinstance(response["lastModifiedOn"], str)

    assert isinstance(response["resource"], int | None)
    assert isinstance(response["resourceSnapshot"], int | None)
    assert isinstance(response["metadata"], dict)
    assert response["resource"] == expected_contents.get("resource_id", None)
    assert response["resourceSnapshot"] == expected_contents.get(
        "resource_snapshot_id", None
    )

    assert helpers.is_iso_format(response["createdOn"])
    assert helpers.is_iso_format(response["lastModifiedOn"])

    # Validate the UserRef structure
    assert isinstance(response["user"]["id"], int)
    assert isinstance(response["user"]["username"], str)
    assert isinstance(response["user"]["url"], str)
    assert response["user"]["id"] == expected_contents["user_id"]

    # Validate the GroupRef structure
    assert isinstance(response["group"]["id"], int)
    assert isinstance(response["group"]["name"], str)
    assert isinstance(response["group"]["url"], str)
    assert response["group"]["id"] == expected_contents["group_id"]

    assert response["payload"] == expected_contents["payload"]


def assert_tags_response_contents_matches_expectations(
    response: list[dict[str, Any]],
    expected_contents: list[int],
) -> None:
    """Assert that tags response contents is valid and matches the expected values.

    Args:
        response: The actual response from the API.
        expected_contents: The expected list of Tag IDs the API.

    Raises:
        AssertionError: If the API response does not match the expected response
            or if the response contents is not valid.
    """

    # Validate the TagRef structure
    for tag in response:
        assert isinstance(tag["id"], int)
        assert isinstance(tag["name"], str)
        assert isinstance(tag["url"], str)

    assert [tag["id"] for tag in response] == expected_contents


def assert_retrieving_draft_by_resource_id_works(
    drafts_client: ModifyResourceDraftsSubCollectionClient,
    *resource_ids: str | int,
    expected: dict[str, Any],
) -> None:
    """Assert that retrieving an existing resource draft by resource id works.

    Args:
        drafts_client: The DraftsSubEndpointClient client.
        resource_id: The id of the resource to retrieve the draft for.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = drafts_client.get_by_id(*resource_ids)
    assert (
        response.status_code == HTTPStatus.OK
        and helpers.convert_response_to_dict(response) == expected
    )


def assert_retrieving_draft_by_id_works(
    drafts_client: NewResourceDraftsSubCollectionClient,
    *resource_ids: str | int,
    draft_id: int,
    expected: dict[str, Any],
) -> None:
    """Assert that retrieving a draft by id works.

    Args:
        drafts_client: The DraftsSubEndpointClient client.
        draft_id: The id of the draft to retrieve.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = drafts_client.get_by_id(*resource_ids, draft_id=draft_id)
    assert (
        response.status_code == HTTPStatus.OK
        and helpers.convert_response_to_dict(response) == expected
    )


def assert_retrieving_drafts_works(
    drafts_client: NewResourceDraftsSubCollectionClient,
    *resource_ids: str | int,
    expected: list[dict[str, Any]],
    group_id: int | None = None,
    paging_info: dict[str, Any] | None = None,
) -> None:
    """Assert that retrieving all drafts for a resource type works.

    Args:
        drafts_client: The DraftsSubEndpointClient client.
        expected: The expected response from the API.
        group_id: The group ID used in query parameters.
        paging_info: The paging information used in query parameters.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """

    query_string: dict[str, Any] = {}

    if group_id is not None:
        query_string["group_id"] = group_id

    if paging_info is not None:
        query_string["index"] = paging_info["index"]
        query_string["page_length"] = paging_info["page_length"]

    response = drafts_client.get(*resource_ids, **query_string)
    assert (
        response.status_code == HTTPStatus.OK
        and helpers.convert_response_to_dict(response)["data"] == expected
    )


def assert_creating_another_existing_draft_fails(
    drafts_client: ModifyResourceDraftsSubCollectionClient,
    *resource_ids: str | int,
    payload: dict[str, Any],
) -> None:
    """Assert that registering another draft for the same resource fails

    Args:
        drafts_client: The DraftsSubEndpointClient client.
        resource_id: The id of the resource to retrieve the draft for.
        payload: A dictionary containing the draft fields.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = drafts_client.create(*resource_ids, **payload)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def assert_existing_draft_is_not_found(
    drafts_client: ModifyResourceDraftsSubCollectionClient,
    *resource_ids: str | int,
) -> None:
    """Assert that a draft of an existing resource is not found.

    Args:
        drafts_client: The DraftsSubEndpointClient client.
        resource_id: The id of the resource to retrieve the draft for.

    Raises:
        AssertionError: If the response status code is not 404.
    """
    response = drafts_client.get_by_id(*resource_ids)
    assert response.status_code == HTTPStatus.NOT_FOUND


def assert_new_draft_is_not_found(
    drafts_client: NewResourceDraftsSubCollectionClient,
    *resource_ids: str | int,
    draft_id: int,
) -> None:
    """Assert that a draft of an existing resource is not found.

    Args:
        drafts_client: The DraftsSubEndpointClient client.
        resource_id: The id of the resource to retrieve the draft for.

    Raises:
        AssertionError: If the response status code is not 404.
    """
    response = drafts_client.get_by_id(*resource_ids, draft_id=draft_id)
    assert response.status_code == HTTPStatus.NOT_FOUND


def assert_retrieving_snapshots_works(
    snapshots_client: SnapshotsSubCollectionClient,
    *resource_ids: str | int,
    expected: list[dict[str, Any]],
) -> None:
    """Assert that retrieving a snapshot by id works.

    Args:
        snapshots_client: The SnapshotsSubCollectionClient client.
        resource_id: The id of the resource to retrieve snapshots for.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = snapshots_client.get(*resource_ids)
    assert (
        response.status_code == HTTPStatus.OK
        and helpers.convert_response_to_dict(response)["data"] == expected
    )


def assert_retrieving_snapshot_by_id_works(
    snapshots_client: SnapshotsSubCollectionClient,
    *resource_ids: str | int,
    snapshot_id: int,
    expected: dict[str, Any],
) -> None:
    """Assert that retrieving a resource snapshot by id works.

    Args:
        snapshots_client: The SnapshotsSubCollectionClient client.
        resource_id: The id of the resource to retrieve a snapshot of.
        snapshot_id: The id to the snapshot to retrieve.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = snapshots_client.get_by_id(*resource_ids, snapshot_id=snapshot_id)
    assert (
        response.status_code == HTTPStatus.OK
        and helpers.convert_response_to_dict(response) == expected
    )
