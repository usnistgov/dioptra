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
from typing import Any, Dict, List, Union

import structlog
from structlog.stdlib import BoundLogger

from dioptra import pyplugs
from dioptra.sdk.utilities.decorators import require_package

from . import import_pytorch

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    from torch.optim import Optimizer

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="torch",
    )


@pyplugs.register
def evaluate_metrics_generic(y_true, y_pred, metrics, func_kwargs) -> Dict[str, float]:
    names = []
    result = []
    for metric in metrics:
        name = metric[0]
        func = metric[1]

        extra_kwargs = func_kwargs.get(name, {})

        names += [name]
        metric_output = func(y_true.copy(), y_pred.copy(), **extra_kwargs)
        result += [metric_output]

    return dict(zip(names, result))


@pyplugs.register
def get_optimizer(
    model: Sequential,
    optimizer: str,
    learning_rate: float,
):
    return import_pytorch.get_optimizer(optimizer)(model.parameters(), learning_rate)
