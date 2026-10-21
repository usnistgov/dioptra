#!/usr/bin/env python
"""Render the Jinja templates containing the deployment's passwords."""

from __future__ import annotations

import binascii
import logging
import os
import random
import secrets
import stat
import string
import unicodedata
import urllib.parse as URL
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

WORDS_FILE = Path("/usr/share/dict/words")
BASE_DIRECTORY = Path.cwd()
PASSWORD_FILES: list[tuple[Path, Path]] = [
    (Path("scripts", "templates", "dot-env.j2"), Path(".env")),
    (
        Path("scripts", "templates", "postgres-passwd.env.j2"),
        Path("secrets", "postgres-passwd.env"),
    ),
    (
        Path("scripts", "templates", "minio-accounts.env.j2"),
        Path("secrets", "{{ cookiecutter.__project_slug }}-minio-accounts.env"),
    ),
    (
        Path("scripts", "templates", "dioptra.service.j2"),
        Path("systemd", "dioptra.service"),
    ),
]

CREDENTIAL_FILES = {
    Path(".env"),
    Path("secrets", "postgres-passwd.env"),
    Path("secrets", "{{ cookiecutter.__project_slug }}-minio-accounts.env"),
}

JINJA_ENV = Environment(loader=FileSystemLoader([str(BASE_DIRECTORY)]))


logger = logging.getLogger("generate_password_templates.py")


def generate_random_passwords(words_file: str | Path) -> dict[str, Any]:
    """Generate random passwords to apply to the Jinja templates.

    Args:
        words_file: Path to a dictionary file containing a list of words.

    Returns:
        A dictionary containing the generated passwords.
    """
    logger.info('Generating "Correct Horse Battery Staple" passwords')
    words = _populate_words(words_file)
    return {
        "minio_mlflow_tracking_password": _generate_random_password(
            words,
            capitalize=False,
            delimiter="_",
        ),
        "minio_kms_secret_key": _generate_random_kms_secret_key(size=32),
        "minio_root_password": _generate_random_password(words),
        "minio_restapi_password": _generate_random_password(
            words,
            capitalize=False,
            delimiter="_",
        ),
        "minio_worker_password": _generate_random_password(
            words,
            capitalize=False,
            delimiter="_",
        ),
        "pgadmin_default_password": _generate_random_password(
            words,
            capitalize=False,
            delimiter="_",
        ),
        "postgres_admin_password": _generate_random_password(
            words,
            min_words=3,
            min_length=20,
        ),
        "postgres_user_dioptra_password": _generate_random_password(
            words,
            min_words=3,
            min_length=20,
            capitalize=False,
            delimiter="_",
        ),
        "dioptra_worker_password": _generate_random_password(
            words,
            min_words=3,
            min_length=20,
        ),
    }


def render_template_files(
    env: Environment,
    template_files: list[tuple[Path, Path]],
    passwords: dict[str, Any],
) -> None:
    """Render the Jinja template files.

    Args:
        env: A Jinja2 environment object.
        template_files: A list of tuples containing the template name and output
            filepath.
        passwords: A dictionary of template variable to password mappings.
    """
    variables = passwords | {"working_directory": str(BASE_DIRECTORY)}
    credential_templates = [
        (template, output)
        for template, output in template_files
        if output in CREDENTIAL_FILES
    ]
    if credential_templates:
        _render_credential_templates(env, credential_templates, variables)

    for template_name, output_filepath in template_files:
        if output_filepath in CREDENTIAL_FILES:
            continue

        if (BASE_DIRECTORY / output_filepath).exists():
            logger.info("The file %s already exists, skipping", str(output_filepath))
            continue

        logger.info("Generating %s", output_filepath)
        content = _render_template(
            env=env,
            # Jinja2 requires forward slashes in the template name.
            template_name=str(template_name.as_posix()),
            variables=variables,
        )

        with (BASE_DIRECTORY / output_filepath).open("wt") as f:
            f.write(content)


@contextmanager
def _credential_directory(output_filepath: Path) -> Iterator[int]:
    """Open the credential's parent directory one component at a time.

    A directory descriptor identifies an already opened directory. Passing it as
    dir_fd resolves a relative name from that directory. Open BASE_DIRECTORY first,
    then open each relative parent component with O_DIRECTORY and O_NOFOLLOW so
    links cannot redirect those opens. Keep every descriptor open through the
    credential operation and close them on every exit.
    """
    if not all(
        hasattr(os, name)
        for name in (
            "O_DIRECTORY",
            "O_NOFOLLOW",
            "O_NONBLOCK",
            "fchmod",
            "fsync",
            "link",
            "unlink",
        )
    ):
        raise OSError(
            "credential protection requires POSIX no-follow file opening and "
            "file-descriptor permission/synchronization operations and hard-link "
            "publication, which are unavailable"
        )
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    with ExitStack() as directories:
        directory_fd = os.open(BASE_DIRECTORY, flags)
        directories.callback(os.close, directory_fd)
        for part in output_filepath.parts[:-1]:
            directory_fd = os.open(part, flags, dir_fd=directory_fd)
            directories.callback(os.close, directory_fd)
        yield directory_fd


