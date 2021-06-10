# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
from __future__ import annotations

from typing import Any

import structlog
from multimethod import multimethod
from structlog.stdlib import BoundLogger

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@multimethod
def estimator_predict(estimator: Any, x: Any, **kwargs) -> Any:
    LOGGER.info(
        "Dispatching to generic function",
        generic="estimator_predict",
        estimator="Generic fallback",
        args_signature=("Any", "Any"),
    )

    try:
        prediction_results: Any = estimator.predict(x, **kwargs)

    except AttributeError:
        LOGGER.exception("Estimator does not have a generic predict method")
        raise

    return prediction_results
