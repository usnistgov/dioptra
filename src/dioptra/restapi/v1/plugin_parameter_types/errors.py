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
"""Error handlers for the plugin parameter type endpoints."""
from __future__ import annotations

from flask_restx import Api


class PluginParameterTypeMatchesBuiltinTypeError(Exception):
    """The plugin parameter type name cannot match a built-in type."""


class PluginParameterTypeAlreadyExistsError(Exception):
    """The plugin parameter type name already exists."""


class PluginParameterTypeDoesNotExistError(Exception):
    """The requested plugin parameter type does not exist."""


class PluginParameterTypeReadOnlyLockError(Exception):
    """The plugin parameter type has a read-only lock and cannot be modified."""


class PluginParameterTypeMissingParameterError(Exception):
    """The requested plugin parameter type is missing a required parameter."""


def register_error_handlers(api: Api) -> None:
    @api.errorhandler(PluginParameterTypeMatchesBuiltinTypeError)
    def handle_plugin_parameter_type_matches_builtin_type_error(error):
        return {
            "message": "Bad Request - The requested plugin parameter type name "
            "matches a built-in type. Please select another and resubmit."
        }, 400

    @api.errorhandler(PluginParameterTypeDoesNotExistError)
    def handle_plugin_parameter_type_does_not_exist_error(error):
        return {
            "message": "Not Found - The requested plugin parameter type does "
            "not exist"
        }, 404

    @api.errorhandler(PluginParameterTypeReadOnlyLockError)
    def handle_plugin_parameter_type_read_only_lock_error(error):
        return {
            "message": "Forbidden - The plugin parameter type has a read-only "
            "lock and cannot be modified."
        }, 403

    @api.errorhandler(PluginParameterTypeMissingParameterError)
    def handle_plugin_parameter_type_missing_parameter_error(error):
        return (
            {
                "message": "Forbidden - The requested plugin parameter "
                "type is missing a required parameter."
            },
            400,
        )

    @api.errorhandler(PluginParameterTypeAlreadyExistsError)
    def handle_plugin_parameter_type_already_exists_error(error):
        return (
            {
                "message": "Bad Request - The plugin parameter type name on "
                "the registration form already exists. Please select "
                "another and resubmit."
            },
            400,
        )
