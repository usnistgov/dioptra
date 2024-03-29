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
"""A module for registering the endpoint routes with the main application.

.. |Api| replace:: :py:class:`flask_restx.Api`
"""
from __future__ import annotations

from flask_restx import Api

V0_ROOT = "api/v0"

AUTH_ROUTE = "auth"
EXPERIMENT_ROUTE = "experiment"
JOB_ROUTE = "job"
QUEUE_ROUTE = "queue"
TASK_PLUGIN_ROUTE = "taskPlugin"
USER_ROUTE = "user"


def register_routes(api: Api) -> None:
    """Registers the endpoint routes with the main application.

    Args:
        api: The main REST |Api| object.
    """
    register_v0_routes(api)


def register_v0_routes(api: Api) -> None:
    """Registers the endpoint routes with the main application.

    Args:
        api: The main REST |Api| object.
    """
    from .v0.auth.controller import api as auth_api
    from .v0.experiment.controller import api as experiment_api
    from .v0.job.controller import api as job_api
    from .v0.queue.controller import api as queue_api
    from .v0.task_plugin.controller import api as task_plugin_api
    from .v0.user.controller import api as user_api

    api.add_namespace(auth_api, path=f"/{V0_ROOT}/{AUTH_ROUTE}")
    api.add_namespace(experiment_api, path=f"/{V0_ROOT}/{EXPERIMENT_ROUTE}")
    api.add_namespace(job_api, path=f"/{V0_ROOT}/{JOB_ROUTE}")
    api.add_namespace(queue_api, path=f"/{V0_ROOT}/{QUEUE_ROUTE}")
    api.add_namespace(task_plugin_api, path=f"/{V0_ROOT}/{TASK_PLUGIN_ROUTE}")
    api.add_namespace(user_api, path=f"/{V0_ROOT}/{USER_ROUTE}")
