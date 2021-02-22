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
    keras_classifier: Sequential = load_tensorflow_keras_classifier(
        name=name, version=version
    )
    wrapped_keras_classifier: KerasClassifier = KerasClassifier(model=keras_classifier)
    LOGGER.info(
        "Wrap Keras classifier for compatibility with Adversarial Robustness Toolbox"
    )

    return wrapped_keras_classifier
