"""A task plugin module containing generic utilities for managing artifacts."""

from __future__ import annotations

import tarfile
from pathlib import Path
from typing import List, Union

import structlog
from structlog.stdlib import BoundLogger

from mitre.securingai import pyplugs

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pyplugs.register
def extract_tarfile(
    filepath: Union[str, Path], tarball_read_mode: str = "r:gz"
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
    filepath = Path(filepath)
    with tarfile.open(filepath, tarball_read_mode) as f:
        f.extractall(path=Path.cwd())


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
