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
"""Read and publish caller-owned deployment files without following symbolic links.

All operations retain descriptor/name checks and single-link regular-file checks.
Mutating callers hold the deployment lock. Permission repair changes modes only,
prints a warning and preserves bytes and ownership. Validation callers disable
repair so that inspection cannot silently fix an unsafe installation.
"""

import fcntl
import hashlib
import json
import os
import secrets
import stat
import sys
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path


def absolute(path: Path) -> Path:
    """Make a caller path absolute without resolving symbolic links.

    Args:
        path: Path relative to the current working directory, or an absolute path.

    Returns:
        Absolute normalized spelling; later descriptor-based opens reject links.
    """
    return Path(os.path.abspath(path))


@contextmanager
def directory(path: Path) -> Iterator[int]:
    """Keep a safely opened directory available for descriptor-relative operations.

    Args:
        path: Directory path; all components must be real directories owned by the
            caller.

    Yields:
        Directory descriptor, closed with intermediate descriptors on exit.

    Raises:
        ValueError: Ownership, type or name-to-descriptor identity differs.
        OSError: A component is missing, inaccessible or a symbolic link.
    """
    path = absolute(path)
    with ExitStack() as opened:
        fd = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        opened.callback(os.close, fd)
        for part in path.parts[1:]:
            fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            opened.callback(os.close, fd)
        identity(fd, path, is_directory=True)
        yield fd
        identity(fd, path, is_directory=True)


def identity(fd: int, path: Path, *, is_directory: bool = False) -> os.stat_result:
    """Require an open descriptor to match its expected caller-owned object.

    Args:
        fd: Open descriptor; the caller retains responsibility for closing it.
        path: Expected name, inspected without following links.
        is_directory: Require a directory instead of a single-link regular file when
            True.

    Returns:
        Current descriptor metadata.

    Raises:
        ValueError: Type, hard-link count, ownership or name/inode identity is unsafe.
        OSError: Descriptor or path metadata cannot be inspected.
    """
    info = os.fstat(fd)
    named = path.lstat()
    correct_type = (
        stat.S_ISDIR(info.st_mode) if is_directory else stat.S_ISREG(info.st_mode)
    )
    if not correct_type or (not is_directory and info.st_nlink != 1):
        raise ValueError(
            f"{path}: expected {'directory' if is_directory else 'single-link regular file'}"
        )
    if info.st_uid != os.geteuid():
        raise ValueError(f"{path}: invoking account must own the object")
    if (info.st_dev, info.st_ino) != (named.st_dev, named.st_ino):
        raise ValueError(f"{path}: path changed during access")
    return info


def mode(fd: int, path: Path, expected: int, *, repair: bool) -> None:
    """Check or repair a known opened object's POSIX permissions.

    When repair is enabled, change only the permission bits, synchronize the descriptor
    and report the old and new modes to stderr. Otherwise require the existing mode to
    match. The caller must already have checked the object's identity and ownership.

    Args:
        fd: Already validated open file/directory descriptor.
        path: Name used in warnings and errors.
        expected: Exact permission bits, for example 0600 for a private file.
        repair: Permit permission repairs when True; False requires compliant inputs
            without changing them.

    Returns:
        None.

    Raises:
        ValueError: The mode differs and repair is disabled.
    """
    before = os.fstat(fd)
    old = stat.S_IMODE(before.st_mode)
    if old == expected:
        return
    if not repair:
        raise ValueError(f"{path}: mode {old:04o}; expected {expected:04o}")
    os.fchmod(fd, expected)
    after = os.fstat(fd)
    if stat.S_IMODE(after.st_mode) != expected or (before.st_uid, before.st_gid) != (
        after.st_uid,
        after.st_gid,
    ):
        raise ValueError(
            f"{path}: could not confirm repaired mode and unchanged ownership"
        )
    os.fsync(fd)
    print(
        f"WARNING: repaired permissions for {path} from {old:04o} to {expected:04o}",
        file=sys.stderr,
    )


