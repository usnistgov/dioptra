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
"""Test suite for job operations.

This module contains a set of tests that validate the CRUD operations and additional
functionalities for the job entity. The tests ensure that the queues can be
registered, renamed, queried, and deleted as expected through the REST API.
"""
from typing import Any

from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from pytest import MonkeyPatch
from werkzeug.test import TestResponse

from dioptra.restapi.routes import V1_EXPERIMENTS_ROUTE, V1_JOBS_ROUTE, V1_ROOT

from ..lib import actions, asserts, helpers, mock_rq

# -- Actions ---------------------------------------------------------------------------


def delete_job(
    client: FlaskClient,
    job_id: int,
) -> TestResponse:
    """Delete a job using the API.

    Args:
        client: The Flask test client.
        job_id: The id of the job to delete.

    Returns:
        The response from the API.
    """
    return client.delete(
        f"/{V1_ROOT}/{V1_JOBS_ROUTE}/{job_id}",
        follow_redirects=True,
    )


def modify_job_status(
    client: FlaskClient,
    experiment_id: int,
    job_id: int,
    new_status: str,
) -> TestResponse:
    """Change the status of a job using the API.

    Args:
        client: The Flask test client.
        experiment_id: The id of the experiment the job belongs too.
        job_id: The id of the job to delete.
        new_status: The new status of the job.

    Returns:
        The response from the API.
    """
    payload = {"status": new_status}
    return client.put(
        f"/{V1_ROOT}/{V1_EXPERIMENTS_ROUTE}/{experiment_id}/jobs/{job_id}/status",
        json=payload,
        follow_redirects=True,
    )


def get_job(
    client: FlaskClient,
    job_id: int,
) -> TestResponse:
    """Get a job using the API.

    Args:
        client: The Flask test client.
        job_id: The id of the job to get.

    Returns:
        The response from the API.
    """
    return client.get(
        f"/{V1_ROOT}/{V1_JOBS_ROUTE}/{job_id}",
        follow_redirects=True,
    )


# -- Assertions ------------------------------------------------------------------------


def assert_job_response_contents_matches_expectations(
    response: dict[str, Any], expected_contents: dict[str, Any]
) -> None:
    """Assert that a job response contents is valid.

    Args:
        response: The actual response from the API.
        expected_contents: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response or if the response contents is not
            valid.
    """
    # Check expected keys
    expected_keys = {
        "id",
        "snapshot",
        "createdOn",
        "lastModifiedOn",
        "latestSnapshot",
        "hasDraft",
        "description",
        "timeout",
        "status",
        "values",
        "user",
        "group",
        "tags",
        "queue",
        "experiment",
        "entrypoint",
        "artifacts",
    }
    assert set(response.keys()) == expected_keys

    # Check basic response types for base resources
    asserts.assert_base_resource_contents_match_expectations(response)

    # Check basic response types for job
    assert isinstance(response["description"], str)
    assert isinstance(response["timeout"], str)
    assert isinstance(response["values"], dict)

    assert response["description"] == expected_contents["description"]
    assert response["timeout"] == expected_contents["timeout"]
    assert response["values"] == expected_contents["values"]

    assert helpers.is_timeout_format(response["timeout"])

    # Check Refs for base resources
    asserts.assert_user_ref_contents_matches_expectations(
        user=response["user"], expected_user_id=expected_contents["user_id"]
    )
    asserts.assert_group_ref_contents_matches_expectations(
        group=response["group"], expected_group_id=expected_contents["group_id"]
    )
    asserts.assert_tag_ref_contents_matches_expectations(tags=response["tags"])

    # Check Refs for jobs
    asserts.assert_queue_ref_contents_matches_expectations(
        queue=response["queue"],
        expected_queue_id=expected_contents["queue_id"],
        expected_group_id=expected_contents["group_id"],
    )
    asserts.assert_experiment_ref_contents_matches_expectations(
        experiment=response["experiment"],
        expected_experiment_id=expected_contents["experiment_id"],
        expected_group_id=expected_contents["group_id"],
    )
    asserts.assert_entrypoint_ref_contents_matches_expectations(
        entrypoint=response["entrypoint"],
        expected_entrypoint_id=expected_contents["entrypoint_id"],
        expected_group_id=expected_contents["group_id"],
    )


