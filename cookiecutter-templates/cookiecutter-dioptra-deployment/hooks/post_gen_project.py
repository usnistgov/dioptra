#!/usr/bin/env python
from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path

TEMP_DIRS: list[str] = ["templates"]
TEMP_FILES: list[Path] = [Path("secrets", ".gitkeep"), Path("systemd", ".gitkeep")]
BASE_DIRECTORY = Path.cwd()
BASE_DIRECTORY_SYMBOL = "$((BASEDIR))"


logger = logging.getLogger("post_gen_project")


def remove_temp_dirs(temp_dirs: list[str]) -> None:
    for temp_dir_name in temp_dirs:
        logger.info("Removing temporary directory: %s", temp_dir_name)
        shutil.rmtree(temp_dir_name)


def remove_temp_files(temp_files: list[Path]) -> None:
    for temp_file_name in temp_files:
        logger.info("Removing temporary file: %s", str(temp_file_name))
        temp_file_name.unlink()


def render_absolute_path_to_base_directory() -> None:
    logger.info(
        'Scanning files and replacing the "%s" symbol with %s',
        BASE_DIRECTORY_SYMBOL,
        str(BASE_DIRECTORY),
    )

    for dirpath, _, filenames in os.walk(BASE_DIRECTORY):
        for filename in filenames:
            filepath = Path(dirpath) / filename

            with filepath.open("rt", encoding="utf-8") as f:
                data = f.read()

            data = data.replace(BASE_DIRECTORY_SYMBOL, str(BASE_DIRECTORY))

            with filepath.open("wt", encoding="utf-8") as f:
                f.write(data)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger.debug("Current working directory: %s", str(BASE_DIRECTORY))
    render_absolute_path_to_base_directory()
    remove_temp_dirs(TEMP_DIRS)
    remove_temp_files(TEMP_FILES)
