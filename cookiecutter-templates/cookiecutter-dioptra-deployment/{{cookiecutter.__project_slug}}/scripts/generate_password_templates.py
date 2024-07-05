#!/usr/bin/env python
"""Render the Jinja templates containing the deployment's passwords."""
from __future__ import annotations

import binascii
import logging
import os
import random
import string
import unicodedata
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
    return dict(
        minio_mlflow_tracking_password=_generate_random_password(
            words,
            capitalize=False,
            delimiter="_",
        ),
        minio_kms_secret_key=_generate_random_kms_secret_key(size=32),
        minio_root_password=_generate_random_password(words),
        minio_restapi_password=_generate_random_password(
            words,
            capitalize=False,
            delimiter="_",
        ),
        minio_worker_password=_generate_random_password(
            words,
            capitalize=False,
            delimiter="_",
        ),
        pgadmin_default_password=_generate_random_password(
            words,
            capitalize=False,
            delimiter="_",
        ),
        postgres_admin_password=_generate_random_password(
            words,
            min_words=3,
            min_length=20,
        ),
        postgres_user_dioptra_password=_generate_random_password(
            words,
            min_words=3,
            min_length=20,
            capitalize=False,
            delimiter="_",
        ),
        dioptra_worker_password=_generate_random_password(
            words,
            min_words=3,
            min_length=20,
        ),
    )


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
    variables = passwords | dict(working_directory=str(BASE_DIRECTORY))
    for template_name, output_filepath in template_files:
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

    return password_string


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

            is_ascii: bool = all([0 <= ord(char) <= 127 for char in normalized_line])
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
