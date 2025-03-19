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
from http import HTTPStatus
from typing import Any

import pytest
from flask_sqlalchemy import SQLAlchemy
from pytest import MonkeyPatch

from dioptra.client.base import DioptraResponseProtocol
from dioptra.client.client import DioptraClient

from ..lib import asserts, helpers, mock_mlflow, mock_rq, routines
from ..test_utils import assert_retrieving_resource_works

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
        "snapshotCreatedOn",
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
        expected_queue_snapshot_id=expected_contents["queue_snapshot_id"],
        expected_group_id=expected_contents["group_id"],
    )
    asserts.assert_experiment_ref_contents_matches_expectations(
        experiment=response["experiment"],
        expected_experiment_id=expected_contents["experiment_id"],
        expected_experiment_snapshot_id=expected_contents["experiment_snapshot_id"],
        expected_group_id=expected_contents["group_id"],
    )
    asserts.assert_entrypoint_ref_contents_matches_expectations(
        entrypoint=response["entrypoint"],
        expected_entrypoint_id=expected_contents["entrypoint_id"],
        expected_entrypoint_snapshot_id=expected_contents["entrypoint_snapshot_id"],
        expected_group_id=expected_contents["group_id"],
    )


def assert_retrieving_job_by_id_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    job_id: int,
    expected: dict[str, Any],
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
    response = dioptra_client.jobs.get_by_id(job_id)
    assert response.status_code == HTTPStatus.OK and response.json() == expected


def assert_retrieving_jobs_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    expected: list[dict[str, Any]],
    group_id: int | None = None,
    sort_by: str | None = None,
    descending: bool | None = None,
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
    assert_retrieving_resource_works(
        dioptra_client=dioptra_client.jobs,
        expected=expected,
        group_id=group_id,
        sort_by=sort_by,
        descending=descending,
        search=search,
        paging_info=paging_info,
    )


def assert_job_is_not_found(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    job_id: int,
) -> None:
    """Assert that a job is not found.

    Args:
        client: The Flask test client.
        job_id: The id of the job to retrieve.

    Raises:
        AssertionError: If the response status code is not 404.
    """
    response = dioptra_client.jobs.get_by_id(job_id)
    assert response.status_code == HTTPStatus.NOT_FOUND


def assert_job_status_matches_expectations(
    dioptra_client: DioptraClient[DioptraResponseProtocol], job_id: int, expected: str
) -> None:
    response = dioptra_client.jobs.get_status(job_id)
    assert (
        response.status_code == HTTPStatus.OK and response.json()["status"] == expected
    )


def assert_job_mlflowrun_matches_expectations(
    dioptra_client: DioptraClient[DioptraResponseProtocol], job_id: int, expected: str
) -> None:
    import uuid

    response = dioptra_client.jobs.get_mlflow_run_id(job_id=job_id)
    assert (
        response.status_code == HTTPStatus.OK
        and uuid.UUID(response.json()["mlflowRunId"]).hex == expected
    )


def assert_job_mlflowrun_already_set(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    job_id: int,
    mlflow_run_id: str,
) -> None:
    response = dioptra_client.jobs.set_mlflow_run_id(
        job_id=job_id, mlflow_run_id=mlflow_run_id
    )
    assert (
        response.status_code == HTTPStatus.BAD_REQUEST
        and response.json()["error"] == "JobMlflowRunAlreadySetError"
    )


