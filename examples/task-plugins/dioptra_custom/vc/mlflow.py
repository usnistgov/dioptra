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
"""A task plugin module for using the MLFlow model registry."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import mlflow
import structlog
from mlflow.entities.model_registry import ModelVersion
from mlflow.tracking import MlflowClient
from structlog.stdlib import BoundLogger

from dioptra import pyplugs

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pyplugs.register
def add_model_to_registry(name: str, model_dir: str) -> Optional[ModelVersion]:
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

    active_run = mlflow.active_run()

    run_id: str = active_run.info.run_id
    artifact_uri: str = active_run.info.artifact_uri
    source: str = f"{artifact_uri}/{model_dir}"

    registered_models = [x.name for x in MlflowClient().search_registered_models()]

    if name not in registered_models:
        LOGGER.info("create registered model", name=name)
        MlflowClient().create_registered_model(name=name)

    LOGGER.info("create model version", name=name, source=source, run_id=run_id)
    model_version: ModelVersion = MlflowClient().create_model_version(
        name=name, source=source, run_id=run_id
    )

    return model_version


@pyplugs.register
def get_experiment_name() -> str:
    """Gets the name of the experiment for the current run.

    Args:
        active_run: The :py:class:`mlflow.ActiveRun` object managing the current run's
            state.

    Returns:
        The name of the experiment.
    """
    active_run = mlflow.active_run()

    experiment_name: str = (
        MlflowClient().get_experiment(active_run.info.experiment_id).name
    )
    LOGGER.info(
        "Obtained experiment name of active run", experiment_name=experiment_name
    )

    return experiment_name


@pyplugs.register
def prepend_cwd(path: str) -> Path:
    ret = Path.cwd() / path
    return ret
