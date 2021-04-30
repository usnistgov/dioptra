"""Error handlers for the task plugin endpoints."""

from flask_restx import Api


class TaskPluginAlreadyExistsError(Exception):
    """A task plugin package with this name already exists."""


class TaskPluginDoesNotExistError(Exception):
    """The requested task plugin package does not exist."""


class TaskPluginUploadError(Exception):
    """The task plugin upload form contains invalid parameters."""


def register_error_handlers(api: Api) -> None:
    @api.errorhandler(TaskPluginDoesNotExistError)
    def handle_task_plugin_does_not_exist_error(error):
        return (
            {"message": "Not Found - The requested task plugin package does not exist"},
            404,
        )

    @api.errorhandler(TaskPluginAlreadyExistsError)
    def handle_task_plugin_already_exists_error(error):
        return (
            {
                "message": "Bad Request - The names of one or more of the uploaded "
                "task plugin packages conflicts with an existing package in the "
                "collection. To update an existing task plugin package, delete it "
                "first and then resubmit."
            },
            400,
        )

    @api.errorhandler(TaskPluginUploadError)
    def handle_task_plugin_registration_error(error):
        return (
            {
                "message": "Bad Request - The task plugin upload form contains invalid "
                "parameters. Please verify and resubmit."
            },
            400,
        )
