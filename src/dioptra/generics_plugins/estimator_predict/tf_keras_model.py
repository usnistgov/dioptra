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
from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Union

import numpy as np
import structlog
from structlog.stdlib import BoundLogger

from dioptra.sdk.exceptions import (
    EstimatorPredictGenericPredTypeError,
    TensorflowDependencyError,
)
from dioptra.sdk.generics import estimator_predict
from dioptra.sdk.utilities.decorators import require_package

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    from tensorflow.keras import Model

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


@estimator_predict.register
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

    except EstimatorPredictGenericPredTypeError as exc:
        LOGGER.exception(
            "Unknown pred_type argument for estimator_predict function.",
            estimator="tensorflow.keras.Model",
            pred_type=pred_type,
        )
        raise exc

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
        labels: Union[np.integer, np.ndarray] = np.argmax(prediction, axis=1)

        if isinstance(labels, np.integer):
            raise RuntimeError(
                "Label prediction should return an array, not an integer."
            )

        return labels

    flattened_labels: np.ndarray = (prediction.flatten() >= 0.5).astype(int)
    return flattened_labels


def _null_predict(*args, **kwargs) -> np.ndarray:
    raise EstimatorPredictGenericPredTypeError
