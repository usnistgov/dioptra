from __future__ import annotations

from typing import Any, Dict, Optional

import structlog
from structlog.stdlib import BoundLogger

from mitre.securingai.sdk.exceptions import TensorflowDependencyError
from mitre.securingai.sdk.generics import fit_estimator
from mitre.securingai.sdk.utilities.decorators import require_package

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    from tensorflow.keras import Model
    from tensorflow.keras.callbacks import History

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )


@fit_estimator.register
def _(estimator: Model, x: Any, **kwargs) -> History:
    LOGGER.info(
        "Dispatch generic function",
        generic="fit_estimator",
        estimator="tensorflow.keras.Model",
        args_signature=("Model", "Any"),
    )

    history: History = fit_keras_model(
        estimator=estimator,
        x=x,
        **kwargs,
    )

    return history


@fit_estimator.register  # type: ignore
def _(estimator: Model, x: Any, y: Any, **kwargs) -> History:
    LOGGER.info(
        "Dispatch generic function",
        generic="fit_estimator",
        estimator="tensorflow.keras.Model",
        args_signature=("Model", "Any", "Any"),
    )

    history: History = fit_keras_model(
        estimator=estimator,
        x=x,
        y=y,
        **kwargs,
    )

    return history


@require_package("tensorflow", exc_type=TensorflowDependencyError)
def fit_keras_model(
    estimator: Model,
    x: Any,
    y: Any = None,
    batch_size: Optional[int] = None,
    nb_epochs: int = 1,
    **kwargs,
) -> History:
    fit_kwargs: Dict[str, Any] = dict(
        y=y, batch_size=batch_size, epochs=nb_epochs, **kwargs
    )
    history: History = estimator.fit(
        x=x,
        **{k: v for k, v in fit_kwargs.items() if v is not None},
    )

    return history
