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
"""Job submission tests using independent database sessions."""

from collections.abc import Callable, Iterator
from functools import partial
from http import HTTPStatus
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from flask import Flask
from pytest import FixtureRequest, MonkeyPatch
from sqlalchemy import select
from sqlalchemy.orm import Session

from dioptra.client.base import DioptraResponseProtocol
from dioptra.client.client import DioptraClient
from dioptra.restapi.config import _is_windows
from dioptra.restapi.db import db, models

from ..lib import actions, asserts, mock_mlflow, mock_rq
from ..lib import db as libdb
from ..lib.client import DioptraFlaskClientSession


@pytest.fixture
def flask_app(
    app_factory: Callable[..., Flask], tmp_path: Path, request: FixtureRequest
) -> Flask:
    """Supply a database that another session can read across commits.

    Args:
        app_factory: Application factory with test dependency bindings.
        tmp_path: Temporary directory for the database file.
        request: Fixture parameters with the application mode, defaulting to dev.

    Returns:
        An application with an independent database and initialized ontology.
    """
    mode = getattr(request, "param", "dev")
    app = app_factory(
        mode,
        LOGIN_DISABLED=mode == "dev",
        DIOPTRA_TLS_ALLOWED_AUTHORITIES=["localhost"],
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{tmp_path / 'submission.sqlite'}",
    )
    if mode == "prod":
        app.config["PREFERRED_URL_SCHEME"] = "https"
    with app.app_context():
        db.create_all()
        libdb.setup_ontology(db.session())
    return app


@pytest.fixture
def db_session(flask_app: Flask) -> Iterator[Session]:
    """Use real database commits in the submission scenarios.

    Args:
        flask_app: Application with a dedicated file-backed database.

    Yields:
        The scoped session used by the main client. The worker can read
        committed state in a different session.
    """
    with flask_app.app_context():
        yield db.session()


@pytest.fixture
def submit_job(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_queues: dict[str, Any],
    registered_experiments: dict[str, Any],
    registered_entrypoints: dict[str, Any],
    monkeypatch: MonkeyPatch,
) -> Callable[..., DioptraResponseProtocol]:
    """Prepare an otherwise valid job submission and isolate its dependencies.

    Args:
        dioptra_client: API client for the test application.
        auth_account: Account already logged in to the client.
        registered_queues: Queues available for submission.
        registered_experiments: Experiments available for submission.
        registered_entrypoints: Entrypoints available for submission.
        monkeypatch: Restores the fake queue and run registry after the test.

    Returns:
        A request callable with valid IDs and inputs that can be overridden.
    """
    import dioptra.restapi.v1.shared.rq_service as rq_service

    monkeypatch.setattr(rq_service, "RQQueue", mock_rq.MockRQQueue)
    monkeypatch.setattr(mock_mlflow.MockState, "registered_runs", {})
    entrypoint = registered_entrypoints["entrypoint1"]
    return partial(
        dioptra_client.experiments.jobs.create,
        experiment_id=registered_experiments["experiment1"]["id"],
        entrypoint_id=entrypoint["id"],
        queue_id=registered_queues["queue1"]["id"],
        values={entrypoint["parameters"][0]["name"]: "new_value"},
        timeout="24h",
    )


@pytest.fixture
def prevent_enqueue(monkeypatch: MonkeyPatch) -> None:
    """Fail the test if the API makes work available to the queue.

    Args:
        monkeypatch: Installs the enqueue assertion for this test only.
    """

    def unexpected_enqueue(queue: mock_rq.MockRQQueue, job: mock_rq.MockRQJob) -> None:
        """Fail immediately if the submission reaches delivery.

        Args:
            queue: Queue on which execution would be scheduled.
            job: Job that should never become available.
        """
        pytest.fail(f"Job {job.id} unexpectedly reached queue {queue.name}")

    monkeypatch.setattr(mock_rq.MockRQQueue, "enqueue_job", unexpected_enqueue)


