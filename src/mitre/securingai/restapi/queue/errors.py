"""Error handlers for the queue endpoints."""

from flask_restx import Api


class QueueAlreadyExistsError(Exception):
    """The queue name already exists."""


class QueueDoesNotExistError(Exception):
    """The requested queue does not exist."""


class QueueRegistrationError(Exception):
    """The queue registration form contains invalid parameters."""


def register_error_handlers(api: Api) -> None:
    @api.errorhandler(QueueDoesNotExistError)
    def handle_queue_does_not_exist_error(error):
        return {"message": "Not Found - The requested queue does not exist"}, 404

    @api.errorhandler(QueueAlreadyExistsError)
    def handle_queue_already_exists_error(error):
        return (
            {
                "message": "Bad Request - The queue name on the registration form "
                "already exists. Please select another and resubmit."
            },
            400,
        )

    @api.errorhandler(QueueRegistrationError)
    def handle_queue_registration_error(error):
        return (
            {
                "message": "Bad Request - The queue registration form contains "
                "invalid parameters. Please verify and resubmit."
            },
            400,
        )
