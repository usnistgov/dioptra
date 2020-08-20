from typing import Any, Callable, List

from injector import Binder


def bind_dependencies(binder: Binder) -> None:
    from .job import bind_dependencies as attach_job_dependencies

    # Bind configurations
    attach_job_dependencies(binder)


def register_providers(modules: List[Callable[..., Any]]) -> None:
    from .job import register_providers as attach_job_providers

    # Append modules to list
    attach_job_providers(modules)
