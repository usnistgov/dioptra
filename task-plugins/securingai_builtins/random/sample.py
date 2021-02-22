from __future__ import annotations

from typing import Optional, Tuple, Union

import numpy as np
import structlog
from numpy.random._generator import Generator as RNGenerator
from structlog.stdlib import BoundLogger

from mitre.securingai import pyplugs

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pyplugs.register
def draw_random_integer(rng: RNGenerator, low: int = 0, high: int = 2 ** 31 - 1) -> int:
    result: int = int(rng.integers(low=low, high=high))

    return result


@pyplugs.register
def draw_random_integers(
    rng: RNGenerator,
    low: int = 0,
    high: int = 2 ** 31 - 1,
    size: Optional[Union[int, Tuple[int, ...]]] = None,
) -> np.ndarray:
    size = size or 1
    result: np.ndarray = rng.integers(low=low, high=high, size=size)

    return result