def assert_retrieving_job_by_id_works(
    client: FlaskClient, job_id: int, expected: dict[str, Any]
) -> None:
    """Assert that retrieving a job by id works.

    Args:
        client: The Flask test client.
        job_id: The id of the job to retrieve.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = client.get(f"/{V1_ROOT}/{V1_JOBS_ROUTE}/{job_id}", follow_redirects=True)
    assert response.status_code == 200 and response.get_json() == expected


def assert_retrieving_jobs_works(
    client: FlaskClient,
    expected: list[dict[str, Any]],
    group_id: int | None = None,
    search: str | None = None,
    paging_info: dict[str, Any] | None = None,
) -> None:
    """Assert that retrieving all jobs works.

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
    query_string: dict[str, Any] = {}

    if group_id:
        query_string["groupId"] = group_id

    if search:
        query_string["search"] = search

    if paging_info:
        query_string["index"] = paging_info["index"]
        query_string["pageLength"] = paging_info["page_length"]

    response = client.get(
        f"/{V1_ROOT}/{V1_JOBS_ROUTE}",
        query_string=query_string,
        follow_redirects=True,
    )
    assert response.status_code == 200 and response.get_json()["data"] == expected


def assert_job_is_not_found(
    client: FlaskClient,
    job_id: int,
) -> None:
    """Assert that a job is not found.

    Args:
        client: The Flask test client.
        job_id: The id of the job to retrieve.

    Raises:
        AssertionError: If the response status code is not 404.
    """
    response = client.get(
        f"/{V1_ROOT}/{V1_JOBS_ROUTE}/{job_id}",
        follow_redirects=True,
    )
    assert response.status_code == 404


def assert_job_status_matches_expectations(
    client: FlaskClient, job_id: int, expected: str
) -> None:
    response = client.get(
        f"/{V1_ROOT}/{V1_JOBS_ROUTE}/{job_id}/status",
        follow_redirects=True,
    )
    assert response.status_code == 200 and response.get_json()["status"] == expected


# -- Tests -----------------------------------------------------------------------------


def test_create_job(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_queues: dict[str, Any],
    registered_experiments: dict[str, Any],
    registered_entrypoints: dict[str, Any],
    monkeypatch: MonkeyPatch,
) -> None:
    """Test that jobs can be correctly registered and retrieved using the API.

    Given an authenticated user, registered queues, registered experiments, and registered entrypoints
    this test validates the following sequence of actions:

    - The user registers a job.
    - The response is valid and matches the expected values given the registration request.
    - The user is able to retrieve information about the job using the job id.
    """

    """
    Register a Job
    ==============

    actions.py::register_job(*args: JobSchema)):
      JobSchema:
        From base resource schema:
          - group_id: The ID of the group the job belongs to.
        From job schema:
          - description: The description of the job
          - queue_id: The ID of queue the job is to run on.
          - experiment_id: The ID of the experiment the job belongs to.
          - entrypoint_id: The ID of the entrypoint that the job calls.
          - values: The values the job supplies to the entrypoint
          - timeout: The timeout value for the job to terminate if not completed by.
    """
    # Inline import necessary to prevent circular import
    import dioptra.restapi.v1.shared.rq_service as rq_service
    monkeypatch.setattr(rq_service, "RQQueue", mock_rq.MockRQQueue)

    description = "The new job."
    queue_id = registered_queues["queue1"]["snapshot"]
    experiment_id = registered_experiments["experiment1"]["snapshot"]
    entrypoint_id = registered_entrypoints["entrypoint1"]["snapshot"]
    values = {
        registered_entrypoints["entrypoint1"]["parameters"][0]["name"]: "new_value",
    }
    timeout = "24h"

    job_response = actions.register_job(
        client=client,
        queue_id=queue_id,
        experiment_id=experiment_id,
        entrypoint_id=entrypoint_id,
        description=description,
        values=values,
        timeout=timeout,
    ).get_json()

    """
    Validate the response matches the expected contents
    ===================================================

    response: The response from actions.py::register_job()
    expected_contents: The raw data passed to actions.py::register_job() as *args
      *Note: group_id is given as an arg for registration in the service layer
    """
    for param in registered_entrypoints["entrypoint1"]["parameters"][1:]:
        values[param["name"]] = param["defaultValue"]
    assert_job_response_contents_matches_expectations(
        response=job_response,
        expected_contents={
            "description": description,
            "timeout": timeout,
            "values": values,
            "user_id": auth_account["id"],
            "group_id": registered_experiments["experiment1"]["group"]["id"],
            "queue_id": queue_id,
            "experiment_id": experiment_id,
            "entrypoint_id": entrypoint_id,
        },
    )

    """
    Validate the job can be retrieved from the database
    ===================================================

    job_id: The id of the job
    expected: The response from the calling get on the database should match
      the response of the actions.py::register_job()
    """
    assert_retrieving_job_by_id_works(
        client, job_id=job_response["id"], expected=job_response
    )


