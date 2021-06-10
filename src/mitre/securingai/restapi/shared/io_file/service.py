# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
import tarfile
from pathlib import Path
from tarfile import TarFile, TarInfo
from typing import BinaryIO, List, Optional, Union

import structlog
from structlog.stdlib import BoundLogger

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class IOFileService(object):
    def safe_extract_archive(
        self,
        output_dir: Union[str, Path],
        archive_file_path: Optional[str] = None,
        archive_fileobj: Optional[BinaryIO] = None,
        **kwargs,
    ) -> List[str]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        extracted_files: List[str] = []

        with self._tarfile_open(
            archive_file_path, archive_fileobj, log=log
        ) as f_archive:
            for archive_file_info in f_archive:
                safe_file_path: Path = self.sanitize_file_path(
                    filepath=archive_file_info.name,
                    path_prefix=output_dir,
                    log=log,
                )

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

        with file_path.open("wb") as f:
            f.write(f_archive_file.read())

        log.info("File extracted from archive", extracted_file=str(file_path))

        return str(file_path)

    @staticmethod
    def sanitize_file_path(
        filepath: Union[str, Path],
        path_prefix: Optional[Union[str, Path]] = None,
        **kwargs,
    ) -> Path:
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841

        path_prefix = path_prefix or Path.cwd()

        return Path(path_prefix) / Path(filepath).name

    @staticmethod
    def _tarfile_open(
        file_path: Optional[str] = None,
        fileobj: Optional[BinaryIO] = None,
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
