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
V1_ROOT = "api/v1"

AUTH_ROUTE = "auth"
EXPERIMENT_ROUTE = "experiment"
JOB_ROUTE = "job"
QUEUE_ROUTE = "queue"
TASK_PLUGIN_ROUTE = "taskPlugin"
USER_ROUTE = "user"

V1_ARTIFACTS_ROUTE = "artifacts"
V1_ENTRYPOINTS_ROUTE = "entrypoints"
V1_JOBS_ROUTE = "jobs"
V1_MLFLOW_RUNS_ROUTE = "mlflow_runs"
V1_PLUGINS_ROUTE = "plugins"
V1_PLUGIN_PARAMETER_TYPES_ROUTE = "pluginParameterTypes"
V1_QUEUES_ROUTE = "queues"
V1_TAGS_ROUTE = "tags"


def register_routes(api: Api) -> None:
    """Registers the endpoint routes with the main application.

    Args:
        api: The main REST |Api| object.
    """
    register_v0_routes(api)
    # register_v1_routes(api)


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


def register_v1_routes(api: Api) -> None:
    """Registers the endpoint routes with the main application.

    Args:
        api: The main REST |Api| object.
    """
    from .v1.artifacts.controller import api as artifacts_api
    from .v1.entrypoints.controller import api as entrypoints_api
    from .v1.jobs.controller import api as jobs_api
    from .v1.mlflow_runs.controller import api as mlflow_runs_api
    from .v1.plugin_parameter_types.controller import api as plugin_parameter_types_api
    from .v1.plugins.controller import api as plugins_api
    from .v1.queues.controller import api as queues_api
    from .v1.tags.controller import api as tags_api

    api.add_namespace(artifacts_api, path=f"/{V1_ROOT}/{V1_ARTIFACTS_ROUTE}")
    api.add_namespace(entrypoints_api, path=f"/{V1_ROOT}/{V1_ENTRYPOINTS_ROUTE}")
    api.add_namespace(jobs_api, path=f"/{V1_ROOT}/{V1_JOBS_ROUTE}")
    api.add_namespace(mlflow_runs_api, path=f"/{V1_ROOT}/{V1_MLFLOW_RUNS_ROUTE}")
    api.add_namespace(plugins_api, path=f"/{V1_ROOT}/{V1_PLUGINS_ROUTE}")
    api.add_namespace(
        plugin_parameter_types_api, path=f"/{V1_ROOT}/{V1_PLUGIN_PARAMETER_TYPES_ROUTE}"
    )
    api.add_namespace(queues_api, path=f"/{V1_ROOT}/{V1_QUEUES_ROUTE}")
    api.add_namespace(tags_api, path=f"/{V1_ROOT}/{V1_TAGS_ROUTE}")
