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
"""Test suite for queue operations.

This module contains a set of tests that validate the CRUD operations and additional
functionalities for the queue entity. The tests ensure that the queues can be
registered, renamed, deleted, and locked/unlocked as expected through the REST API.
"""
from __future__ import annotations

from typing import Any, Dict

import pytest
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from werkzeug.test import TestResponse

from dioptra.restapi.job.routes import BASE_ROUTE as JOB_BASE_ROUTE


# -- Fixtures --------------------------------------------------------------------------

@pytest.fixture
def job_form_request(workflow_tar_gz: BinaryIO) -> Dict[str, Any]:
    return {
        "experiment_name": "mnist",
        "queue": "tensorflow_cpu",
        "timeout": "12h",
        "entry_point": "main",
        "entry_point_kwargs": "-P var1=testing",
        "workflow": (workflow_tar_gz, "workflows.tar.gz"),
    }

# -- Actions ---------------------------------------------------------------------------

def submit_job(
        client: FlaskClient, 
        job_form_request: Dict[str, Any],
    ) -> TestResponse:
    """Submit a job using the API.

    Args:
        client: The Flask test client.
        experiment_name: The name of a registered experiment.
        queue: The name of an active queue.
        timeout: The maximum alloted time for a job before it times out and is stopped. 
            If omitted, the job timeout will default to 24 hours.
        entry_point: The name of the entry point to run.
        entry_point_kwargs: A list of entry point parameter values to use for the job. 
            The list is a string with the following format: 
            -P param1=value1
            -P param2=value2
        depends_on: A job UUID to set as a dependency for this new job. The new job will not 
            run until this job completes successfully. If omitted, then the new job will start as 
            soon as computing resources are available.
        workflow: A tarball archive or zip file containing the entry point scripts.


    Returns:
        The response from the API.
    """
    return client.post(
        f"/api/{JOB_BASE_ROUTE}/",
        json=job_form_request,
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
    
def test_retrieve_job(
    client: FlaskClient, db: SQLAlchemy
) -> None:
    """Test that a job can be retrieved through the api following the 
       scenario below.

    Scenario: Get a Job
        Given I am an authorized user and a job exists, 
        I need to be able to submit a get request 
        in order to retrieve that job using its id as an identifier.

    This test validates by following these actions:
    - A user submits a job.
    - The user is able to retrieve information about the job that matches the 
      information that was provided during registration id as an identifier.
    - The returned information matches the information that was provided during 
      registration.
    """
    job_expected = submit_job(client).get_json()
    assert_retrieving_job_by_id_works(
        client, id=job_expected["jobId"], expected=job_expected
    )
    
def test_list_jobs(
    client: FlaskClient, db: SQLAlchemy
) -> None:
    """Test that the list of jobs can be retrieved through the api following the 
       scenario below.

     Scenario: Get the List of Submitted Jobs
        Given I am an authorized user and a set of jobs exist, 
        I need to be able to submit a get request 
        in order to retrieve the list of submitted jobs.

    This test validates by following these actions:
    - A user registers a set of jobs.
    - The user is able to retrieve information about the jobs that
      matches the information that was provided during registration.
    - The user is able to retrieve a list of all submitted jobs.
    - The returned list of jobs matches the information that was provided
      during registration.
    """
    job1_expected = submit_job(client).get_json()
    job2_expected = submit_job(client).get_json()
    job3_expected = submit_job(client).get_json()
    job_expected_list = [
        job1_expected, job2_expected, job3_expected
    ]
    assert_retrieving_all_jobs_works(client, expected=job_expected_list)
    
    