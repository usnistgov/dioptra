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
import shlex
import subprocess
from pathlib import Path
from subprocess import CompletedProcess
from tempfile import TemporaryDirectory
from typing import List, Optional

import boto3
import structlog
from botocore.client import BaseClient
from rq.job import Job as RQJob
from rq.job import get_current_job
from structlog.stdlib import BoundLogger

from dioptra.sdk.utilities.s3.uri import s3_uri_to_bucket_prefix
from dioptra.worker.s3_download import s3_download

LOGGER: BoundLogger = structlog.stdlib.get_logger()


def _download_workflow(s3: BaseClient, dest_dir: str, workflow_uri: str):
    """
    Download the file pointed to by workflow_uri, to directory dest_dir.
    Directory structure implied by workflow_uri is not mirrored in the local
    filesystem.

    Args:
        s3: A boto3 S3 client object
        dest_dir: A directory, as a str, which must already exist
        workflow_uri: An S3 URI referring to a file
    """
    bucket, key = s3_uri_to_bucket_prefix(workflow_uri)
    dest_file = Path(key).name  # get the last path component (a filename)
    dest_path = Path(dest_dir) / dest_file

    s3.download_file(bucket, key, str(dest_path))


def run_mlflow_task(
    workflow_uri: str,
    entry_point: str,
    experiment_id: str,
    conda_env: str = "base",
    entry_point_kwargs: Optional[str] = None,
    s3: Optional[BaseClient] = None,
) -> CompletedProcess:
    mlflow_s3_endpoint_url = os.getenv("MLFLOW_S3_ENDPOINT_URL")
    dioptra_plugins_s3_uri = os.getenv("DIOPTRA_PLUGINS_S3_URI")
    dioptra_custom_plugins_s3_uri = os.getenv("DIOPTRA_CUSTOM_PLUGINS_S3_URI")
    dioptra_plugin_dir = os.getenv("DIOPTRA_PLUGIN_DIR")

    # For mypy; assume correct environment variables
    assert mlflow_s3_endpoint_url
    assert dioptra_plugins_s3_uri
    assert dioptra_custom_plugins_s3_uri
    assert dioptra_plugin_dir

    if not s3:
        s3 = boto3.client("s3", endpoint_url=mlflow_s3_endpoint_url)

    cmd: List[str] = [
        "/usr/local/bin/run-mlflow-job.sh",
        "--s3-workflow",
        workflow_uri,
        "--entry-point",
        entry_point,
        "--conda-env",
        conda_env,
        "--experiment-id",
        experiment_id,
    ]

    env = os.environ.copy()
    rq_job: Optional[RQJob] = get_current_job()

    if rq_job is not None:
        env["DIOPTRA_RQ_JOB_ID"] = rq_job.get_id()

    log: BoundLogger = LOGGER.new(rq_job_id=env.get("DIOPTRA_RQ_JOB_ID"))

    if entry_point_kwargs is not None:
        cmd.extend(shlex.split(entry_point_kwargs))

    with TemporaryDirectory(dir=os.getenv("DIOPTRA_WORKDIR")) as tmpdir:
        log.info("Downloading workflow: %s", workflow_uri)
        _download_workflow(s3, tmpdir, workflow_uri)

        log.info("Downloading plugins")
        s3_download(
            s3,
            dioptra_plugin_dir,
            True,
            True,
            dioptra_plugins_s3_uri,
            dioptra_custom_plugins_s3_uri,
        )

        log.info("Executing MLFlow job", cmd=" ".join(cmd))
        p = subprocess.run(args=cmd, cwd=tmpdir, env=env)

    if p.returncode > 0:
        log.warning(
            "MLFlow job stopped unexpectedly", returncode=p.returncode, stderr=p.stderr
        )

    return p
