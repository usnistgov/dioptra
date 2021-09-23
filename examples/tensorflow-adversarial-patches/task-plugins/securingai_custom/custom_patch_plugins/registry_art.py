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

import mlflow
import structlog
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


@pyplugs.register
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
