import mlflow
from mlflow.entities import Run as MlflowRun
from prefect import task
from tensorflow.keras.models import Model

from mitre.securingai import pyplugs
from mitre.securingai.sdk.exceptions import (
    ARTDependencyError,
    TensorflowDependencyError,
)
from mitre.securingai.sdk.utilities.decorators import require_package


@task
@require_package("art", exc_type=ARTDependencyError)
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def add_model_manually_to_registry(
    model: Model, active_run: MlflowRun, artifact_path: str, model_name: str
) -> None:
    mlflow.keras.log_model(
        keras_model=model, artifact_path=artifact_path, registered_model_name=model_name
    )
