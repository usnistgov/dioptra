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
"""A task plugin module for using the MLFlow Tracking service."""

from __future__ import annotations

from typing import Dict

import mlflow
import structlog
from structlog.stdlib import BoundLogger

from dioptra import pyplugs
from dioptra.sdk.exceptions import TensorflowDependencyError
from dioptra.sdk.utilities.decorators import require_package

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    from tensorflow.keras.models import Sequential

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


@pyplugs.register
def log_metrics(metrics: Dict[str, float]) -> None:
    """Logs metrics to the MLFlow Tracking service for the current run.

    Args:
        metrics: A dictionary with the metrics to be logged. The keys are the metric
            names and the values are the metric values.

    See Also:
        - :py:func:`mlflow.log_metric`
    """
    for metric_name, metric_value in metrics.items():
        mlflow.log_metric(key=metric_name, value=metric_value)
        LOGGER.info(
            "Log metric to MLFlow Tracking server",
            metric_name=metric_name,
            metric_value=metric_value,
        )


@pyplugs.register
def log_parameters(parameters: Dict[str, float]) -> None:
    """Logs parameters to the MLFlow Tracking service for the current run.

    Parameters can only be set once per run.

    Args:
        parameters: A dictionary with the parameters to be logged. The keys are the
            parameter names and the values are the parameter values.

    See Also:
        - :py:func:`mlflow.log_param`
    """
    for parameter_name, parameter_value in parameters.items():
        mlflow.log_param(key=parameter_name, value=parameter_value)
        LOGGER.info(
            "Log parameter to MLFlow Tracking server",
            parameter_name=parameter_name,
            parameter_value=parameter_value,
        )


@pyplugs.register
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def log_tensorflow_keras_estimator(estimator: Sequential, model_dir: str) -> None:
    """Logs a Keras estimator trained during the current run to the MLFlow registry.

    Args:
        estimator: A trained Keras estimator.
        model_dir: The relative artifact directory where MLFlow should save the
            model.
    """
    mlflow.keras.log_model(model=estimator, artifact_path=model_dir)
    LOGGER.info(
        "Tensorflow Keras model logged to tracking server",
        model_dir=model_dir,
    )
