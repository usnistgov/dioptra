from __future__ import annotations

from typing import Any, Callable, Dict, Optional

import numpy as np
import structlog
from structlog.stdlib import BoundLogger

from mitre.securingai.sdk.exceptions import (
    EstimatorPredictGenericPredTypeError,
    TensorflowDependencyError,
)
from mitre.securingai.sdk.generics import estimator_predict
from mitre.securingai.sdk.utilities.decorators import require_package

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    from tensorflow.keras import Model

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


@estimator_predict.register  # type: ignore
def _(estimator: Model, x: Any, pred_type: str, **kwargs) -> np.ndarray:
    LOGGER.info(
        "Dispatch generic function",
        generic="estimator_predict",
        estimator="tensorflow.keras.Model",
        args_signature=("Model", "Any", "str"),
    )

    predict: Callable[..., np.ndarray] = dict(
        prob=keras_model_predict_proba,
        label=keras_model_predict_label,
    ).get(pred_type, _null_predict)

    try:
        prediction: np.ndarray = predict(
            estimator=estimator,
            x=x,
            **kwargs,
        )

    except EstimatorPredictGenericPredTypeError:
        LOGGER.exception(
            "Unknown pred_type argument for estimator_predict function.",
            estimator="tensorflow.keras.Model",
            pred_type=pred_type,
        )
        raise EstimatorPredictGenericPredTypeError

    return prediction


@require_package("tensorflow", exc_type=TensorflowDependencyError)
def keras_model_predict_proba(
    estimator: Model,
    x: Any,
    batch_size: Optional[int] = None,
    **kwargs,
) -> np.ndarray:
    predict_kwargs: Dict[str, Any] = dict(batch_size=batch_size, **kwargs)
    prediction: np.ndarray = estimator.predict(
        x=x,
        **{k: v for k, v in predict_kwargs.items() if v is not None},
    )

    return prediction


@require_package("tensorflow", exc_type=TensorflowDependencyError)
def keras_model_predict_label(
    estimator: Model,
    x: Any,
    batch_size: Optional[int] = None,
    **kwargs,
) -> np.ndarray:
    predict_kwargs: Dict[str, Any] = dict(batch_size=batch_size, **kwargs)
    prediction: np.ndarray = estimator.predict(
        x=x,
        **{k: v for k, v in predict_kwargs.items() if v is not None},
    )

    if prediction.shape[1] > 1:
        return np.argmax(prediction, axis=1)

    return (prediction.flatten() >= 0.5).astype(int)


def _null_predict(*args, **kwargs) -> np.ndarray:
    raise EstimatorPredictGenericPredTypeError
