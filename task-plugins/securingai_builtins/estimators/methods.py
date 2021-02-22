from __future__ import annotations

import datetime
from typing import Any, Dict, Optional

import mlflow
import structlog
from structlog.stdlib import BoundLogger

from mitre.securingai import pyplugs
from mitre.securingai.sdk.generics import estimator_predict, fit_estimator

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pyplugs.register
def fit(
    estimator: Any,
    x: Any = None,
    y: Any = None,
    fit_kwargs: Optional[Dict[str, Any]] = None,
) -> Any:
    fit_kwargs = fit_kwargs or {}
    time_start: datetime.datetime = datetime.datetime.now()

    LOGGER.info(
        "Begin estimator fit",
        timestamp=time_start.isoformat(),
    )

    estimator_fit_result: Any = fit_estimator(estimator, x, y, **fit_kwargs)

    time_end: datetime.datetime = datetime.datetime.now()

    total_seconds: float = (time_end - time_start).total_seconds()
    total_minutes: float = total_seconds / 60

    mlflow.log_metric("training_time_in_minutes", total_minutes)
    LOGGER.info(
        "Estimator fit complete",
        timestamp=time_end.isoformat(),
        total_minutes=total_minutes,
    )

    return estimator_fit_result


@pyplugs.register
def predict(
    estimator: Any,
    x: Any = None,
    predict_kwargs: Optional[Dict[str, Any]] = None,
) -> Any:
    predict_kwargs = predict_kwargs or {}
    prediction: Any = estimator_predict(estimator, x, **predict_kwargs)

    return prediction
