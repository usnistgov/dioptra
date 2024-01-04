#!/usr/bin/env python

import binascii
import logging
import os
import random
import string
import sys
import unicodedata
from cookiecutter.main import cookiecutter
from pathlib import Path

WORDS_FILE = Path("/usr/share/dict/words")
TEMP_DIRS = ["templates"]
BASE_DIRECTORY = Path.cwd()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("dioptra-deploy")


def get_random_passwords(words_file):
    logger.info("Generating \"Correct Horse Battery Staple\" passwords")

    words = _populate_words(words_file)
    variables = dict(
        __minio_mlflow_tracking_password=_generate_random_password(
            words,
            capitalize=False,
            delimiter="_",
        ),
        __minio_kms_secret_key=_generate_random_kms_secret_key(size=32),
        __minio_root_password=_generate_random_password(words),
        __minio_restapi_password=_generate_random_password(
            words,
            capitalize=False,
            delimiter="_",
        ),
        __minio_worker_password=_generate_random_password(
            words,
            capitalize=False,
            delimiter="_",
        ),
        __pgadmin_default_password=_generate_random_password(
            words,
            capitalize=False,
            delimiter="_",
        ),
        __postgres_admin_password=_generate_random_password(
            words,
            min_words=3,
            min_length=20,
        ),
        __postgres_user_dioptra_password=_generate_random_password(
            words,
            min_words=3,
            min_length=20,
            capitalize=False,
            delimiter="_",
        ),
    )

    return variables


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

            is_ascii: bool = all(
                [0 <= ord(char) <= 127 for char in normalized_line]
            )
            is_not_plural: bool = not normalized_line.endswith("'s")
            is_not_short: bool = len(normalized_line) >= 4

            if is_ascii and is_not_plural and is_not_short:
                words.add(normalized_line)

    return list(words)


if __name__ == "__main__":
    script_path = Path(sys.argv[0])
    template_path = script_path.with_name("cookiecutter-dioptra-deployment")

    logger.debug("Current working directory: %s", str(BASE_DIRECTORY))
    logger.debug("Template directory: %s", str(template_path))

    extra_context = {
        "__base_directory": str(BASE_DIRECTORY)
    }
    passwords = get_random_passwords(WORDS_FILE)
    extra_context.update(passwords)

    cookiecutter(str(template_path), extra_context=extra_context)
