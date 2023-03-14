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
from __future__ import annotations

import numpy as np
import pytest


@pytest.mark.parametrize(
    "seed",
    [-200, 400, 42, 0],
)
@pytest.mark.parametrize(
    ("low", "high"),
    [(1, None), (20, None), (200, 204), (-200, 10), (-40, -30), (0, 20), (-20, 0)],
)
def test_draw_random_integer(seed, low, high) -> None:
    from dioptra_builtins.random.sample import draw_random_integer

    rng = np.random.default_rng(seed if seed >= 0 else None)
    if seed < 0:
        seed = rng.bit_generator._seed_seq.entropy

    result: int = draw_random_integer(rng, low, high)

    if high is not None:
        assert low <= result and result < high
    else:
        assert 0 <= result and result < low


@pytest.mark.parametrize(
    "seed",
    [-200, 400, 42, 0],
)
@pytest.mark.parametrize(
    ("low", "high"),
    [(1, None), (20, None), (200, 204), (-200, 10), (-40, -30), (0, 20), (-20, 0)],
)
@pytest.mark.parametrize(
    "size",
    [0, 10, (15, 20), (3, 4, 5), (6, 0, 7)],
)
def test_draw_random_integers(seed, low, high, size) -> None:
    from dioptra_builtins.random.sample import draw_random_integers

    rng = np.random.default_rng(seed if seed >= 0 else None)
    if seed < 0:
        seed = rng.bit_generator._seed_seq.entropy

    result: np.ndarray = draw_random_integers(rng, low, high, size)

    if size == 0:
        size = 1
    if type(size) is not tuple:
        size = (size,)
    assert result.shape == size
