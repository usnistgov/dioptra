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
from pathlib import Path
from typing import ClassVar, Final, TypeVar, Any

from .base import CollectionClient, IllegalArgumentError

T = TypeVar("T")

JOB_FILES_DOWNLOAD: Final[str] = "jobFilesDownload"
ENTRYPOINT_VALIDATION: Final[str] = "entrypointValidate"


class WorkflowsCollectionClient(CollectionClient[T]):
    """The client for managing Dioptra's /workflows collection.

    Attributes:
        name: The name of the collection.
    """

    name: ClassVar[str] = "workflows"

    def download_job_files(
        self,
        job_id: str | int,
        file_type: str = "tar_gz",
        output_dir: Path | None = None,
        file_stem: str = "job_files",
    ) -> Path:
        """
        Download a compressed file archive containing the files needed to execute a
        submitted job.

        The downloaded file's name is the file stem followed by the file extension
        corresponding to the specified file type. For example, if the file stem is
        "job_files" and the file type is "tar_gz", the downloaded file will be named
        "job_files.tar.gz".

        Args:
            job_id: The job id, an integer.
            file_type: The type of file to download. Options are "tar_gz" and "zip".
                Optional, defaults to "tar_gz".
            output_dir: The directory where the downloaded file should be saved. The
                directory will be created if it does not exist. If None, the file will
                be saved in the current working directory. Optional, defaults to None.
            file_stem: The file stem to use for naming the downloaded file. Optional,
                defaults to "job_files".

        Returns:
            The path to the downloaded file.

        Raises:
            IllegalArgumentError: If the file type is not one of "tar_gz" or "zip".
        """
        file_extensions = {
            "tar_gz": ".tar.gz",
            "zip": ".zip",
        }

        if (output_ext := file_extensions.get(file_type)) is None:
            raise IllegalArgumentError(
                'Illegal value for file_type (reason: must be one of "tar_gz", "zip"): '
                f"{file_type}."
            )

        job_files_path = (
            Path(file_stem).with_suffix(output_ext)
            if output_dir is None
            else Path(output_dir, file_stem).with_suffix(output_ext)
        )
        params = {"jobId": job_id, "fileType": file_type}

        return self._session.download(
            self.url, JOB_FILES_DOWNLOAD, output_path=job_files_path, params=params
        )
    
    def validate_entrypoint(
        self,
        task_graph: str,
        plugins: list[int],
        entrypoint_parameters: list[dict[str, Any]],
    ):
        payload = {
            "taskGraph" : task_graph,
            "plugins": plugins,
            "parameters": entrypoint_parameters,
        }

        return self._session.post(
            self.url, ENTRYPOINT_VALIDATION, json_=payload
        )
