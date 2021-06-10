# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
"""A task plugin module for using the MLFlow model registry."""

from __future__ import annotations

from typing import Optional

import structlog
from mlflow.entities import Run as MlflowRun
from mlflow.entities.model_registry import ModelVersion
from mlflow.keras import load_model as load_tf_keras_model
from mlflow.tracking import MlflowClient
from structlog.stdlib import BoundLogger

from mitre.securingai import pyplugs
from mitre.securingai.sdk.exceptions import TensorflowDependencyError
from mitre.securingai.sdk.utilities.decorators import require_package

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    from tensorflow.keras.models import Sequential

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


@pyplugs.register
def add_model_to_registry(
    active_run: MlflowRun, name: str, model_dir: str
) -> Optional[ModelVersion]:
    """Registers a trained model logged during the current run to the MLFlow registry.

    Args:
        active_run: The :py:class:`mlflow.ActiveRun` object managing the current run's
            state.
        name: The registration name to use for the model.
        model_dir: The relative artifact directory where MLFlow logged the model trained
            during the current run.

    Returns:
        A :py:class:`~mlflow.entities.model_registry.ModelVersion` object created by the
        backend.
    """
    if not name.strip():
        return None

    run_id: str = active_run.info.run_id
    artifact_uri: str = active_run.info.artifact_uri
    source: str = f"{artifact_uri}/{model_dir}"

    registered_models = [x.name for x in MlflowClient().list_registered_models()]

    if name not in registered_models:
        LOGGER.info("create registered model", name=name)
        MlflowClient().create_registered_model(name=name)

    LOGGER.info("create model version", name=name, source=source, run_id=run_id)
    model_version: ModelVersion = MlflowClient().create_model_version(
        name=name, source=source, run_id=run_id
    )

    return model_version


@pyplugs.register
def get_experiment_name(active_run: MlflowRun) -> str:
    """Gets the name of the experiment for the current run.

    Args:
        active_run: The :py:class:`mlflow.ActiveRun` object managing the current run's
            state.

    Returns:
        The name of the experiment.
    """
    experiment_name: str = (
        MlflowClient().get_experiment(active_run.info.experiment_id).name
    )
    LOGGER.info(
        "Obtained experiment name of active run", experiment_name=experiment_name
    )

    return experiment_name


@pyplugs.register
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def load_tensorflow_keras_classifier(name: str, version: int) -> Sequential:
    """Loads a registered Keras classifier.

    Args:
        name: The name of the registered model in the MLFlow model registry.
        version: The version number of the registered model in the MLFlow registry.

    Returns:
        A trained :py:class:`tf.keras.Sequential` object.
    """
    uri: str = f"models:/{name}/{version}"
    LOGGER.info("Load Keras classifier from model registry", uri=uri)

    return load_tf_keras_model(model_uri=uri)
