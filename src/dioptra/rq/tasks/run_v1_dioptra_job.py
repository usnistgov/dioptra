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
import importlib
import os
import tarfile
import tempfile
from pathlib import Path
from typing import Final

import structlog
from structlog.stdlib import BoundLogger

from dioptra.client import connect_json_dioptra_client
from dioptra.sdk.utilities.contexts import sys_path_dirs
from dioptra.sdk.utilities.paths import set_cwd

LOGGER: BoundLogger = structlog.stdlib.get_logger()

ENV_DIOPTRA_API: Final[str] = "DIOPTRA_API"
ENV_DIOPTRA_WORKER_USERNAME: Final[str] = "DIOPTRA_WORKER_USERNAME"
ENV_DIOPTRA_WORKER_PASSWORD: Final[str] = "DIOPTRA_WORKER_PASSWORD"
ENV_MLFLOW_S3_ENDPOINT_URL: Final[str] = "MLFLOW_S3_ENDPOINT_URL"


def run_v1_dioptra_job(job_id: int, experiment_id: int) -> None:  # noqa: C901
    """Fetches the job files from the Dioptra API and runs the job.

    Args:
        job_id: The Dioptra job ID.
        experiment_id: The Dioptra experiment ID.
    """
    log = LOGGER.new(job_id=job_id, experiment_id=experiment_id)  # noqa: F841

    if (username := os.getenv(ENV_DIOPTRA_WORKER_USERNAME)) is None:
        log.error(f"{ENV_DIOPTRA_WORKER_USERNAME} environment variable is not set")
        raise ValueError(
            f"{ENV_DIOPTRA_WORKER_USERNAME} environment variable is not set"
        )

    if (password := os.getenv(ENV_DIOPTRA_WORKER_PASSWORD)) is None:
        log.error(f"{ENV_DIOPTRA_WORKER_PASSWORD} environment variable is not set")
        raise ValueError(
            f"{ENV_DIOPTRA_WORKER_PASSWORD} environment variable is not set"
        )

    # Instantiate a Dioptra client and login using worker's authentication details
    try:
        client = connect_json_dioptra_client()

    except ValueError:
        log.error(f"{ENV_DIOPTRA_API} environment variable is not set")
        raise ValueError(f"{ENV_DIOPTRA_API} environment variable is not set") from None

    client.auth.login(username=username, password=password)

    # Set Dioptra Job status to "started"
    client.experiments.jobs.set_status(
        experiment_id=experiment_id, job_id=job_id, status="started"
    )

    if os.getenv(ENV_MLFLOW_S3_ENDPOINT_URL) is None:
        client.experiments.jobs.set_status(
            experiment_id=experiment_id, job_id=job_id, status="failed"
        )
        log.error(f"{ENV_MLFLOW_S3_ENDPOINT_URL} environment variable is not set")
        raise ValueError(
            f"{ENV_MLFLOW_S3_ENDPOINT_URL} environment variable is not set"
        )

    # Set up a temporary directory and set it as the current working directory
    with tempfile.TemporaryDirectory() as tempdir, set_cwd(tempdir):
        working_dir = Path(tempdir)
        plugins_dir = working_dir / "plugins"
        run_dioptra_job_path = working_dir / "run_dioptra_job.py"

        # Use client to download the job files for the provided job_id
        try:
            job_files_package = client.workflows.download_job_files(
                job_id=job_id, output_dir=working_dir
            )

        except Exception as e:
            client.experiments.jobs.set_status(
                experiment_id=experiment_id, job_id=job_id, status="failed"
            )
            log.exception("Could not download job files")
            raise e

        # Unpack the (trusted) tar.gz file in it.
        try:
            with tarfile.open(job_files_package, mode="r:*") as tar:
                tar.extractall(path=working_dir, filter="data")

        except Exception as e:
            client.experiments.jobs.set_status(
                experiment_id=experiment_id, job_id=job_id, status="failed"
            )
            log.exception("Could not extract from tar file")
            raise e

        # Import the run_dioptra_job.py file as a module
        try:
            with sys_path_dirs(dirs=(str(working_dir),)):
                run_dioptra_job = importlib.import_module(run_dioptra_job_path.stem)

        except Exception as e:
            client.experiments.jobs.set_status(
                experiment_id=experiment_id, job_id=job_id, status="failed"
            )
            log.exception("Could not import run_dioptra_job.py")
            raise e

        # Execute the main function in the included script file.
        try:
            was_stopped = run_dioptra_job.main(
                plugins_dir=plugins_dir,
                enable_mlflow_tracking=True,
                dioptra_client=client,
                logger=log,
            )

            if was_stopped:
                # We don't have a job status value for "stopped" or "killed"...
                client.experiments.jobs.set_status(
                    experiment_id=experiment_id, job_id=job_id, status="failed"
                )
            else:
                client.experiments.jobs.set_status(
                    experiment_id=experiment_id, job_id=job_id, status="finished"
                )

        except Exception as e:
            client.experiments.jobs.set_status(
                experiment_id=experiment_id, job_id=job_id, status="failed"
            )
            log.exception("Error running job")
            raise e
