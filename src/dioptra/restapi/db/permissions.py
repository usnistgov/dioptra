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
"""
"Checkers" of various kinds, including assert_* style functions which raise
exceptions, and non-assert style functions which just return information
without raising exceptions.
"""

import inspect
from typing import Callable, ParamSpec, TypeVar

from dioptra.restapi.db.repository import utils

Param = ParamSpec("Param")
RetType = TypeVar("RetType")


def permissioned_write(resource_arg: str):
    def decorator(func: Callable[Param, RetType]) -> Callable[Param, RetType]:
        def wrapper(self, *args, **kwargs) -> RetType:
            callargs = inspect.getcallargs(func, self, *args, **kwargs)
            resource = callargs[resource_arg]

            resource = utils.get_resource(self.session, resource)
            # TODO: replace with more generic check
            utils.assert_can_delete_resource(self.session, self.user, resource)

            return func(self, *args, **kwargs)

        return wrapper

    return decorator
