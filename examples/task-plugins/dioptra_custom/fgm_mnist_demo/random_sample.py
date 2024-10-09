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
"""A task plugin module for drawing random samples."""

from __future__ import annotations

from typing import Optional, Tuple, Union

import numpy as np
import structlog
from numpy.random._generator import Generator as RNGenerator
from structlog.stdlib import BoundLogger

from dioptra import pyplugs

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pyplugs.register
def draw_random_integer(rng: RNGenerator, low: int = 0, high: int = 2**31 - 1) -> int:
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
    high: int = 2**31 - 1,
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