def ensure_directory(path: Path, expected: int = 0o700, *, repair: bool = True) -> None:
    """Create or check one protected deployment directory.

    Check directory identity, ownership and permissions. With repair enabled, create a
    missing directory or correct its permitted mode difference. With repair disabled, a
    missing or noncompliant directory fails without changes.

    Args:
        path: Directory to inspect or create beneath an existing safe parent.
        expected: Required permission bits; defaults to 0700.
        repair: Allow creation and safe permission corrections when True.

    Returns:
        None.
    """
    with directory(path.parent) as parent:
        if repair:
            try:
                os.mkdir(path.name, expected, dir_fd=parent)
            except FileExistsError:
                pass
            os.fsync(parent)
        with directory(path) as fd:
            identity(fd, path, is_directory=True)
            mode(fd, path, expected, repair=repair)


def read(path: Path, expected: int | None, *, repair: bool = False) -> bytes:
    """Read a caller-owned regular file with stable contents and a 16 MiB limit.

    Args:
        path: Input file; every path component must be free of symbolic links.
        expected: Exact required mode, or None to permit any mode without group/other
            write.
        repair: Permit permission repairs when True; False requires compliant inputs
            without changing them.

    Returns:
        Complete contents as bytes after stable identity/metadata checks.

    Raises:
        ValueError: Safety, permissions, stability or size checks fail.
        OSError: The file cannot be read or inspected.
    """
    with directory(path.parent) as parent:
        fd = os.open(
            path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent
        )
        with os.fdopen(fd, "rb") as stream:
            identity(fd, path)
            if expected is not None:
                mode(fd, path, expected, repair=repair)
            elif os.fstat(fd).st_mode & 0o022:
                raise ValueError(
                    f"{path}: configuration must not be group/other writable"
                )
            before = os.fstat(fd)
            content = stream.read(16 * 1024 * 1024 + 1)
            after = identity(fd, path)
            if _stable(before) != _stable(after) or len(content) > 16 * 1024 * 1024:
                raise ValueError(f"{path}: changed during access or exceeds 16 MiB")
            return content


def write(
    path: Path, content: bytes, expected: int = 0o600, *, replace: bool = False
) -> None:
    """Publish file bytes through a synchronized temporary file in the same directory.

    Write and synchronize a temporary file in the destination directory, then publish it
    with the requested permissions and synchronize the directory. A failed publication
    retains the private temporary file for inspection.

    The caller must hold the deployment lock when replacing a file. Skip this call if an
    identical existing file must keep its inode, because replacement creates a new file
    even when the bytes are unchanged.

    Args:
        path: Output path in an existing caller-owned directory.
        content: Complete bytes to publish.
        expected: Final POSIX mode, 0600 unless overridden.
        replace: Allow atomic replacement of a safely inspected existing regular file.

    Returns:
        None.

    Raises:
        FileExistsError: The destination exists and replacement is disabled.
        ValueError: The destination or its parent fails the file-safety checks.
        OSError: Writing, publication or synchronization fails.
    """
    with directory(path.parent) as parent:
        staging = path.with_name("." + path.name + "." + secrets.token_hex(16))
        fd = os.open(
            staging.name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=parent,
        )
        with os.fdopen(fd, "wb") as stream:
            identity(fd, staging)
            if stream.write(content) != len(content):
                raise OSError(f"{path}: incomplete write")
            stream.flush()
            os.fchmod(fd, expected)
            os.fsync(fd)
            identity(fd, staging)
            _publish(parent, staging, path, replace)
        os.fsync(parent)


