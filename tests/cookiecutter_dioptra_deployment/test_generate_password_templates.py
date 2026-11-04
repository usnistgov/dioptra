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
import errno
import importlib.util
import logging
import os
import signal
import stat
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest
from jinja2 import TemplateError

pytestmark = pytest.mark.skipif(
    os.name != "posix", reason="credential protection requires POSIX file permissions"
)

CREDENTIAL_PATHS = [
    ".env",
    "secrets/postgres-passwd.env",
    "secrets/dioptra-deployment-rustfs-accounts.env",
]
TEST_PASSWORD = "test-password-only"
PASSWORDS = dict.fromkeys(
    (
        "rustfs_mlflow_tracking_password",
        "rustfs_kms_secret_key",
        "rustfs_root_password",
        "rustfs_restapi_password",
        "rustfs_worker_password",
        "pgadmin_default_password",
        "postgres_admin_password",
        "postgres_user_dioptra_password",
        "dioptra_worker_password",
    ),
    TEST_PASSWORD,
)


@pytest.fixture
def generator(result, monkeypatch):
    """Load the generator from an isolated rendered deployment."""
    assert result.exit_code == 0
    monkeypatch.chdir(result.project_path)
    spec = importlib.util.spec_from_file_location(
        "generate_password_templates",
        result.project_path / "scripts" / "generate_password_templates.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    open_file = os.open
    descriptors = []

    def tracked_open(*args, **kwargs):
        fd = open_file(*args, **kwargs)
        descriptors.append(fd)
        return fd

    monkeypatch.setattr(module.os, "open", tracked_open)
    yield module

    # Check descriptor closure for every success, race and failure scenario below.
    for fd in descriptors:
        with pytest.raises(OSError) as exc:
            os.fstat(fd)
        assert exc.value.errno == errno.EBADF


def render(generator, output=None, passwords=PASSWORDS):
    """Exercise the public entry point for the whole set or a nonsecret output."""
    templates = generator.PASSWORD_FILES
    if output is not None:
        templates = [
            (source, path)
            for source, path in templates
            if (
                str(path) in CREDENTIAL_PATHS
                if output in CREDENTIAL_PATHS
                else path == Path(output)
            )
        ]
    generator.render_template_files(generator.JINJA_ENV, templates, passwords)


def seed_credentials():
    """Create a complete nonempty existing set with synthetic arbitrary bytes."""
    for output in CREDENTIAL_PATHS:
        Path(output).write_bytes(b"existing-test-credential=\xff\x00\n")
        Path(output).chmod(0o600)


def assert_no_credentials():
    """Check that no final credentials or current staging files remain."""
    for output in CREDENTIAL_PATHS:
        assert not Path(output).exists()
        assert staging_files(output) == []


def staging_files(output):
    path = Path(output)
    return list(path.parent.glob(f".{path.name}.*.tmp"))


def is_staging_fd(fd, output):
    return any(
        stage.stat().st_ino == os.fstat(fd).st_ino for stage in staging_files(output)
    )


def file_metadata(info):
    """Compare identity, protection and contents metadata without access times."""
    return {
        name: getattr(info, name)
        for name in (
            "st_dev",
            "st_ino",
            "st_mode",
            "st_uid",
            "st_gid",
            "st_size",
            "st_nlink",
            "st_mtime_ns",
        )
    }


def repairs(caplog):
    return [
        record.message
        for record in caplog.records
        if "Repaired permissions" in record.message
    ]


def test_credentials_are_protected_before_first_write(generator, monkeypatch, caplog):
    """Protect every credential before its first secret write.

    Given a permissive umask, generation writes only to mode-0600 staging,
    then publishes complete files with unchanged ownership and a single link.
    The nonsecret systemd output keeps ordinary creation permissions.
    """
    caplog.set_level(logging.INFO, logger=generator.logger.name)
    fdopen = os.fdopen
    writes = []

    @contextmanager
    def checked_fdopen(fd, *args, **kwargs):
        with fdopen(fd, *args, **kwargs) as stream:
            real_write = stream.write

            def write(content):
                info = os.fstat(fd)
                assert stat.S_IMODE(info.st_mode) == 0o600
                assert info.st_size == 0
                staging = [
                    (path, candidate)
                    for path in CREDENTIAL_PATHS
                    for candidate in staging_files(path)
                    if candidate.stat().st_ino == info.st_ino
                ]
                assert len(staging) == 1
                assert not Path(staging[0][0]).exists()
                writes.append(info)
                return real_write(content)

            with monkeypatch.context() as patch:
                patch.setattr(stream, "write", write)
                yield stream

    monkeypatch.setattr(generator.os, "fdopen", checked_fdopen)
    previous_umask = os.umask(0)
    try:
        render(generator)
    finally:
        os.umask(previous_umask)

    assert generator.CREDENTIAL_FILES == {Path(path) for path in CREDENTIAL_PATHS}
    assert {info.st_ino for info in writes} == {
        Path(path).stat().st_ino for path in CREDENTIAL_PATHS
    }
    for path in CREDENTIAL_PATHS:
        assert stat.S_IMODE(Path(path).stat().st_mode) == 0o600
        assert TEST_PASSWORD in Path(path).read_text()
        current = Path(path).stat()
        original = next(info for info in writes if info.st_ino == current.st_ino)
        assert (current.st_uid, current.st_gid) == (original.st_uid, original.st_gid)
        assert current.st_nlink == 1
        assert staging_files(path) == []
    assert stat.S_IMODE(Path("systemd/dioptra.service").stat().st_mode) == 0o666
    assert repairs(caplog) == []
    assert TEST_PASSWORD not in caplog.text


def test_restrictive_umask_still_produces_owner_read_write(generator):
    """Create usable protected credentials under a restrictive umask.

    Given a umask that removes all permissions, generation establishes mode
    0600 for every credential output before writing it.
    """
    previous_umask = os.umask(0o777)
    try:
        render(generator)
    finally:
        os.umask(previous_umask)
    assert all(
        stat.S_IMODE(Path(path).stat().st_mode) == 0o600 for path in CREDENTIAL_PATHS
    )


@pytest.mark.parametrize("output", CREDENTIAL_PATHS)
@pytest.mark.parametrize("mode", [0o400, 0o600, 0o644, 0o666, 0o4600])
def test_existing_credentials_are_preserved_and_repaired_once(
    generator, caplog, output, mode
):
    """Preserve existing bytes and ownership while repairing permissions.

    Given a complete nonempty set and one selected initial mode, rerunning
    initialization sets mode 0600 and reports only an actual repair.
    A second run preserves the same arbitrary bytes without another repair.
    """
    seed_credentials()
    caplog.set_level(logging.INFO, logger=generator.logger.name)
    path = Path(output)
    content = b"existing-test-credential=\xff\x00\n"
    path.write_bytes(content)
    path.chmod(mode)
    original = path.stat()
    original_mode = stat.S_IMODE(original.st_mode)

    render(generator, output)

    current = path.stat()
    assert path.read_bytes() == content
    assert (current.st_dev, current.st_ino, current.st_uid, current.st_gid) == (
        original.st_dev,
        original.st_ino,
        original.st_uid,
        original.st_gid,
    )
    assert stat.S_IMODE(current.st_mode) == 0o600
    expected = (
        [f"Repaired permissions for {output} from {original_mode:04o} to 0600"]
        if original_mode != 0o600
        else []
    )
    assert repairs(caplog) == expected
    assert "existing-test-credential" not in caplog.text
    assert TEST_PASSWORD not in caplog.text

    caplog.clear()
    render(generator, output)
    assert path.read_bytes() == content
    assert repairs(caplog) == []


def test_compliant_files_do_not_require_chmod(generator, monkeypatch):
    """Preserve compliant credentials without requiring permission changes.

    Given a complete mode-0600 set, initialization succeeds even when an
    injected chmod implementation would fail if called.
    """
    seed_credentials()
    path = Path(".env")
    path.write_bytes(b"existing-test-credential")
    path.chmod(0o600)

    def unexpected_chmod(*args):
        pytest.fail("an already compliant file must not need permission repair")

    monkeypatch.setattr(generator.os, "fchmod", unexpected_chmod)
    render(generator, ".env")


def test_existing_systemd_permissions_are_unchanged(generator, caplog):
    """Preserve the existing nonsecret systemd unit.

    Given an existing mode-0644 unit, generation leaves its contents and
    permissions unchanged and reports no credential permission repair.
    """
    caplog.set_level(logging.INFO, logger=generator.logger.name)
    path = Path("systemd/dioptra.service")
    path.write_bytes(b"existing nonsecret unit")
    path.chmod(0o644)
    render(generator, str(path))
    assert path.read_bytes() == b"existing nonsecret unit"
    assert stat.S_IMODE(path.stat().st_mode) == 0o644
    assert repairs(caplog) == []


@pytest.mark.parametrize("output", CREDENTIAL_PATHS)
@pytest.mark.parametrize("broken", [False, True])
def test_symlinks_are_rejected_without_touching_targets(
    generator, tmp_path, output, broken
):
    """Reject credential symlinks without changing their targets.

    Given a valid or dangling symlink at a credential destination, generation
    fails and preserves the link and any existing target bytes and mode.
    """
    target = tmp_path / "target"
    if not broken:
        target.write_bytes(b"unrelated test file")
        target.chmod(0o640)
    path = Path(output)
    path.symlink_to(target)

    with pytest.raises(RuntimeError, match="Cannot secure credential set"):
        render(generator, output)

    assert path.is_symlink()
    if broken:
        assert not target.exists()
    else:
        assert target.read_bytes() == b"unrelated test file"
        assert stat.S_IMODE(target.stat().st_mode) == 0o640


@pytest.mark.parametrize("kind", ["directory", "fifo", "hardlink"])
def test_nonordinary_credential_files_are_rejected(generator, tmp_path, kind):
    """Reject directories, FIFOs and unrelated hard-linked credentials.

    Given one of these objects at the destination, initialization fails
    without changing its mode or any unrelated hard-linked contents.
    """
    path = Path(".env")
    target = tmp_path / "target"
    if kind == "directory":
        path.mkdir()
    elif kind == "fifo":
        os.mkfifo(path, 0o644)
    else:
        target.write_bytes(b"unrelated test file")
        target.chmod(0o644)
        path.hardlink_to(target)
    original = path.lstat()

    with pytest.raises(RuntimeError, match="regular credential file"):
        render(generator, ".env")

    assert path.lstat().st_mode == original.st_mode
    if kind == "hardlink":
        assert target.read_bytes() == b"unrelated test file"


def test_linked_parent_directory_is_rejected(generator, tmp_path):
    """Reject a symlink in the credential's parent path.

    Given a secrets directory linked to an external directory, initialization
    fails without reading, rewriting or changing the target credential's mode.
    """
    target_dir = tmp_path / "external-secrets"
    target_dir.mkdir()
    target = target_dir / "postgres-passwd.env"
    target.write_bytes(b"unrelated test file")
    target.chmod(0o644)
    Path("secrets").rmdir()
    Path("secrets").symlink_to(target_dir, target_is_directory=True)

    with pytest.raises(RuntimeError, match="Cannot secure credential set"):
        render(generator, "secrets/postgres-passwd.env")

    assert target.read_bytes() == b"unrelated test file"
    assert stat.S_IMODE(target.stat().st_mode) == 0o644


@pytest.mark.parametrize("symlink", [False, True])
def test_creation_race_never_overwrites_the_winning_file(
    generator, monkeypatch, tmp_path, symlink
):
    """Reject a competing destination without adopting its credentials.

    An injected creator wins the first publication with a file or symlink.
    The transaction preserves that object and removes every owned staging file,
    leaving the other credential destinations absent.
    """
    path = Path(".env")
    target = tmp_path / "target"
    target.write_bytes(b"unrelated test file")
    target.chmod(0o640)
    link = os.link

    def racing_link(*args, **kwargs):
        if symlink:
            path.symlink_to(target)
        else:
            path.write_bytes(b"concurrent initializer credential")
            path.chmod(0o644)
        return link(*args, **kwargs)

    monkeypatch.setattr(generator.os, "link", racing_link)
    with pytest.raises(RuntimeError, match="preserved unrelated"):
        render(generator)
    assert path.is_symlink() == symlink
    if not symlink:
        assert path.read_bytes() == b"concurrent initializer credential"
        assert stat.S_IMODE(path.stat().st_mode) == 0o644
    assert target.read_bytes() == b"unrelated test file"
    assert stat.S_IMODE(target.stat().st_mode) == 0o640
    for output in CREDENTIAL_PATHS:
        assert staging_files(output) == []
        if output != ".env":
            assert not Path(output).exists()


@pytest.mark.parametrize("existing", [False, True])
def test_replaced_path_is_rejected_before_chmod_or_write(
    generator, monkeypatch, tmp_path, existing
):
    """Detect an injected path replacement before changing the opened file.

    The replacement occurs immediately after opening an existing credential
    or new staging file. Initialization rejects the changed path and leaves
    the original bytes and unrelated symlink target unchanged.
    """
    path = Path(".env")
    if existing:
        seed_credentials()
        path.write_bytes(b"original test credential")
        path.chmod(0o644)
    target = tmp_path / "target"
    target.write_bytes(b"unrelated test file")
    target.chmod(0o640)
    saved = tmp_path / "original"
    open_file = os.open

    def replacing_open(name, flags, *args, **kwargs):
        fd = open_file(name, flags, *args, **kwargs)
        if (existing and name == ".env") or (not existing and flags & os.O_EXCL):
            replaced = path if existing else Path(name)
            replaced.rename(saved)
            replaced.symlink_to(target)
        return fd

    monkeypatch.setattr(generator.os, "open", replacing_open)
    with pytest.raises(RuntimeError, match="path changed|preserved unrelated"):
        render(generator, ".env")

    assert target.read_bytes() == b"unrelated test file"
    assert stat.S_IMODE(target.stat().st_mode) == 0o640
    assert saved.read_bytes() == (b"original test credential" if existing else b"")
    assert stat.S_IMODE(saved.stat().st_mode) == (0o644 if existing else 0o600)


@pytest.mark.parametrize("failure", ["denied", "ineffective"])
def test_failed_permission_repair_is_actionable_and_never_reported_as_repaired(
    generator, monkeypatch, caplog, failure
):
    """Report injected permission-repair failures without claiming success.

    Given a complete set with one mode-0644 file, denied or ineffective chmod makes
    initialization fail with rerun guidance while preserving bytes and mode.
    """
    seed_credentials()
    caplog.set_level(logging.INFO, logger=generator.logger.name)
    path = Path(".env")
    path.write_bytes(b"original test credential")
    path.chmod(0o644)

    def failed_chmod(fd, mode):
        if failure == "denied":
            raise PermissionError("permission repair denied for test")

    monkeypatch.setattr(generator.os, "fchmod", failed_chmod)
    with pytest.raises(RuntimeError, match="Cannot secure credential set") as exc:
        render(generator, ".env")

    assert ".env" in str(exc.value)
    assert "deployment user" in str(exc.value)
    assert "rerun init-deployment.sh" in str(exc.value)
    assert path.read_bytes() == b"original test credential"
    assert stat.S_IMODE(path.stat().st_mode) == 0o644
    assert repairs(caplog) == []


def test_replaced_path_after_repair_is_detected(
    generator, monkeypatch, tmp_path, caplog
):
    """Detect an injected replacement after permission repair.

    The chmod operation secures the original inode and substitutes a symlink.
    Initialization rejects the changed path, preserves both contents and
    reports no successful repair for the substituted destination.
    """
    seed_credentials()
    caplog.set_level(logging.INFO, logger=generator.logger.name)
    path = Path(".env")
    path.write_bytes(b"original test credential")
    path.chmod(0o644)
    target = tmp_path / "target"
    target.write_bytes(b"unrelated test file")
    target.chmod(0o640)
    saved = tmp_path / "original"
    chmod = os.fchmod

    def replacing_chmod(fd, mode):
        chmod(fd, mode)
        path.rename(saved)
        path.symlink_to(target)

    monkeypatch.setattr(generator.os, "fchmod", replacing_chmod)
    with pytest.raises(RuntimeError, match="path changed during initialization"):
        render(generator, ".env")

    assert saved.read_bytes() == b"original test credential"
    assert stat.S_IMODE(saved.stat().st_mode) == 0o600
    assert target.read_bytes() == b"unrelated test file"
    assert stat.S_IMODE(target.stat().st_mode) == 0o640
    assert repairs(caplog) == []


def test_inaccessible_existing_file_fails_without_replacing_it(generator, monkeypatch):
    """Preserve an existing credential when access is denied.

    Given an injected read-only-open denial, initialization reports the
    failure without replacing the credential or changing its mode.
    """
    seed_credentials()
    path = Path(".env")
    path.write_bytes(b"original test credential")
    path.chmod(0o600)
    open_file = os.open

    def denied_open(name, flags, *args, **kwargs):
        if name == ".env":
            raise PermissionError("test denies credential access")
        return open_file(name, flags, *args, **kwargs)

    monkeypatch.setattr(generator.os, "open", denied_open)
    with pytest.raises(RuntimeError, match="test denies credential access"):
        render(generator, ".env")
    assert path.read_bytes() == b"original test credential"
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_generator_process_fails_for_an_unsafe_credential_path(generator, tmp_path):
    """Propagate an unsafe-path failure from the generated script.

    Given a credential symlink, a separate generator process exits nonzero
    with actionable guidance, leaves the target unchanged and emits no contents.
    """
    target = tmp_path / "target"
    target.write_bytes(b"unrelated test file")
    target.chmod(0o640)
    Path(".env").symlink_to(target)
    result = subprocess.run(
        [sys.executable, "scripts/generate_password_templates.py"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert "Cannot secure credential set" in result.stderr
    assert "rerun init-deployment.sh" in result.stderr
    assert "unrelated test file" not in result.stderr
    assert target.read_bytes() == b"unrelated test file"
    assert stat.S_IMODE(target.stat().st_mode) == 0o640


@pytest.mark.parametrize("api", ["O_NOFOLLOW", "fchmod", "fsync", "link", "unlink"])
def test_missing_nofollow_support_fails_with_an_actionable_message(
    generator, monkeypatch, api
):
    """Explain injected missing POSIX credential APIs before touching the set.

    Given an environment missing a required operation, initialization gives POSIX
    capability and rerun guidance before creating a credential destination.
    """
    monkeypatch.delattr(generator.os, api)
    with pytest.raises(RuntimeError, match="requires POSIX no-follow") as exc:
        render(generator, ".env")
    assert "rerun init-deployment.sh" in str(exc.value)
    assert not Path(".env").exists()


def test_missing_dir_fd_support_fails_with_an_actionable_message(
    generator, monkeypatch
):
    """Explain injected directory-relative opening unavailability.

    Given an os.open implementation that rejects dir_fd, initialization fails
    with rerun guidance and leaves the credential destination absent.
    """
    open_file = os.open

    def unsupported_open(name, flags, *args, **kwargs):
        if "dir_fd" in kwargs:
            raise NotImplementedError("dir_fd is unavailable for test")
        return open_file(name, flags, *args, **kwargs)

    monkeypatch.setattr(generator.os, "open", unsupported_open)
    with pytest.raises(RuntimeError, match="dir_fd is unavailable") as exc:
        render(generator, ".env")
    assert "rerun init-deployment.sh" in str(exc.value)
    assert not Path(".env").exists()


@pytest.mark.parametrize("output", CREDENTIAL_PATHS)
def test_render_error_does_not_create_a_credential_file(generator, monkeypatch, output):
    """Leave no credential output when an injected corrupt template fails.

    Given deliberately malformed Jinja syntax, rendering raises TemplateError
    before creating the credential destination or staging file.
    """
    template = next(
        source for source, path in generator.PASSWORD_FILES if path == Path(output)
    )
    template.write_text("{% if %}")
    open_file = os.open

    def checked_open(path, flags, *args, **kwargs):
        assert not flags & os.O_CREAT
        return open_file(path, flags, *args, **kwargs)

    monkeypatch.setattr(generator.os, "open", checked_open)
    with pytest.raises(TemplateError):
        render(generator, output)

    assert_no_credentials()


def test_existing_credentials_do_not_require_template_rendering(generator, monkeypatch):
    """Skip credential rendering when a complete nonempty set already exists.

    Given a complete set of arbitrary bytes and a template loader that fails
    if called, initialization preserves the file's contents, mode and owner.
    """
    seed_credentials()
    path = Path(".env")
    content = b"original test credential=\xff\x00\n"
    path.write_bytes(content)
    path.chmod(0o600)
    original = path.stat()

    def unexpected_render(*args, **kwargs):
        pytest.fail("an existing credential must not need template rendering")

    monkeypatch.setattr(generator.JINJA_ENV, "get_template", unexpected_render)
    render(generator, ".env")

    assert path.read_bytes() == content
    current = path.stat()
    assert (current.st_ino, current.st_mode, current.st_uid, current.st_gid) == (
        original.st_ino,
        original.st_mode,
        original.st_uid,
        original.st_gid,
    )


@pytest.mark.parametrize(
    "failure",
    [
        "stream_open",
        "write",
        "partial_write",
        "short_write",
        "flush",
        "close",
    ],
)
def test_stream_failure_cleans_staging_and_allows_retry(
    generator, monkeypatch, failure
):
    """Keep failed output unpublished and permit a complete retry.

    Given an injected later-member stream, write, flush or close failure,
    generation closes resources and removes every owned staging and final name.
    A later attempt with fresh passwords publishes a complete consistent set.
    """
    output = "secrets/postgres-passwd.env"
    fdopen = os.fdopen
    streams = []

    @contextmanager
    def failed_stream(fd, *args, **kwargs):
        if not is_staging_fd(fd, output):
            with fdopen(fd, *args, **kwargs) as stream:
                yield stream
            return
        if failure == "stream_open":
            raise OSError("test stream creation failed")
        stream = fdopen(fd, *args, **kwargs)
        streams.append(stream)
        real_write, real_flush = stream.write, stream.flush

        def write(content):
            if failure == "write":
                raise OSError("test stream write failed")
            if failure in ("partial_write", "short_write"):
                written = real_write(content[:10])
                real_flush()
                if failure == "partial_write":
                    raise OSError("test stream failed after partial output")
                return written
            return real_write(content)

        def flush():
            assert not Path(output).exists()
            if failure == "flush":
                raise OSError("test stream flush failed")
            return real_flush()

        try:
            with monkeypatch.context() as patch:
                patch.setattr(stream, "write", write)
                patch.setattr(stream, "flush", flush)
                yield stream
        finally:
            stream.close()
            if failure == "close":
                raise OSError("test stream close failed")

    with monkeypatch.context() as patch:
        patch.setattr(generator.os, "fdopen", failed_stream)
        with pytest.raises(RuntimeError, match="Cannot secure credential set"):
            render(generator, output)

    assert not Path(output).exists()
    assert staging_files(output) == []
    assert all(stream.closed for stream in streams)
    assert_no_credentials()
    retry_passwords = dict.fromkeys(PASSWORDS, "retry-password-only")
    render(generator, output, retry_passwords)
    assert "retry-password-only" in Path(output).read_text()
    assert all(
        "retry-password-only" in Path(path).read_text() for path in CREDENTIAL_PATHS
    )
    assert stat.S_IMODE(Path(output).stat().st_mode) == 0o600
    assert Path(output).stat().st_nlink == 1
    assert staging_files(output) == []


@pytest.mark.parametrize("change", ["permissions", "path"])
def test_changes_during_write_are_detected_after_stream_closure(
    generator, monkeypatch, tmp_path, change
):
    """Detect injected permission or path changes during staging writes.

    After the writer alters staging permissions or substitutes a symlink,
    initialization closes the stream and rejects the change before publication.
    Cleanup preserves substituted paths and unrelated targets.
    """
    path = Path(".env")
    target = tmp_path / "target"
    target.write_bytes(b"unrelated test file")
    target.chmod(0o640)
    saved = tmp_path / "original"
    fdopen = os.fdopen
    fstat = os.fstat
    streams = []
    checks_after_close = []

    @contextmanager
    def changed_stream(fd, *args, **kwargs):
        with fdopen(fd, *args, **kwargs) as stream:
            streams.append(stream)
            real_write = stream.write

            def write(content):
                written = real_write(content)
                staging = staging_files(".env")[0]
                if change == "permissions":
                    staging.chmod(0o644)
                else:
                    staging.rename(saved)
                    staging.symlink_to(target)
                return written

            with monkeypatch.context() as patch:
                patch.setattr(stream, "write", write)
                yield stream

    def checked_fstat(fd):
        if streams:
            assert streams[-1].closed
            checks_after_close.append(fd)
        return fstat(fd)

    monkeypatch.setattr(generator.os, "fdopen", changed_stream)
    monkeypatch.setattr(generator.os, "fstat", checked_fstat)
    with pytest.raises(RuntimeError, match="Cannot secure credential set"):
        render(generator, ".env")

    assert checks_after_close
    assert all(stream.closed for stream in streams)
    assert target.read_bytes() == b"unrelated test file"
    assert stat.S_IMODE(target.stat().st_mode) == 0o640
    assert not path.exists()
    if change == "permissions":
        assert staging_files(".env") == []
    else:
        assert TEST_PASSWORD in saved.read_text()
        assert len(staging_files(".env")) == 1
        assert staging_files(".env")[0].is_symlink()


@pytest.mark.parametrize("output", CREDENTIAL_PATHS)
@pytest.mark.parametrize("mode", [0o600, 0o644])
def test_empty_existing_credentials_require_explicit_recovery(
    generator, caplog, output, mode
):
    """Reject an empty existing destination without changing it.

    Given an empty credential file, initialization asks the operator to inspect,
    remove or restore it, preserves its identity and owner, and reports no skip
    or permission repair.
    """
    seed_credentials()
    caplog.set_level(logging.INFO, logger=generator.logger.name)
    path = Path(output)
    path.write_bytes(b"")
    path.chmod(mode)
    original = path.stat()

    with pytest.raises(
        RuntimeError, match="credential set is incomplete or contains an empty file"
    ) as exc:
        render(generator, output)

    assert "inspect" in str(exc.value)
    assert "remove" in str(exc.value)
    assert "restore" in str(exc.value)
    assert file_metadata(path.stat()) == file_metadata(original)
    assert path.read_bytes() == b""
    assert repairs(caplog) == []
    assert "skipping" not in caplog.text
    assert staging_files(output) == []


def test_empty_rendered_content_is_not_staged(generator, monkeypatch):
    """Reject an injected empty template result before creating staging or output."""
    monkeypatch.setattr(generator, "_render_template", lambda *args: "")
    with pytest.raises(RuntimeError, match="rendered credential content is empty"):
        render(generator, ".env")
    assert not Path(".env").exists()
    assert staging_files(".env") == []


def test_publication_follows_complete_write_flush_and_close(
    generator, monkeypatch, caplog
):
    """Complete all three streams before publishing any credential.

    Every stream must flush, synchronize and close with no final names present.
    Publication observes all three protected staging files, then final checks
    and directory synchronization precede success logs.
    """
    caplog.set_level(logging.INFO, logger=generator.logger.name)
    fdopen, link, fsync = os.fdopen, os.link, os.fsync
    streams, synced_files, synced_directories, published = [], [], [], []

    @contextmanager
    def tracked_stream(fd, *args, **kwargs):
        with fdopen(fd, *args, **kwargs) as stream:
            streams.append(stream)
            real_flush = stream.flush

            def flush():
                assert all(not Path(path).exists() for path in CREDENTIAL_PATHS)
                return real_flush()

            with monkeypatch.context() as patch:
                patch.setattr(stream, "flush", flush)
                yield stream

    def checked_fsync(fd):
        info = os.fstat(fd)
        if stat.S_ISDIR(info.st_mode):
            assert all(Path(path).exists() for path in CREDENTIAL_PATHS)
            assert all(not staging_files(path) for path in CREDENTIAL_PATHS)
            synced_directories.append(info.st_ino)
        else:
            assert all(not Path(path).exists() for path in CREDENTIAL_PATHS)
            synced_files.append(info.st_ino)
        assert not any(
            record.message.startswith("Generating ") for record in caplog.records
        )
        return fsync(fd)

    def checked_link(source, destination, **kwargs):
        assert len(streams) == len(synced_files) == 3
        assert all(stream.closed for stream in streams)
        assert kwargs["src_dir_fd"] == kwargs["dst_dir_fd"]
        assert kwargs["follow_symlinks"] is False
        output = next(
            Path(path) for path in CREDENTIAL_PATHS if Path(path).name == destination
        )
        assert not output.exists()
        info = os.stat(source, dir_fd=kwargs["src_dir_fd"], follow_symlinks=False)
        assert stat.S_IMODE(info.st_mode) == 0o600 and info.st_nlink == 1
        assert info.st_ino in synced_files
        published.append(output)
        link(source, destination, **kwargs)

    monkeypatch.setattr(generator.os, "fdopen", tracked_stream)
    monkeypatch.setattr(generator.os, "fsync", checked_fsync)
    monkeypatch.setattr(generator.os, "link", checked_link)
    render(generator)
    assert published == sorted(map(Path, CREDENTIAL_PATHS))
    assert len(synced_directories) == 3
    assert all(Path(path).stat().st_nlink == 1 for path in CREDENTIAL_PATHS)
    assert all(not staging_files(path) for path in CREDENTIAL_PATHS)
    assert len([r for r in caplog.records if r.message.startswith("Generating ")]) == 4


@pytest.mark.parametrize("failure", ["unsupported", "unavailable", "denied"])
def test_failed_publication_cleans_staging_without_fallback(
    generator, monkeypatch, failure
):
    """Fail clearly when an injected filesystem fault prevents publication.

    Unsupported hard links, unavailable APIs and denied linking leave no final
    destination or staging file. Removing the injected fault permits a retry.
    """

    def failed_link(*args, **kwargs):
        if failure == "unavailable":
            raise NotImplementedError("test linking API unavailable")
        if failure == "denied":
            raise PermissionError("test linking denied")
        raise OSError(errno.EOPNOTSUPP, "test filesystem does not support hard links")

    with monkeypatch.context() as patch:
        patch.setattr(generator.os, "link", failed_link)
        with pytest.raises(
            RuntimeError, match="hard-link support is required|preserved unrelated"
        ):
            render(generator, ".env")
    assert not Path(".env").exists()
    assert staging_files(".env") == []
    render(generator, ".env")
    assert TEST_PASSWORD in Path(".env").read_text()


@pytest.mark.parametrize("kind", ["empty", "hardlink"])
def test_invalid_publication_winner_is_preserved(
    generator, monkeypatch, tmp_path, kind
):
    """Preserve an injected competing empty file or unrelated hard link.

    Given either concurrent destination, the transaction rejects it without
    adoption or modification and removes this attempt's staging files.
    """
    link = os.link
    target = tmp_path / "target"
    target.write_bytes(b"unrelated test file")
    target.chmod(0o644)
    originals = []

    def racing_link(*args, **kwargs):
        if kind == "empty":
            Path(".env").touch(mode=0o644)
        else:
            link(target, ".env")
        originals.append(Path(".env").stat())
        return link(*args, **kwargs)

    monkeypatch.setattr(generator.os, "link", racing_link)
    with pytest.raises(
        RuntimeError, match="incomplete|no hard links|preserved unrelated"
    ):
        render(generator, ".env")
    assert file_metadata(Path(".env").stat()) == file_metadata(originals[0])
    assert Path(".env").read_bytes() == (
        b"" if kind == "empty" else target.read_bytes()
    )
    assert target.read_bytes() == b"unrelated test file"
    assert stat.S_IMODE(target.stat().st_mode) == 0o644
    assert staging_files(".env") == []


@pytest.mark.parametrize("replacement", ["file", "symlink"])
def test_failed_write_cleanup_preserves_substituted_staging(
    generator, monkeypatch, tmp_path, replacement
):
    """Preserve an unrelated substitute when a write fails.

    The injected writer renames its staging file, replaces that name and raises
    after partial output. Cleanup detects the changed inode, preserves both the
    substitute and unrelated target, and never creates a credential destination.
    """
    target = tmp_path / "target"
    target.write_bytes(b"unrelated test file")
    target.chmod(0o640)
    saved = tmp_path / "partial"
    fdopen = os.fdopen

    @contextmanager
    def failed_stream(fd, *args, **kwargs):
        with fdopen(fd, *args, **kwargs) as stream:
            real_write = stream.write

            def write(content):
                real_write(content[:10])
                stream.flush()
                staging = staging_files(".env")[0]
                staging.rename(saved)
                if replacement == "symlink":
                    staging.symlink_to(target)
                else:
                    staging.write_bytes(b"unrelated replacement")
                    staging.chmod(0o640)
                raise OSError("test write failed after staging substitution")

            with monkeypatch.context() as patch:
                patch.setattr(stream, "write", write)
                yield stream

    monkeypatch.setattr(generator.os, "fdopen", failed_stream)
    with pytest.raises(RuntimeError, match="preserved unrelated"):
        render(generator, ".env")
    assert not Path(".env").exists()
    substituted = staging_files(".env")[0]
    assert substituted.read_bytes() == (
        target.read_bytes() if replacement == "symlink" else b"unrelated replacement"
    )
    assert saved.stat().st_size == 10
    assert stat.S_IMODE(saved.stat().st_mode) == 0o600
    assert target.read_bytes() == b"unrelated test file"
    assert stat.S_IMODE(target.stat().st_mode) == 0o640


def test_renamed_parent_is_detected_and_cleanup_stays_in_opened_directory(
    generator, monkeypatch, tmp_path
):
    """Detect an injected parent replacement before publication.

    A writer renames the opened secrets directory and substitutes another one.
    Initialization removes its staging file from the original directory and
    preserves the substitute without creating a final credential in either.
    """
    output = "secrets/postgres-passwd.env"
    saved = tmp_path / "original-secrets"
    fdopen = os.fdopen

    @contextmanager
    def changed_stream(fd, *args, **kwargs):
        with fdopen(fd, *args, **kwargs) as stream:
            yield stream
        Path("secrets").rename(saved)
        Path("secrets").mkdir()
        (Path("secrets") / "unrelated").write_bytes(b"unrelated test file")

    monkeypatch.setattr(generator.os, "fdopen", changed_stream)
    with pytest.raises(RuntimeError, match="Cannot secure credential set"):
        render(generator, output)
    assert list(saved.iterdir()) == []
    assert [p.name for p in Path("secrets").iterdir()] == ["unrelated"]
    assert not Path(output).exists()


@pytest.mark.parametrize(
    "phase", ["during_write", "before_publication", "partial_publication"]
)
def test_killed_process_leaves_only_complete_final_credentials(generator, phase):
    """Reject a partial credential set left by a deliberately killed process.

    SIGKILL during writing or before linking leaves protected staging and permits
    fresh generation. SIGKILL after the first publication leaves one complete
    destination; rerun rejects the partial set without generating missing members.
    """
    code = """
import os
import runpy
import signal
from contextlib import contextmanager

generator = runpy.run_path("scripts/generate_password_templates.py")
fdopen = os.fdopen
@contextmanager
def interrupted_stream(*args, **kwargs):
    with fdopen(*args, **kwargs) as stream:
        if PHASE == "during_write":
            stream.write("partial test output")
            stream.flush()
            os.kill(os.getpid(), signal.SIGKILL)
        yield stream
os.fdopen = interrupted_stream
link = os.link
def interrupted_link(*args, **kwargs):
    if PHASE == "partial_publication":
        link(*args, **kwargs)
    os.kill(os.getpid(), signal.SIGKILL)
os.link = interrupted_link
generator["render_template_files"](
    generator["JINJA_ENV"], generator["PASSWORD_FILES"], PASSWORDS
)
"""
    code = code.replace("PHASE", repr(phase)).replace("PASSWORDS", repr(PASSWORDS))
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=30
    )
    assert result.returncode == -signal.SIGKILL
    assert result.stdout == result.stderr == ""
    stages = [stage for output in CREDENTIAL_PATHS for stage in staging_files(output)]
    assert len(stages) == (1 if phase == "during_write" else 3)
    originals = {stage: stage.stat() for stage in stages}
    assert all(stat.S_IMODE(info.st_mode) == 0o600 for info in originals.values())
    retry_passwords = dict.fromkeys(PASSWORDS, "fresh-retry-only")
    if phase == "partial_publication":
        assert Path(".env").stat().st_nlink == 2
        content = Path(".env").read_bytes()
        with pytest.raises(RuntimeError, match="hard links|incomplete"):
            render(generator, passwords=retry_passwords)
        assert Path(".env").read_bytes() == content
        assert all(
            not Path(path).exists() for path in CREDENTIAL_PATHS if path != ".env"
        )
    else:
        assert all(not Path(path).exists() for path in CREDENTIAL_PATHS)
        render(generator, passwords=retry_passwords)
        assert all(
            "fresh-retry-only" in Path(path).read_text() for path in CREDENTIAL_PATHS
        )
        assert all(Path(path).stat().st_nlink == 1 for path in CREDENTIAL_PATHS)
    assert all(
        file_metadata(stage.stat()) == file_metadata(originals[stage])
        for stage in stages
    )


def test_staging_collision_preserves_the_existing_file(generator, monkeypatch):
    """Preserve an unrelated file when the injected staging name already exists.

    Given a fixed random token and an existing staging pathname, exclusive
    creation fails without modifying or deleting that file or publishing output.
    """
    monkeypatch.setattr(generator.secrets, "token_hex", lambda size: "collision")
    staging = Path("..env.collision.tmp")
    staging.write_bytes(b"unrelated staging file")
    staging.chmod(0o640)
    original = staging.stat()
    with pytest.raises(RuntimeError, match="Cannot secure credential set"):
        render(generator, ".env")
    assert file_metadata(staging.stat()) == file_metadata(original)
    assert staging.read_bytes() == b"unrelated staging file"
    assert not Path(".env").exists()


def test_rollback_continues_after_a_cleanup_failure(generator, monkeypatch, caplog):
    """Attempt every owned cleanup after an injected rollback failure.

    A directory-sync error triggers rollback, and unlink of the last credential
    is deliberately denied. Other owned files are removed, the retained member
    is reported, and rerun rejects that partial set without filling its gaps.
    """
    caplog.set_level(logging.INFO, logger=generator.logger.name)
    fsync, unlink = os.fsync, os.unlink
    retained = Path("secrets/postgres-passwd.env")
    attempted = []

    def failed_sync(fd):
        if stat.S_ISDIR(os.fstat(fd).st_mode):
            raise OSError("test directory synchronization failed")
        return fsync(fd)

    def denied_unlink(path, *args, **kwargs):
        attempted.append(str(path))
        if path == retained.name:
            raise PermissionError("test rollback unlink denied")
        return unlink(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(generator.os, "fsync", failed_sync)
        patch.setattr(generator.os, "unlink", denied_unlink)
        with pytest.raises(RuntimeError, match="rollback incomplete"):
            render(generator)
    assert {Path(path).name for path in CREDENTIAL_PATHS} <= set(attempted)
    assert retained.exists() and retained.stat().st_nlink == 1
    assert stat.S_IMODE(retained.stat().st_mode) == 0o600
    assert TEST_PASSWORD in retained.read_text()
    assert all(
        not Path(path).exists() for path in CREDENTIAL_PATHS if Path(path) != retained
    )
    assert all(not staging_files(path) for path in CREDENTIAL_PATHS)
    assert not any(r.message.startswith("Generating ") for r in caplog.records)
    original = retained.stat()
    with pytest.raises(RuntimeError, match="incomplete"):
        render(generator)
    assert file_metadata(retained.stat()) == file_metadata(original)


@pytest.mark.parametrize("change", ["permissions", "path"])
def test_changes_during_publication_are_detected(
    generator, monkeypatch, tmp_path, change
):
    """Roll back the set after injected publication-time changes.

    The publisher changes the first file's mode or substitutes its final path.
    Validation rejects the change and removes all remaining attempt-owned names
    while preserving substituted objects and unrelated targets.
    """
    target = tmp_path / "target"
    target.write_bytes(b"unrelated test file")
    target.chmod(0o640)
    saved = tmp_path / "published"
    link = os.link
    count = 0

    def changed_link(*args, **kwargs):
        nonlocal count
        link(*args, **kwargs)
        count += 1
        if count == 1:
            if change == "permissions":
                Path(".env").chmod(0o644)
            else:
                Path(".env").rename(saved)
                Path(".env").symlink_to(target)

    monkeypatch.setattr(generator.os, "link", changed_link)
    with pytest.raises(RuntimeError, match="Cannot secure credential set"):
        render(generator)
    assert all(not staging_files(path) for path in CREDENTIAL_PATHS)
    assert target.read_bytes() == b"unrelated test file"
    assert stat.S_IMODE(target.stat().st_mode) == 0o640
    if change == "path":
        assert Path(".env").is_symlink()
        assert TEST_PASSWORD in saved.read_text()
        assert all(
            not Path(path).exists() for path in CREDENTIAL_PATHS if path != ".env"
        )
    else:
        assert_no_credentials()


def read_env(path):
    return dict(
        line.split("=", 1) for line in Path(path).read_text().splitlines() if line
    )


def assert_shared_values_match():
    environment = read_env(".env")
    accounts = read_env("secrets/dioptra-deployment-rustfs-accounts.env")
    shared_names = {
        "RUSTFS_SECRET_KEY": "RUSTFS_SECRET_KEY",
        "MLFLOW_TRACKING_AWS_SECRET_ACCESS_KEY": "RUSTFS_MLFLOW_TRACKING_PASSWORD",
        "RESTAPI_AWS_SECRET_ACCESS_KEY": "RUSTFS_RESTAPI_PASSWORD",
        "WORKER_AWS_SECRET_ACCESS_KEY": "RUSTFS_WORKER_PASSWORD",
    }
    for environment_name, accounts_name in shared_names.items():
        assert environment[environment_name] == accounts[accounts_name]


@pytest.mark.parametrize(
    "present",
    [
        [".env"],
        ["secrets/postgres-passwd.env"],
        ["secrets/dioptra-deployment-rustfs-accounts.env"],
        CREDENTIAL_PATHS[:2],
        CREDENTIAL_PATHS[::2],
        CREDENTIAL_PATHS[1:],
    ],
)
def test_partial_existing_set_is_never_completed_or_repaired(
    generator, monkeypatch, caplog, present
):
    """Reject every partial existing set before rendering or permission changes.

    Given one or two nonempty credentials, generation preserves their bytes,
    owners and insecure modes, leaves missing members absent and explains how
    to restore a consistent set or remove all members for fresh generation.
    """
    caplog.set_level(logging.INFO, logger=generator.logger.name)
    originals = {}
    for output in present:
        Path(output).write_bytes(b"existing synthetic credential")
        Path(output).chmod(0o644)
        originals[output] = Path(output).stat()

    def unexpected_operation(*args, **kwargs):
        pytest.fail("partial existing credentials must not be rendered or repaired")

    monkeypatch.setattr(generator.JINJA_ENV, "get_template", unexpected_operation)
    monkeypatch.setattr(generator.os, "fchmod", unexpected_operation)
    with pytest.raises(RuntimeError, match="credential set is incomplete") as exc:
        render(generator)
    assert "restore a consistent" in str(exc.value)
    assert "remove all remaining credential outputs" in str(exc.value)
    for output in CREDENTIAL_PATHS:
        if output in present:
            assert file_metadata(Path(output).stat()) == file_metadata(
                originals[output]
            )
            assert Path(output).read_bytes() == b"existing synthetic credential"
        else:
            assert not Path(output).exists()
        assert staging_files(output) == []
    assert repairs(caplog) == []
    assert "skipping" not in caplog.text and "Generating" not in caplog.text


def test_public_entry_point_requires_the_complete_credential_inventory(generator):
    """Reject a credential-only subset passed to the public rendering entry point."""
    selected = [item for item in generator.PASSWORD_FILES if item[1] == Path(".env")]
    with pytest.raises(RuntimeError, match="requires all three credential templates"):
        generator.render_template_files(generator.JINJA_ENV, selected, PASSWORDS)
    assert_no_credentials()


def test_fresh_credentials_share_one_password_mapping(generator):
    """Generate every credential from the same supplied password mapping.

    Given distinct synthetic values for each password, the public entry point
    produces the expected three contents and duplicates shared values exactly.
    """
    passwords = {
        name: f"distinct-{index}-test-only" for index, name in enumerate(PASSWORDS)
    }
    render(generator, passwords=passwords)
    for template, output in generator.PASSWORD_FILES:
        if str(output) not in CREDENTIAL_PATHS:
            continue
        assert output.read_text() == generator._render_template(
            generator.JINJA_ENV, template.as_posix(), passwords
        )
        assert stat.S_IMODE(output.stat().st_mode) == 0o600
        assert output.stat().st_nlink == 1
    assert_shared_values_match()


@pytest.mark.parametrize("member", [0, 1, 2])
@pytest.mark.parametrize("after_link", [False, True])
def test_publication_failure_rolls_back_every_owned_member(
    generator, monkeypatch, caplog, member, after_link
):
    """Roll back the entire set after an injected publication failure.

    Linking fails before or immediately after the selected member is published.
    Every attempt-owned final and staging name disappears, no success is logged,
    and a fresh mapping can generate a complete consistent set on retry.
    """
    caplog.set_level(logging.INFO, logger=generator.logger.name)
    link = os.link
    published = []

    def failed_link(source, destination, **kwargs):
        position = len(published)
        if position == member and not after_link:
            raise OSError("test publication failed before linking")
        link(source, destination, **kwargs)
        published.append(destination)
        if position == member:
            raise OSError("test publication failed after linking")

    with monkeypatch.context() as patch:
        patch.setattr(generator.os, "link", failed_link)
        with pytest.raises(RuntimeError, match="cannot publish"):
            render(generator)
    assert len(published) == member + int(after_link)
    assert_no_credentials()
    assert not any(r.message.startswith("Generating ") for r in caplog.records)
    passwords = dict.fromkeys(PASSWORDS, "publication-retry-only")
    render(generator, passwords=passwords)
    assert all(
        "publication-retry-only" in Path(path).read_text() for path in CREDENTIAL_PATHS
    )
    assert_shared_values_match()


@pytest.mark.parametrize("directory", [0, 1, 2])
def test_directory_sync_failure_rolls_back_the_completed_set(
    generator, monkeypatch, caplog, directory
):
    """Roll back all credentials after an injected directory-sync failure.

    The selected directory synchronization fails after publication and staging
    removal. Generation reports failure, removes every owned final name and
    permits a complete retry with a fresh password mapping.
    """
    caplog.set_level(logging.INFO, logger=generator.logger.name)
    fsync = os.fsync
    synchronized = []

    def failed_sync(fd):
        if stat.S_ISDIR(os.fstat(fd).st_mode):
            assert all(Path(path).exists() for path in CREDENTIAL_PATHS)
            assert all(not staging_files(path) for path in CREDENTIAL_PATHS)
            if len(synchronized) == directory:
                raise OSError("test directory synchronization failed")
            synchronized.append(fd)
        return fsync(fd)

    with monkeypatch.context() as patch:
        patch.setattr(generator.os, "fsync", failed_sync)
        with pytest.raises(RuntimeError, match="directory synchronization failed"):
            render(generator)
    assert len(synchronized) == directory
    assert_no_credentials()
    assert not any(r.message.startswith("Generating ") for r in caplog.records)
    passwords = dict.fromkeys(PASSWORDS, "directory-retry-only")
    render(generator, passwords=passwords)
    assert all(
        "directory-retry-only" in Path(path).read_text() for path in CREDENTIAL_PATHS
    )
    assert_shared_values_match()


def test_later_staging_open_failure_cleans_prepared_members(generator, monkeypatch):
    """Remove earlier staging after an injected failure to create the last member.

    Exclusive opening of the PostgreSQL staging file is denied after the other
    files have been prepared. Generation leaves no final or staging credentials.
    """
    open_file = os.open
    prepared = []

    def failed_open(path, flags, *args, **kwargs):
        if flags & os.O_EXCL:
            if str(path).startswith(".postgres-passwd.env."):
                assert len(prepared) == 2
                raise PermissionError("test last staging open denied")
            prepared.append(str(path))
        return open_file(path, flags, *args, **kwargs)

    monkeypatch.setattr(generator.os, "open", failed_open)
    with pytest.raises(RuntimeError, match="last staging open denied"):
        render(generator)
    assert_no_credentials()


def test_substituted_later_final_is_preserved_while_earlier_members_roll_back(
    generator, monkeypatch, tmp_path
):
    """Preserve a substituted later destination while rolling back owned members.

    An injected publisher replaces the second final name with an unrelated file
    and fails. Cleanup removes earlier owned credentials and every owned staging
    name while preserving the replacement and the renamed complete file.
    """
    link = os.link
    saved = tmp_path / "published"
    replacement = []
    count = 0

    def changed_link(source, destination, **kwargs):
        nonlocal count
        link(source, destination, **kwargs)
        count += 1
        if count == 2:
            output = next(
                Path(path)
                for path in CREDENTIAL_PATHS
                if Path(path).name == destination
            )
            output.rename(saved)
            output.write_bytes(b"unrelated concurrent file")
            output.chmod(0o640)
            replacement.append(output)
            raise OSError("test failure after final substitution")

    monkeypatch.setattr(generator.os, "link", changed_link)
    with pytest.raises(RuntimeError, match="preserved unrelated"):
        render(generator)
    assert count == 2
    assert saved.read_text() and TEST_PASSWORD in saved.read_text()
    assert replacement[0].read_bytes() == b"unrelated concurrent file"
    assert stat.S_IMODE(replacement[0].stat().st_mode) == 0o640
    assert all(
        not Path(path).exists()
        for path in CREDENTIAL_PATHS
        if Path(path) != replacement[0]
    )
    assert all(not staging_files(path) for path in CREDENTIAL_PATHS)


def test_generator_process_creates_and_preserves_a_consistent_set(generator):
    """Generate a complete consistent set through the actual script entry point.

    Two separate invocations use fresh random mappings. The first creates all
    credentials with matching shared values; the second preserves the complete
    existing set's bytes, ownership and protection without printing passwords.
    """
    command = [sys.executable, "scripts/generate_password_templates.py"]
    first = subprocess.run(command, capture_output=True, text=True, timeout=30)
    assert first.returncode == 0
    assert_shared_values_match()
    originals = {
        path: (Path(path).read_bytes(), Path(path).stat()) for path in CREDENTIAL_PATHS
    }
    second = subprocess.run(command, capture_output=True, text=True, timeout=30)
    assert second.returncode == 0
    for path, (content, original) in originals.items():
        assert Path(path).read_bytes() == content
        current = Path(path).stat()
        assert (current.st_ino, current.st_uid, current.st_gid) == (
            original.st_ino,
            original.st_uid,
            original.st_gid,
        )
        assert current.st_nlink == 1 and stat.S_IMODE(current.st_mode) == 0o600
    values = read_env("secrets/dioptra-deployment-rustfs-accounts.env")
    for name, value in values.items():
        if name.endswith(("_PASSWORD", "_SECRET_KEY")):
            assert (
                value not in first.stdout + first.stderr + second.stdout + second.stderr
            )


def test_generator_process_rejects_a_partial_existing_set(generator):
    """Reject partial prior generation through the actual script entry point.

    Given an existing .env alone, a separate process exits nonzero with set
    recovery guidance, preserves that file and creates no missing credentials.
    """
    Path(".env").write_bytes(b"existing synthetic credential")
    original = Path(".env").stat()
    result = subprocess.run(
        [sys.executable, "scripts/generate_password_templates.py"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert "restore a consistent credential set" in result.stderr
    assert "remove all remaining credential outputs" in result.stderr
    assert file_metadata(Path(".env").stat()) == file_metadata(original)
    assert Path(".env").read_bytes() == b"existing synthetic credential"
    assert all(not Path(path).exists() for path in CREDENTIAL_PATHS if path != ".env")
    assert all(not staging_files(path) for path in CREDENTIAL_PATHS)


def test_competing_complete_initializer_is_never_adopted(generator, monkeypatch):
    """Keep a competing initializer's complete set without adopting its values.

    An injected second initializer publishes a fresh set before the first links.
    The first fails and removes only its own staging files; the winner's bytes,
    owners and modes remain unchanged, and later rerun preserves that whole set.
    """
    link = os.link
    competing_passwords = dict.fromkeys(PASSWORDS, "competing-set-only")
    competing = []
    originals = {}

    def competing_link(*args, **kwargs):
        if not competing:
            competing.append(True)
            render(generator, passwords=competing_passwords)
            originals.update(
                {
                    path: (Path(path).read_bytes(), Path(path).stat())
                    for path in CREDENTIAL_PATHS
                }
            )
        return link(*args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(generator.os, "link", competing_link)
        with pytest.raises(RuntimeError, match="preserved unrelated"):
            render(generator)
    assert all(not staging_files(path) for path in CREDENTIAL_PATHS)
    render(generator, passwords=dict.fromkeys(PASSWORDS, "unused-later-values"))
    for path, (content, original) in originals.items():
        assert Path(path).read_bytes() == content
        assert file_metadata(Path(path).stat()) == file_metadata(original)
        assert "competing-set-only" in Path(path).read_text()
    assert_shared_values_match()


@pytest.mark.parametrize("persistent", [False, True])
def test_staging_unlink_failure_rolls_back_all_final_names(
    generator, monkeypatch, persistent
):
    """Roll back all final names after an injected staging-removal failure.

    A one-time unlink error is recovered during rollback. A persistent error
    leaves only protected staging and reports incomplete rollback. A fresh retry
    succeeds with new values while preserving any abandoned staging.
    """
    unlink = os.unlink
    failed = []
    output = "secrets/postgres-passwd.env"

    def failed_unlink(path, *args, **kwargs):
        if str(path).startswith(".postgres-passwd.env.") and (persistent or not failed):
            failed.append(str(path))
            raise PermissionError("test staging unlink failed")
        return unlink(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(generator.os, "unlink", failed_unlink)
        expected = "rollback incomplete" if persistent else "test staging unlink failed"
        with pytest.raises(RuntimeError, match=expected):
            render(generator)
    assert all(not Path(path).exists() for path in CREDENTIAL_PATHS)
    remaining = {
        stage: stage.stat()
        for path in CREDENTIAL_PATHS
        for stage in staging_files(path)
    }
    assert len(remaining) == int(persistent)
    for stage, original in remaining.items():
        assert stage in staging_files(output)
        assert stat.S_IMODE(original.st_mode) == 0o600
        assert original.st_nlink == 1
    passwords = dict.fromkeys(PASSWORDS, "staging-unlink-retry-only")
    render(generator, passwords=passwords)
    assert all(
        "staging-unlink-retry-only" in Path(path).read_text()
        for path in CREDENTIAL_PATHS
    )
    assert all(
        file_metadata(stage.stat()) == file_metadata(original)
        for stage, original in remaining.items()
    )
    assert_shared_values_match()


def test_later_file_sync_failure_rolls_back_the_set(generator, monkeypatch):
    """Roll back every member after an injected later-file synchronization failure.

    PostgreSQL staging synchronization fails after the other streams complete.
    No final or staging names survive, and fresh passwords produce a complete
    consistent set when the fault is removed.
    """
    fsync = os.fsync

    def failed_sync(fd):
        if is_staging_fd(fd, "secrets/postgres-passwd.env"):
            raise OSError("test later-file synchronization failed")
        return fsync(fd)

    with monkeypatch.context() as patch:
        patch.setattr(generator.os, "fsync", failed_sync)
        with pytest.raises(RuntimeError, match="later-file synchronization failed"):
            render(generator)
    assert_no_credentials()
    passwords = dict.fromkeys(PASSWORDS, "file-sync-retry-only")
    render(generator, passwords=passwords)
    assert all(
        "file-sync-retry-only" in Path(path).read_text() for path in CREDENTIAL_PATHS
    )
    assert_shared_values_match()