def test_job_get_all(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_jobs: dict[str, Any],
) -> None:
    """Test that all jobs can be retrieved.

    Given an authenticated user and registered jobs this test validates the following
    sequence of actions:

    - The user is able to retrieve a list of all registered jobs.
    - The returned list of jobs matches the full list of registered jobs.
    """
    job_expected_list = list(registered_jobs.values())
    assert_retrieving_jobs_works(client, expected=job_expected_list)


def test_job_search_query(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_jobs: dict[str, Any],
) -> None:
    """Test that jobs can be queried with a search term.

    Given an authenticated user and registered jobs this test validates the following
    sequence of actions:

    - The user is able to retrieve a list of all registered jobs with a query on its
      description.
    - The returned list of jobs matches the expected list from the query.
    """
    job_expected_list = list(registered_jobs.values())[:2]
    assert_retrieving_jobs_works(
        client, expected=job_expected_list, search="description:*job*"
    )
    jobs_expected_list = list(registered_jobs.values())
    assert_retrieving_jobs_works(client, expected=jobs_expected_list, search="*")


def test_job_group_query(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_jobs: dict[str, Any],
) -> None:
    """Test that jobs can be queried with a group filter.

    Given an authenticated user and registered jobs this test validates the following
    sequence of actions:

    - The user is able to retrieve a list of all registered jobs with the specified
      group id.
    - The returned list of jobs matches the expected list from the query.
    """
    job_expected_list = list(registered_jobs.values())
    assert_retrieving_jobs_works(
        client,
        expected=job_expected_list,
        group_id=auth_account["groups"][0]["id"],
    )


def test_delete_job(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_jobs: dict[str, Any],
) -> None:
    """Test that a job can be deleted by referencing its id.

    Given an authenticated user and registered jobs, this test validates the following
    sequence of actions:

    - The user deletes a job by referencing its id.
    - The user attempts to retrieve information about the deleted job.
    - The request fails with an appropriate error message and response code.
    """
    job_to_delete = registered_jobs["job1"]
    delete_job(client, job_id=job_to_delete["id"])
    assert_job_is_not_found(client, job_id=job_to_delete["id"])


def test_job_get_status(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_jobs: dict[str, Any],
) -> None:
    """Test that the status of a job can be retrieved by the user.

    Given an authenticated user and registered jobs, this test validates the following
    sequence of actions:

    - The user is able to retrieve a the status of a registered job.
    - The returned job status matches the expected status.
    """
    job_to_check = registered_jobs["job1"]
    status = "queued"
    assert_job_status_matches_expectations(
        client, job_id=job_to_check["id"], expected=status
    )


def test_modify_job_status(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_jobs: dict[str, Any],
) -> None:
    """Test that the status of a job can be modified by the user.

    Given an authenticated user and registered jobs, this test validates the following
    sequence of actions:

    - The user is able to modify the status of a registered job.
    - The returned job status matches the expected new status.
    """
    job_to_change_status = registered_jobs["job1"]
    job_id = job_to_change_status["id"]
    experiment_id = job_to_change_status["experiment"]["snapshotId"]
    new_status = "started"
    modify_job_status(
        client=client,
        job_id=job_id,
        experiment_id=experiment_id,
        new_status=new_status,
    )
    assert_job_status_matches_expectations(
        client, job_id=job_to_change_status["id"], expected=new_status
    )


