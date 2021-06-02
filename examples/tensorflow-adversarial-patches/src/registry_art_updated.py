from __future__ import annotations

import mlflow
import structlog
from prefect import task
from structlog.stdlib import BoundLogger

from mitre.securingai import pyplugs
from mitre.securingai.sdk.exceptions import (
    ARTDependencyError,
    TensorflowDependencyError,
)
from mitre.securingai.sdk.utilities.decorators import require_package

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


@task
@require_package("art", exc_type=ARTDependencyError)
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def load_wrapped_tensorflow_keras_classifier(
    name: str,
    version: int,
    clip_values: Tuple = None,
    imagenet_preprocessing: bool = False,
) -> KerasClassifier:

    uri = f"models:/{name}/{version}"
    LOGGER.info("Load Keras classifier from model registry", uri=uri)
    keras_classifier = mlflow.keras.load_model(uri)
    if imagenet_preprocessing:
        mean_b = 103.939
        mean_g = 116.779
        mean_r = 123.680

        wrapped_keras_classifier = KerasClassifier(
            model=keras_classifier,
            clip_values=clip_values,
            preprocessing=([mean_b, mean_g, mean_r], 1),
        )
    else:
        wrapped_keras_classifier = KerasClassifier(
            model=keras_classifier, clip_values=clip_values
        )
    LOGGER.info(
        "Wrap Keras classifier for compatibility with Adversarial Robustness Toolbox"
    )

    return wrapped_keras_classifier
