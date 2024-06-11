#!/usr/bin/env python
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

from types import FunctionType
from typing import Callable, Dict, List, Optional, Tuple, Union

import mlflow
import numpy as np
from prefect import task
from tensorflow.keras.models import Model

from dioptra import pyplugs
from dioptra.sdk.exceptions import (
    ARTDependencyError,
    TensorflowDependencyError,
)
from dioptra.sdk.utilities.decorators import require_package

try:
    from art.defences.trainer import AdversarialTrainerMadryPGD
    from art.estimators.classification import KerasClassifier
    from art.utils import to_categorical
    from tensorflow.keras.metrics import Metric
    from tensorflow.keras.models import Model
    from tensorflow.keras.optimizers.legacy import Optimizer
except ImportError:
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="art",
    )


@pyplugs.register
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
