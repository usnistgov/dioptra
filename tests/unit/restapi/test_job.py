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
functionalities for the job entity. The tests ensure that the jobs can be submitted and
retrieved as expected through the REST API.
"""
from __future__ import annotations

from typing import Any, BinaryIO, Callable

import pytest
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from pytest import MonkeyPatch
from werkzeug.test import TestResponse

from dioptra.restapi.experiment.routes import BASE_ROUTE as EXPERIMENT_BASE_ROUTE
from dioptra.restapi.job.routes import BASE_ROUTE as JOB_BASE_ROUTE
from dioptra.restapi.queue.routes import BASE_ROUTE as QUEUE_BASE_ROUTE
from dioptra.restapi.shared.s3.service import S3Service

from .lib import mock_rq, mock_s3

# -- Fixtures --------------------------------------------------------------------------


@pytest.fixture
def job_request_factory(
    workflow_tar_gz_factory: Callable[[], BinaryIO]
) -> Callable[[], dict[str, Any]]:
    """Return a factory for creating a job submission request.

    Args:
        workflow_tar_gz_factory: A factory for generating workflow.tar.gz files.

    Returns:
        A factory function for creating job submission requests.
    """
    def wrapped() -> dict[str, Any]:
        return {
            "experimentName": "mnist",
            "queue": "tensorflow_cpu",
            "timeout": "12h",
            "entryPoint": "main",
            "entryPointKwargs": "-P var1=testing",
            "workflow": (workflow_tar_gz_factory(), "workflows.tar.gz"),
        }

    return wrapped


# -- Actions ---------------------------------------------------------------------------


def register_mnist_experiment(client: FlaskClient) -> TestResponse:
    """Register the mnist experiment using the API.

    Args:
        client: The Flask test client.

    Returns:
        The response from the API.
    """
    return client.post(
        f"/api/{EXPERIMENT_BASE_ROUTE}/",
        json={"name": "mnist"},
        follow_redirects=True,
    )


def register_tensorflow_cpu_queue(client: FlaskClient) -> TestResponse:
    """Register the tensorflow cpu queue using the API.

    Args:
        client: The Flask test client.

    Returns:
        The response from the API.
    """
    return client.post(
        f"/api/{QUEUE_BASE_ROUTE}/",
        json={"name": "tensorflow_cpu"},
        follow_redirects=True,
    )


def submit_job(
    client: FlaskClient,
    form_request: dict[str, Any],
) -> TestResponse:
    """Submit a job using the API.

    Args:
        client: The Flask test client.
        form_request: The job parameters to include in the submission request.

    Returns:
        The response from the API.
    """
    return client.post(
        f"/api/{JOB_BASE_ROUTE}/",
        content_type="multipart/form-data",
        data=form_request,
        follow_redirects=True,
    )


# -- Assertions ------------------------------------------------------------------------


def assert_retrieving_job_by_id_works(
    client: FlaskClient, id: int, expected: dict[str, Any]
) -> None:
    """Assert that retrieving a job by id works.

    Args:
        client: The Flask test client.
        id: The id of the job to retrieve.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = client.get(f"/api/{JOB_BASE_ROUTE}/{id}", follow_redirects=True)
    assert response.status_code == 200 and response.get_json() == expected


def assert_retrieving_all_jobs_works(
    client: FlaskClient, expected: list[dict[str, Any]]
) -> None:
    """Assert that retrieving all experiments works.

    Args:
        client: The Flask test client.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = client.get(f"/api/{JOB_BASE_ROUTE}", follow_redirects=True)
    assert response.status_code == 200 and response.get_json() == expected


# -- Tests -----------------------------------------------------------------------------


def test_submit_job(
    monkeypatch: MonkeyPatch,
    client: FlaskClient,
    db: SQLAlchemy,
    job_request_factory: Callable[[], dict[str, Any]],
) -> None:
    """Test that a job can be submitted following the scenario below::

        Setup: An experiment 'mnist' and queue 'tensorflow_cpu' is registered.

        Scenario: Get a Job
            Given I am an authorized user,
            I need to be able to submit a job request,
            in order to queue up a job as part of an experiment.

    This test validates this scenario by following these actions:

    - A user submits a job.
    - The user retrieves information about the job that matches the information that
      was provided during registration id as an identifier.
    - The returned information matches what was provided during registration.
    """
    # Inline import necessary to prevent circular import
    import dioptra.restapi.shared.rq.service as rq_service

    monkeypatch.setattr(rq_service, "RQQueue", mock_rq.MockRQQueue)
    monkeypatch.setattr(S3Service, "upload", mock_s3.mock_s3_upload)

    register_mnist_experiment(client)
    register_tensorflow_cpu_queue(client)
    job_expected = submit_job(client, form_request=job_request_factory()).get_json()  # noqa: B950; fmt: skip
    assert_retrieving_job_by_id_works(client, id=job_expected["jobId"], expected=job_expected)  # noqa: B950; fmt: skip


def test_list_jobs(
    monkeypatch: MonkeyPatch,
    client: FlaskClient,
    db: SQLAlchemy,
    job_request_factory: Callable[[], dict[str, Any]],
) -> None:
    """Test that multiple submitted jobs can be retrieved following the scenario below::

        Setup: An experiment 'mnist' and queue 'tensorflow_cpu' is registered.

        Scenario: Get the List of Submitted Jobs
            Given I am an authorized user and a set of jobs exist,
            I need to be able to submit a get request
            in order to retrieve the list of submitted jobs.

    This test validates this scenario by following these actions:

    - A user submits 3 jobs.
    - The user is able to retrieve a list of all the submitted jobs.
    - The returned list of 3 jobs matches the information provided during submission.
    """
    # Inline import necessary to prevent circular import
    import dioptra.restapi.shared.rq.service as rq_service

    monkeypatch.setattr(rq_service, "RQQueue", mock_rq.MockRQQueue)
    monkeypatch.setattr(S3Service, "upload", mock_s3.mock_s3_upload)

    register_mnist_experiment(client)
    register_tensorflow_cpu_queue(client)
    job1_expected = submit_job(client, form_request=job_request_factory()).get_json()  # noqa: B950; fmt: skip
    job2_expected = submit_job(client, form_request=job_request_factory()).get_json()  # noqa: B950; fmt: skip
    job3_expected = submit_job(client, form_request=job_request_factory()).get_json()  # noqa: B950; fmt: skip
    job_expected_list = [job1_expected, job2_expected, job3_expected]
    assert_retrieving_all_jobs_works(client, expected=job_expected_list)
