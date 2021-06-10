# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
import os
import subprocess
from typing import Any, Dict, Optional

import mlflow.tracking as tracking
import structlog
from mlflow.entities import RunStatus
from mlflow.exceptions import ExecutionException
from mlflow.projects.backend.abstract_backend import AbstractBackend
from mlflow.projects.submitted_run import LocalSubmittedRun
from mlflow.projects.utils import (
    MLFLOW_LOCAL_BACKEND_RUN_ID_CONFIG,
    PROJECT_STORAGE_DIR,
    fetch_and_validate_project,
    get_entry_point_command,
    get_or_create_run,
    get_run_env_vars,
    load_project,
)

from .securingai_clients import SecuringAIDatabaseClient
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
        SecuringAIDatabaseClient().set_mlflow_run_id_in_db(
            run_id=active_run.info.run_id
        )
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
    """Run an entry point command in a subprocess, returning a SubmittedRun that can be
    used to query the run's status.

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

    SecuringAIDatabaseClient().update_active_job_status(status="started")
    return LocalSubmittedRun(run_id, process)


def _wait_for(submitted_run_obj):
    """Wait on the passed-in submitted run, reporting its status to the tracking
    server.
    """
    run_id = submitted_run_obj.run_id
    active_run = None

    # Note: there's a small chance we fail to report the run's status to the tracking
    # server if we're interrupted before we reach the try block below
    try:
        active_run = (
            tracking.MlflowClient().get_run(run_id) if run_id is not None else None
        )

        if submitted_run_obj.wait():
            _logger.info(f"=== Run (ID '{run_id}') succeeded ===")
            SecuringAIDatabaseClient().update_active_job_status(status="finished")
            _maybe_set_run_terminated(active_run, "FINISHED")

        else:
            SecuringAIDatabaseClient().update_active_job_status(status="failed")
            _maybe_set_run_terminated(active_run, "FAILED")
            raise ExecutionException("Run (ID '%s') failed" % run_id)

    except KeyboardInterrupt:
        _logger.error(f"=== Run (ID '{run_id}') interrupted, cancelling run ===")
        submitted_run_obj.cancel()
        SecuringAIDatabaseClient().update_active_job_status(status="failed")
        _maybe_set_run_terminated(active_run, "FAILED")
        raise


def _maybe_set_run_terminated(active_run, status):
    """If the passed-in active run is defined and still running (i.e. hasn't already
    been terminated within user code), mark it as terminated with the passed-in status.
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
    job: Optional[Dict[str, Any]] = SecuringAIDatabaseClient().get_active_job()

    if job is None:
        return None

    client = tracking.MlflowClient()
    client.set_tag(run_id=run_id, key=SECURINGAI_JOB_ID, value=job.get("job_id", ""))
    client.set_tag(run_id=run_id, key=SECURINGAI_QUEUE, value=job.get("queue", ""))
    client.set_tag(
        run_id=run_id, key=SECURINGAI_DEPENDS_ON, value=job.get("depends_on", "")
    )