def test_manage_job_snapshots(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_jobs: dict[str, Any],
) -> None:
    """Test that different snapshots of a job can be retrieved by the user.

    Given an authenticated user and registered jobs, this test validates the following
    sequence of actions:

    - The user modifies a job status
    - The user retrieves information about the original snapshot of the job and gets
      the expected response
    - The user retrieves information about the new snapshot of the job and gets the
      expected response
    - The user retrieves a list of all snapshots of the job and gets the expected
      response
    """
    job_to_change_status = registered_jobs["job1"]
    job_id = job_to_change_status["id"]
    modify_job_status(
        client,
        job_id=job_to_change_status["id"],
        experiment_id=job_to_change_status["experiment"]["snapshotId"],
        new_status="started",
    )
    modified_job = get_job(client, job_id=job_id).get_json()
    modified_job.pop("hasDraft")
    modified_job.pop("artifacts")
    job_to_change_status.pop("hasDraft")
    job_to_change_status.pop("artifacts")
    job_to_change_status["latestSnapshot"] = False
    job_to_change_status["lastModifiedOn"] = modified_job["lastModifiedOn"]
    asserts.assert_retrieving_snapshot_by_id_works(
        client,
        resource_route=V1_JOBS_ROUTE,
        resource_id=job_to_change_status["id"],
        snapshot_id=job_to_change_status["snapshot"],
        expected=job_to_change_status,
    )
    asserts.assert_retrieving_snapshot_by_id_works(
        client,
        resource_route=V1_JOBS_ROUTE,
        resource_id=modified_job["id"],
        snapshot_id=modified_job["snapshot"],
        expected=modified_job,
    )
    expected_snapshots = [job_to_change_status, modified_job]
    asserts.assert_retrieving_snapshots_works(
        client,
        resource_route=V1_JOBS_ROUTE,
        resource_id=job_to_change_status["id"],
        expected=expected_snapshots,
    )


def test_tag_job(
    client: FlaskClient,
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_jobs: dict[str, Any],
    registered_tags: dict[str, Any],
) -> None:
    """Test that tags can applied to jobs.

    Given an authenticated user, registered jobs, and registered tags this test validates
    the following sequence of actions:

    - The user appends tags to a job
    - The user retrieves information about the tags of the job and gets
      the expected response
    - The user removes a tag from a job
    - The user retrieves information about the tags of the job and gets
      the expected response
    - The user modifies a tag from a job
    - The user retrieves information about the tags of the job and gets
      the expected response
    - The user removes all tags from a job
    - The user attempts to retrieve information about the tags of the job and gets
      the gets the expected response of no tags
    """
    job = registered_jobs["job1"]
    tags = [tag["id"] for tag in registered_tags.values()]

    # test append
    response = actions.append_tags(
        client,
        resource_route=V1_JOBS_ROUTE,
        resource_id=job["id"],
        tag_ids=[tags[0], tags[1]],
    )
    asserts.assert_tags_response_contents_matches_expectations(
        response.get_json(), [tags[0], tags[1]]
    )
    response = actions.append_tags(
        client,
        resource_route=V1_JOBS_ROUTE,
        resource_id=job["id"],
        tag_ids=[tags[1], tags[2]],
    )
    asserts.assert_tags_response_contents_matches_expectations(
        response.get_json(), [tags[0], tags[1], tags[2]]
    )

    # test remove
    actions.remove_tag(
        client, resource_route=V1_JOBS_ROUTE, resource_id=job["id"], tag_id=tags[1]
    )
    response = actions.get_tags(
        client, resource_route=V1_JOBS_ROUTE, resource_id=job["id"]
    )
    asserts.assert_tags_response_contents_matches_expectations(
        response.get_json(), [tags[0], tags[2]]
    )

    # test modify
    response = actions.modify_tags(
        client,
        resource_route=V1_JOBS_ROUTE,
        resource_id=job["id"],
        tag_ids=[tags[1], tags[2]],
    )
    asserts.assert_tags_response_contents_matches_expectations(
        response.get_json(), [tags[1], tags[2]]
    )

    # test delete
    response = actions.remove_tags(
        client, resource_route=V1_JOBS_ROUTE, resource_id=job["id"]
    )
    response = actions.get_tags(
        client, resource_route=V1_JOBS_ROUTE, resource_id=job["id"]
    )
    asserts.assert_tags_response_contents_matches_expectations(response.get_json(), [])
