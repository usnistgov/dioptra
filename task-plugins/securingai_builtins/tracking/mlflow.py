from __future__ import annotations

from typing import Dict

import mlflow
import structlog
from structlog.stdlib import BoundLogger

from mitre.securingai import pyplugs

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pyplugs.register
def log_metrics(metrics: Dict[str, float]) -> None:
    for metric_name, metric_value in metrics.items():
        mlflow.log_metric(key=metric_name, value=metric_value)
        LOGGER.info(
            "Log metric to MLFlow Tracking server",
            metric_name=metric_name,
            metric_value=metric_value,
        )


@pyplugs.register
def log_parameters(parameters: Dict[str, float]) -> None:
    for parameter_name, parameter_value in parameters.items():
        mlflow.log_param(key=parameter_name, value=parameter_value)
        LOGGER.info(
            "Log parameter to MLFlow Tracking server",
            parameter_name=parameter_name,
            parameter_value=parameter_value,
        )
