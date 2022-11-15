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
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Iterator, List

ENV_VAR_PLUGIN_DIR = "DIOPTRA_PLUGIN_DIR"


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
