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
import uuid
from pathlib import Path
from typing import Final, cast
from urllib.parse import urlencode, urlparse, urlunparse

import requests
import structlog
from structlog.stdlib import BoundLogger

from dioptra.restapi.routes import (
    V1_AUTH_ROUTE,
    V1_EXPERIMENTS_ROUTE,
    V1_JOBS_ROUTE,
    V1_ROOT,
    V1_WORKFLOWS_ROUTE,
)
from dioptra.sdk.utilities.contexts import sys_path_dirs
from dioptra.sdk.utilities.paths import set_cwd

LOGGER: BoundLogger = structlog.stdlib.get_logger()

ENV_DIOPTRA_API: Final[str] = "DIOPTRA_API"
ENV_DIOPTRA_WORKER_USERNAME: Final[str] = "DIOPTRA_WORKER_USERNAME"
ENV_DIOPTRA_WORKER_PASSWORD: Final[str] = "DIOPTRA_WORKER_PASSWORD"
ENV_MLFLOW_S3_ENDPOINT_URL: Final[str] = "MLFLOW_S3_ENDPOINT_URL"

DOWNLOAD_CHUNK_SIZE: Final[int] = 10 * 1024
TAR_GZ_FILE_TYPE: Final[str] = "tar_gz"
TAR_GZ_EXTENSION: Final[str] = ".tar.gz"

JOB_FILES_DOWNLOAD_ENDPOINT: Final[str] = f"{V1_WORKFLOWS_ROUTE}/jobFilesDownload"


class SimpleDioptraClient(object):
    def __init__(self, username: str, password: str, api_url: str):
        self._api_scheme, self._api_netloc = self._extract_scheme_and_netloc(api_url)
        self._username = username
        self._password = password
        self._session: requests.Session | None = None

    @property
    def session(self) -> requests.Session:
        if self._session is None:
            self.login()

        return cast(requests.Session, self._session)

    def login(self) -> None:
        if self._session is None:
            self._session = requests.Session()

        response = self._session.post(
            self._build_url(f"{V1_AUTH_ROUTE}/login"),
            json={"username": self._username, "password": self._password},
        )
        response.raise_for_status()

    def download_job_files(self, job_id: int, output_dir: Path) -> Path:
        url = self._build_url(
            JOB_FILES_DOWNLOAD_ENDPOINT,
            query_params={"jobId": str(job_id), "fileType": TAR_GZ_FILE_TYPE},
        )
        job_files_path = (output_dir / "job_files").with_suffix(TAR_GZ_EXTENSION)
        with (
            self.session.get(url, stream=True) as response,
            job_files_path.open(mode="wb") as f,
        ):
            for chunk in response.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                f.write(chunk)

        return job_files_path

    def set_job_status(self, job_id: int, experiment_id: int, status: str) -> None:
        url = self._build_url(
            f"{V1_EXPERIMENTS_ROUTE}/{experiment_id}/jobs/{job_id}/status"
        )
        response = self.session.put(url, json={"status": status})
        response.raise_for_status()

    def set_job_mlflow_run_id(
        self, job_id: int, mlflow_run_id: str | uuid.UUID
    ) -> None:
        url = self._build_url(f"{V1_JOBS_ROUTE}/{job_id}/mlflowRun")
        payload = {
            "mlflowRunId": (
                mlflow_run_id.hex
                if isinstance(mlflow_run_id, uuid.UUID)
                else mlflow_run_id
            )
        }
        response = self.session.post(url, json=payload)
        response.raise_for_status()

    def _build_url(
        self, endpoint: str, query_params: dict[str, str] | None = None
    ) -> str:
        query_params = query_params or {}

        return urlunparse(
            (
                self._api_scheme,
                self._api_netloc,
                f"/{V1_ROOT}/{endpoint}",
                "",
                urlencode(query_params),
                "",
            )
        )

    @staticmethod
    def _extract_scheme_and_netloc(api_url: str) -> tuple[str, str]:
        parsed_api_url = urlparse(url=api_url)
        return parsed_api_url.scheme, parsed_api_url.netloc


def run_v1_dioptra_job(job_id: int, experiment_id: int) -> None:
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

    if (api_url := os.getenv(ENV_DIOPTRA_API)) is None:
        log.error(f"{ENV_DIOPTRA_API} environment variable is not set")
        raise ValueError(f"{ENV_DIOPTRA_API} environment variable is not set")

    # Instantiate a Dioptra client and login using worker's authentication details
    client = SimpleDioptraClient(username=username, password=password, api_url=api_url)

    # Set Dioptra Job status to "started"
    client.set_job_status(job_id=job_id, experiment_id=experiment_id, status="started")

    if os.getenv(ENV_MLFLOW_S3_ENDPOINT_URL) is None:
        client.set_job_status(
            job_id=job_id, experiment_id=experiment_id, status="failed"
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
        job_files_package = client.download_job_files(
            job_id=job_id, output_dir=working_dir
        )

        # Unpack the (trusted) tar.gz file in it.
        with tarfile.open(job_files_package, mode="r:*") as tar:
            tar.extractall(path=working_dir, filter="data")

        # Import the run_dioptra_job.py file as a module
        with sys_path_dirs(dirs=(str(working_dir),)):
            run_dioptra_job = importlib.import_module(run_dioptra_job_path.stem)

        # Execute the main function in the included script file.
        try:
            run_dioptra_job.main(
                plugins_dir=plugins_dir,
                enable_mlflow_tracking=True,
                dioptra_client=client,
                logger=log,
            )
            client.set_job_status(
                job_id=job_id, experiment_id=experiment_id, status="finished"
            )

        except Exception as e:
            client.set_job_status(
                job_id=job_id, experiment_id=experiment_id, status="failed"
            )
            log.exception("Error running job")
            raise e