@pytest.mark.parametrize(
    "flask_app",
    [
        "dev",
        pytest.param(
            "prod",
            marks=pytest.mark.skipif(
                _is_windows(), reason="Production startup requires a POSIX host."
            ),
        ),
    ],
    indirect=True,
)
def test_job_binding_has_no_http_write_operations(
    submit_job, dioptra_client, client, flask_app, monkeypatch
) -> None:
    """Verify that lifecycle reporting and run reads never reopen binding writes.

    Authenticate against the configured application, submit a job and turn on its
    debug flag. Both run resources are read-only, and status validation rejects
    reset. Subsequent reads still report the original run and status.
    """
    monkeypatch.setitem(flask_app.config, "DEBUG", True)
    response = submit_job()
    assert response.status_code == HTTPStatus.OK
    job = response.json()
    job_id, experiment_id = job["id"], job["experiment"]["id"]
    run = dioptra_client.jobs.get_mlflow_run_id(job_id).json()
    assert run["mlflowRunId"]
    scoped_job = f"/api/v1/experiments/{experiment_id}/jobs/{job_id}"

    assert client.post(f"/api/v1/jobs/{job_id}/mlflowRun").status_code == (
        HTTPStatus.METHOD_NOT_ALLOWED
    )
    assert client.post(f"{scoped_job}/mlflowRun").status_code == (
        HTTPStatus.METHOD_NOT_ALLOWED
    )
    assert client.put(f"{scoped_job}/status", json={"status": "reset"}).status_code == (
        HTTPStatus.BAD_REQUEST
    )
    assert dioptra_client.jobs.get_mlflow_run_id(job_id).json() == run
    asserts.assert_job_status_matches_expectations(dioptra_client, job_id, "queued")


def test_worker_can_read_run_as_soon_as_job_is_queued(
    submit_job, dioptra_client, monkeypatch
) -> None:
    """Verify the job and its assigned run are readable when RQ receives work.

    At the enqueue boundary a separate database session reads the queued job
    and its run. A worker can therefore process the job immediately after
    delivery using only the trusted job and experiment IDs.
    """
    observed = []

    def read_at_delivery(
        queue: mock_rq.MockRQQueue, job: mock_rq.MockRQJob
    ) -> mock_rq.MockRQJob:
        """Capture the durable binding and worker inputs at queue delivery.

        Args:
            queue: Queue receiving the submitted job.
            job: RQ job received at the delivery boundary.

        Returns:
            The job acknowledging delivery to the submitter.
        """
        with Session(db.engine) as reader:
            job_id = int(job.id)
            binding = reader.get(models.JobMlflowRun, job_id)
            status = reader.scalar(
                select(models.Job.status).where(models.Job.resource_id == job_id)
            )
            observed.append(
                (binding.mlflow_run_id if binding else None, status, job.cmd_kwargs)
            )
        return job

    monkeypatch.setattr(mock_rq.MockRQQueue, "enqueue_job", read_at_delivery)
    response = submit_job()

    assert response.status_code == HTTPStatus.OK
    job = response.json()
    run = dioptra_client.jobs.get_mlflow_run_id(job["id"]).json()
    run_id = UUID(run["mlflowRunId"])
    assert observed == [
        (
            run_id,
            "queued",
            {"job_id": job["id"], "experiment_id": job["experiment"]["id"]},
        )
    ]
    assert mock_mlflow.MockState.registered_runs[run_id.hex].info._experiment_id == 0


@pytest.mark.parametrize("timeout", ["1y", "0"])
def test_invalid_timeout_does_not_allocate_or_enqueue(
    timeout, submit_job, prevent_enqueue, monkeypatch
) -> None:
    """Verify invalid execution time limits fail during submission validation.

    An unknown unit and a zero duration both produce a request error before
    allocating a run or creating queue work. A caller can correct the input
    without leaving an unused allocation.
    """

    def unexpected_allocation(
        client: mock_mlflow.MockMlflowClient, experiment_id: str
    ) -> None:
        """Fail if the invalid input reaches MLflow.

        Args:
            client: Tracking client selected for allocation.
            experiment_id: Experiment in which a run would be allocated.
        """
        pytest.fail(f"Unexpected allocation in experiment {experiment_id} via {client}")

    monkeypatch.setattr(
        mock_mlflow.MockMlflowClient, "create_run", unexpected_allocation
    )
    response = submit_job(timeout=timeout)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert db.session.scalar(select(models.Job.resource_id)) is None