def _check_credential_file(
    fd: int, directory_fd: int, output_filepath: Path
) -> os.stat_result:
    """Check regular-file type, link count and current path identity."""
    opened = os.fstat(fd)
    # The descriptor retains the opened object's identity. Check both paths to
    # detect observed replacements, including a renamed parent directory.
    # These separate checks do not lock files; deployment directories must be trusted.
    named = os.stat(output_filepath.name, dir_fd=directory_fd, follow_symlinks=False)
    current = (BASE_DIRECTORY / output_filepath).lstat()
    if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
        raise OSError(
            f"expected a regular credential file with no hard links at {output_filepath}"
        )
    if any(
        (info.st_dev, info.st_ino) != (opened.st_dev, opened.st_ino)
        for info in (named, current)
    ):
        raise OSError(
            f"credential path changed during initialization for {output_filepath}; "
            "rerun safely"
        )
    return opened


def _confirm_credential_protection(
    fd: int,
    directory_fd: int,
    output_filepath: Path,
    original: os.stat_result,
) -> None:
    """Confirm mode 0600, unchanged ownership and the opened file's identity."""
    current = _check_credential_file(fd, directory_fd, output_filepath)
    if stat.S_IMODE(current.st_mode) != 0o600 or (
        current.st_uid,
        current.st_gid,
    ) != (original.st_uid, original.st_gid):
        raise OSError(
            f"could not confirm mode 0600 and unchanged ownership for {output_filepath}"
        )


