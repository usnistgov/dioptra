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
import pathlib
import tempfile
from typing import Any, Mapping, MutableMapping, Optional

import boto3
import mlflow
import structlog
from botocore.client import BaseClient
from rq.job import get_current_job

from dioptra.mlflow_plugins.dioptra_clients import DioptraDatabaseClient
from dioptra.mlflow_plugins.dioptra_tags import (
    DIOPTRA_DEPENDS_ON,
    DIOPTRA_JOB_ID,
    DIOPTRA_QUEUE,
)
from dioptra.task_engine.task_engine import run_experiment
from dioptra.task_engine.validation import is_valid
from dioptra.worker.s3_download import s3_download


def _get_logger() -> Any:
    """
    Get a logger for this module.

    Returns:
        A logger object
    """
    return structlog.get_logger(__name__)


def run_task_engine_task(
    experiment_id: int,
    experiment_desc: Mapping[str, Any],
    global_parameters: MutableMapping[str, Any],
    s3: Optional[BaseClient] = None,
):
    """
    Run an experiment via the task engine.

    Args:
        experiment_id: The ID of the experiment to use for this run
        experiment_desc: A declarative experiment description, as a mapping
        global_parameters: Global parameters for this run, as a mapping from
            parameter name to value
        s3: An optional boto3 S3 client object to use.  If not given, construct
            one according to environment variables.  This argument is not
            normally used, but useful in unit tests when you need a specially
            configured object with stubbed responses.
    """
    rq_job = get_current_job()
    rq_job_id = rq_job.get_id() if rq_job else None

    with structlog.contextvars.bound_contextvars(rq_job_id=rq_job_id):
        log = _get_logger()

        mlflow_s3_endpoint_url = os.getenv("MLFLOW_S3_ENDPOINT_URL")
        dioptra_plugins_s3_uri = os.getenv("DIOPTRA_PLUGINS_S3_URI")
        dioptra_custom_plugins_s3_uri = os.getenv("DIOPTRA_CUSTOM_PLUGINS_S3_URI")
        dioptra_plugin_dir = os.getenv("DIOPTRA_PLUGIN_DIR")
        dioptra_work_dir = os.getenv("DIOPTRA_WORKDIR")

        # For mypy; assume correct environment variables
        assert mlflow_s3_endpoint_url
        assert dioptra_plugins_s3_uri
        assert dioptra_custom_plugins_s3_uri
        assert dioptra_plugin_dir

        if not s3:
            s3 = boto3.client("s3", endpoint_url=mlflow_s3_endpoint_url)

        if is_valid(experiment_desc):
            s3_download(
                s3,
                dioptra_plugin_dir,
                True,
                True,
                dioptra_plugins_s3_uri,
                dioptra_custom_plugins_s3_uri,
            )

            saved_cwd = pathlib.Path.cwd()
            with tempfile.TemporaryDirectory(dir=dioptra_work_dir) as tempdir:
                os.chdir(tempdir)
                try:
                    _run_experiment(
                        rq_job_id, experiment_id, experiment_desc, global_parameters
                    )
                finally:
                    os.chdir(saved_cwd)

        else:
            log.error("Experiment description was invalid!")


def _run_experiment(
    rq_job_id: str,
    experiment_id: int,
    experiment_desc: Mapping[str, Any],
    global_parameters: MutableMapping[str, Any],
):
    """
    Run the given experiment, doing some bookkeeping related to the Dioptra job
    and Mlflow.

    Args:
        rq_job_id: The redis queue job ID for this job, which is also the
            Dioptra job ID
        experiment_id: The ID of the experiment to use for this run
        experiment_desc: A declarative experiment description, as a mapping
        global_parameters: Global parameters for this run, as a mapping from
            parameter name to value
    """
    log = _get_logger()
    db_client = None

    mlflow.set_experiment(experiment_id=str(experiment_id))
    run = mlflow.start_run()

    try:
        db_client = DioptraDatabaseClient()
        job = db_client.get_job(rq_job_id)

        db_client.set_mlflow_run_id_for_job(run.info.run_id, rq_job_id)

        mlflow.set_tag(DIOPTRA_JOB_ID, rq_job_id)
        mlflow.set_tag(DIOPTRA_QUEUE, job.get("queue", ""))
        mlflow.set_tag(DIOPTRA_DEPENDS_ON, job.get("depends_on", ""))

        mlflow.log_dict(experiment_desc, "experiment.yaml")
        mlflow.log_params(global_parameters)

        db_client.update_job_status(rq_job_id, "started")

        run_experiment(experiment_desc, global_parameters)

        log.info("=== Run succeeded ===")
        mlflow.end_run()
        db_client.update_job_status(rq_job_id, "finished")

    except Exception:
        mlflow.end_run("FAILED")

        if db_client:
            db_client.update_job_status(rq_job_id, "failed")

        raise
