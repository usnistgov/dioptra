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
    uri: str = f"models:/{name}/{version}"
    LOGGER.info("Load Keras classifier from model registry", uri=uri)

    return load_tf_keras_model(model_uri=uri)
