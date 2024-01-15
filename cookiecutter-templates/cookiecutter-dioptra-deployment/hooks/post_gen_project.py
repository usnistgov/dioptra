#!/usr/bin/env python

import logging
import shutil


TEMP_DIRS = ["templates"]
TEMP_FILES = []

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


if __name__ == "__main__":
    remove_temp_dirs(TEMP_DIRS)
    remove_temp_files(TEMP_FILES)
