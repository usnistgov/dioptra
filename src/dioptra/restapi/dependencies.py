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
"""A module for binding configurations to shared services using dependency injection."""
from __future__ import annotations

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
