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
    ExistingResourceDraftsSubCollectionClient,
    NewResourceDraftsSubCollectionClient,
)
from dioptra.client.snapshots import SnapshotsSubCollectionClient


def assert_retrieving_draft_by_resource_id_works(
    drafts_client: ExistingResourceDraftsSubCollectionClient,
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
    assert response.status_code == HTTPStatus.OK and response.json() == expected


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
    assert response.status_code == HTTPStatus.OK and response.json() == expected


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
    assert response.status_code == HTTPStatus.OK and response.json()["data"] == expected


def assert_creating_another_existing_draft_fails(
    drafts_client: ExistingResourceDraftsSubCollectionClient,
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
    response = drafts_client.create(
        *resource_ids, **payload
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def assert_existing_draft_is_not_found(
    drafts_client: ExistingResourceDraftsSubCollectionClient,
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
    *resource_ids: int,
    expected: dict[str, Any],
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
    assert response.status_code == HTTPStatus.OK and response.json()["data"] == expected


def assert_retrieving_snapshot_by_id_works(
    snapshots_client: SnapshotsSubCollectionClient,
    *resource_ids: int,
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
    assert response.status_code == HTTPStatus.OK and response.json() == expected
