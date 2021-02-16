from __future__ import annotations

from typing import Any

import structlog
from multimethod import multimethod
from structlog.stdlib import BoundLogger

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@multimethod
def fit_estimator(estimator: Any, x: Any, y: Any, **kwargs) -> Any:
    LOGGER.info(
        "Dispatching to generic function",
        generic="fit_estimator",
        estimator="Generic fallback",
        args_signature=("Any", "Any", "Any"),
    )

    try:
        fit_results: Any = estimator.fit(x, y, **kwargs)

    except AttributeError:
        LOGGER.exception("Estimator does not have a fit method")
        raise

    return fit_results
