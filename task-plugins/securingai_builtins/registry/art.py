# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
"""A task plugin module for interfacing the |ART| with the MLFlow model registry.

.. |ART| replace:: `Adversarial Robustness Toolbox\
   <https://adversarial-robustness-toolbox.readthedocs.io/en/latest/>`__
"""

from __future__ import annotations

import structlog
from structlog.stdlib import BoundLogger

from mitre.securingai import pyplugs
from mitre.securingai.sdk.exceptions import (
    ARTDependencyError,
    TensorflowDependencyError,
)
from mitre.securingai.sdk.utilities.decorators import require_package

from .mlflow import load_tensorflow_keras_classifier

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    from art.estimators.classification import KerasClassifier

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="art",
    )


try:
    from tensorflow.keras.models import Sequential

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


@pyplugs.register
@require_package("art", exc_type=ARTDependencyError)
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def load_wrapped_tensorflow_keras_classifier(
    name: str, version: int
) -> KerasClassifier:
    """Loads and wraps a registered Keras classifier for compatibility with the |ART|.

    Args:
        name: The name of the registered model in the MLFlow model registry.
        version: The version number of the registered model in the MLFlow registry.

    Returns:
        A trained :py:class:`~art.estimators.classification.KerasClassifier` object.

    See Also:
        - :py:class:`art.estimators.classification.KerasClassifier`
        - :py:func:`.mlflow.load_tensorflow_keras_classifier`
    """
    keras_classifier: Sequential = load_tensorflow_keras_classifier(
        name=name, version=version
    )
    wrapped_keras_classifier: KerasClassifier = KerasClassifier(model=keras_classifier)
    LOGGER.info(
        "Wrap Keras classifier for compatibility with Adversarial Robustness Toolbox"
    )

    return wrapped_keras_classifier
