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


class ResourceDoesNotExistError(Exception):
    """The resource does not exist."""


class DraftDoesNotExistError(Exception):
    """The requested draft does not exist."""


class DraftAlreadyExistsError(Exception):
    """The draft already exists."""


def register_base_error_handlers(api: Api) -> None:
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

    @api.errorhandler(ResourceDoesNotExistError)
    def handle_resource_does_not_exist(error):
        return {"message": "Not Found - The requested resource does not exist"}, 404

    @api.errorhandler(DraftDoesNotExistError)
    def handle_draft_does_not_exist(error):
        return {"message": "Not Found - The requested draft does not exist"}, 404

    @api.errorhandler(DraftAlreadyExistsError)
    def handle_draft_already_exists(error):
        return (
            {"message": "Bad Request - The draft for this resource already exists."},
            400,
        )


def register_error_handlers(api: Api) -> None:
    """Registers the error handlers with the main application.

    Args:
        api: The main REST |Api| object.
    """

    from dioptra.restapi import v1

    register_base_error_handlers(api)
    v1.artifacts.errors.register_error_handlers(api)
    v1.entrypoints.errors.register_error_handlers(api)
    v1.experiments.errors.register_error_handlers(api)
    v1.groups.errors.register_error_handlers(api)
    v1.jobs.errors.register_error_handlers(api)
    v1.models.errors.register_error_handlers(api)
    v1.plugin_parameter_types.errors.register_error_handlers(api)
    v1.plugins.errors.register_error_handlers(api)
    v1.queues.errors.register_error_handlers(api)
    v1.tags.errors.register_error_handlers(api)
    v1.users.errors.register_error_handlers(api)