def test_lost_run_allocation_reply_prevents_submission(
    submit_job, prevent_enqueue, monkeypatch
) -> None:
    """Verify a tracking timeout before confirmation leaves no job to execute.

    MLflow allocates a run and its response is lost. The API reports an error,
    leaves no job record, and cannot compensate against an unconfirmed run.
    """
    create_run = mock_mlflow.MockMlflowClient.create_run

    def lose_allocation_reply(
        client: mock_mlflow.MockMlflowClient, experiment_id: str
    ) -> None:
        """Allocate the run and raise a timeout before revealing its ID.

        Args:
            client: Test tracking client that receives the request.
            experiment_id: Experiment in which to create the run.

        Raises:
            TimeoutError: The allocation reply is lost.
        """
        create_run(client, experiment_id)
        raise TimeoutError("Lost MLflow response")

    monkeypatch.setattr(
        mock_mlflow.MockMlflowClient, "create_run", lose_allocation_reply
    )
    response = submit_job()

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert db.session.scalar(select(models.Job.resource_id)) is None
    assert len(mock_mlflow.MockState.registered_runs) == 1


@pytest.mark.parametrize("deletion_succeeds", [True, False])
def test_confirmed_binding_rollback_attempts_to_discard_unused_run(
    deletion_succeeds, submit_job, prevent_enqueue, db_session, monkeypatch
) -> None:
    """Verify the API compensates after an observed pre-commit rollback.

    The job write succeeds before a simulated error flushes the binding.
    Rolling back the transaction removes the job. Since enqueue never began,
    the API attempts to discard the allocated run. A tracking failure
    during deletion leaves an unused run and preserves the submission error.
    """
    flush = db_session.flush
    delete_run = mock_mlflow.MockMlflowClient.delete_run
    deleted_runs = []

    def fail_binding_write(*args: Any, **kwargs: Any) -> None:
        """Raise before writing the staged run binding to the database.

        Args:
            *args: Positional arguments forwarded to the session flush.
            **kwargs: Keyword arguments forwarded to the session flush.

        Raises:
            RuntimeError: The pending association cannot be persisted.
        """
        if any(isinstance(row, models.JobMlflowRun) for row in db_session.new):
            raise RuntimeError("Simulated binding write failure")
        flush(*args, **kwargs)

    def discard_run(client: mock_mlflow.MockMlflowClient, run_id: str) -> None:
        """Capture the compensation attempt and simulate its tracking outcome.

        Args:
            client: Tracking client that owns the allocated run.
            run_id: ID of the unused run the API attempts to discard.

        Raises:
            TimeoutError: The scenario injects a tracking failure on deletion.
        """
        deleted_runs.append(run_id)
        if not deletion_succeeds:
            raise TimeoutError("Could not confirm run deletion")
        delete_run(client, run_id)

    monkeypatch.setattr(db_session, "flush", fail_binding_write)
    monkeypatch.setattr(mock_mlflow.MockMlflowClient, "delete_run", discard_run)
    response = submit_job()

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert db.session.scalar(select(models.Job.resource_id)) is None
    (run_id,) = deleted_runs
    assert (run_id not in mock_mlflow.MockState.registered_runs) == deletion_succeeds


def test_uncertain_database_commit_preserves_possible_binding(
    submit_job, prevent_enqueue, db_session
) -> None:
    """Verify a lost commit reply stops submission while preserving the run.

    The database commits, then the session reports a timeout. The API cannot
    establish whether the binding persisted, and deleting the run would
    leave a committed job pointing to a missing run.
    """
    commit = db_session.commit

    def lose_commit_reply() -> None:
        """Commit the staged job and run binding before losing the reply.

        Raises:
            TimeoutError: The database commit reply is lost.
        """
        commit()
        raise TimeoutError("Lost database commit response")

    with MonkeyPatch.context() as patch:
        patch.setattr(db_session, "commit", lose_commit_reply)
        response = submit_job()

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert "confirm" in response.json()["message"]
    binding = db.session.scalars(select(models.JobMlflowRun)).one()
    assert mock_mlflow.MockState.registered_runs[binding.mlflow_run_id.hex]


