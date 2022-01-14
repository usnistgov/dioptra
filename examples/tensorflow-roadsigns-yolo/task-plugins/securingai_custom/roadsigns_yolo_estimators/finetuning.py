from __future__ import annotations

import datetime
from types import FunctionType
from typing import Any, Dict, List, Optional, Union

import mlflow
import structlog
from structlog.stdlib import BoundLogger

from mitre.securingai import pyplugs
from mitre.securingai.sdk.generics import fit_estimator

from .losses import YOLOLoss

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    from tensorflow.keras.metrics import Metric
    from tensorflow.keras.optimizers import Optimizer

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


@pyplugs.register
def finetune(
    estimator: Any,
    model_architecture: str,
    optimizer: Optimizer,
    metrics: Optional[List[Union[Metric, FunctionType]]] = None,
    loss: str = "yolo_loss",
    skip: bool = True,
    x: Any = None,
    y: Any = None,
    fit_kwargs: Optional[Dict[str, Any]] = None,
) -> Any:
    if skip:
        return None

    fit_kwargs = fit_kwargs or {}
    finetune_loss = YOLOLoss() if loss == "yolo_loss" else loss
    base_model_name = [x.name for x in estimator.layers if model_architecture in x.name]

    base_model = estimator.get_layer(base_model_name[0])
    base_model.trainable = True
    estimator.compile(
        loss=finetune_loss,
        optimizer=optimizer,
        metrics=metrics if metrics else None,
    )

    time_start: datetime.datetime = datetime.datetime.now()

    LOGGER.info(
        "Begin estimator finetune",
        timestamp=time_start.isoformat(),
    )

    estimator_fit_result: Any = fit_estimator(estimator, x, y, **fit_kwargs)

    time_end: datetime.datetime = datetime.datetime.now()

    total_seconds: float = (time_end - time_start).total_seconds()
    total_minutes: float = total_seconds / 60

    mlflow.log_metric("finetuning_time_in_minutes", total_minutes)
    LOGGER.info(
        "Estimator finetune complete",
        timestamp=time_end.isoformat(),
        total_minutes=total_minutes,
    )

    return estimator_fit_result
