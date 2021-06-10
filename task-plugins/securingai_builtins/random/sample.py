# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
"""A task plugin module for drawing random samples."""

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
    """Returns a random integer from `low` (inclusive) to `high` (exclusive).

    The integer is sampled from a uniform distribution.

    Args:
        rng: A random number generator returned by :py:func:`~.rng.init_rng`.
        low: Lowest (signed) integers to be drawn from the distribution (unless
            `high=None`, in which case this parameter is `0` and this value is used for
            `high`).
        high: If not `None`, one above the largest (signed) integer to be drawn from the
            distribution (see above for behavior if `high=None`)

    Returns:
        A random integer.

    See Also:
        - :py:meth:`numpy.random.Generator.integers`
    """
    result: int = int(rng.integers(low=low, high=high))

    return result


@pyplugs.register
def draw_random_integers(
    rng: RNGenerator,
    low: int = 0,
    high: int = 2 ** 31 - 1,
    size: Optional[Union[int, Tuple[int, ...]]] = None,
) -> np.ndarray:
    """Returns random integers from `low` (inclusive) to `high` (exclusive).

    The integers are sampled from a uniform distribution.

    Args:
        rng: A random number generator returned by :py:func:`~.rng.init_rng`.
        low: Lowest (signed) integers to be drawn from the distribution (unless
            `high=None`, in which case this parameter is `0` and this value is used for
            `high`).
        high: If not `None`, one above the largest (signed) integer to be drawn from the
            distribution (see above for behavior if `high=None`).
        size: The output shape of array. If the given shape is, e.g., `(m, n, k)`, then
            `m * n * k` samples are drawn. If `None`, a single value is returned. The
            default is `None`.

    Returns:
        A `size`-shaped array of random integers.

    See Also:
        - :py:meth:`numpy.random.Generator.integers`
    """
    size = size or 1
    result: np.ndarray = rng.integers(low=low, high=high, size=size)

    return result
