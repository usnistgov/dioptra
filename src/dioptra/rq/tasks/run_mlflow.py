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
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, Union

import boto3
import mlflow.projects
import rq
import structlog
from botocore.client import BaseClient
from structlog.stdlib import BoundLogger

from dioptra.restapi.v0.shared.io_file.service import IOFileService
from dioptra.sdk.utilities.paths import set_cwd
from dioptra.sdk.utilities.s3.uri import s3_uri_to_bucket_prefix
from dioptra.worker.s3_download import s3_download

LOGGER: BoundLogger = structlog.stdlib.get_logger()


def run_mlflow_task(
    workflow_uri: str,
    entry_point: str,
    experiment_id: int,
    entry_point_kwargs: Optional[str] = None,
    s3: Optional[BaseClient] = None,
):
    rq_job = rq.get_current_job()
    rq_job_id = rq_job.get_id() if rq_job else None

    with structlog.contextvars.bound_contextvars(rq_job_id=rq_job_id):
        log: BoundLogger = LOGGER.new()

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

        run_params = _kwargs_to_dict(entry_point_kwargs)

        with TemporaryDirectory(dir=dioptra_work_dir) as tmpdir:
            log.info("Setting up workflow: %s", workflow_uri)
            workflow_file = _setup_workflow(s3, tmpdir, workflow_uri)

            mlproject_dir = _find_mlproject(tmpdir)

            if not mlproject_dir:
                log.fatal("Missing MLproject file!")
                return

            s3_download(
                s3,
                dioptra_plugin_dir,
                True,
                True,
                dioptra_plugins_s3_uri,
                dioptra_custom_plugins_s3_uri,
            )

            with set_cwd(tmpdir):
                mlflow.projects.run(
                    str(mlproject_dir),
                    backend="dioptra",
                    backend_config={"workflow_filepath": str(workflow_file)},
                    entry_point=entry_point,
                    experiment_id=str(experiment_id),
                    parameters=run_params,
                    env_manager="local",
                )


def _setup_workflow(
    s3: BaseClient, dest_dir: Union[str, Path], workflow_uri: str
) -> Path:
    """
    Set up the MLproject workflow to be run.  This will download and extract
    the archive.

    Args:
        s3: A boto3 S3 client object
        dest_dir: A path to a directory to download to, and where the archive
            will be extracted.  This directory must exist.
        workflow_uri: An S3 URI referring to a file

    Returns:
        The path to the downloaded workflow file.
    """
    workflow_file = _download_workflow(s3, dest_dir, workflow_uri)

    io_file_svc = IOFileService()
    io_file_svc.safe_extract_archive(
        dest_dir, archive_file_path=workflow_file, preserve_paths=True
    )

    return workflow_file


def _download_workflow(
    s3: BaseClient, dest_dir: Union[str, Path], workflow_uri: str
) -> Path:
    """
    Download the file pointed to by workflow_uri, to directory dest_dir.
    Directory structure implied by workflow_uri is not mirrored in the local
    filesystem.

    Args:
        s3: A boto3 S3 client object
        dest_dir: A path to a directory, which must already exist
        workflow_uri: An S3 URI referring to a file

    Returns:
        The path to the downloaded file
    """
    bucket, key = s3_uri_to_bucket_prefix(workflow_uri)
    dest_file = Path(key).name  # get the last path component (a filename)
    dest_path = Path(dest_dir) / dest_file

    s3.download_file(bucket, key, str(dest_path))

    return dest_path


def _find_mlproject(workflow_dir: Union[str, Path]) -> Optional[Path]:
    """
    Search for a subdirectory containing a file named "MLproject".

    Args:
        workflow_dir: A path to a directory to search

    Returns:
        A path to a directory if an MLproject file is found; None if a
        MLproject file is not found.
    """
    for dirpath, _, filenames in os.walk(workflow_dir):
        if "MLproject" in filenames:
            mlproject_dir = Path(dirpath)
            break
    else:
        mlproject_dir = None

    return mlproject_dir


def _kwargs_to_dict(entry_point_kwargs: Optional[str]) -> dict[str, str]:
    """
    Adapt mlflow commandline keyword args which set up parameters for a run,
    to a parameter dict as required to programmatically run a project.
    Expected syntax for keyword args is:

        -P arg1=value1 -P arg2=value2 ...

    This will be converted to a dict as {"arg1": "value1", "arg2": "value2"}.

    Args:
        entry_point_kwargs: mlflow commandline keyword args which set up
            parameters for a run.  Also supports None or empty string, meaning
            there are no args.

    Returns:
        A dict mapping parameter name to value.  It may be empty if there
        were no args found.
    """

    arg_dict = {}
    if entry_point_kwargs:
        arg_list = shlex.split(entry_point_kwargs)

        for arg in arg_list:
            # In case the user squished the "arg=value" up against the "-P",
            # remove "-P" if needed.
            if arg.startswith("-P"):
                arg = arg[2:]

            eq_idx = arg.find("=")
            if eq_idx > -1:
                arg_name = arg[:eq_idx]
                arg_value = arg[eq_idx + 1 :]

                arg_dict[arg_name] = arg_value

    return arg_dict
