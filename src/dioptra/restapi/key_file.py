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
"""Select, provision and read persistent API signing keys.

``resolve_key_file`` selects a path, ``initialize_key`` creates or preserves a
key, and ``read_key`` validates an existing key for application startup.
Initialization and reading apply platform-specific filesystem checks.
"""

import logging
import os
import re
import secrets
import stat
import sys
from collections.abc import Iterator, Mapping
from contextlib import ExitStack, contextmanager
from pathlib import Path


def _is_windows() -> bool:
    return sys.platform == "win32"


def _resolve_key_file(path: object, environment: Mapping[str, str]) -> Path:
    """Select and normalize a path from the supplied environment snapshot."""
    selected = (
        path if path is not None else environment.get("DIOPTRA_RESTAPI_SECRET_KEY_FILE")
    )
    if selected is None:
        selected = Path.home() / ".local/share/dioptra/restapi/secret-key"
    if not isinstance(selected, (str, Path)) or not str(selected):
        raise ValueError("SECRET_KEY_FILE requires a nonempty filesystem path.")
    # abspath normalizes relative components without resolving symbolic links.
    return Path(os.path.abspath(Path(selected).expanduser()))


def resolve_key_file(path: str | Path | None = None) -> Path:
    """Select an absolute key path without following symbolic links.

    Args:
        path: Explicit path. If omitted, use ``DIOPTRA_RESTAPI_SECRET_KEY_FILE``
            or the per-user ``~/.local/share/dioptra/restapi/secret-key`` default.
            Relative paths use the invocation directory; tilde expansion is supported.

    Returns:
        The normalized absolute path. No files are accessed.

    Raises:
        ValueError: If the selected path is empty or is not a string or Path.
    """
    return _resolve_key_file(path, dict(os.environ))


def _key_error(path: Path, requirement: str) -> ValueError:
    return ValueError(
        f"Cannot use signing key at {path}: {requirement}. "
        "Initialize it explicitly with 'dioptra-api init-key --key-file PATH' "
        "using the API account before startup; inspect an existing file before rerunning."
    )


def _validate_key_content(content: bytes, path: Path) -> str:
    """Validate the bounded hexadecimal file contents and return the key without LF."""
    if re.fullmatch(rb"[0-9a-f]{64}\n?", content) is None:
        raise _key_error(
            path, "expected 64 lowercase ASCII hex characters and at most one LF"
        )
    return content[:64].decode("ascii")


@contextmanager
def _key_directory(path: Path, *, create: bool = False) -> Iterator[int]:
    """Open each parent directory without following symbolic links.

    Yield the selected parent directory descriptor and close all descriptors on
    exit. When creating, request mode 0777 for missing ancestors and 0700 for the
    immediate parent, subject to umask. Existing directory modes are left for the
    caller to check or repair. Reject a parent whose path no longer identifies the
    opened object. The caller must supply an absolute key path.
    """
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    with ExitStack() as directories:
        directory_fd = os.open(path.anchor, flags)
        directories.callback(os.close, directory_fd)
        for index, part in enumerate(path.parts[1:-1], start=1):
            if create:
                mode = 0o700 if index == len(path.parts) - 2 else 0o777
                try:
                    os.mkdir(part, mode, dir_fd=directory_fd)
                except FileExistsError:
                    pass
            directory_fd = os.open(part, flags, dir_fd=directory_fd)
            directories.callback(os.close, directory_fd)
        opened = os.fstat(directory_fd)
        current = path.parent.lstat()
        if (opened.st_dev, opened.st_ino) != (current.st_dev, current.st_ino):
            raise _key_error(path, "the key directory changed during access")
        yield directory_fd


def _check_key_file(fd: int, directory_fd: int, path: Path) -> os.stat_result:
    """Verify the open file and its names still identify the protected key.

    Compare descriptor and path identities, require one regular-file link and
    effective-user ownership, and return the open file's stat for further
    permission checks. The caller owns both descriptors.
    """
    opened = os.fstat(fd)
    named = os.stat(path.name, dir_fd=directory_fd, follow_symlinks=False)
    current = path.lstat()
    parent = os.fstat(directory_fd)
    current_parent = path.parent.lstat()
    if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
        raise _key_error(
            path,
            "expected a regular file with exactly one filesystem link; if initialization "
            "is concurrent or interrupted, inspect staging links and rerun after it completes",
        )
    if opened.st_uid != os.geteuid():
        raise _key_error(path, "the API account must own the key file")
    if any(
        (info.st_dev, info.st_ino) != (opened.st_dev, opened.st_ino)
        for info in (named, current)
    ) or (parent.st_dev, parent.st_ino) != (
        current_parent.st_dev,
        current_parent.st_ino,
    ):
        raise _key_error(path, "the key path changed during access")
    return opened