def _publish(parent: int, staging: Path, path: Path, replace: bool) -> None:
    """Publish a staged file inside an already opened parent directory.

    Args:
        parent: Validated directory descriptor, retained by the caller.
        staging: Synchronized temporary file in that directory.
        path: Final output name in the same directory.
        replace: Atomically replace a safely inspected existing file when True.
            False claims an unused name with a hard link, then removes staging.

    Returns:
        None. The caller synchronizes the parent after publication.

    Raises:
        FileExistsError: Exclusive publication finds an existing output.
        ValueError: A replacement target fails identity/ownership/type checks.
        OSError: Opening, linking, renaming or unlinking fails.
    """
    if replace:
        try:
            fd = os.open(
                path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent
            )
        except FileNotFoundError:
            pass
        else:
            try:
                identity(fd, path)
            finally:
                os.close(fd)
        os.replace(staging.name, path.name, src_dir_fd=parent, dst_dir_fd=parent)
    else:
        os.link(
            staging.name,
            path.name,
            src_dir_fd=parent,
            dst_dir_fd=parent,
            follow_symlinks=False,
        )
        os.unlink(staging.name, dir_fd=parent)


def digest(content: bytes) -> str:
    """Hash bytes for content comparisons without exposing the bytes in output.

    Args:
        content: Public or private file content.

    Returns:
        Lowercase hexadecimal SHA-256 digest.
    """
    return hashlib.sha256(content).hexdigest()


def json_bytes(value: object) -> bytes:
    """Encode a state or completion record deterministically.

    Args:
        value: JSON-serializable record.

    Returns:
        UTF-8 sorted-key indented JSON with one trailing newline.
    """
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


@contextmanager
def lock(path: Path) -> Iterator[None]:
    """Hold the deployment mutation lock without waiting for another writer.

    Create the lock file if necessary and check or repair its mode to 0600. Close the
    descriptor on leaving the context to release the lock. Retain the file itself so
    later writers lock the same filesystem object.

    Args:
        path: Caller-owned lock-file path in an existing protected directory.

    Yields:
        None while the exclusive advisory lock is held.

    Raises:
        BlockingIOError: Another cooperating process holds the lock.
        ValueError: The file is unsafe.
        OSError: The file cannot be opened or locked.
    """
    with directory(path.parent) as parent:
        fd = _lock_descriptor(parent, path.name)
        with os.fdopen(fd, "rb+"):
            identity(fd, path)
            mode(fd, path, 0o600, repair=True)
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            identity(fd, path)
            yield


def _stable(info: os.stat_result) -> tuple:
    """Compare mutation-relevant metadata without treating read-updated atime as a write."""
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_uid,
        info.st_gid,
        info.st_nlink,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


def _lock_descriptor(parent: int, name: str) -> int:
    """Separate exclusive creation from existing-file opens for concurrent writers.

    Creation uses O_EXCL; an existing name is opened without O_CREAT. Neither
    branch follows links or replaces a file. The caller checks the opened
    descriptor's type, links, ownership and permissions before using the lock.
    """
    flags = os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK
    try:
        return os.open(name, flags | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=parent)
    except FileExistsError:
        return os.open(name, flags, dir_fd=parent)


def remove_verified(path: Path, expected: bytes) -> None:
    """Remove a live file only if it still matches the bytes already archived.

    The caller must hold the deployment lock and save a private archive first. Recheck
    the live file's identity and exact bytes, then unlink it and synchronize its parent
    directory. This function removes the live name; it does not create the backup.

    Args:
        path: Known live name to unlink after the caller has saved a protected archive.
        expected: Exact archived bytes required before removal.

    Returns:
        None.

    Raises:
        ValueError: The file contents or metadata no longer match.
        OSError: The file cannot be inspected or removed, or directory synchronization
            fails.
    """
    with directory(path.parent) as parent:
        fd = os.open(
            path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent
        )
        with os.fdopen(fd, "rb") as stream:
            before = identity(fd, path)
            if stream.read(len(expected) + 1) != expected or _stable(before) != _stable(
                identity(fd, path)
            ):
                raise ValueError(
                    f"{path}: contents changed before archived-input removal"
                )
            os.unlink(path.name, dir_fd=parent)
            os.fsync(parent)
