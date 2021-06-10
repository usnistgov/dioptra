# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Iterator, List

ENV_VAR_PLUGIN_DIR = "AI_PLUGIN_DIR"


@contextmanager
def plugin_dirs(dirs: Iterable[str] = (".",)) -> Iterator[None]:
    sys_path_copy: List[str] = sys.path.copy()
    env_var_dirs: List[str] = [
        str(Path(x).resolve())
        for x in os.getenv(ENV_VAR_PLUGIN_DIR, default="").split(":")
        if x
        and Path(x).is_absolute()
        and Path(x).resolve().is_dir()
        and str(Path(x).resolve()) not in sys.path
    ]
    dirs = [
        str(Path(x).resolve())
        for x in dirs
        if x and Path(x).resolve().is_dir() and str(Path(x).resolve()) not in sys.path
    ]

    try:
        sys.path = _remove_duplicate_paths(
            [*sys.path[:1], *env_var_dirs, *dirs, *sys.path[1:]]
        )
        yield

    finally:
        sys.path = sys_path_copy


def _remove_duplicate_paths(dirs: Iterable[str]) -> List[str]:
    return list(dict.fromkeys(dirs))
