"""Protect explicit key provisioning, preservation and publication failures."""

import os
import re
import stat

import pytest

from dioptra.restapi import key_file

POSIX = pytest.mark.skipif(
    os.name == "nt",
    reason="POSIX descriptor, link and permission guarantees need POSIX.",
)


@pytest.fixture
def selected(tmp_path):
    """Use an exclusive API data directory, avoiding system temporary symlinks."""
    return tmp_path.resolve() / "restapi" / "secret-key"


def test_create_and_preserve(selected):
    """Provision one random key and retain its bytes and identity on reruns.

    Explicit development provisioning is portable. Exactly 64 lowercase ASCII
    hexadecimal characters plus LF must be generated, and no rotation may occur.
    """
    assert key_file.initialize_key(selected, development=True)
    before = selected.stat()
    content = selected.read_bytes()
    assert re.fullmatch(rb"[0-9a-f]{64}\n", content)
    assert key_file.read_key(selected, development=True).encode() == content[:-1]
    assert not key_file.initialize_key(selected, development=True)
    assert selected.read_bytes() == content
    assert selected.stat().st_ino == before.st_ino
    assert list(selected.parent.iterdir()) == [selected]


@POSIX
def test_modes_ancestors_and_unrelated_data(selected, caplog):
    """Restrict only the selected API data directory and report real repairs.

    Existing ancestors and unrelated data keep their modes and contents. Both
    parent and key repairs must be explicit and valid reruns remain stable.
    """
    selected.parent.parent.chmod(0o755)
    selected.parent.mkdir(mode=0o750)
    unrelated = selected.parent / "dioptra.db"
    unrelated.write_bytes(b"other API data")
    unrelated.chmod(0o640)
    selected.write_bytes(b"a" * 64)
    selected.chmod(0o644)
    owner = selected.stat().st_uid, selected.stat().st_gid
    assert not key_file.initialize_key(selected)
    assert stat.S_IMODE(selected.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(selected.stat().st_mode) == 0o600
    assert (selected.stat().st_uid, selected.stat().st_gid) == owner
    assert selected.parent.parent.stat().st_mode & 0o777 == 0o755
    assert unrelated.read_bytes() == b"other API data"
    assert stat.S_IMODE(unrelated.stat().st_mode) == 0o640
    assert str(selected) in caplog.text
    assert "0644" in caplog.text and "0600" in caplog.text
    assert "0750" in caplog.text and "0700" in caplog.text
    caplog.clear()
    key_file.initialize_key(selected)
    assert "Repaired" not in caplog.text


@POSIX
def test_new_ancestors_follow_umask(selected):
    """Create missing ordinary ancestors under the process umask.

    The dedicated immediate parent alone requires 0700. A restrictive umask must
    also leave the generated key at exactly 0600 before its content is written.
    """
    path = selected.parent / "higher" / "restapi" / selected.name
    previous = os.umask(0o027)
    try:
        key_file.initialize_key(path, development=True)
    finally:
        os.umask(previous)
    assert path.parent.parent.stat().st_mode & 0o777 == 0o750
    assert path.parent.stat().st_mode & 0o777 == 0o700
    assert path.stat().st_mode & 0o7777 == 0o600


@pytest.mark.parametrize(
    "content",
    [b"", b"deploy123", b"a" * 63, b"A" * 64, b"a" * 64 + b"\r\n", b"b" * 100000],
)
def test_invalid_content_never_replaced(selected, content):
    """Preserve invalid supplied material for explicit operator inspection.

    Initialization rejects malformed or former-fallback content with setup
    guidance and never converts an existing invalid file into a fresh key.
    """
    selected.parent.mkdir(mode=0o700)
    selected.write_bytes(content)
    selected.chmod(0o600)
    with pytest.raises(ValueError, match="init-key") as caught:
        key_file.initialize_key(selected, development=True)
    assert selected.read_bytes() == content
    assert "deploy123" not in str(caught.value)
    assert "b" * 64 not in str(caught.value)
    assert list(selected.parent.iterdir()) == [selected]


@POSIX
def test_repair_precedes_content_validation(selected, caplog):
    """Leave a completed permission repair in place after invalid content fails.

    The initializer must promptly restrict a readable unsafe file before reading
    malformed content, and its diagnostic must not claim initialization succeeded.
    """
    selected.parent.mkdir(mode=0o700)
    selected.write_bytes(b"invalid")
    selected.chmod(0o644)
    with pytest.raises(ValueError):
        key_file.initialize_key(selected)
    assert selected.read_bytes() == b"invalid"
    assert selected.stat().st_mode & 0o7777 == 0o600
    assert "0644" in caplog.text and "0600" in caplog.text
    assert "Preserved" not in caplog.text


@POSIX
@pytest.mark.parametrize(
    "kind",
    [
        "hardlink",
        "symlink",
        "parent-link",
        "ancestor-link",
        "directory",
        "fifo",
        "foreign-owner",
    ],
)
def test_unsafe_objects_fail_before_file_repair(selected, kind, monkeypatch):
    """Reject redirected, nonregular or unowned objects without repairing them.

    Exactly one link, ordinary type, ownership and observed identity precede
    chmod. FIFOs must not block and an unsafe existing key must remain intact.
    """
    selected.parent.mkdir(mode=0o700)
    selected.write_bytes(b"a" * 64)
    selected.chmod(0o644)
    path = selected
    if kind == "hardlink":
        os.link(selected, selected.with_name("alias"))
    elif kind == "symlink":
        path = selected.with_name("alias")
        path.symlink_to(selected)
    elif kind in {"parent-link", "ancestor-link"}:
        alias = selected.parent.parent / "alias"
        target = selected.parent if kind == "parent-link" else selected.parent.parent
        alias.symlink_to(target, target_is_directory=True)
        path = (
            alias / selected.name
            if kind == "parent-link"
            else alias / selected.parent.name / selected.name
        )
    elif kind in {"directory", "fifo"}:
        selected.unlink()
        if kind == "directory":
            selected.mkdir(mode=0o755)
        else:
            os.mkfifo(selected, mode=0o644)
    else:
        real_fstat = os.fstat

        def foreign_file(fd):
            info = real_fstat(fd)
            if stat.S_ISREG(info.st_mode):
                values = list(info)
                values[4] = info.st_uid + 1
                return os.stat_result(values)
            return info

        monkeypatch.setattr(key_file.os, "fstat", foreign_file)
    before_mode = selected.stat().st_mode
    with pytest.raises(ValueError):
        key_file.initialize_key(path, development=True)
    assert selected.stat().st_mode == before_mode


@POSIX
@pytest.mark.parametrize("failure", ["write", "flush", "close"])
def test_prepublication_failure_cleans_only_owned_staging(
    selected, failure, monkeypatch
):
    """Never expose an incomplete final key after an injected operation failure.

    Failed writes, flushes and closes must remove this attempt's staging. An unrelated temporary file must remain untouched.
    """
    selected.parent.mkdir(mode=0o700)
    unrelated = selected.parent / ".unrelated.tmp"
    unrelated.write_bytes(b"retained")
    real_fdopen = os.fdopen

    def open_stream(*args, **kwargs):
        stream = real_fdopen(*args, **kwargs)
        real_write = stream.write
        real_flush = stream.flush
        real_close = stream.close

        def write(content):
            # Check actual protection when bytes first reach the real stream.
            assert os.fstat(stream.fileno()).st_mode & 0o7777 == 0o600
            assert selected.parent.stat().st_mode & 0o7777 == 0o700
            if failure == "write":
                real_write(content[:10])
                raise OSError("injected write failure")
            return real_write(content)

        def flush():
            # Restore before context-manager cleanup can call flush again.
            scoped.setattr(stream, "flush", real_flush)
            raise OSError("injected flush failure")

        def close():
            scoped.setattr(stream, "close", real_close)
            real_close()
            raise OSError("injected close failure")

        scoped.setattr(stream, "write", write)
        if failure == "flush":
            scoped.setattr(stream, "flush", flush)
        if failure == "close":
            scoped.setattr(stream, "close", close)
        return stream

    with monkeypatch.context() as scoped:
        scoped.setattr(key_file.os, "fdopen", open_stream)
        with pytest.raises(ValueError, match="initialization failed"):
            key_file.initialize_key(selected)
    assert not selected.exists()
    assert list(selected.parent.iterdir()) == [unrelated]
    assert unrelated.read_bytes() == b"retained"


@POSIX
@pytest.mark.parametrize("failure", ["file-sync", "publication"])
def test_synchronization_or_publication_failure(selected, failure, monkeypatch):
    """Remove owned staging after injected sync or no-replacement publication errors.

    These filesystem failures occur after the complete write. Neither may leave
    an incomplete final key or discard an unrelated temporary file.
    """
    selected.parent.mkdir(mode=0o700)
    unrelated = selected.parent / ".unrelated.tmp"
    unrelated.write_bytes(b"retained")

    def fail(*args, **kwargs):
        raise OSError("injected filesystem failure")

    monkeypatch.setattr(
        key_file.os, "fsync" if failure == "file-sync" else "link", fail
    )
    with pytest.raises(ValueError, match="initialization failed"):
        key_file.initialize_key(selected)
    assert not selected.exists()
    assert list(selected.parent.iterdir()) == [unrelated]
    assert unrelated.read_bytes() == b"retained"


@POSIX
@pytest.mark.parametrize("failure", ["staging-removal", "directory-sync"])
def test_published_key_survives_finalization_failure(selected, failure, monkeypatch):
    """Preserve a complete final key after an injected finalization failure.

    Publication may already have exposed the key to another process. Failure to
    unlink staging or sync its directory must return nonzero without rollback.
    """
    real_unlink = os.unlink
    real_fsync = os.fsync

    def unlink(*args, **kwargs):
        if failure == "staging-removal":
            raise OSError("injected unlink failure")
        return real_unlink(*args, **kwargs)

    def sync(fd):
        if failure == "directory-sync" and stat.S_ISDIR(os.fstat(fd).st_mode):
            raise OSError("injected directory synchronization failure")
        return real_fsync(fd)

    with monkeypatch.context() as scoped:
        scoped.setattr(key_file.os, "unlink", unlink)
        scoped.setattr(key_file.os, "fsync", sync)
        with pytest.raises(
            ValueError, match="complete key was published but finalization failed"
        ):
            key_file.initialize_key(selected)
    content = selected.read_bytes()
    assert re.fullmatch(rb"[0-9a-f]{64}\n", content)
    if failure == "staging-removal":
        assert selected.stat().st_nlink == 2
        with pytest.raises(ValueError, match="initialization.*completes"):
            key_file.read_key(selected)
        staging = next(path for path in selected.parent.iterdir() if path != selected)
        staging.unlink()
    assert not key_file.initialize_key(selected)
    assert selected.read_bytes() == content


@POSIX
@pytest.mark.parametrize("winner_finishing", [False, True])
def test_competing_publication_preserves_winner(
    selected, winner_finishing, monkeypatch
):
    """Validate a competing winner once without retrying or overwriting it.

    The injected competitor either has a final single-link key or is still
    removing staging. Only the former permits immediate preservation success.
    """
    real_link = os.link
    winner = b"b" * 64 + b"\n"

    def publish_winner(*args, **kwargs):
        selected.write_bytes(winner)
        selected.chmod(0o600)
        if winner_finishing:
            real_link(selected, selected.with_name("competitor-staging"))
        raise FileExistsError("injected competing winner")

    monkeypatch.setattr(key_file.os, "link", publish_winner)
    if winner_finishing:
        with pytest.raises(ValueError, match="one filesystem link"):
            key_file.initialize_key(selected)
        assert selected.stat().st_nlink == 2
    else:
        assert not key_file.initialize_key(selected)
        assert list(selected.parent.iterdir()) == [selected]
    assert selected.read_bytes() == winner


@POSIX
def test_replaced_staging_is_preserved(selected, monkeypatch):
    """Preserve an unrelated replacement at an attempt's staging name.

    An injected staging replacement before publication must prevent publishing
    or cleanup of that replacement, while leaving no final key behind.
    """
    real_write = key_file._write_key
    replacement = b"unrelated replacement"

    def replace(fd, content):
        real_write(fd, content)
        staging = next(selected.parent.iterdir())
        staging.unlink()
        staging.write_bytes(replacement)

    monkeypatch.setattr(key_file, "_write_key", replace)
    with pytest.raises(ValueError, match="staging changed"):
        key_file.initialize_key(selected)
    assert not selected.exists()
    assert next(selected.parent.iterdir()).read_bytes() == replacement


def test_windows_requires_explicit_development(selected, monkeypatch):
    """Require explicit consent to native-Windows development provisioning.

    A scoped platform replacement verifies policy dispatch only. It does not
    establish native-Windows rename, ACL or execution behavior on a POSIX host.
    """
    monkeypatch.setattr(key_file, "_is_windows", lambda: True)
    with pytest.raises(ValueError, match="--development"):
        key_file.initialize_key(selected)
    assert not selected.parent.exists()
    assert key_file.initialize_key(selected, development=True)
    content = selected.read_bytes()
    assert not key_file.initialize_key(selected, development=True)
    assert selected.read_bytes() == content


@POSIX
def test_protection_is_rechecked_before_publication(selected, monkeypatch):
    """Reject an injected permission change after writing but before publication.

    Required 0600 protection is a postcondition, not an assumption based on file
    creation. A changed staging file must never become the final signing key.
    """
    real_write = key_file._write_key

    def change_mode(fd, content):
        real_write(fd, content)
        os.fchmod(fd, 0o644)

    monkeypatch.setattr(key_file, "_write_key", change_mode)
    with pytest.raises(ValueError, match="0600"):
        key_file.initialize_key(selected)
    assert not selected.exists()
    assert not list(selected.parent.iterdir())
