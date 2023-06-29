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
from typing import Callable, Dict, List, Tuple, Union

import structlog
from structlog.stdlib import BoundLogger

from dioptra import pyplugs
from dioptra.sdk.exceptions import TensorflowDependencyError
from dioptra.sdk.utilities.decorators import require_package

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    from torch import nn
    from torch.nn import (
        BatchNorm2d,
        Conv2d,
        Dropout,
        Flatten,
        Linear,
        MaxPool2d,
        ReLU,
        Sequential,
        Softmax,
    )

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="torch",
    )


@pyplugs.register
def init_classifier(
    model_architecture: str,
    input_shape: Tuple[int, int, int],
    n_classes: int,
) -> Sequential:
    classifier: Sequential = PYTORCH_CLASSIFIERS_REGISTRY[model_architecture](
        input_shape,
        n_classes,
    )
    return classifier


def le_net(input_shape: Tuple[int, int, int], n_classes: int) -> Sequential:
    model = Sequential(
        # first convolutional layer:
        Conv2d(1, 20, 5, 1),
        ReLU(),
        MaxPool2d(2, 2),
        # second conv layer, with pooling and dropout:
        Conv2d(20, 50, 5, 1),
        ReLU(),
        MaxPool2d(2, 2),
        Flatten(),
        # dense hidden layer, with dropout:
        Linear(4 * 4 * 50, 500),
        ReLU(),
        # output layer:
        Linear(500, 10),
        Softmax(),
    )
    return model


PYTORCH_CLASSIFIERS_REGISTRY: Dict[
    str, Callable[[Tuple[int, int, int], int], Sequential]
] = dict(le_net=le_net)
