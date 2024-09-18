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

import datetime
from typing import Any, Dict, Optional

import mlflow
import structlog
from structlog.stdlib import BoundLogger

from dioptra import pyplugs
from dioptra.sdk.generics import estimator_predict, fit_estimator

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pyplugs.register
def fit(
    estimator: Any,
    x: Any = None,
    y: Any = None,
    fit_kwargs: Optional[Dict[str, Any]] = None,
) -> Any:
    """Fits the estimator to the given data.

    This task plugin wraps :py:func:`~dioptra.sdk.generics.fit_estimator`, which is a
    generic function that uses multiple argument dispatch to handle the estimator
    fitting method for different machine learning libraries. The modules attached to the
    advertised plugin entry point `dioptra.generics.fit_estimator` are used to build the
    function dispatch registry at runtime. For more information on the supported fitting
    methods and `fit_kwargs` arguments, please refer to the documentation of the
    registered dispatch functions.

    Args:
        estimator: The model to be trained.
        x: The input data to be used for training.
        y: The target data to be used for training.
        fit_kwargs: An optional dictionary of keyword arguments to pass to the
            dispatched function.

    Returns:
        The object returned by the estimator's fitting function. For further details on
        the type of object this method can return, see the documentation for the
        registered dispatch functions.

    See Also:
        - :py:func:`dioptra.sdk.generics.fit_estimator`
    """
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
    """Uses the estimator to make predictions on the given input data.

    This task plugin wraps :py:func:`~dioptra.sdk.generics.estimator_predict`, which is
    a generic function that uses multiple argument dispatch to handle estimator
    prediction methods for different machine learning libraries. The modules attached to
    the advertised plugin entry point `dioptra.generics.estimator_predict` are used to
    build the function dispatch registry at runtime. For more information on the
    supported prediction methods and `predict_kwargs` arguments, refer to the
    documentation of the registered dispatch functions.

    Args:
        estimator: A trained model to be used to generate predictions.
        x: The input data for which to generate predictions.
        predict_kwargs: An optional dictionary of keyword arguments to pass to the
            dispatched function.

    Returns:
        The object returned by the estimator's predict function. For further details on
        the type of object this method can return, see the documentation for the
        registered dispatch functions.

    See Also:
        - :py:func:`dioptra.sdk.generics.estimator_predict`
    """
    predict_kwargs = predict_kwargs or {}
    prediction: Any = estimator_predict(estimator, x, **predict_kwargs)

    return prediction
