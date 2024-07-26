#!/usr/bin/env python
from __future__ import annotations

import logging
from pathlib import Path
from typing import Final

DATASETS_DIRECTORY: Final[str] = "{{ cookiecutter.datasets_directory }}"

logger = logging.getLogger("pre_gen_project")


def validate_datasets_directory(datasets_directory: str) -> None:
    """Validates the datasets directory"""

    if datasets_directory == "":
        return None

    dir_path = Path(datasets_directory)

    if not dir_path.exists():
        message = f"The provided datasets directory ({dir_path}) does not exist."
        logger.info(message)
        raise FileNotFoundError(message)

    if not dir_path.is_dir():
        message = f"The provided datasets directory ({dir_path}) is not a directory."
        logger.info(message)
        raise NotADirectoryError(message)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    validate_datasets_directory(DATASETS_DIRECTORY)
