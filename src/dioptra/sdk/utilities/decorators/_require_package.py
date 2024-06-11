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
import importlib
from functools import wraps
from typing import Any, Callable, Optional, Type, TypeVar, cast

import structlog
from structlog.stdlib import BoundLogger

from dioptra.sdk.exceptions.base import BaseOptionalDependencyError

LOGGER: BoundLogger = structlog.stdlib.get_logger()

Exc = Type[BaseOptionalDependencyError]
Function = Callable[..., Any]
T = TypeVar("T", bound=Function)


def require_package(
    name: str,
    exc_message: Optional[str] = None,
    exc_type: Exc = BaseOptionalDependencyError,
) -> Callable[[T], T]:
    def decorator(func: T) -> T:
        error_msg: str = f'The package "{name}" is required to use {func.__name__}'
        exc: BaseOptionalDependencyError = (
            exc_type(exc_message) if exc_message else exc_type(error_msg)
        )

        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                importlib.import_module(name=name)

            except ModuleNotFoundError:
                LOGGER.exception(error_msg, args=args, kwargs=kwargs)
                raise exc

            return func(*args, **kwargs)

        return cast(T, wrapper)

    return decorator
