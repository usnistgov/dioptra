import os
import subprocess
from typing import Optional

import mlflow.tracking as tracking
import structlog
from flask import Flask
from mlflow.entities import RunStatus
from mlflow.exceptions import ExecutionException
from mlflow.projects.submitted_run import LocalSubmittedRun
from mlflow.projects.backend.abstract_backend import AbstractBackend
from mlflow.projects.utils import (
    fetch_and_validate_project,
    get_or_create_run,
    get_run_env_vars,
    load_project,
    get_entry_point_command,
    MLFLOW_LOCAL_BACKEND_RUN_ID_CONFIG,
    PROJECT_STORAGE_DIR,
)

from mitre.securingai.restapi import create_app
from mitre.securingai.restapi.app import db
from mitre.securingai.restapi.models import Job
from mitre.securingai.restapi.shared.job_queue.model import JobStatus

from .securingai_tags import SECURINGAI_DEPENDS_ON, SECURINGAI_JOB_ID, SECURINGAI_QUEUE


PROJECT_WORKFLOW_FILEPATH = "workflow_filepath"
_logger = structlog.get_logger()


class SecuringAIProjectBackend(AbstractBackend):
    def run(
        self,
        project_uri,
        entry_point,
        params,
        version,
        backend_config,
        tracking_uri,
        experiment_id,
    ):
        _logger.info(
            "Starting Securing AI execution backend",
            project_uri=project_uri,
            entry_point=entry_point,
            params=params,
            version=version,
            backend_config=backend_config,
            tracking_uri=tracking_uri,
            experiment_id=experiment_id,
        )
        work_dir = fetch_and_validate_project(project_uri, version, entry_point, params)
        project = load_project(work_dir)
        storage_dir = backend_config[PROJECT_STORAGE_DIR]
        workflow_filepath = backend_config[PROJECT_WORKFLOW_FILEPATH]

        if MLFLOW_LOCAL_BACKEND_RUN_ID_CONFIG in backend_config:
            run_id = backend_config[MLFLOW_LOCAL_BACKEND_RUN_ID_CONFIG]

        else:
            run_id = None

        _logger.info(f"=== Get/create run in experiment '{experiment_id}' ===")
        active_run = get_or_create_run(
            run_id, project_uri, experiment_id, work_dir, version, entry_point, params
        )
        _set_mlflow_run_id_in_db(run_id=active_run.info.run_id)
        _set_securingai_tags(run_id=active_run.info.run_id)
        _log_workflow_artifact(
            run_id=active_run.info.run_id, workflow_filepath=workflow_filepath
        )

        command_args = []
        command_separator = " "
        command_args += get_entry_point_command(
            project, entry_point, params, storage_dir
        )
        command_str = command_separator.join(command_args)
        submitted_run_obj = _run_entry_point(
            command_str, work_dir, experiment_id, run_id=active_run.info.run_id
        )

        _wait_for(submitted_run_obj)

        return submitted_run_obj


def _run_entry_point(command, work_dir, experiment_id, run_id):
    """Run an entry point command in a subprocess, returning a SubmittedRun that can be used to
    query the run's status.

    :param command: Entry point command to run
    :param work_dir: Working directory in which to run the command
    :param run_id: MLflow run ID associated with the entry point execution.
    """
    _logger.info(f"=== Running command '{command}' in run with ID '{run_id}' ===")

    env = os.environ.copy()
    env.update(get_run_env_vars(run_id, experiment_id))

    # in case os name is not 'nt', we are not running on windows. It introduces
    # bash command otherwise.
    if os.name != "nt":
        process = subprocess.Popen(
            ["bash", "-c", command], close_fds=True, cwd=work_dir, env=env
        )

    else:
        process = subprocess.Popen(
            ["cmd", "/c", command], close_fds=True, cwd=work_dir, env=env
        )

    _update_task_status(status=JobStatus.started)
    return LocalSubmittedRun(run_id, process)


def _wait_for(submitted_run_obj):
    """Wait on the passed-in submitted run, reporting its status to the tracking server."""
    run_id = submitted_run_obj.run_id
    active_run = None

    # Note: there's a small chance we fail to report the run's status to the tracking server if
    # we're interrupted before we reach the try block below
    try:
        active_run = (
            tracking.MlflowClient().get_run(run_id) if run_id is not None else None
        )

        if submitted_run_obj.wait():
            _logger.info(f"=== Run (ID '{run_id}') succeeded ===")
            _update_task_status(status=JobStatus.finished)
            _maybe_set_run_terminated(active_run, "FINISHED")

        else:
            _update_task_status(status=JobStatus.failed)
            _maybe_set_run_terminated(active_run, "FAILED")
            raise ExecutionException("Run (ID '%s') failed" % run_id)

    except KeyboardInterrupt:
        _logger.error(f"=== Run (ID '{run_id}') interrupted, cancelling run ===")
        submitted_run_obj.cancel()
        _update_task_status(status=JobStatus.failed)
        _maybe_set_run_terminated(active_run, "FAILED")
        raise


def _maybe_set_run_terminated(active_run, status):
    """
    If the passed-in active run is defined and still running (i.e. hasn't already been terminated
    within user code), mark it as terminated with the passed-in status.
    """
    if active_run is None:
        return

    run_id = active_run.info.run_id
    cur_status = tracking.MlflowClient().get_run(run_id).info.status

    if RunStatus.is_terminated(cur_status):
        return

    tracking.MlflowClient().set_terminated(run_id, status)


def _log_workflow_artifact(run_id, workflow_filepath):
    client = tracking.MlflowClient()
    client.log_artifact(run_id=run_id, local_path=workflow_filepath)


def _set_securingai_tags(run_id):
    app: Flask = create_app(env=os.getenv("AI_RESTAPI_ENV"))
    rq_job_id: Optional[str] = os.getenv("AI_RQ_JOB_ID")

    if rq_job_id is None:
        return None

    client = tracking.MlflowClient()

    with app.app_context():
        job: Job = Job.query.get(rq_job_id)
        client.set_tag(run_id=run_id, key=SECURINGAI_JOB_ID, value=job.job_id)
        client.set_tag(run_id=run_id, key=SECURINGAI_QUEUE, value=job.queue.name)
        client.set_tag(run_id=run_id, key=SECURINGAI_DEPENDS_ON, value=job.depends_on)


def _update_task_status(status: JobStatus) -> None:
    app: Flask = create_app(env=os.getenv("AI_RESTAPI_ENV"))
    rq_job_id: Optional[str] = os.getenv("AI_RQ_JOB_ID")

    if rq_job_id is None:
        return None

    _logger.info(
        f"=== Updating task status for job with ID '{rq_job_id}' to {status.name} ==="
    )

    with app.app_context():
        job = Job.query.get(rq_job_id)

        if job.status != status:
            job.update(changes={"status": status})
            db.session.commit()


def _set_mlflow_run_id_in_db(run_id) -> None:
    app: Flask = create_app(env=os.getenv("AI_RESTAPI_ENV"))
    rq_job_id: Optional[str] = os.getenv("AI_RQ_JOB_ID")

    if rq_job_id is None:
        return None

    _logger.info("=== Setting MLFlow run ID in Securing AI database ===")

    with app.app_context():
        job = Job.query.get(rq_job_id)
        job.update(changes={"mlflow_run_id": run_id})
        db.session.commit()
