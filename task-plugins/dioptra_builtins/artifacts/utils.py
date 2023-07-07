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
"""A task plugin module containing generic utilities for managing artifacts."""

from __future__ import annotations

import os
import tarfile
import uuid
from pathlib import Path
from tarfile import TarFile
from typing import Any, List, Union

import structlog
from structlog.stdlib import BoundLogger

from dioptra import pyplugs

LOGGER: BoundLogger = structlog.stdlib.get_logger()


def is_within_directory(directory: Union[str, Path], target: Union[str, Path]) -> bool:
    abs_directory = os.path.abspath(directory)
    abs_target = os.path.abspath(target)

    prefix = os.path.commonprefix([abs_directory, abs_target])

    return prefix == abs_directory


def safe_extract(tar: TarFile, path: Union[str, Path] = ".") -> None:
    for member in tar.getmembers():
        member_path = os.path.join(path, member.name)
        if not is_within_directory(path, member_path):
            raise Exception("Attempted Path Traversal in Tar File")

    tar.extractall(path, members=None, numeric_owner=False)


@pyplugs.register
def extract_tarfile(
    filepath: Union[str, Path],
    tarball_read_mode: str = "r:gz",
    output_dir: Any = None,
) -> None:
    """Extracts a tarball archive into the current working directory.

    Args:
        filepath: The location of the tarball archive file provided as a string or a
            :py:class:`~pathlib.Path` object.
        tarball_read_mode: The read mode for the tarball, see :py:func:`tarfile.open`
            for the full list of compression options. The default is `"r:gz"` (gzip
            compression).

    See Also:
        - :py:func:`tarfile.open`
    """
    output_dir = Path(output_dir) if output_dir is not None else Path.cwd()

    filepath = Path(filepath)
    with tarfile.open(filepath, tarball_read_mode) as f:
        safe_extract(f, path=output_dir)


@pyplugs.register
def make_directories(dirs: List[Union[str, Path]]) -> None:
    """Creates directories if they do not exist.

    Args:
        dirs: A list of directories provided as strings or :py:class:`~pathlib.Path`
            objects.
    """
    for d in dirs:
        d = Path(d)
        d.mkdir(parents=True, exist_ok=True)
        LOGGER.info("Directory created", directory=d)


@pyplugs.register
def extract_tarfile_in_unique_subdir(
    filepath: Union[str, Path],
    tarball_read_mode: str = "r:gz",
) -> Path:
    """Extracts a tarball archive into a unique subdirectory of the
    current working directory.

    Args:
        filepath: The location of the tarball archive file provided as a string or a
            :py:class:`~pathlib.Path` object.
        tarball_read_mode: The read mode for the tarball, see :py:func:`tarfile.open`
            for the full list of compression options. The default is `"r:gz"` (gzip
            compression).

    See Also:
        - :py:func:`tarfile.open`
    """
    output_dir = Path(uuid.uuid4().hex)
    output_dir.mkdir(mode=0o700, parents=True, exist_ok=True)

    filepath = Path(filepath)
    with tarfile.open(filepath, tarball_read_mode) as f:
        safe_extract(f, path=output_dir)
    return output_dir
