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
from typing import Any, ClassVar, Final, Literal, TypeVar

from .base import (
    CollectionClient,
    DioptraFile,
    IllegalArgumentError,
)

T1 = TypeVar("T1")
T2 = TypeVar("T2")
JOB_FILES_DOWNLOAD: Final[str] = "jobFilesDownload"
SIGNATURE_ANALYSIS: Final[str] = "pluginTaskSignatureAnalysis"
RESOURCE_IMPORT: Final[str] = "resourceImport"
DRAFT_COMMIT: Final[str] = "draftCommit"


class WorkflowsCollectionClient(CollectionClient[T1, T2]):
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

    def analyze_plugin_task_signatures(self, python_code: str) -> T1:
        """
        Requests signature analysis for the functions in an annotated python file.

        Args:
            python_code: The contents of the python file.
            filename: The name of the file.

        Returns:
            The response from the Dioptra API.

        """

        return self._session.post(
            self.url,
            SIGNATURE_ANALYSIS,
            json_={"pythonCode": python_code},
        )

    def import_resources(
        self,
        group_id: int,
        source: str | DioptraFile | list[DioptraFile],
        config_path: str | None = None,
        resolve_name_conflicts_strategy: Literal["fail", "overwrite"] | None = None,
    ):
        """
        Import resources from a archive file or git repository

        Args:
            group_id: The group to import resources into
            source: The source to import from. Can be a str containing a git url, a
                DioptraFile containing an archive file or a list[DioptraFile]
                containing resource files.
            config_path: The path to the toml configuration file in the import source.
                If None, the API will use "dioptra.toml" as the default. Defaults to
                None.
            resolve_name_conflicts_strategy: The strategy for resolving name conflicts.
                Either "fail" or "overwrite". If None, the API will use "fail" as the
                default. Defaults to None.

        Raises:
            IllegalArgumentError: If more than one import source is provided or if no
                import source is provided.
        """
        data: dict[str, Any] = {"group": str(group_id)}
        files_: dict[str, DioptraFile | list[DioptraFile]] = {}

        if not isinstance(source, (str, DioptraFile, list)):
            raise IllegalArgumentError(
                "Illegal type for source (reason: must be one of str, DioptraFile, "
                f"or list[DioptraFile]): {type(source)}"
            )

        if isinstance(source, list):
            if not all([isinstance(x, DioptraFile) for x in source]):
                illegal_types = set(
                    [type(x).__name__ for x in source if not isinstance(x, DioptraFile)]
                )
                raise IllegalArgumentError(
                    "Illegal type for source (reason: list contains type(s) other "
                    f"than DioptraFile): {', '.join(sorted(illegal_types))}"
                )

            data["sourceType"] = "upload_files"
            files_["files"] = source

        if isinstance(source, str):
            data["sourceType"] = "git"
            data["gitUrl"] = source

        if isinstance(source, DioptraFile):
            data["sourceType"] = "upload_archive"
            files_["archiveFile"] = source

        if config_path is not None:
            data["configPath"] = config_path

        if resolve_name_conflicts_strategy is not None:
            data["resolveNameConflictsStrategy"] = resolve_name_conflicts_strategy

        return self._session.post(
            self.url, RESOURCE_IMPORT, data=data, files=files_ or None
        )

    def commit_draft(
        self,
        draft_id: str | int,
    ) -> T1:
        """
        Commit a draft as a new resource snapshot.

        The draft can be a draft of a new resource or a draft modifications to an
        existing resource.

        Args:
            draft_id: The draft id, an intiger.

        Returns:
            A dictionary containing the contents of the new resource.
        """

        return self._session.post(self.url, DRAFT_COMMIT, str(draft_id))
