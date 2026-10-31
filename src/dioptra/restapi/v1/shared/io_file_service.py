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
import json
import math
import subprocess
import sys
import tarfile
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from tempfile import TemporaryDirectory
from time import monotonic
from typing import IO, Any, cast

import structlog
from structlog.stdlib import BoundLogger

LOGGER: BoundLogger = structlog.stdlib.get_logger()

CHUNK_SIZE = 64 * 1024
MAX_ARCHIVE_BYTES = 100 * 1024 * 1024
MAX_TOTAL_BYTES = 500 * 1024 * 1024
MAX_FILE_BYTES = 50 * 1024 * 1024
MAX_ENTRIES = 10_000
MAX_METADATA_BYTES = 1024 * 1024
MAX_TOTAL_METADATA_BYTES = 16 * 1024 * 1024
MAX_HEADER_RECORDS = 30_000


@dataclass(frozen=True)
class ArchiveLimits:
    """Per-extraction budgets, including headers not yielded by tarfile.

    Metadata includes its padded body and 512-byte header. The expanded budget
    additionally allows padding for each raw header and the two end markers.
    These are byte/work limits, not a bound on all decompressor memory.
    """

    archive_bytes: int = MAX_ARCHIVE_BYTES
    file_bytes: int = MAX_FILE_BYTES
    total_bytes: int = MAX_TOTAL_BYTES
    entries: int = MAX_ENTRIES
    metadata_bytes: int = MAX_METADATA_BYTES
    total_metadata_bytes: int = MAX_TOTAL_METADATA_BYTES
    header_records: int = MAX_HEADER_RECORDS
    chunk_size: int = CHUNK_SIZE

    def __post_init__(self) -> None:
        if any(type(value) is not int or value <= 0 for value in asdict(self).values()):
            raise ValueError("Archive limits must be positive integers.")

    @property
    def expanded_bytes(self) -> int:
        return (
            self.total_bytes
            + self.total_metadata_bytes
            + 512 * (self.header_records + 2)
        )


def _default_limits() -> ArchiveLimits:
    # Preserve the service's existing configurable/monkeypatched content limits.
    return ArchiveLimits(
        archive_bytes=MAX_ARCHIVE_BYTES,
        file_bytes=MAX_FILE_BYTES,
        total_bytes=MAX_TOTAL_BYTES,
        entries=MAX_ENTRIES,
        metadata_bytes=MAX_METADATA_BYTES,
        total_metadata_bytes=MAX_TOTAL_METADATA_BYTES,
        header_records=MAX_HEADER_RECORDS,
        chunk_size=CHUNK_SIZE,
    )


class _ExpandedReader:
    """Limit reads before passing sizes to the uncompressed tar stream."""

    def __init__(self, source: IO[bytes], limit: int) -> None:
        self.source = source
        self.remaining = limit

    def read(self, size: int = -1) -> bytes:
        if size < 0 or size > self.remaining:
            raise ValueError("Import archive exceeds the expanded size limit.")
        data = self.source.read(size)
        self.remaining -= len(data)
        return data

    def seek(self, offset: int, whence: int = 0) -> int:
        if whence != 0:
            raise ValueError("Import archive requires an unsupported seek.")
        distance = offset - self.tell()
        if distance < 0:
            return self.source.seek(offset)
        # Account for skipped padding/content instead of letting a decompressor
        # consume an unchecked forward seek internally.
        while distance:
            chunk = self.read(min(distance, CHUNK_SIZE))
            if not chunk:
                raise tarfile.ReadError("unexpected end of data")
            distance -= len(chunk)
        return self.tell()

    def tell(self) -> int:
        return self.source.tell()

    def close(self) -> None:
        self.source.close()


