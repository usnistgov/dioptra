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
"""Error handlers for the plugin endpoints."""
from __future__ import annotations

from flask_restx import Api


class PluginAlreadyExistsError(Exception):
    """The plugin name already exists."""


class PluginDoesNotExistError(Exception):
    """The requested plugin does not exist."""


class PluginFileAlreadyExistsError(Exception):
    """The plugin file filename already exists."""


class PluginFileDoesNotExistError(Exception):
    """The requested plugin file does not exist."""


class PluginTaskParameterTypeNotFoundError(Exception):
    """One ore more referenced plugin task parameter types were not found."""


class PluginTaskNameAlreadyExistsError(Exception):
    """More than one plugin task is being assigned the same name."""


class PluginTaskInputParameterNameAlreadyExistsError(Exception):
    """More than one plugin task input parameter is being assigned the same name."""


class PluginTaskOutputParameterNameAlreadyExistsError(Exception):
    """More than one plugin task output parameter is being assigned the same name."""


def register_error_handlers(api: Api) -> None:
    @api.errorhandler(PluginDoesNotExistError)
    def handle_plugin_does_not_exist_error(error):
        return {"message": "Not Found - The requested plugin does not exist"}, 404

    @api.errorhandler(PluginAlreadyExistsError)
    def handle_plugin_already_exists_error(error):
        return (
            {
                "message": "Bad Request - The plugin name on the registration form "
                "already exists. Please select another and resubmit."
            },
            400,
        )

    @api.errorhandler(PluginFileDoesNotExistError)
    def handle_plugin_file_does_not_exist_error(error):
        return {"message": "Not Found - The requested plugin file does not exist"}, 404

    @api.errorhandler(PluginFileAlreadyExistsError)
    def handle_plugin_file_already_exists_error(error):
        return (
            {
                "message": "Bad Request - The plugin file filename on the "
                "registration form already exists. Please select another and resubmit."
            },
            400,
        )

    @api.errorhandler(PluginTaskParameterTypeNotFoundError)
    def handle_plugin_task_parameter_type_not_found_error(error):
        return {
            "message": "Bad Request - One or more referenced plugin task parameter "
            "types were not found."
        }, 400

    @api.errorhandler(PluginTaskNameAlreadyExistsError)
    def handle_plugin_task_name_already_exists_error(error):
        return {
            "message": "Bad Request - More than one plugin task is being assigned the "
            "same name."
        }, 400

    @api.errorhandler(PluginTaskInputParameterNameAlreadyExistsError)
    def handle_plugin_task_input_parameter_name_already_exists_error(error):
        return {
            "message": "Bad Request - More than one plugin task input parameter is "
            "being assigned the same name."
        }, 400

    @api.errorhandler(PluginTaskOutputParameterNameAlreadyExistsError)
    def handle_plugin_task_output_parameter_name_already_exists_error(error):
        return {
            "message": "Bad Request - More than one plugin task output parameter is "
            "being assigned the same name."
        }, 400
