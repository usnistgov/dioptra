from __future__ import annotations

from typing import Tuple

import numpy as np
import structlog
from numpy.random._generator import Generator as RNGenerator
from structlog.stdlib import BoundLogger

from mitre.securingai import pyplugs

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pyplugs.register
@pyplugs.task_nout(2)
def init_rng(seed: int = -1) -> Tuple[int, RNGenerator]:
    rng = np.random.default_rng(seed if seed >= 0 else None)

    if seed < 0:
        seed = rng.bit_generator._seed_seq.entropy

    return int(seed), rng
