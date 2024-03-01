#!/usr/bin/env python
from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Final

TEMP_DIRS: Final[list[str]] = ["templates"]
TEMP_FILES: Final[list[Path]] = [
    Path("secrets", ".gitkeep"),
    Path("systemd", ".gitkeep"),
]


logger = logging.getLogger("post_gen_project")


def remove_temp_dirs(temp_dirs: list[str]) -> None:
    for temp_dir_name in temp_dirs:
        logger.info("Removing temporary directory: %s", temp_dir_name)
        shutil.rmtree(temp_dir_name)


def remove_temp_files(temp_files: list[Path]) -> None:
    for temp_file_name in temp_files:
        logger.info("Removing temporary file: %s", str(temp_file_name))
        temp_file_name.unlink()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    remove_temp_dirs(TEMP_DIRS)
    remove_temp_files(TEMP_FILES)