@pytest.mark.parametrize("save_failure", [True, False])
def test_definite_queue_rejection_reports_outcome(
    save_failure,
    submit_job,
    prevent_enqueue,
    dioptra_client,
    db_session,
    monkeypatch,
) -> None:
    """Verify a proven pre-delivery queue failure is visible on the saved job.

    Local job preparation fails before Redis receives the queue request. The
    response identifies the attempted submission, and the job retains its
    run. The failed snapshot and log are saved together. If saving them
    fails, the response still identifies the definite enqueue rejection.
    """

    def reject_preparation(*args: Any, **kwargs: Any) -> None:
        """Fail before contacting the queue.

        Args:
            *args: Arguments for local job preparation.
            **kwargs: Keyword arguments for local job preparation.

        Raises:
            RuntimeError: The queue job cannot be prepared.
        """
        raise RuntimeError("Simulated local job preparation failure")

    monkeypatch.setattr(mock_rq.MockRQQueue, "create_job", reject_preparation)
    if not save_failure:
        flush = db_session.flush

        def fail_rejection_log(*args: Any, **kwargs: Any) -> None:
            """Fail the transaction that writes the failed snapshot and log.

            Args:
                *args: Positional arguments forwarded to the session flush.
                **kwargs: Keyword arguments forwarded to the session flush.

            Raises:
                RuntimeError: The job log cannot be written.
            """
            if any(isinstance(row, models.JobLog) for row in db_session.new):
                raise RuntimeError("Simulated rejection log write failure")
            flush(*args, **kwargs)

        monkeypatch.setattr(db_session, "flush", fail_rejection_log)

    response = submit_job()

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    error = response.json()
    job_id = error["detail"]["jobId"]
    assert str(job_id) in error["message"]
    assert error["detail"]["submissionOutcome"] == "not_queued"
    status = dioptra_client.jobs.get_status(job_id).json()["status"]
    assert status == ("failed" if save_failure else "queued")
    run = dioptra_client.jobs.get_mlflow_run_id(job_id).json()
    assert UUID(run["mlflowRunId"]).hex in mock_mlflow.MockState.registered_runs
    logs = dioptra_client.jobs.get_logs_by_id(job_id).json()["data"]
    if save_failure:
        assert any(log["severity"] == "ERROR" and log["message"] for log in logs)
    else:
        assert not logs


def test_lost_queue_acknowledgement_preserves_worker_update(
    submit_job, flask_app, auth_account, dioptra_client, monkeypatch
) -> None:
    """Verify a lost queue reply preserves a worker's lifecycle update.

    Simulated delivery lets a second API client start the job before the
    enqueue attempt reports a timeout. The submitter receives an uncertain
    outcome. The job remains started and its run remains available.
    """

    def deliver_without_reply(
        queue: mock_rq.MockRQQueue, job: mock_rq.MockRQJob
    ) -> None:
        """Start the queued job through a separate API client, then time out.

        Args:
            queue: The queue that received the job.
            job: The job whose status the worker should advance.

        Raises:
            TimeoutError: The enclosing submitter does not receive a reply.
        """
        payload = job.cmd_kwargs
        assert payload is not None
        with flask_app.app_context(), flask_app.test_client() as worker:
            actions.login(worker, auth_account["username"], auth_account["password"])
            worker_client = DioptraClient(DioptraFlaskClientSession(worker))
            status = worker_client.experiments.jobs.set_status(
                payload["experiment_id"], payload["job_id"], "started"
            )
            assert status.status_code == HTTPStatus.OK
        raise TimeoutError(f"Lost acknowledgement from {queue.name}")

    monkeypatch.setattr(mock_rq.MockRQQueue, "enqueue_job", deliver_without_reply)
    response = submit_job()

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    error = response.json()
    job_id = error["detail"]["jobId"]
    assert str(job_id) in error["message"]
    assert error["detail"]["submissionOutcome"] == "queue_acceptance_unknown"
    assert dioptra_client.jobs.get_status(job_id).json()["status"] == "started"
    run = dioptra_client.jobs.get_mlflow_run_id(job_id).json()
    assert UUID(run["mlflowRunId"]).hex in mock_mlflow.MockState.registered_runs