def _read_windows_development_key(path: Path) -> str:
    """Read and validate a development key using detectable Windows file checks.

    Reject links and changes to the named object during the bounded read. These
    checks do not provide POSIX no-follow or owner-only access guarantees.
    """
    for component in [*reversed(path.parents), path]:
        info = component.lstat()
        if stat.S_ISLNK(info.st_mode) or (
            getattr(info, "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        ):
            raise _key_error(path, "symbolic links are unsupported")
    original = path.lstat()
    if not stat.S_ISREG(original.st_mode) or original.st_nlink != 1:
        raise _key_error(
            path,
            "expected a regular file with exactly one filesystem link; if initialization "
            "is concurrent or interrupted, inspect staging links and rerun after it completes",
        )
    with path.open("rb", buffering=0) as stream:
        opened = os.fstat(stream.fileno())
        if (opened.st_dev, opened.st_ino) != (original.st_dev, original.st_ino):
            raise _key_error(path, "the key path changed during access")
        content = stream.read(66)
        current = path.lstat()
        if (opened.st_dev, opened.st_ino) != (current.st_dev, current.st_ino):
            raise _key_error(path, "the key path changed during access")
    return _validate_key_content(content, path)


def read_key(path: Path, *, development: bool = False) -> str:
    """Read an existing signing key under the selected platform's access rules.

    POSIX requires an API-owned 0700 parent, a regular single-link file owned by
    the effective UID, and mode 0400 or 0600. Native Windows allows development
    reads with reduced filesystem guarantees. All platforms require 64 lowercase
    hexadecimal characters with at most one trailing LF. Reading never creates,
    repairs or replaces a file.

    Args:
        path: Absolute path to the existing key file.
        development: Permit the reduced Windows development checks when True.

    Returns:
        The 64-character key, without the optional trailing LF.

    Raises:
        ValueError: If the file is missing, unreadable, unsafe or malformed, or if
            a production read is requested on native Windows.
    """
    if _is_windows() and not development:
        raise _key_error(path, "production is unsupported on native Windows")
    try:
        if _is_windows():
            return _read_windows_development_key(path)
        with _key_directory(path) as directory_fd:
            parent = os.fstat(directory_fd)
            if parent.st_uid != os.geteuid() or stat.S_IMODE(parent.st_mode) != 0o700:
                raise _key_error(
                    path, "the API account must own the parent directory with mode 0700"
                )
            fd = os.open(
                path.name,
                os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                dir_fd=directory_fd,
            )
            with os.fdopen(fd, "rb", buffering=0) as stream:
                opened = _check_key_file(stream.fileno(), directory_fd, path)
                if stat.S_IMODE(opened.st_mode) not in {0o400, 0o600}:
                    raise _key_error(path, "the key file requires mode 0400 or 0600")
                content = stream.read(66)
                current = _check_key_file(stream.fileno(), directory_fd, path)
                if (current.st_mode, current.st_uid, current.st_gid) != (
                    opened.st_mode,
                    opened.st_uid,
                    opened.st_gid,
                ):
                    raise _key_error(
                        path, "key ownership or permissions changed during access"
                    )
                return _validate_key_content(content, path)
    except OSError:
        raise _key_error(
            path,
            "the selected protected regular file must exist and be readable, without symbolic links",
        ) from None


def _repair_mode(fd: int, path: Path, mode: int) -> os.stat_result:
    """Set and verify the requested mode without changing the file UID or GID.

    Return the resulting stat and log any permission repair. The caller owns the
    descriptor and its lifetime; an unsuccessful verification raises ValueError.
    """
    original = os.fstat(fd)
    previous = stat.S_IMODE(original.st_mode)
    if previous != mode:
        os.fchmod(fd, mode)
    current = os.fstat(fd)
    if stat.S_IMODE(current.st_mode) != mode or (
        current.st_uid,
        current.st_gid,
    ) != (original.st_uid, original.st_gid):
        raise _key_error(path, "could not confirm permissions and unchanged ownership")
    if previous != mode:
        logging.getLogger(__name__).warning(
            "Repaired permissions for %s from %04o to %04o", path, previous, mode
        )
    return current


def _preserve_key(path: Path, directory_fd: int, resources: ExitStack) -> bool:
    """Validate and preserve an existing key through an owned descriptor.

    Return False if the file is absent. Otherwise check its identity, repair mode
    to 0600, validate its content, and return True. Register the descriptor with
    the caller's ExitStack so it stays open until the caller exits that stack.
    """
    try:
        fd = os.open(
            path.name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
            dir_fd=directory_fd,
        )
    except FileNotFoundError:
        return False
    resources.callback(os.close, fd)
    _check_key_file(fd, directory_fd, path)
    original = _repair_mode(fd, path, 0o600)
    with os.fdopen(fd, "rb", buffering=0, closefd=False) as stream:
        content = stream.read(66)
    _confirm_key_protection(fd, directory_fd, path, original)
    _validate_key_content(content, path)
    return True


def _confirm_key_protection(
    fd: int, directory_fd: int, path: Path, original: os.stat_result
) -> None:
    """Recheck file identity, mode 0600 and ownership after key operations."""
    current = _check_key_file(fd, directory_fd, path)
    if stat.S_IMODE(current.st_mode) != 0o600 or (current.st_uid, current.st_gid) != (
        original.st_uid,
        original.st_gid,
    ):
        raise _key_error(path, "could not confirm mode 0600 and unchanged ownership")


def _remove_owned_staging(fd: int, directory_fd: int, staging: Path) -> None:
    """Remove only the still-matching staging name while its descriptor is open."""
    try:
        named = os.stat(staging.name, dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        return
    opened = os.fstat(fd)
    if (named.st_dev, named.st_ino) != (opened.st_dev, opened.st_ino):
        raise _key_error(staging, "staging changed; preserved the unrelated object")
    os.unlink(staging.name, dir_fd=directory_fd)


def _write_key(fd: int, content: bytes) -> None:
    """Write and synchronize the complete key before publication.

    The caller owns the descriptor. This function closes its stream buffers before
    returning and raises if writing, flushing, synchronization or closure fails.
    """
    with os.fdopen(fd, "wb", closefd=False) as stream:
        if stream.write(content) != len(content):
            raise OSError("could not write the complete signing key")
        stream.flush()
        os.fsync(fd)


def _publish_staged_key(
    path: Path, staging: Path, fd: int, directory_fd: int, resources: ExitStack
) -> bool:
    """Link a complete staging file without replacing a competing key.

    Return True when the final name is published and still needs finalization.
    If another initializer wins, remove this attempt's staging, validate the
    winning key and return False. The caller owns both descriptors and the stack;
    a winning key's descriptor is registered there for the same lifetime.
    """
    try:
        os.link(
            staging.name,
            path.name,
            src_dir_fd=directory_fd,
            dst_dir_fd=directory_fd,
            follow_symlinks=False,
        )
    except FileExistsError:
        _remove_owned_staging(fd, directory_fd, staging)
        if not _preserve_key(path, directory_fd, resources):
            raise _key_error(path, "the competing key disappeared") from None
        return False
    return True


def initialize_key(path: Path, *, development: bool = False) -> bool:
    """Create a persistent random key or preserve an existing valid key.

    On POSIX, create or repair the immediate API data directory to 0700 and its
    key file to 0600, without changing ownership or existing contents. Higher
    ancestors retain their permissions. Selecting a custom path authorizes this
    parent repair. An existing file is preserved even when its contents are
    invalid. Its permissions are repaired before content validation, so a repair
    can remain after validation rejects the file. A completed published key
    survives finalization failures and must be inspected before rerunning.

    Native Windows uses ordinary access controls without an owner-only ACL claim.
    The development option does not weaken POSIX filesystem checks.

    Args:
        path: Key file path, normalized to an absolute path before use.
        development: Permit native Windows initialization with reduced filesystem
            guarantees when True.

    Returns:
        True if a new key was created, or False if an existing valid key was kept.

    Raises:
        ValueError: If the file cannot be initialized or preserved safely, or if
            native Windows initialization is requested without development mode.
            Diagnostics do not include secret content.
    """
    path = resolve_key_file(path)
    if _is_windows():
        if not development:
            raise _key_error(
                path,
                "native Windows initialization requires --development; "
                "use Linux, macOS or a Linux container for production",
            )
        return _initialize_windows_development_key(path)

    published = False
    try:
        with ExitStack() as resources:
            directory_fd = resources.enter_context(_key_directory(path, create=True))
            parent = os.fstat(directory_fd)
            if parent.st_uid != os.geteuid():
                raise _key_error(path, "the API account must own the parent directory")
            _repair_mode(directory_fd, path.parent, 0o700)
            if _preserve_key(path, directory_fd, resources):
                return False

            staging = path.with_name(f".{path.name}.{secrets.token_hex(16)}.tmp")
            fd = os.open(
                staging.name,
                os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=directory_fd,
            )
            resources.callback(os.close, fd)
            try:
                _check_key_file(fd, directory_fd, staging)
                original = _repair_mode(fd, staging, 0o600)
                _write_key(fd, (secrets.token_hex(32) + "\n").encode("ascii"))
                _confirm_key_protection(fd, directory_fd, staging, original)
                if not _publish_staged_key(path, staging, fd, directory_fd, resources):
                    return False
                published = True
                _remove_owned_staging(fd, directory_fd, staging)
                os.fsync(directory_fd)
                _confirm_key_protection(fd, directory_fd, path, original)
                return True
            except BaseException:
                # Publication is the completion boundary for preserving the key.
                # Never remove the final name, including after partial finalization.
                if not published:
                    _remove_owned_staging(fd, directory_fd, staging)
                raise
    except (OSError, ValueError) as exc:
        if published:
            raise _key_error(
                path,
                "a complete key was published but finalization failed; "
                "inspect the key and any staging links, then rerun after "
                "initialization completes",
            ) from exc
        if isinstance(exc, ValueError):
            raise
        raise _key_error(
            path,
            "initialization failed; check ownership, permissions, no-follow "
            "directory access and same-directory hard-link support, then rerun",
        ) from exc


def _remove_owned_windows_staging(
    staging: Path, original: os.stat_result | None
) -> None:
    """Remove staging only when its device and inode match the saved identity.

    A missing original stat means no staging file was identified, so leave the
    name alone. The caller invokes this after the staging stream context exits.
    This path-based check preserves unrelated replacements without claiming
    POSIX race protection.
    """
    if original is None or not staging.exists():
        return
    current = staging.lstat()
    if (current.st_dev, current.st_ino) != (original.st_dev, original.st_ino):
        raise _key_error(staging, "staging changed; preserved unrelated file")
    staging.unlink()


def _initialize_windows_development_key(path: Path) -> bool:
    """Create or preserve a key using portable Windows development checks.

    Return True after publishing a new key and False for an existing valid key,
    including a competing initializer's key. Preserve a published key after a
    finalization failure; remove only a staging file still owned by this call.
    The checks do not claim POSIX race protection or owner-only permissions.
    """
    staging = path.with_name(f".{path.name}.{secrets.token_hex(16)}.tmp")
    original = None
    published = False
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Reuse the development reader's detectable link and type checks for an
        # existing file. Missing files alone allow a new staging attempt.
        if path.exists() or path.is_symlink():
            _read_windows_development_key(path)
            return False
        for component in [*reversed(path.parent.parents), path.parent]:
            info = component.lstat()
            if stat.S_ISLNK(info.st_mode) or (
                getattr(info, "st_file_attributes", 0)
                & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
            ):
                raise _key_error(path, "symbolic links are unsupported")
        try:
            with staging.open("xb") as stream:
                original = os.fstat(stream.fileno())
                content = (secrets.token_hex(32) + "\n").encode("ascii")
                if stream.write(content) != len(content):
                    raise OSError("could not write the complete signing key")
                stream.flush()
                os.fsync(stream.fileno())
            try:
                # Native Windows rename refuses an existing destination. Do not
                # replace this with os.replace, which would rotate a winning key.
                os.rename(staging, path)
            except FileExistsError:
                _read_windows_development_key(path)
                return False
            published = True
            _read_windows_development_key(path)
            return True
        finally:
            _remove_owned_windows_staging(staging, original)
    except (OSError, ValueError) as exc:
        if published:
            raise _key_error(
                path,
                "a complete key was published but finalization failed; inspect "
                "the key before rerunning",
            ) from exc
        if isinstance(exc, ValueError):
            raise
        raise _key_error(
            path, "development initialization failed; inspect and rerun"
        ) from exc
