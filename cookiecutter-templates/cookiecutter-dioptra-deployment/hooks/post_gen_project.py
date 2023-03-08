#!/usr/bin/env python

import binascii
import logging
import os
import random
import shutil
import unicodedata
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

WORDS_FILE = Path("/usr/share/dict/words")
TEMP_DIRS = ["templates"]
TEMP_FILES = []
BASE_DIRECTORY = Path.cwd()
BASE_DIRECTORY_SYMBOL = "$((BASEDIR))"
PASSWORD_FILES = [
    Path("secrets") / "postgres-passwd.env",
    Path("secrets") / "{{ cookiecutter.__project_slug }}-db.env",
    Path("secrets") / "{{ cookiecutter.__project_slug }}-dbadmin.env",
    Path("secrets") / "{{ cookiecutter.__project_slug }}-minio-accounts.env",
    Path("secrets") / "{{ cookiecutter.__project_slug }}-minio.env",
    Path("secrets") / "{{ cookiecutter.__project_slug }}-mlflow-tracking-database-uri.env",
    Path("secrets") / "{{ cookiecutter.__project_slug }}-mlflow-tracking.env",
    Path("secrets") / "{{ cookiecutter.__project_slug }}-restapi-database-uri.env",
    Path("secrets") / "{{ cookiecutter.__project_slug }}-restapi.env",
    Path("secrets") / "{{ cookiecutter.__project_slug }}-worker.env",
]
JINJA_ENV = Environment(loader=FileSystemLoader([str(BASE_DIRECTORY)]))


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("post_gen_project")


def remove_temp_dirs(temp_dirs):
    for temp_dir_name in temp_dirs:
        logger.info("Removing temporary directory: %s", temp_dir_name)
        shutil.rmtree(temp_dir_name)


def remove_temp_files(temp_files):
    for temp_file_name in temp_files:
        logger.info("Removing temporary file: %s", str(temp_file_name))
        temp_file_name.unlink()


def insert_random_passwords(password_files, words_file, env):
    logger.info("Generating \"Correct Horse Battery Staple\" passwords")

    words = _populate_words(words_file)
    variables = dict(
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
    )

    for filepath in password_files:
        logger.info("Inserting generated passwords in file: %s", str(filepath))

        content = _render_template(
            env=env,
            template_name=str(filepath),
            variables=variables,
        )

        with (BASE_DIRECTORY / filepath).open("wt") as f:
            f.write(content)


def render_absolute_path_to_base_directory():
    logger.info(
        "Scanning files and replacing the \"%s\" symbol with %s",
        BASE_DIRECTORY_SYMBOL,
        str(BASE_DIRECTORY),
    )

    for dirpath, dirnames, filenames in os.walk(BASE_DIRECTORY):
        for filename in filenames:
            filepath = Path(dirpath) / filename

            with filepath.open("rt") as f:
                data = f.read()

            data = data.replace(BASE_DIRECTORY_SYMBOL, str(BASE_DIRECTORY))

            with filepath.open("wt") as f:
                f.write(data)


def _render_template(env, template_name, variables):
    template = env.get_template(template_name)
    return template.render(**variables)


def _generate_random_kms_secret_key(size: int = 32):
    return binascii.b2a_base64(os.urandom(size)).decode()


def _generate_random_password(
    words,
    min_words: int = 4,
    min_length: int = 25,
    delimiter: str = "-",
    capitalize: bool = True,
    append_number: bool = True,
):
    password_components = [
        x.capitalize() if capitalize else x for x in random.sample(words, k=min_words)
    ]
    end_number = (
        [str(x) for x in random.sample(range(10), k=1)] if append_number else []
    )

    password_string: str = delimiter.join(password_components + end_number)

    while len(password_string) <= min_length:
        extra_word: str = [
            x.capitalize() if capitalize else x for x in random.sample(words, k=1)
        ][0]

        while extra_word in password_components:
            extra_word: str = [
                x.capitalize() if capitalize else x for x in random.sample(words, k=1)
            ][0]

        password_components.append(extra_word)
        password_string = delimiter.join(password_components + end_number)

    return password_string


def _populate_words(words_file, source_encoding="utf-8", unicode_normalize_form="NFKD"):
    words = set()

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
    logger.debug("Current working directory: %s", str(BASE_DIRECTORY))

    render_absolute_path_to_base_directory()
    insert_random_passwords(PASSWORD_FILES, WORDS_FILE, JINJA_ENV)
    remove_temp_dirs(TEMP_DIRS)
    remove_temp_files(TEMP_FILES)
