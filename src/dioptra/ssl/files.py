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
"""Protect caller-selected certificate files with POSIX descriptor operations.

Directories must be trusted by their owner. No-follow opens and identity checks
reject detected replacements; they do not lock out an owner modifying a directory.
"""

import fcntl
import os
import stat
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path


def absolute(path: str | Path) -> Path:
    """Make a path absolute without resolving symbolic links.

    Args:
        path: File or directory path, interpreted relative to the working directory.

    Returns:
        An absolute path with redundant separators and parent components removed.
        Symbolic links remain unexamined so subsequent safe opens can reject them.
    """
    return Path(os.path.abspath(path))


@contextmanager
def directory(path: Path) -> Iterator[int]:
    """Open a directory without following symbolic links in any component.

    Check directory identity before yielding and again after normal completion. The
    owner must still be trusted not to change directory entries during access;
    descriptor-based opening does not prevent a trusted owner from making concurrent
    changes.

    Args:
        path: Directory to open. Relative paths use the current working directory.

    Yields:
        A directory file descriptor for use with descriptor-relative file operations.
        This context manager closes it and all intermediate descriptors on exit.

    Raises:
        OSError: A component is missing, inaccessible, or a symbolic link.
        ValueError: The named directory no longer identifies the opened directory.
    """
    path = absolute(path)
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    with ExitStack() as opened:
        fd = os.open(path.anchor, flags)
        opened.callback(os.close, fd)
        for part in path.parts[1:]:
            fd = os.open(part, flags, dir_fd=fd)
            opened.callback(os.close, fd)
        confirm(fd, path, directory=True)
        yield fd
        confirm(fd, path, directory=True)


def confirm(fd: int, path: Path, *, directory: bool = False) -> os.stat_result:
    """Check that an open descriptor still refers to the named file or directory.

    Args:
        fd: Open descriptor owned by the caller; this function does not close it.
        path: Expected name of the opened object, checked without following links.
        directory: Require a directory instead of a regular file with one hard link.

    Returns:
        The descriptor's current filesystem metadata.

    Raises:
        ValueError: The object has the wrong type, extra hard links, or a different
            device/inode from the named object.
        OSError: The descriptor or named object cannot be inspected.
    """
    info = os.fstat(fd)
    named = path.lstat()
    correct_type = (
        stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)
    )
    if not correct_type or (not directory and info.st_nlink != 1):
        raise ValueError(
            f"{path}: expected {'directory' if directory else 'single-link regular file'}"
        )
    if (info.st_dev, info.st_ino) != (named.st_dev, named.st_ino):
        raise ValueError(f"{path}: path changed during access")
    return info


def owned(info: os.stat_result, path: Path) -> None:
    """Require a directory owned by this process's user and protected from other writers.

    Args:
        info: Directory metadata obtained from an already opened descriptor.
        path: Directory name to include in an error message.

    Returns:
        None. Filesystem metadata is not changed.

    Raises:
        ValueError: The owner differs from the effective user, or group/other write
            permission is enabled.
    """
    if info.st_uid != os.geteuid() or info.st_mode & 0o022:
        raise ValueError(
            f"{path}: requires caller ownership and no group/other write access"
        )


def read(path: Path, *, private: bool = False) -> bytes:
    """Read a regular file of at most 16 MiB without following symbolic links.

    Inspect and read the file without repairing permissions or modifying contents.

    Args:
        path: File to read. Every parent directory must also be free of symbolic links.
        private: Require ownership by the effective user and mode 0400 or 0600. False
            permits public files without these extra owner/mode restrictions.

    Returns:
        The file contents as bytes. The file and its parent directories are closed
        before returning.

    Raises:
        ValueError: The file has extra hard links, violates private permissions, changes
            during the read, or exceeds the size limit.
        OSError: Opening, reading or inspecting the path fails.
    """
    path = absolute(path)
    with directory(path.parent) as parent:
        fd = os.open(
            path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent
        )
        with os.fdopen(fd, "rb") as stream:
            before = confirm(fd, path)
            if private and (
                before.st_uid != os.geteuid()
                or stat.S_IMODE(before.st_mode) not in {0o400, 0o600}
            ):
                raise ValueError(
                    f"{path}: private file requires caller ownership and mode 0400 or 0600"
                )
            content = stream.read(16 * 1024 * 1024 + 1)
            after = confirm(fd, path)
            if _stable(before) != _stable(after) or len(content) > 16 * 1024 * 1024:
                raise ValueError(
                    f"{path}: input changed during access or exceeds 16 MiB"
                )
            return content


def write_new(path: Path, content: bytes, mode: int) -> None:
    """Create and synchronize a file without replacing an existing name.

    A failed write can leave a partial output at the requested path. Retain it for
    inspection; a retry must use an unused name rather than overwrite the partial file.

    Args:
        path: Unused output path in a caller-owned directory without group/other write
            access. Symbolic links in the path are not permitted.
        content: Complete bytes to write.
        mode: Final POSIX permissions. The file is initially created with mode 0600.

    Returns:
        None after the file and parent directory have been synchronized.

    Raises:
        FileExistsError: The output name is already in use.
        ValueError: Directory ownership or file identity checks fail.
        OSError: Creation, writing, permission changes or synchronization fails.
    """
    path = absolute(path)
    with directory(path.parent) as parent:
        owned(os.fstat(parent), path.parent)
        fd = os.open(
            path.name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=parent,
        )
        with os.fdopen(fd, "wb") as stream:
            confirm(fd, path)
            if stream.write(content) != len(content):
                raise OSError(f"{path}: incomplete write")
            stream.flush()
            os.fchmod(fd, mode)
            os.fsync(fd)
            confirm(fd, path)
        os.fsync(parent)


@contextmanager
def lock(path: Path) -> Iterator[None]:
    """Hold an exclusive advisory lock while a caller updates signing history.

    Wait until other cooperating writers release the lock. Keep the lock file after
    releasing it: removing the name could let another writer create and lock a different
    file while an existing writer still holds the original.

    Args:
        path: Separate lock-file path in a caller-owned protected directory. An existing
            lock must be a caller-owned regular file with mode 0600 and one hard link.

    Yields:
        None while the lock is held. Closing its descriptor releases the lock.

    Raises:
        ValueError: The lock file or directory fails safety checks.
        OSError: The path cannot be opened or the operating system cannot lock it.
    """
    path = absolute(path)
    with directory(path.parent) as parent:
        owned(os.fstat(parent), path.parent)
        fd = _lock_descriptor(parent, path.name)
        with os.fdopen(fd, "rb+"):
            info = confirm(fd, path)
            if info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o600:
                raise ValueError(
                    f"{path}: lock requires caller ownership and mode 0600"
                )
            fcntl.flock(fd, fcntl.LOCK_EX)
            confirm(fd, path)
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
