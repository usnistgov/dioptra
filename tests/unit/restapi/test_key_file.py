"""Persistent key path, representation and runtime file-access tests."""

import os
import secrets
from pathlib import Path

import pytest

from dioptra.restapi import key_file
from dioptra.restapi.key_file import read_key, resolve_key_file


@pytest.fixture
def key_path(tmp_path):
    parent = tmp_path.resolve() / "api-data"
    parent.mkdir(mode=0o700)
    path = parent / "secret-key"
    path.touch(mode=0o600)
    path.chmod(0o600)
    path.write_bytes((secrets.token_hex(32) + "\n").encode("ascii"))
    return path


def test_path_precedence_and_normalization(tmp_path, monkeypatch):
    """Select explicit, environment and user-default paths in that order.

    Paths are normalized before server directory changes, with tilde expansion
    but without expansion of embedded environment expressions.
    """
    home = Path("~").expanduser()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    monkeypatch.delenv("DIOPTRA_RESTAPI_SECRET_KEY_FILE", raising=False)
    assert resolve_key_file() == tmp_path / ".local/share/dioptra/restapi/secret-key"
    monkeypatch.setenv("DIOPTRA_RESTAPI_SECRET_KEY_FILE", "environment/key")
    assert resolve_key_file() == tmp_path / "environment/key"
    assert resolve_key_file("~/explicit/key") == home / "explicit/key"
    assert resolve_key_file("./data/../$KEY") == tmp_path / "$KEY"


@pytest.mark.parametrize("source", ["argument", "environment"])
def test_empty_path_fails(source, monkeypatch):
    """Reject an empty selected path without silently using another source.

    Empty input is an explicit configuration error. Falling back could read a
    different account's or checkout's signing key and change cookie acceptance.
    """
    monkeypatch.setenv(
        "DIOPTRA_RESTAPI_SECRET_KEY_FILE", "" if source == "environment" else "other"
    )
    with pytest.raises(ValueError, match="SECRET_KEY_FILE"):
        resolve_key_file("" if source == "argument" else None)


@pytest.mark.parametrize("suffix", [b"", b"\n"])
def test_valid_key_representation(key_path, suffix):
    """Read exactly the encoded key, independent of the optional trailing LF.

    Flask uses the 64-character text rather than decoded random bytes. Both
    allowed file representations must therefore produce the identical key.
    """
    content = secrets.token_hex(32)
    key_path.write_bytes(content.encode("ascii") + suffix)
    assert read_key(key_path, development=True) == content


@pytest.mark.parametrize(
    "content",
    [
        b"",
        b"deploy123",
        b"a" * 63,
        b"A" * 64,
        b"g" * 64,
        b"a" * 64 + b"\r\n",
        b"a" * 64 + b"\n\n",
        b" " + b"a" * 64,
        b"a" * 64 + b" ",
        pytest.param(b"a" * 100000, id="oversized"),
        b"\xff" * 64,
    ],
)
def test_invalid_content_is_preserved_without_disclosure(key_path, content):
    """Reject malformed, empty, oversized and former-fallback key content.

    Runtime reading neither repairs invalid material nor prints it in setup
    guidance. Exact file bytes remain available for explicit operator inspection.
    """
    key_path.write_bytes(content)
    with pytest.raises(ValueError, match="init-key") as caught:
        read_key(key_path, development=True)
    assert str(key_path) in str(caught.value)
    assert "deploy123" not in str(caught.value)
    assert "a" * 64 not in str(caught.value)
    assert key_path.read_bytes() == content


def test_missing_key_is_not_generated(key_path):
    """Fail startup for an absent selected key with explicit setup guidance.

    Reading must never generate a replacement or switch to a fallback location,
    because a new key would silently invalidate existing authentication cookies.
    """
    key_path.unlink()
    with pytest.raises(ValueError, match="init-key"):
        read_key(key_path, development=True)
    assert not key_path.exists()


@pytest.mark.skipif(
    os.name == "nt",
    reason="POSIX file permission enforcement is unavailable on native Windows.",
)
@pytest.mark.parametrize("mode", [0o400, 0o600])
def test_protected_read_only_key_is_accepted(key_path, mode):
    """Accept protected owner-readable files without changing their mode.

    Read-only volume mounts and owner-read-only files are supported at runtime.
    Initialization may repair permissions, but reading has no write authority.
    """
    key_path.chmod(mode)
    before = key_path.stat()
    assert len(read_key(key_path)) == 64
    after = key_path.stat()
    assert after.st_mode == before.st_mode
    assert after.st_uid == before.st_uid
    assert after.st_ino == before.st_ino


