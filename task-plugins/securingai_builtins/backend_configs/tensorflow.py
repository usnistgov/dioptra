"""A task plugin module for initializing and configuring Tensorflow."""

from __future__ import annotations

import structlog
from structlog.stdlib import BoundLogger

from mitre.securingai import pyplugs
from mitre.securingai.sdk.exceptions import TensorflowDependencyError
from mitre.securingai.sdk.utilities.decorators import require_package

LOGGER: BoundLogger = structlog.stdlib.get_logger()


try:
    import tensorflow as tf

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


@pyplugs.register
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def init_tensorflow(seed: int) -> None:
    """Initializes Tensorflow to ensure compatibility and reproducibility.

    This task plugin **must** be run before any other features from Tensorflow are used.
    It disables Tensorflow's eager execution, which is not compatible with the Testbed's
    entry point structure, and sets Tensorflow's internal seed for its random number
    generator.

    Args:
        seed: The seed to use for Tensorflow's random number generator.
    """
    tf.compat.v1.disable_eager_execution()
    tf.random.set_seed(seed)
