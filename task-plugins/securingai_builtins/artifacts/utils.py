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
    filepath = Path(filepath)
    with tarfile.open(filepath, tarball_read_mode) as f:
        f.extractall(path=Path.cwd())


@pyplugs.register
def make_directories(dirs: List[Union[str, Path]]) -> None:
    for d in dirs:
        d = Path(d)
        d.mkdir(parents=True, exist_ok=True)
        LOGGER.info("Directory created", directory=d)
