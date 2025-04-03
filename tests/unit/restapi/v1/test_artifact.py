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
"""Test suite for model operations.

This module contains a set of tests that validate the CRUD operations and additional
functionalities for the model entity. The tests ensure that the models can be
registered, renamed, deleted, and locked/unlocked as expected through the REST API.
"""
from http import HTTPStatus
from typing import Any

import pytest
from flask_sqlalchemy import SQLAlchemy

from dioptra.client.base import DioptraResponseProtocol
from dioptra.client.client import DioptraClient

from ..lib import helpers
from ..test_utils import assert_retrieving_resource_works

# -- Assertions ------------------------------------------------------------------------


def assert_artifact_response_contents_matches_expectations(
    response: dict[str, Any],
    expected_contents: dict[str, Any],
) -> None:
    """Assert that artifact response contents is valid.

    Args:
        response: The actual response from the API.
        expected_contents: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response or if the response contents is not
            valid.
    """
    expected_keys = {
        "id",
        "snapshot",
        "group",
        "user",
        "createdOn",
        "snapshotCreatedOn",
        "lastModifiedOn",
        "latestSnapshot",
        "hasDraft",
        "uri",
        "description",
        "tags",
    }
    assert set(response.keys()) == expected_keys

    # Validate the non-Ref fields
    assert isinstance(response["id"], int)
    assert isinstance(response["snapshot"], int)
    assert isinstance(response["uri"], str)
    assert isinstance(response["description"], str)
    assert isinstance(response["createdOn"], str)
    assert isinstance(response["snapshotCreatedOn"], str)
    assert isinstance(response["lastModifiedOn"], str)
    assert isinstance(response["latestSnapshot"], bool)
    assert isinstance(response["hasDraft"], bool)

    assert response["uri"] == expected_contents["uri"]
    assert response["description"] == expected_contents["description"]

    assert helpers.is_iso_format(response["createdOn"])
    assert helpers.is_iso_format(response["snapshotCreatedOn"])
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

    # Validate the TagRef structure
    for tag in response["tags"]:
        assert isinstance(tag["id"], int)
        assert isinstance(tag["name"], str)
        assert isinstance(tag["url"], str)


def assert_retrieving_artifact_by_id_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    artifact_id: int,
    expected: dict[str, Any],
) -> None:
    """Assert that retrieving a artifact by id works.

    Args:
        client: The Flask test client.
        artifact_id: The id of the artifact to retrieve.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = dioptra_client.artifacts.get_by_id(artifact_id)
    response_data = response.json()
    assert response.status_code == HTTPStatus.OK and response_data == expected


def assert_retrieving_artifacts_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    expected: list[dict[str, Any]],
    group_id: int | None = None,
    sort_by: str | None = None,
    descending: bool | None = None,
    search: str | None = None,
    paging_info: dict[str, Any] | None = None,
) -> None:
    """Assert that retrieving all artifacts works.

    Args:
        client: The Flask test client.
        expected: The expected response from the API.
        group_id: The group ID used in query parameters.
        search: The search string used in query parameters.
        paging_info: The paging information used in query parameters.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """

    assert_retrieving_resource_works(
        dioptra_client=dioptra_client.artifacts,
        expected=expected,
        group_id=group_id,
        sort_by=sort_by,
        descending=descending,
        search=search,
        paging_info=paging_info,
    )


def assert_registering_existing_artifact_uri_fails(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    uri: str,
    group_id: int,
    job_id: int,
) -> None:
    """Assert that registering an artifact with an existing uri fails.

    Args:
        client: The Flask test client.
        uri: The uri to assign to the new artifact.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = dioptra_client.artifacts.create(
        group_id=group_id, job_id=job_id, uri=uri, description=""
    )
    assert response.status_code == HTTPStatus.CONFLICT


# -- Tests -----------------------------------------------------------------------------


