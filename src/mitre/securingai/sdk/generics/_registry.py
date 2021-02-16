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
        for entrypoint in entrypoints.get_group_all(f"securingai.generics.{generic}"):
            _register(generic=generic, entrypoint=entrypoint)
