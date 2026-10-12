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
import tarfile
from collections.abc import Callable
from pathlib import Path, PurePosixPath, PureWindowsPath
from time import monotonic
from typing import IO

import structlog
from structlog.stdlib import BoundLogger

LOGGER: BoundLogger = structlog.stdlib.get_logger()

CHUNK_SIZE = 64 * 1024
MAX_ARCHIVE_BYTES = 100 * 1024 * 1024
MAX_TOTAL_BYTES = 500 * 1024 * 1024
MAX_FILE_BYTES = 50 * 1024 * 1024
MAX_ENTRIES = 10_000


def check_deadline(deadline: float) -> None:
    if monotonic() >= deadline:
        raise ValueError("Import archive extraction timed out.")


class UnsafeArchiveMemberPath(Exception):
    """
    Instances represent unsafe paths in an archive file.  E.g. those which
    contain "..", which might cause files to be written outside a target
    directory.
    """

    def __init__(self, archive_member_path: str | Path):
        message = "Unsafe archive member path: " + str(archive_member_path)
        super().__init__(message)

        self.archive_member_path = Path(archive_member_path)


class IOFileService(object):
    @staticmethod
    def relative_import_path(name: str, *, allow_parent: bool = False) -> PurePosixPath:
        """Validate portable relative paths without consulting the process cwd."""
        path = PurePosixPath(name)
        if (
            not name
            or path.is_absolute()
            or "\\" in name
            or ":" in name
            or any(ord(char) < 32 or ord(char) == 127 for char in name)
            or any(
                part.lower() == ".git" or PureWindowsPath(part).is_reserved()
                for part in path.parts
            )
            or (not allow_parent and ".." in path.parts)
        ):
            raise ValueError("Import path must be a safe relative path.")
        return path

    @staticmethod
    def resolve_import_path(root: Path, name: str, *, base: Path | None = None) -> Path:
        """Resolve config references, allowing '..' only within the import root."""
        path = IOFileService.relative_import_path(name, allow_parent=True)
        root = root.resolve()
        target = (base or root).joinpath(*path.parts).resolve()
        if not target.is_relative_to(root):
            raise ValueError("Import path escapes the import directory.")
        return target

    @staticmethod
    def write_file(
        output_dir: Path,
        filename: str,
        source: IO[bytes],
        *,
        remaining_bytes: int = MAX_TOTAL_BYTES,
        on_chunk: Callable[[bytes], None] | None = None,
        deadline: float = float("inf"),
    ) -> int:
        """Copy one file into a private import directory; return bytes written.

        Callers own the temporary directory, cleanup, and total/entry counters.
        The optional callback lets multipart imports hash the bytes as they copy.
        """
        check_deadline(deadline)
        path = IOFileService.relative_import_path(filename)
        if not path.parts:
            raise ValueError("Import file must have a filename.")
        target = output_dir.resolve().joinpath(*path.parts)
        if target.resolve() != target:
            raise ValueError("Import path contains a symlink.")
        size = 0
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as output:
                while chunk := source.read(CHUNK_SIZE):
                    check_deadline(deadline)
                    size += len(chunk)
                    if size > MAX_FILE_BYTES:
                        raise ValueError("Import file exceeds the size limit.")
                    if size > remaining_bytes:
                        raise ValueError("Import exceeds the total content size limit.")
                    output.write(chunk)
                    if on_chunk is not None:
                        on_chunk(chunk)
        except (FileExistsError, IsADirectoryError, NotADirectoryError) as error:
            raise ValueError(
                "Import contains a duplicate file or file/directory conflict."
            ) from error
        return size

    def safe_extract_archive(
        self,
        output_dir: str | Path,
        archive_file_path: str | Path | None = None,
        archive_fileobj: IO[bytes] | None = None,
        preserve_paths: bool = False,
        strip_root: bool = False,
        timeout_seconds: float = 120,
        **kwargs,
    ) -> list[str]:
        """Extract regular files with a fresh, cooperative extraction-time budget."""
        deadline = monotonic() + timeout_seconds
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        extracted_files: list[str] = []
        output_dir = Path(output_dir).resolve()
        root = None
        count = 0
        total_bytes = 0

        with tarfile.open(
            name=archive_file_path, fileobj=archive_fileobj, mode="r:*"
        ) as f_archive:
            for count, member in enumerate(f_archive, start=1):
                check_deadline(deadline)
                if count > MAX_ENTRIES:
                    raise ValueError("Import contains too many entries.")

                path = self.relative_import_path(member.name)
                if not (member.isdir() or member.isfile()) or member.issparse():
                    raise ValueError("Import archive contains an unsafe entry.")

                if strip_root:
                    path, root = self._strip_archive_root(
                        path, root, is_dir=member.isdir()
                    )

                safe_file_path = self.sanitize_file_path(
                    str(path), output_dir, preserve_paths=preserve_paths
                )
                if safe_file_path is None:
                    raise UnsafeArchiveMemberPath(member.name)

                if member.isdir():
                    safe_file_path.mkdir(parents=True, exist_ok=True)
                    continue

                if member.size < 0 or member.size > MAX_FILE_BYTES:
                    raise ValueError("Import file exceeds the size limit.")

                source = f_archive.extractfile(member)
                if source is None:
                    raise ValueError("Import archive contains an unreadable file.")

                with source:
                    total_bytes += self.write_file(
                        output_dir,
                        safe_file_path.relative_to(output_dir).as_posix(),
                        source,
                        remaining_bytes=MAX_TOTAL_BYTES - total_bytes,
                        deadline=deadline,
                    )

                extracted_files.append(str(safe_file_path))

                log.debug(
                    "File extracted from archive", extracted_file=str(safe_file_path)
                )

        check_deadline(deadline)
        if count == 0:
            raise ValueError("Import archive is empty.")
        return extracted_files

    @staticmethod
    def _strip_archive_root(
        path: PurePosixPath, root: str | None, *, is_dir: bool
    ) -> tuple[PurePosixPath, str]:
        if not path.parts or (len(path.parts) == 1 and not is_dir):
            raise ValueError("Repository archive must have one wrapper directory.")
        root = root or path.parts[0]
        if path.parts[0] != root:
            raise ValueError("Repository archive must have one wrapper directory.")
        return PurePosixPath(*path.parts[1:]), root

    @staticmethod
    def sanitize_file_path(
        filepath: str | Path,
        path_prefix: str | Path | None = None,
        preserve_paths: bool = False,
        **kwargs,
    ) -> Path | None:
        """Return a contained path (or basename), rejecting unsafe paths and links."""
        name = str(filepath) if preserve_paths else Path(filepath).name
        try:
            path = IOFileService.relative_import_path(name)
            root = Path(path_prefix or Path.cwd())
            target = root.joinpath(*path.parts)
            return (
                target
                if target.resolve() == root.resolve().joinpath(*path.parts)
                else None
            )
        except (ValueError, OSError, RuntimeError):
            return None