def test_create_artifact(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_jobs: dict[str, Any],
) -> None:
    """Test that artifacts can be correctly registered and retrieved using the API.

    Given an authenticated user, this test validates the following sequence of actions:

    - The user registers an artifact with uri "s3://bucket/model_v1.artifact".
    - The response is valid matches the expected values given the registration request.
    - The user is able to retrieve information about the artifact using the artifact id.
    """
    uri = "s3://bucket/model_v1.artifact"
    description = "The first artifact."
    job_id = registered_jobs["job1"]["id"]
    user_id = auth_account["id"]
    group_id = auth_account["groups"][0]["id"]
    artifact_response = dioptra_client.artifacts.create(
        group_id=group_id, job_id=job_id, uri=uri, description=description
    )

    artifact_expected = artifact_response.json()

    assert_artifact_response_contents_matches_expectations(
        response=artifact_expected,
        expected_contents={
            "uri": uri,
            "description": description,
            "user_id": user_id,
            "group_id": group_id,
        },
    )
    assert_retrieving_artifact_by_id_works(
        dioptra_client, artifact_id=artifact_expected["id"], expected=artifact_expected
    )


def test_artifacts_get_all(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_artifacts: dict[str, Any],
) -> None:
    """Test that all artifacts can be retrieved.

    Given an authenticated user and registered artifacts, this test validates the
    following sequence of actions:

    - A user registers three artifacts with uris
        - "s3://bucket/model_v1.artifact"
        - "s3://bucket/cnn.artifact"
        - "s3://bucket/model.artifact"
        - "s3://bucket/model_v2.artifact"
    - The user is able to retrieve a list of all registered artifacts.
    - The returned list of artifacts matches the full list of registered artifacts.
    """
    artifacts_expected_list = list(registered_artifacts.values())
    assert_retrieving_artifacts_works(dioptra_client, expected=artifacts_expected_list)


@pytest.mark.parametrize(
    "sort_by, descending , expected",
    [
        ("description", True, ["artifact2", "artifact1", "artifact4", "artifact3"]),
        ("description", False, ["artifact3", "artifact4", "artifact1", "artifact2"]),
        ("createdOn", True, ["artifact4", "artifact3", "artifact2", "artifact1"]),
        ("createdOn", False, ["artifact1", "artifact2", "artifact3", "artifact4"]),
    ],
)
def test_artifact_sort(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_artifacts: dict[str, Any],
    sort_by: str,
    descending: bool,
    expected: list[str],
) -> None:
    """Test that artifacts can be sorted by column.

    Given an authenticated user and registered artifacts, this test validates the
    following sequence of actions:

    - A user registers four artifacts with these descriptions:
        "Model artifact.",
        "Trained conv net model artifact.",
        "Another model",
        "Fine-tuned model.".
    - The user is able to retrieve a list of all registered artifacts sorted by a column
    - The returned list of artifacts matches the order in the parametrize lists above.
    """

    expected_queues = [
        registered_artifacts[expected_name] for expected_name in expected
    ]
    assert_retrieving_artifacts_works(
        dioptra_client, sort_by=sort_by, descending=descending, expected=expected_queues
    )


def test_artifact_search_query(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_artifacts: dict[str, Any],
) -> None:
    """Test that artifacts can be queried with a search term.

    Given an authenticated user and registered artifacts, this test validates the
    following sequence of actions:

    - The user is able to retrieve a list of all registered artifacts with 'artifact' in
        their description.
    - The returned list of artifacts matches the expected matches from the query.
    """
    artifacts_expected_list = list(registered_artifacts.values())[:2]
    assert_retrieving_artifacts_works(
        dioptra_client,
        expected=artifacts_expected_list,
        search="description:*artifact*",
    )


def test_artifact_group_query(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_artifacts: dict[str, Any],
) -> None:
    """Test that artifacts can retrieved using a group filter.

    Given an authenticated user and registered artifacts, this test validates the
    following sequence of actions:

    - The user is able to retrieve a list of all registered artifacts that are owned by
      the default group.
    - The returned list of artifacts matches the expected list owned by the default
      group.
    """
    artifacts_expected_list = list(registered_artifacts.values())
    assert_retrieving_artifacts_works(
        dioptra_client,
        expected=artifacts_expected_list,
        group_id=auth_account["groups"][0]["id"],
    )


def test_cannot_register_existing_artifact_uri(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_artifacts: dict[str, Any],
) -> None:
    """Test that registering a artifact with an existing uri fails.

    Given an authenticated user and registered artifacts, this test validates the
    following sequence of actions:

    - The user attempts to register a second artifact with the same uri.
    - The request fails with an appropriate error message and response code.
    """
    existing_artifact = registered_artifacts["artifact1"]
    assert_registering_existing_artifact_uri_fails(
        dioptra_client,
        uri=existing_artifact["uri"],
        group_id=existing_artifact["group"]["id"],
        job_id=0,  # TODO: fill in once job stuff is done.
    )
