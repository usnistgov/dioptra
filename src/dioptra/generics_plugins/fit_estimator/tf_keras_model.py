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

from typing import Any, Dict, Optional

import structlog
from structlog.stdlib import BoundLogger

from dioptra.sdk.exceptions import TensorflowDependencyError
from dioptra.sdk.generics import fit_estimator
from dioptra.sdk.utilities.decorators import require_package

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


@fit_estimator.register
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
