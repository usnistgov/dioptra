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
from __future__ import annotations

import tarfile
from pathlib import Path
from tarfile import TarFile, TarInfo
from typing import IO, List, Optional, Union

import structlog
from structlog.stdlib import BoundLogger

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class UnsafeArchiveMemberPath(Exception):
    """
    Instances represent unsafe paths in an archive file.  E.g. those which
    contain "..", which might cause files to be written outside a target
    directory.
    """

    def __init__(self, archive_member_path: Union[str, Path]):
        message = "Unsafe archive member path: " + str(archive_member_path)
        super().__init__(message)

        self.archive_member_path = Path(archive_member_path)


class IOFileService(object):
    def safe_extract_archive(
        self,
        output_dir: Union[str, Path],
        archive_file_path: Optional[Union[str, Path]] = None,
        archive_fileobj: Optional[IO[bytes]] = None,
        preserve_paths: bool = False,
        **kwargs,
    ) -> List[str]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        extracted_files: List[str] = []

        with self._tarfile_open(
            archive_file_path, archive_fileobj, log=log
        ) as f_archive:
            for archive_file_info in f_archive:
                safe_file_path: Optional[Path] = self.sanitize_file_path(
                    filepath=archive_file_info.name,
                    path_prefix=output_dir,
                    preserve_paths=preserve_paths,
                    log=log,
                )

                if safe_file_path is None:
                    raise UnsafeArchiveMemberPath(archive_file_info.name)

                response: Optional[str] = self.safe_extract_archive_file(
                    file_path=safe_file_path,
                    f_archive=f_archive,
                    archive_file_info=archive_file_info,
                    log=log,
                )

                if response is not None:
                    extracted_files.append(response)

        return extracted_files

    @staticmethod
    def safe_extract_archive_file(
        file_path: Path,
        f_archive: TarFile,
        archive_file_info: TarInfo,
        **kwargs,
    ) -> Optional[str]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        if not archive_file_info.isfile():
            return None

        f_archive_file = f_archive.extractfile(archive_file_info)

        if f_archive_file is None:
            return None

        file_path.parent.mkdir(parents=True, exist_ok=True)

        with file_path.open("wb") as f:
            f.write(f_archive_file.read())

        log.debug("File extracted from archive", extracted_file=str(file_path))

        return str(file_path)

    @staticmethod
    def sanitize_file_path(
        filepath: Union[str, Path],
        path_prefix: Optional[Union[str, Path]] = None,
        preserve_paths: bool = False,
        **kwargs,
    ) -> Optional[Path]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841

        filepath = Path(filepath)

        if preserve_paths:
            # Let's say we are willing to drop drive letters and root
            # directory.  But any ".." path component is considered
            # unsafe.  Also, if the path is only an anchor, it is unsafe.
            filepath_parts = filepath.parts

            if filepath.anchor:
                # The "anchor" is a combination of windows drive letter
                # (if any), and root path (if any).  Part 0 always contains the
                # anchor, if present.
                filepath_parts = filepath_parts[1:]

            safe_filepath: Optional[Union[str, Path]]
            if len(filepath_parts) == 0 or ".." in filepath_parts:
                safe_filepath = None
            else:
                safe_filepath = Path(*filepath_parts)

        else:
            safe_filepath = filepath.name

        if safe_filepath is None:
            safe_path = None
        else:
            safe_path = Path(path_prefix or Path.cwd()) / safe_filepath

        return safe_path

    @staticmethod
    def _tarfile_open(
        file_path: Optional[Union[str, Path]] = None,
        fileobj: Optional[IO[bytes]] = None,
        **kwargs,
    ) -> TarFile:
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841

        def open_file_path() -> TarFile:
            return tarfile.open(name=file_path, mode="r:*")

        def open_fileobj() -> TarFile:
            return tarfile.open(fileobj=fileobj)

        if fileobj is not None:
            return open_fileobj()

        return open_file_path()
