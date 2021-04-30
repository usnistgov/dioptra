"""A module for binding configurations to shared services using dependency injection."""

from typing import Any, Callable, List

from injector import Binder


def bind_dependencies(binder: Binder) -> None:
    """Binds interfaces to implementations within the main application.

    Args:
        binder: A :py:class:`~injector.Binder` object.
    """
    from .experiment import bind_dependencies as attach_experiment_dependencies
    from .job import bind_dependencies as attach_job_dependencies
    from .queue import bind_dependencies as attach_job_queue_dependencies
    from .task_plugin import bind_dependencies as attach_task_plugin_dependencies

    # Bind configurations
    attach_experiment_dependencies(binder)
    attach_job_dependencies(binder)
    attach_job_queue_dependencies(binder)
    attach_task_plugin_dependencies(binder)


def register_providers(modules: List[Callable[..., Any]]) -> None:
    """Registers type providers within the main application.

    Args:
        modules: A list of callables used for configuring the dependency injection
            environment.
    """
    from .experiment import register_providers as attach_experiment_providers
    from .job import register_providers as attach_job_providers
    from .queue import register_providers as attach_job_queue_providers
    from .task_plugin import register_providers as attach_task_plugin_providers

    # Append modules to list
    attach_experiment_providers(modules)
    attach_job_providers(modules)
    attach_job_queue_providers(modules)
    attach_task_plugin_providers(modules)