@pytest.mark.skipif(
    os.name == "nt",
    reason="POSIX permission masks are not enforced on native Windows development.",
)
@pytest.mark.parametrize("mode", [0o000, 0o200, 0o640, 0o604, 0o700, 0o1600])
def test_unsafe_key_permissions_rejected_without_repair(key_path, mode):
    """Reject missing owner-read permission and any extra access bits.

    Runtime accepts only 0400 or 0600 and must not silently repair permissions,
    including when a privileged account could otherwise read an unsafe file.
    """
    key_path.chmod(mode)
    with pytest.raises(ValueError):
        read_key(key_path)
    assert key_path.stat().st_mode & 0o7777 == mode


@pytest.mark.skipif(
    os.name == "nt",
    reason="POSIX parent permissions are unavailable on native Windows development.",
)
def test_parent_requires_owned_mode_0700(key_path, monkeypatch):
    """Require the selected key's immediate parent to be protected and owned.

    An unsafe data directory or a different effective account must fail without
    chmod or chown. Higher trusted ancestors retain their ordinary permissions.
    """
    key_path.parent.chmod(0o750)
    with pytest.raises(ValueError, match="0700"):
        read_key(key_path)
    assert key_path.parent.stat().st_mode & 0o7777 == 0o750
    key_path.parent.chmod(0o700)
    monkeypatch.setattr(key_file.os, "geteuid", lambda: key_path.stat().st_uid + 1)
    with pytest.raises(ValueError, match="own"):
        read_key(key_path)


@pytest.mark.skipif(
    os.name == "nt",
    reason="POSIX link and no-follow descriptor checks require a POSIX host.",
)
@pytest.mark.parametrize(
    "link", ["file-symlink", "parent-symlink", "ancestor-symlink", "hard-link"]
)
def test_linked_key_paths_rejected(key_path, link, tmp_path):
    """Reject file links and symbolic links in every parent component.

    A protected mode alone does not bind the key to one auditable filesystem
    location. Both redirected paths and additional hard links remain invalid.
    """
    if link == "hard-link":
        os.link(key_path, key_path.with_name("other"))
        selected = key_path
    elif link == "file-symlink":
        selected = key_path.with_name("linked")
        selected.symlink_to(key_path)
    elif link == "parent-symlink":
        alias = tmp_path.resolve() / "alias"
        alias.symlink_to(key_path.parent, target_is_directory=True)
        selected = alias / key_path.name
    else:
        alias = tmp_path.resolve() / "alias"
        alias.symlink_to(tmp_path.resolve(), target_is_directory=True)
        selected = alias / key_path.parent.name / key_path.name
    with pytest.raises(ValueError):
        read_key(selected)


@pytest.mark.skipif(
    os.name == "nt",
    reason="Creating a FIFO for nonblocking file-type validation requires POSIX.",
)
def test_nonregular_key_does_not_block(key_path):
    """Reject named pipes without waiting for a writer.

    A supplied non-file path must fail during startup rather than hanging the
    process while trying to consume secret material from an unexpected stream.
    """
    key_path.unlink()
    os.mkfifo(key_path, mode=0o600)
    with pytest.raises(ValueError, match="regular"):
        read_key(key_path)


def test_key_directory_is_not_a_file(key_path):
    """Reject directories where the key file is expected.

    File-type checks remain active on all platforms, including development's
    native-Windows filesystem exception.
    """
    key_path.unlink()
    key_path.mkdir()
    with pytest.raises(ValueError):
        read_key(key_path, development=True)


@pytest.mark.skipif(
    os.name == "nt",
    reason="The injected path replacement exercises POSIX descriptor identity checks.",
)
def test_replaced_path_is_detected(key_path, monkeypatch):
    """Detect an observed path replacement after opening the selected inode.

    A scoped replacement changes the named file during a metadata check. The
    opened original must not be accepted as the current path's key.
    """
    original = key_file.os.fstat
    replaced = False

    def replace_path(fd):
        nonlocal replaced
        info = original(fd)
        if not replaced and info.st_ino == key_path.stat().st_ino:
            replaced = True
            key_path.rename(key_path.with_name("original"))
            key_path.write_bytes((secrets.token_hex(32) + "\n").encode("ascii"))
            key_path.chmod(0o600)
        return info

    monkeypatch.setattr(key_file.os, "fstat", replace_path)
    with pytest.raises(ValueError, match="changed"):
        read_key(key_path)


def test_windows_development_keeps_content_rules(key_path, monkeypatch):
    """Retain persistent keys and content checks under the Windows exception.

    A scoped platform replacement exercises the reduced filesystem contract on
    every host. It accepts ordinary file permissions only for development and
    still rejects production and malformed keys without modifying their bytes.
    """
    monkeypatch.setattr(key_file, "_is_windows", lambda: True)
    key_path.chmod(0o644)
    before = key_path.read_bytes()
    assert read_key(key_path, development=True) == before[:64].decode("ascii")
    assert key_path.read_bytes() == before
    with pytest.raises(ValueError, match="native Windows"):
        read_key(key_path)
    key_path.write_bytes(b"deploy123")
    with pytest.raises(ValueError):
        read_key(key_path, development=True)
