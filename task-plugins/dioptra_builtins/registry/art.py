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
"""A task plugin module for interfacing the |ART| with the MLFlow model registry.

.. |ART| replace:: `Adversarial Robustness Toolbox\
   <https://adversarial-robustness-toolbox.readthedocs.io/en/latest/>`__
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np
import structlog
from structlog.stdlib import BoundLogger

from dioptra import pyplugs
from dioptra.sdk.exceptions import ARTDependencyError, TensorflowDependencyError
from dioptra.sdk.utilities.decorators import require_package

from .mlflow import load_tensorflow_keras_classifier

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    from art.estimators.classification import TensorFlowV2Classifier

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="art",
    )


try:
    from tensorflow.keras import losses
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
    imagenet_preprocessing: bool = False,
    classifier_kwargs: Optional[Dict[str, Any]] = None,
) -> TensorFlowV2Classifier:
    """Loads and wraps a registered Keras classifier for compatibility with the |ART|.

    Args:
        name: The name of the registered model in the MLFlow model registry.
        version: The version number of the registered model in the MLFlow registry.
        classifier_kwargs: A dictionary mapping argument names to values which will
            be passed to the TensorFlowV2Classifier constructor.
    Returns:
        A trained :py:class:`~art.estimators.classification.TensorFlowV2Classifier`
            object.

    See Also:
        - :py:class:`art.estimators.classification.TensorFlowV2Classifier`
        - :py:func:`.mlflow.load_tensorflow_keras_classifier`
    """
    classifier_kwargs = classifier_kwargs or {}
    keras_classifier: Sequential = load_tensorflow_keras_classifier(
        name=name, version=version
    )
    nb_classes = keras_classifier.output_shape[1]
    input_shape = keras_classifier.input_shape
    loss_object = losses.get(keras_classifier.loss)
    preprocessing = (
        (np.array([103.939, 116.779, 123.680]), np.array([1.0, 1.0, 1.0]))
        if imagenet_preprocessing
        else None
    )
    wrapped_keras_classifier: TensorFlowV2Classifier = TensorFlowV2Classifier(
        model=keras_classifier,
        nb_classes=nb_classes,
        input_shape=input_shape,
        loss_object=loss_object,
        preprocessing=preprocessing,
        **classifier_kwargs,
    )
    LOGGER.info(
        "Wrap Keras classifier for compatibility with Adversarial Robustness Toolbox"
    )

    return wrapped_keras_classifier
