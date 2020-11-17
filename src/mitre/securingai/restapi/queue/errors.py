from flask_restx import Api


class QueueAlreadyExistsError(Exception):
    pass


class QueueDoesNotExistError(Exception):
    pass


class QueueRegistrationError(Exception):
    pass


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