def _bounded_tarinfo(limits: ArchiveLimits) -> type[tarfile.TarInfo]:
    metadata_bytes = 0
    header_records = 0
    metadata_types = {
        tarfile.XHDTYPE,
        tarfile.XGLTYPE,
        tarfile.SOLARIS_XHDTYPE,
        tarfile.GNUTYPE_LONGNAME,
        tarfile.GNUTYPE_LONGLINK,
    }

    class BoundedTarInfo(tarfile.TarInfo):
        def _proc_member(self, archive: Any) -> tarfile.TarInfo:
            # This dispatch hook runs after each fixed 512-byte header, before
            # tarfile reads its extension body. frombuf() is insufficient: patched
            # Python versions use a private _frombuf() for recursive headers.
            # Keep the hook covered by PAX/GNU tests on supported Python versions.
            nonlocal metadata_bytes, header_records
            if not isinstance(archive.fileobj, _ExpandedReader):
                archive.fileobj = _ExpandedReader(
                    archive.fileobj, limits.expanded_bytes - 512
                )
            header_records += 1
            if header_records > limits.header_records:
                raise ValueError("Import archive contains too many header records.")
            if self.size < 0:
                raise ValueError("Import archive contains a negative entry size.")
            if self.type == tarfile.GNUTYPE_SPARSE:
                raise ValueError("Import archive contains an unsafe entry.")
            if self.type in metadata_types:
                size = 512 + ((self.size + 511) // 512) * 512
                if size > limits.metadata_bytes:
                    raise ValueError(
                        "Import archive metadata exceeds the record size limit."
                    )
                metadata_bytes += size
                if metadata_bytes > limits.total_metadata_bytes:
                    raise ValueError(
                        "Import archive metadata exceeds the total size limit."
                    )
            return cast(tarfile.TarInfo, super()._proc_member(archive))  # type: ignore[misc]

    return BoundedTarInfo


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
        limits: ArchiveLimits | None = None,
    ) -> int:
        """Copy one file into a private import directory; return bytes written.

        Callers own the temporary directory, cleanup, and total/entry counters.
        The optional callback lets multipart imports hash the bytes as they copy.
        """
        check_deadline(deadline)
        limits = limits or _default_limits()
        path = IOFileService.relative_import_path(filename)
        if not path.parts:
            raise ValueError("Import file must have a filename.")
        target = output_dir.resolve().joinpath(*path.parts)
        if target.resolve() != target:
            raise ValueError("Import path contains a symlink.")
        size = 0
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.is_dir():
                raise ValueError(
                    "Import contains a duplicate file or file/directory conflict."
                )
            with target.open("xb") as output:
                while chunk := source.read(limits.chunk_size):
                    check_deadline(deadline)
                    size += len(chunk)
                    if size > limits.file_bytes:
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
        *,
        limits: ArchiveLimits | None = None,
        **kwargs,
    ) -> list[str]:
        """Extract in a supervised process into the caller's private staging dir.

        The parser and extraction worker is killed and reaped on timeout, before
        the caller can clean up its directory. Preparing the bounded local input
        uses cooperative checks; callers must provide a local, nonblocking stream.
        The caller continues to own cleanup and publishing/transaction rollback.
        """
        if not math.isfinite(timeout_seconds) or timeout_seconds < 0:
            raise ValueError("Archive timeout must be finite and nonnegative.")
        deadline = monotonic() + timeout_seconds
        check_deadline(deadline)
        limits = limits or _default_limits()
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        with TemporaryDirectory(prefix="dioptra-archive-") as work_dir:
            work = Path(work_dir)
            input_path = work / "input.tar"
            if archive_fileobj is not None:
                self._copy_archive(archive_fileobj, input_path, limits, deadline)
            elif archive_file_path is not None:
                with Path(archive_file_path).open("rb") as source:
                    self._copy_archive(source, input_path, limits, deadline)
            else:
                raise ValueError("An archive file or file object is required.")
            spec_path = work / "request.json"
            result_path = work / "result.json"
            spec_path.write_text(
                json.dumps(
                    {
                        "input": str(input_path),
                        "output": str(Path(output_dir).resolve()),
                        "preserve_paths": preserve_paths,
                        "strip_root": strip_root,
                        "deadline": deadline,
                        "limits": asdict(limits),
                        "result": str(result_path),
                    }
                ),
                encoding="utf-8",
            )
            check_deadline(deadline)
            # Running this file directly avoids importing Flask's application
            # factory in the worker. -I also excludes user startup/PYTHONPATH code.
            with subprocess.Popen(
                [sys.executable, "-I", str(Path(__file__).resolve()), str(spec_path)],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ) as process:
                try:
                    process.wait(timeout=max(0, deadline - monotonic()))
                except subprocess.TimeoutExpired as error:
                    process.kill()
                    process.wait()
                    raise ValueError("Import archive extraction timed out.") from error
                finally:
                    if process.poll() is None:
                        process.kill()
                        process.wait()
            check_deadline(deadline)
            if process.returncode != 0 or not result_path.is_file():
                raise ValueError("Import archive extraction worker failed.")
            # Neither a pipe nor a partially written result can outlive the wait.
            with result_path.open("rb") as result_file:
                raw = result_file.read(
                    limits.total_metadata_bytes * 2 + 1024 * limits.entries + 65537
                )
            if (
                len(raw)
                > limits.total_metadata_bytes * 2 + 1024 * limits.entries + 65536
            ):
                raise ValueError(
                    "Import archive extraction result exceeds the size limit."
                )
            result = json.loads(raw)
            check_deadline(deadline)
            if "error" in result:
                raise ValueError(result["error"])
            extracted_files: list[str] = result["files"]
        for path in extracted_files:
            log.debug("File extracted from archive", extracted_file=path)
        return extracted_files

    @staticmethod
    def _copy_archive(
        source: IO[bytes], destination: Path, limits: ArchiveLimits, deadline: float
    ) -> None:
        size = 0
        with destination.open("xb") as output:
            while True:
                check_deadline(deadline)
                chunk = source.read(
                    min(limits.chunk_size, limits.archive_bytes - size + 1)
                )
                if not chunk:
                    break
                size += len(chunk)
                if size > limits.archive_bytes:
                    raise ValueError("Import archive exceeds the size limit.")
                output.write(chunk)
        check_deadline(deadline)

    def _extract_archive(
        self,
        output_dir: str | Path,
        archive_file_path: str | Path,
        preserve_paths: bool,
        strip_root: bool,
        deadline: float,
        limits: ArchiveLimits,
    ) -> list[str]:
        """Worker-only parser/extractor; never call in a request-serving process."""
        extracted_files: list[str] = []
        output_dir = Path(output_dir).resolve()
        root = None
        count = 0
        total_bytes = 0

        with tarfile.open(
            name=archive_file_path, mode="r:*", tarinfo=_bounded_tarinfo(limits)
        ) as f_archive:
            for count, member in enumerate(f_archive, start=1):
                check_deadline(deadline)
                if count > limits.entries:
                    raise ValueError("Import contains too many entries.")
                # We use explicit TarInfo objects and reject links, so no member
                # lookup is needed. Avoid retaining a PAX dictionary per file.
                f_archive.members.clear()  # type: ignore[attr-defined]

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

                if member.size < 0 or member.size > limits.file_bytes:
                    raise ValueError("Import file exceeds the size limit.")

                source = f_archive.extractfile(member)
                if source is None:
                    raise ValueError("Import archive contains an unreadable file.")

                with source:
                    total_bytes += self.write_file(
                        output_dir,
                        safe_file_path.relative_to(output_dir).as_posix(),
                        source,
                        remaining_bytes=limits.total_bytes - total_bytes,
                        deadline=deadline,
                        limits=limits,
                    )

                extracted_files.append(str(safe_file_path))

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


def _archive_worker(spec_path: str) -> None:
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    result_path = Path(spec["result"])
    result: dict[str, list[str] | str]
    try:
        files = IOFileService()._extract_archive(
            spec["output"],
            spec["input"],
            spec["preserve_paths"],
            spec["strip_root"],
            spec["deadline"],
            ArchiveLimits(**spec["limits"]),
        )
        result = {"files": files}
    except Exception as error:
        result = {"error": str(error)[:4096] or type(error).__name__}
    temporary = result_path.with_suffix(".tmp")
    temporary.write_text(json.dumps(result), encoding="utf-8")
    temporary.replace(result_path)


if __name__ == "__main__":
    _archive_worker(sys.argv[1])
