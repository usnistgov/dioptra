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
"""A module for registering the error handlers for the application.

.. |Api| replace:: :py:class:`flask_restx.Api`
"""
from __future__ import annotations

from flask_restx import Api


class BackendDatabaseError(Exception):
    """The backend database returned an unexpected response."""


class SearchNotImplementedError(Exception):
    """The search functionality has not been implemented."""


class SearchParseError(Exception):
    """The search query could not be parsed."""


def register_base_v1_error_handlers(api: Api) -> None:
    @api.errorhandler(BackendDatabaseError)
    def handle_backend_database_error(error):
        return {
            "message": "The backend database returned an unexpected response, please "
            "contact the system administrator"
        }, 500

    @api.errorhandler(SearchNotImplementedError)
    def handle_search_not_implemented_error(error):
        return {"message": "The search functionality has not been implemented"}, 501

    @api.errorhandler(SearchParseError)
    def handle_search_parse_error(error):
        return {
            "message": "The provided search query could not be parsed",
            "query": error.args[0],
            "reason": error.args[1],
        }, 422


def register_error_handlers(api: Api, restapi_version: str) -> None:
    """Registers the error handlers with the main application.

    Args:
        api: The main REST |Api| object.
    """
    if restapi_version == "v0":
        register_v0_error_handlers(api)

    elif restapi_version == "v1":
        register_v1_error_handlers(api)


def register_v0_error_handlers(api: Api) -> None:
    """Registers the error handlers with the main application.

    Args:
        api: The main REST |Api| object.
    """
    from .v0.experiment import (
        register_error_handlers as attach_experiment_error_handlers,
    )
    from .v0.job import register_error_handlers as attach_job_error_handlers
    from .v0.queue import register_error_handlers as attach_job_queue_error_handlers
    from .v0.task_plugin import (
        register_error_handlers as attach_task_plugin_error_handlers,
    )
    from .v0.user import register_error_handlers as attach_user_error_handlers

    # Add error handlers
    attach_experiment_error_handlers(api)
    attach_job_error_handlers(api)
    attach_job_queue_error_handlers(api)
    attach_task_plugin_error_handlers(api)
    attach_user_error_handlers(api)


def register_v1_error_handlers(api: Api) -> None:
    """Registers the error handlers with the main application.

    Args:
        api: The main REST |Api| object.
    """

    from dioptra.restapi import v1

    register_base_v1_error_handlers(api)
    v1.groups.errors.register_error_handlers(api)
    v1.plugins.errors.register_error_handlers(api)
    v1.plugin_parameter_types.errors.register_error_handlers(api)
    v1.queues.errors.register_error_handlers(api)
    v1.users.errors.register_error_handlers(api)
