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

from __future__ import annotations

import datetime
from typing import Any, Dict, Optional

import mlflow
import structlog
from structlog.stdlib import BoundLogger

from dioptra import pyplugs
from dioptra.sdk.generics import estimator_predict, fit_estimator

LOGGER: BoundLogger = structlog.stdlib.get_logger()
import numpy as np
import torch
from torch.autograd import Variable
from torch.nn import CrossEntropyLoss


@pyplugs.register
def fit(
    estimator: Any,
    optimizer: Any,
    training_ds: Any,
    fit_kwargs: Optional[Dict[str, Any]] = None,
) -> Any:
    time_start: datetime.datetime = datetime.datetime.now()

    LOGGER.info(
        "Begin estimator fit",
        timestamp=time_start.isoformat(),
    )

    loss_fn = CrossEntropyLoss()
    ave_loss = 0
    for epoch in range(30):
        for batch_idx, (x, target) in enumerate(training_ds):
            optimizer.zero_grad()
            x, target = Variable(x), Variable(target)
            out = estimator(x)
            loss = loss_fn(out, target)
            ave_loss = ave_loss * 0.9 + loss.data.item() * 0.1
            loss.backward()
            optimizer.step()

    time_end = datetime.datetime.now()

    total_seconds = (time_end - time_start).total_seconds()
    total_minutes = total_seconds / 60

    mlflow.log_metric("training_time_in_minutes", total_minutes)
    LOGGER.info(
        "pytorch model training complete",
        timestamp=time_end.isoformat(),
        total_minutes=total_minutes,
    )
    mlflow.pytorch.log_model(estimator, "model")
    return estimator


@pyplugs.register
@pyplugs.task_nout(2)
def predict(
    estimator: Any,
    testing_ds: Any = None,
    predict_kwargs: Optional[Dict[str, Any]] = None,
) -> Any:
    estimator.eval()

    y_true = []
    y_pred = []

    for batch_idx, (data, target) in enumerate(testing_ds):
        t_x = Variable(data)
        t_y = Variable(target)
        outputs = estimator(t_x)
        _, predicted = torch.max(outputs.data, 1)

        y_pred += list(predicted.numpy())
        y_true += list(t_y.numpy())
    print(len(y_pred))
    print(len(y_true))

    return np.array(y_true), np.array(y_pred)
