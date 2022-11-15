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
from typing import Dict, List

import entrypoints
import structlog
from entrypoints import EntryPoint
from structlog.stdlib import BoundLogger

LOGGER: BoundLogger = structlog.stdlib.get_logger()


_GENERICS: List[str] = ["estimator_predict", "fit_estimator"]
_GENERICS_ENTRYPOINTS: Dict[str, Dict[str, EntryPoint]] = {}


def _register(generic: str, entrypoint: EntryPoint) -> None:
    generic_registry = _GENERICS_ENTRYPOINTS.setdefault(generic, {})

    try:
        generic_registry[entrypoint.name] = entrypoint.load()

    except (AttributeError, ImportError):
        LOGGER.exception(
            "Failed to register dispatch method for generic", name=f"{generic}()"
        )


def register_entrypoints() -> None:
    for generic in _GENERICS:
        for entrypoint in entrypoints.get_group_all(f"dioptra.generics.{generic}"):
            _register(generic=generic, entrypoint=entrypoint)