def _remove_owned_credential(fd: int, directory_fd: int, filepath: Path) -> bool:
    """Unlink a matching inode, accepting absence and preserving unrelated objects.

    The caller retains the descriptor through cleanup. Identity checks and unlink
    require trusted deployment directories; they do not lock out external writers.
    """
    try:
        named = os.stat(filepath.name, dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        return True
    opened = os.fstat(fd)
    if (named.st_dev, named.st_ino) != (opened.st_dev, opened.st_ino):
        return False
    os.unlink(filepath.name, dir_fd=directory_fd)
    return True


def _write_credential_staging(
    fd: int, directory_fd: int, staging: Path, content: str
) -> os.stat_result:
    """Write and synchronize staging using a descriptor owned by the caller.

    The stream owns only its buffers. Flush, file synchronization and stream
    closure must all succeed before any credential destination is published.
    """
    original = _check_credential_file(fd, directory_fd, staging)
    if stat.S_IMODE(original.st_mode) != 0o600:
        os.fchmod(fd, 0o600)
    _confirm_credential_protection(fd, directory_fd, staging, original)
    with os.fdopen(fd, "w", closefd=False) as stream:
        if stream.write(content) != len(content):
            raise OSError("credential stream did not write the complete content")
        stream.flush()
        os.fsync(fd)
    _confirm_credential_protection(fd, directory_fd, staging, original)
    return original


def _inspect_credential_files(
    template_files: list[tuple[Path, Path]],
    directory_fds: dict[Path, int],
    resources: ExitStack,
) -> dict[Path, tuple[int, os.stat_result]]:
    """Inspect all existing credentials with descriptors owned by resources."""
    existing_files = {}
    for _, output in template_files:
        try:
            fd = os.open(
                output.name,
                os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                dir_fd=directory_fds[output],
            )
        except FileNotFoundError:
            continue
        resources.callback(os.close, fd)
        existing_files[output] = (
            fd,
            _check_credential_file(fd, directory_fds[output], output),
        )
    if existing_files and (
        len(existing_files) != len(CREDENTIAL_FILES)
        or any(original.st_size == 0 for _, original in existing_files.values())
    ):
        raise OSError(
            "credential set is incomplete or contains an empty file; inspect "
            "all three paths and restore a consistent credential set, or "
            "remove all remaining credential outputs only if fresh "
            "generation is appropriate"
        )
    return existing_files


def _preserve_credential_files(
    existing_files: dict[Path, tuple[int, os.stat_result]],
    directory_fds: dict[Path, int],
) -> None:
    """Repair a complete set without writing contents or taking descriptor ownership."""
    repaired = []
    for output, (fd, original) in existing_files.items():
        _check_credential_file(fd, directory_fds[output], output)
        old_mode = stat.S_IMODE(original.st_mode)
        if old_mode != 0o600:
            try:
                os.fchmod(fd, 0o600)
            except (OSError, NotImplementedError) as exc:
                raise OSError(f"cannot repair permissions for {output}: {exc}") from exc
            repaired.append((output, old_mode))
        _confirm_credential_protection(fd, directory_fds[output], output, original)
    for output, (fd, original) in existing_files.items():
        _confirm_credential_protection(fd, directory_fds[output], output, original)
    for output, old_mode in repaired:
        logger.info("Repaired permissions for %s from %04o to 0600", output, old_mode)
    for output in existing_files:
        logger.info("The file %s already exists, skipping", output)


def _publish_credential_files(
    staged_files: dict[Path, tuple[Path, int]],
    original_files: dict[Path, os.stat_result],
    directory_fds: dict[Path, int],
) -> None:
    """Publish and synchronize the set while the caller retains all descriptors."""
    for output, (staging, fd) in staged_files.items():
        _confirm_credential_protection(
            fd, directory_fds[output], staging, original_files[output]
        )
    for output, (staging, _) in staged_files.items():
        try:
            os.link(
                staging.name,
                output.name,
                src_dir_fd=directory_fds[output],
                dst_dir_fd=directory_fds[output],
                follow_symlinks=False,
            )
        except (OSError, NotImplementedError) as exc:
            raise OSError(
                f"cannot publish {output} without replacing an existing file; "
                f"same-directory hard-link support is required: {exc}"
            ) from exc
    for output, (staging, fd) in staged_files.items():
        if not _remove_owned_credential(fd, directory_fds[output], staging):
            raise OSError(
                f"credential staging path changed; preserved unrelated {staging}"
            )
        _confirm_credential_protection(
            fd, directory_fds[output], output, original_files[output]
        )
    for directory_fd in directory_fds.values():
        os.fsync(directory_fd)
    for output, (_, fd) in staged_files.items():
        _confirm_credential_protection(
            fd, directory_fds[output], output, original_files[output]
        )


def _rollback_credential_files(
    staged_files: dict[Path, tuple[Path, int]], directory_fds: dict[Path, int]
) -> None:
    """Attempt every owned-name removal before reporting any cleanup failure."""
    cleanup_errors, preserved_paths = [], []
    for output, (staging, fd) in reversed(staged_files.items()):
        for filepath in (output, staging):
            try:
                if not _remove_owned_credential(fd, directory_fds[output], filepath):
                    preserved_paths.append(str(filepath))
            except (OSError, NotImplementedError) as cleanup_error:
                cleanup_errors.append(f"{filepath}: {cleanup_error}")
    if cleanup_errors:
        raise OSError(
            "credential rollback incomplete; inspect the credential set "
            "before rerunning: "
            + "; ".join(
                cleanup_errors
                + [f"preserved unrelated {path}" for path in preserved_paths]
            )
        )
    if preserved_paths:
        raise OSError(
            "credential generation failed; preserved unrelated paths: "
            + ", ".join(preserved_paths)
        )


def _render_credential_templates(
    env: Environment,
    template_files: list[tuple[Path, Path]],
    variables: dict[str, Any],
) -> None:
    """Preserve a complete existing set or prepare and publish all credentials.

    One ExitStack owns every directory and file descriptor through validation,
    publication and rollback. Caught creation failures remove only attempt-owned
    names. SIGKILL and power loss can leave partial sets, which reruns reject.
    """
    try:
        if (
            len(template_files) != len(CREDENTIAL_FILES)
            or {output for _, output in template_files} != CREDENTIAL_FILES
        ):
            raise OSError(
                "credential generation requires all three credential templates"
            )
        # Cooperating initializers compete for the same first destination.
        template_files = sorted(template_files, key=lambda item: item[1].as_posix())
        with ExitStack() as resources:
            directory_fds = {
                output: resources.enter_context(_credential_directory(output))
                for _, output in template_files
            }

            # Inspect and preserve the whole existing set before generating anything.
            existing_files = _inspect_credential_files(
                template_files, directory_fds, resources
            )
            if existing_files:
                _preserve_credential_files(existing_files, directory_fds)
                return

            # Render all three before preparing any protected staging files.
            contents = [
                (output, _render_template(env, template.as_posix(), variables))
                for template, output in template_files
            ]
            if any(not content for _, content in contents):
                raise OSError(
                    "rendered credential content is empty; inspect the templates"
                )
            staged_files: dict[Path, tuple[Path, int]] = {}
            original_files = {}
            try:
                for output, content in contents:
                    staging = output.with_name(
                        f".{output.name}.{secrets.token_hex(16)}.tmp"
                    )
                    fd = os.open(
                        staging.name,
                        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                        0o600,
                        dir_fd=directory_fds[output],
                    )
                    resources.callback(os.close, fd)
                    # Register candidate final names before writing or calling link.
                    staged_files[output] = (staging, fd)
                    original_files[output] = _write_credential_staging(
                        fd, directory_fds[output], staging, content
                    )

                # Publish all three, then validate and synchronize the completed set.
                _publish_credential_files(staged_files, original_files, directory_fds)
            except BaseException:
                _rollback_credential_files(staged_files, directory_fds)
                raise
            for output in staged_files:
                logger.info("Generating %s", output)
    except (OSError, NotImplementedError) as exc:
        raise RuntimeError(
            f"Cannot secure credential set: {exc}. "
            "Check that credential paths are ordinary files without links and that "
            "the deployment user can access them and set their permissions. "
            "Inspect and restore a consistent credential set, or remove all remaining "
            "credential outputs only if fresh generation is appropriate, then rerun "
            "init-deployment.sh."
        ) from exc


def _render_template(
    env: Environment, template_name: str, variables: dict[str, Any]
) -> str:
    """Render a Jinja template.

    Args:
        env: A Jinja2 environment object.
        template_name: Name of the template file.
        variables: A dictionary of template variable to password mappings.
    """
    template = env.get_template(template_name)
    return template.render(**variables)


def _generate_random_kms_secret_key(size: int = 32) -> str:
    """Generate a random KMS secret key.

    Args:
        size: The size of the secret key in bytes.

    Returns:
        A random KMS secret key encoded as a base64 string.
    """
    return binascii.b2a_base64(os.urandom(size)).decode().strip()


def _generate_random_password(
    words: list[str],
    min_words: int = 4,
    min_length: int = 25,
    delimiter: str = "-",
    capitalize: bool = True,
    append_number: bool = True,
) -> str:
    """Generate a random password.

    Args:
        words: A list of words.
        min_words: The minimum number of words to use in the password.
        min_length: The minimum length of the password.
        delimiter: The delimiter to use between words.
        capitalize: Whether to capitalize the first letter of each word.
        append_number: Whether to append a random number to the end of the password.

    Returns:
        A random password.
    """
    password_components = [
        x.capitalize() if capitalize else x for x in random.sample(words, k=min_words)
    ]
    end_number = (
        [str(x) for x in random.sample(range(10), k=1)] if append_number else []
    )

    password_string = delimiter.join(password_components + end_number)

    while len(password_string) <= min_length:
        extra_word = [
            x.capitalize() if capitalize else x for x in random.sample(words, k=1)
        ][0]

        while extra_word in password_components:
            extra_word = [
                x.capitalize() if capitalize else x for x in random.sample(words, k=1)
            ][0]

        password_components.append(extra_word)
        password_string = delimiter.join(password_components + end_number)

    password_string = _password_encoding(password_string)
    return password_string


def _password_encoding(password):

    key = "word"
    ue_param = URL.urlencode({key: password})
    url_safe_word = ue_param[len(key) + 1 :]

    return url_safe_word


def _populate_words(
    words_file: str | Path,
    source_encoding: str = "utf-8",
    unicode_normalize_form: str = "NFKD",
) -> list[str]:
    """Populate a list of words from a dictionary file.

    If the dictionary file does not exist, a list of "words" made up of randomized
    lowercase ASCII characters will be generated and returned instead.

    Args:
        words_file: Path to a dictionary file containing a list of words.
        source_encoding: The encoding of the dictionary file.
        unicode_normalize_form: The unicode normalization form to apply to the
            dictionary file.

    Returns:
        A list of words.
    """
    words = set()

    # if dictionary file does not exist, fall back to random words
    if not Path(words_file).exists():
        chars = list(string.ascii_lowercase)
        for _ in range(int(10000)):
            length = random.randint(4, 8)
            word = "".join(random.choices(chars, k=length))

            words.add(word)

        return list(words)

    with open(words_file, "rb") as f:
        for line in f:
            normalized_line: str = unicodedata.normalize(
                unicode_normalize_form,
                line.decode(source_encoding).lower().strip(),
            )

            is_ascii: bool = all(0 <= ord(char) <= 127 for char in normalized_line)
            is_not_plural: bool = not normalized_line.endswith("'s")
            is_not_short: bool = len(normalized_line) >= 4

            if is_ascii and is_not_plural and is_not_short:
                words.add(normalized_line)

    return list(words)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger.info("Current working directory: %s", str(BASE_DIRECTORY))
    passwords = generate_random_passwords(WORDS_FILE)
    render_template_files(JINJA_ENV, PASSWORD_FILES, passwords)
