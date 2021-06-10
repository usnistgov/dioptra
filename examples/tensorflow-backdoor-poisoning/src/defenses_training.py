#!/usr/bin/env python
# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.

from __future__ import annotations

from types import FunctionType
from typing import Callable, Dict, List, Optional, Tuple, Union

import mlflow
import numpy as np
from prefect import task
from tensorflow.keras.models import Model

from mitre.securingai import pyplugs
from mitre.securingai.sdk.exceptions import (
    ARTDependencyError,
    TensorflowDependencyError,
)
from mitre.securingai.sdk.utilities.decorators import require_package

try:
    from art.defences.trainer import AdversarialTrainerMadryPGD
    from art.estimators.classification import KerasClassifier
    from art.utils import to_categorical
    from tensorflow.keras.metrics import Metric
    from tensorflow.keras.models import Model
    from tensorflow.keras.optimizers import Optimizer
except ImportError:
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="art",
    )


@task
@require_package("art", exc_type=ARTDependencyError)
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def create_Madry_PGD_model(
    model: Model,
    training_ds: DirectoryIterator,
    eps: float,
    eps_step: float,
    learning_rate: float,
    batch_size: int,
    epochs: int,
    optimizer: Optimizer,
    metrics: List[Union[Metric, FunctionType]],
) -> Model:

    def_model = KerasClassifier(model)
    proxy = AdversarialTrainerMadryPGD(
        def_model, nb_epochs=epochs, eps=eps, eps_step=eps_step
    )
    x_train, y_train = training_ds.next()
    proxy.fit(x_train, y_train)

    model = def_model.model
    model.compile(
        loss="categorical_crossentropy",
        optimizer=optimizer,
        metrics=metrics,
    )
    return model