def assert_job_metrics_validation_error(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    job_id: int,
    metric_name: str,
    metric_value: float,
) -> None:
    response = dioptra_client.jobs.append_metric_by_id(
        job_id=job_id, metric_name=metric_name, metric_value=metric_value
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def assert_job_metrics_matches_expectations(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    job_id: int,
    expected: list[dict[str, Any]],
) -> None:
    response = dioptra_client.jobs.get_metrics_by_id(job_id=job_id)
    assert response.status_code == HTTPStatus.OK and response.json() == expected


def assert_experiment_metrics_matches_expectations(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    experiment_id: int,
    expected: list[dict[str, Any]],
) -> None:
    response = dioptra_client.experiments.get_metrics_by_id(experiment_id=experiment_id)
    assert response.status_code == HTTPStatus.OK and response.json()["data"] == expected


def assert_job_metrics_snapshots_matches_expectations(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    job_id: int,
    metric_name: str,
    expected: list[dict[str, Any]],
) -> None:
    response = dioptra_client.jobs.get_metrics_snapshots_by_id(
        job_id=job_id, metric_name=metric_name
    )
    assert response.status_code == HTTPStatus.OK

    history = response.json()["data"]

    assert all(
        [
            "name" in m and "value" in m and "timestamp" in m and "step" in m
            for m in history
        ]
    )
    assert all(
        [
            any([e["name"] == m["name"] and e["value"] == e["value"] for e in expected])
            for m in history
        ]
    )


# -- Tests -----------------------------------------------------------------------------


def test_create_job(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_queues: dict[str, Any],
    registered_experiments: dict[str, Any],
    registered_entrypoints: dict[str, Any],
    monkeypatch: MonkeyPatch,
) -> None:
    """Test that jobs can be correctly registered and retrieved using the API.

    Given an authenticated user, registered queues, registered experiments, and
    registered entrypoints, this test validates the following sequence of actions:

    - The user registers a job.
    - The response is valid and matches the expected values given the registration
      request.
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
    queue_id = registered_queues["queue1"]["id"]
    experiment_id = registered_experiments["experiment1"]["id"]
    entrypoint_id = registered_entrypoints["entrypoint1"]["id"]
    values = {
        registered_entrypoints["entrypoint1"]["parameters"][0]["name"]: "new_value",
    }
    timeout = "24h"

    job_response = dioptra_client.experiments.jobs.create(
        experiment_id=experiment_id,
        entrypoint_id=entrypoint_id,
        queue_id=queue_id,
        values=values,
        timeout=timeout,
        description=description,
    ).json()

    """
    Validate the response matches the expected contents
    ===================================================

    response: The response from actions.py::register_job()
    expected_contents: The raw data passed to actions.py::register_job() as *args
      *Note: group_id is given as an arg for registration in the service layer
    """

    queue_id = registered_queues["queue1"]["id"]
    experiment_id = registered_experiments["experiment1"]["id"]
    entrypoint_id = registered_entrypoints["entrypoint1"]["id"]
    queue_snapshot_id = registered_queues["queue1"]["snapshot"]
    experiment_snapshot_id = registered_experiments["experiment1"]["snapshot"]
    entrypoint_snapshot_id = registered_entrypoints["entrypoint1"]["snapshot"]

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
            "queue_snapshot_id": queue_snapshot_id,
            "experiment_snapshot_id": experiment_snapshot_id,
            "entrypoint_snapshot_id": entrypoint_snapshot_id,
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
        dioptra_client, job_id=job_response["id"], expected=job_response
    )


def test_create_job_with_empty_values(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_queues: dict[str, Any],
    registered_experiments: dict[str, Any],
    registered_entrypoints: dict[str, Any],
    monkeypatch: MonkeyPatch,
) -> None:
    """Test that new job can be create with EMPTY values using API
    Args:
        dioptra_client (DioptraClient[DioptraResponseProtocol]): _description_
        auth_account (dict[str, Any]): _description_
        registered_queues (dict[str, Any]): _description_
        registered_experiments (dict[str, Any]): _description_
        registered_entrypoints (dict[str, Any]): _description_
        monkeypatch (MonkeyPatch): _description_
    """

    """ Test that jobs (!!! with no-params !!!) can be correctly registered and retrieved using the API.
    General plan:
    Given an authenticated user, registered queues, registered experiments, and
    registered entrypoints, this test validates the following sequence of actions:
    - The user registers an entry point with no queues, no plugins, and no params.
    - The user registers a job.
    - The response is valid and matches the expected values given the registration
      request.
    - The user is able to retrieve information about the job using the job id.
    """
    # Begin with registering the entry-point with empty parameters, queues, and plugins
    import dioptra.restapi.v1.shared.rq_service as rq_service

    monkeypatch.setattr(rq_service, "RQQueue", mock_rq.MockRQQueue)

    entrypoint_name = "entrypoint_no_params"
    description = "The new job."
    queue_id = registered_queues["queue1"]["id"]
    experiment_id = registered_experiments["experiment1"]["id"]
    entrypoint_id = registered_entrypoints[entrypoint_name]["id"]
    values = {}
    timeout = "24h"

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
    job_response = dioptra_client.experiments.jobs.create(
        experiment_id=experiment_id,
        entrypoint_id=entrypoint_id,
        queue_id=queue_id,
        values=values,
        timeout=timeout,
        description=description,
    ).json()

    """
    Validate the response matches the expected contents
    ===================================================
    response: The response from actions.py::register_job()
    expected_contents: The raw data passed to actions.py::register_job() as *args
      *Note: group_id is given as an arg for registration in the service layer
    """
    (queue_snapshot_id, queue_id) = (
        registered_queues["queue1"]["snapshot"],
        registered_queues["queue1"]["id"],
    )

    (experiment_snapshot_id, experiment_id, group_id) = (
        registered_experiments["experiment1"]["snapshot"],
        registered_experiments["experiment1"]["id"],
        registered_experiments["experiment1"]["group"]["id"],
    )

    (entrypoint_snapshot_id, entrypoint_id) = (
        registered_entrypoints[entrypoint_name]["snapshot"],
        registered_entrypoints[entrypoint_name]["id"],
    )

    assert_job_response_contents_matches_expectations(
        response=job_response,
        expected_contents={
            "description": description,
            "timeout": timeout,
            "values": values,
            "user_id": auth_account["id"],
            "group_id": group_id,
            "queue_id": queue_id,
            "experiment_id": experiment_id,
            "entrypoint_id": entrypoint_id,
            "queue_snapshot_id": queue_snapshot_id,
            "experiment_snapshot_id": experiment_snapshot_id,
            "entrypoint_snapshot_id": entrypoint_snapshot_id,
        },
    )
    assert_retrieving_job_by_id_works(
        dioptra_client, job_id=job_response["id"], expected=job_response
    )


def test_mlflowrun(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_jobs: dict[str, Any],
    registered_mlflowrun_incomplete: dict[str, Any],
):
    import uuid

    job_uuid = uuid.uuid4().hex

    # explicitly use job3 because we did not set a mlflowrun on this job

    mlflowrun_response = dioptra_client.jobs.set_mlflow_run_id(  # noqa: F841
        job_id=registered_jobs["job3"]["id"], mlflow_run_id=job_uuid
    ).json()

    assert_job_mlflowrun_matches_expectations(
        dioptra_client, job_id=registered_jobs["job3"]["id"], expected=job_uuid
    )

    assert_job_mlflowrun_already_set(
        dioptra_client, job_id=registered_jobs["job1"]["id"], mlflow_run_id=job_uuid
    )


def test_metrics(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_jobs: dict[str, Any],
    registered_experiments: dict[str, Any],
    registered_mlflowrun: dict[str, Any],
    monkeypatch: MonkeyPatch,
) -> None:
    import mlflow.exceptions
    import mlflow.tracking

    monkeypatch.setattr(mlflow.tracking, "MlflowClient", mock_mlflow.MockMlflowClient)
    monkeypatch.setattr(
        mlflow.exceptions, "MlflowException", mock_mlflow.MockMlflowException
    )

    experiment_id = registered_experiments["experiment1"]["id"]
    job1_id = registered_jobs["job1"]["id"]
    job2_id = registered_jobs["job2"]["id"]
    job3_id = registered_jobs["job3"]["id"]

    metric_response = dioptra_client.jobs.append_metric_by_id(  # noqa: F841
        job_id=job1_id,
        metric_name="accuracy",
        metric_value=4.0,
    ).json()

    assert_job_metrics_matches_expectations(
        dioptra_client, job_id=job1_id, expected=[{"name": "accuracy", "value": 4.0}]
    )

    metric_response = dioptra_client.jobs.append_metric_by_id(  # noqa: F841
        job_id=job1_id,
        metric_name="accuracy",
        metric_value=4.1,
    ).json()

    metric_response = dioptra_client.jobs.append_metric_by_id(  # noqa: F841
        job_id=job1_id,
        metric_name="accuracy",
        metric_value=4.2,
    ).json()

    metric_response = dioptra_client.jobs.append_metric_by_id(  # noqa: F841
        job_id=job1_id,
        metric_name="roc_auc",
        metric_value=0.99,
    ).json()

    metric_response = dioptra_client.jobs.append_metric_by_id(  # noqa: F841
        job_id=job2_id,
        metric_name="job_2_metric",
        metric_value=0.11,
    ).json()

    assert_job_metrics_matches_expectations(
        dioptra_client,
        job_id=job1_id,
        expected=[
            {"name": "accuracy", "value": 4.2},
            {"name": "roc_auc", "value": 0.99},
        ],
    )

    assert_job_metrics_validation_error(
        dioptra_client,
        job_id=job1_id,
        metric_name="!+_",
        metric_value=4.0,
    )

    assert_job_metrics_validation_error(
        dioptra_client,
        job_id=job1_id,
        metric_name="!!!!!",
        metric_value=4.0,
    )

    assert_job_metrics_validation_error(
        dioptra_client,
        job_id=job1_id,
        metric_name="$23",
        metric_value=4.0,
    )

    assert_job_metrics_validation_error(
        dioptra_client,
        job_id=job1_id,
        metric_name="abcdefghijk(lmnop)",
        metric_value=4.0,
    )

    assert_experiment_metrics_matches_expectations(
        dioptra_client,
        experiment_id=experiment_id,
        expected=[
            {
                "id": job1_id,
                "metrics": [
                    {"name": "accuracy", "value": 4.2},
                    {"name": "roc_auc", "value": 0.99},
                ],
            },
            {"id": job2_id, "metrics": [{"name": "job_2_metric", "value": 0.11}]},
            {"id": job3_id, "metrics": []},
        ],
    )

    assert_job_metrics_snapshots_matches_expectations(
        dioptra_client,
        job_id=registered_jobs["job1"]["id"],
        metric_name="accuracy",
        expected=[
            {"name": "accuracy", "value": 4.2},
            {"name": "accuracy", "value": 4.1},
            {"name": "accuracy", "value": 4.0},
        ],
    )


def test_job_get_all(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    assert_retrieving_jobs_works(dioptra_client, expected=job_expected_list)


@pytest.mark.parametrize(
    "sortBy, descending , expected",
    [
        ("description", True, ["job2", "job1", "job3"]),
        ("description", False, ["job3", "job1", "job2"]),
        ("createdOn", True, ["job3", "job2", "job1"]),
        ("createdOn", False, ["job1", "job2", "job3"]),
    ],
)
def test_job_sort(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_jobs: dict[str, Any],
    sortBy: str,
    descending: bool,
    expected: list[str],
) -> None:
    """Test that jobs can be sorted by column.

    Given an authenticated user and registered jobs, this test validates the following
    sequence of actions:

    - A user registers three jobs descriptions:
      "The first job.",
      "The second job.",
      "Not retrieved.".
    - The user is able to retrieve a list of all registered jobs sorted by a column
      ascending/descending.
    - The returned list of jobs matches the order in the parametrize lists above.
    """

    expected_jobs = [registered_jobs[expected_name] for expected_name in expected]
    assert_retrieving_jobs_works(
        dioptra_client, sort_by=sortBy, descending=descending, expected=expected_jobs
    )


def test_job_search_query(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
        dioptra_client, expected=job_expected_list, search="description:*job*"
    )
    jobs_expected_list = list(registered_jobs.values())
    assert_retrieving_jobs_works(
        dioptra_client, expected=jobs_expected_list, search="*"
    )


def test_job_group_query(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
        dioptra_client,
        expected=job_expected_list,
        group_id=auth_account["groups"][0]["id"],
    )


def test_delete_job(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    dioptra_client.jobs.delete_by_id(job_to_delete["id"])
    assert_job_is_not_found(dioptra_client, job_id=job_to_delete["id"])


def test_job_get_status(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_jobs: dict[str, Any],
) -> None:
    """Test that the status of a job can be retrieved by the user.

    Given an authenticated user and registered jobs, this test validates the following
    sequence of actions:

    - The user is able to retrieve the status of a registered job.
    - The returned job status matches the expected status.
    """
    job_to_check = registered_jobs["job1"]
    status = "queued"
    assert_job_status_matches_expectations(
        dioptra_client, job_id=job_to_check["id"], expected=status
    )


def test_modify_job_status(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    experiment_id = job_to_change_status["experiment"]["id"]
    new_status = "started"
    dioptra_client.experiments.jobs.set_status(
        experiment_id=experiment_id, job_id=job_id, status=new_status
    )
    assert_job_status_matches_expectations(
        dioptra_client, job_id=job_to_change_status["id"], expected=new_status
    )


def test_manage_job_snapshots(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
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
    dioptra_client.experiments.jobs.set_status(
        experiment_id=job_to_change_status["experiment"]["id"],
        job_id=job_id,
        status="started",
    )
    modified_job = dioptra_client.jobs.get_by_id(job_id).json()

    # Run routine: resource snapshots tests
    routines.run_resource_snapshots_tests(
        dioptra_client.jobs.snapshots,
        resource_to_rename=job_to_change_status,
        modified_resource=modified_job,
        drop_additional_fields=["artifacts"],
    )


def test_tag_job(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    db: SQLAlchemy,
    auth_account: dict[str, Any],
    registered_jobs: dict[str, Any],
    registered_tags: dict[str, Any],
) -> None:
    """Test that tags can applied to jobs.

    Given an authenticated user, registered jobs, and registered tags this test
    validates the following sequence of actions:

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
    tag_ids = [tag["id"] for tag in registered_tags.values()]

    # Run routine: resource tag tests
    routines.run_resource_tag_tests(
        dioptra_client.jobs.tags,
        job["id"],
        tag_ids=tag_ids,
    )
