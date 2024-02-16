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

from .dioptra_clients import DioptraDatabaseClient
from .dioptra_tags import DIOPTRA_DEPENDS_ON, DIOPTRA_JOB_ID, DIOPTRA_QUEUE

PROJECT_WORKFLOW_FILEPATH = "workflow_filepath"
_logger = structlog.get_logger()


class DioptraProjectBackend(AbstractBackend):
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
            "Starting Dioptra execution backend",
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
        DioptraDatabaseClient().set_mlflow_run_id_in_db(run_id=active_run.info.run_id)
        _set_dioptra_tags(run_id=active_run.info.run_id)
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

    DioptraDatabaseClient().update_active_job_status(status="started")
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
            DioptraDatabaseClient().update_active_job_status(status="finished")
            _maybe_set_run_terminated(active_run, "FINISHED")

        else:
            DioptraDatabaseClient().update_active_job_status(status="failed")
            _maybe_set_run_terminated(active_run, "FAILED")
            raise ExecutionException("Run (ID '%s') failed" % run_id)

    except KeyboardInterrupt:
        _logger.error(f"=== Run (ID '{run_id}') interrupted, cancelling run ===")
        submitted_run_obj.cancel()
        DioptraDatabaseClient().update_active_job_status(status="failed")
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


def _set_dioptra_tags(run_id: str) -> None:
    job: Optional[Dict[str, Any]] = DioptraDatabaseClient().get_active_job()

    if job is None:
        return None

    client = tracking.MlflowClient()
    client.set_tag(run_id=run_id, key=DIOPTRA_JOB_ID, value=job.get("job_id", ""))
    client.set_tag(run_id=run_id, key=DIOPTRA_QUEUE, value=job.get("queue", ""))
    client.set_tag(
        run_id=run_id, key=DIOPTRA_DEPENDS_ON, value=job.get("depends_on", "")
    )
