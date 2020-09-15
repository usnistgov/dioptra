from flask_restx import Api


class ExperimentAlreadyExistsError(Exception):
    pass


class ExperimentDoesNotExistError(Exception):
    pass


class ExperimentRegistrationError(Exception):
    pass


def register_error_handlers(api: Api) -> None:
    @api.errorhandler(ExperimentDoesNotExistError)
    def handle_experiment_does_not_exist_error(error):
        return {"message": "Not Found - The requested experiment does not exist"}, 404

    @api.errorhandler(ExperimentAlreadyExistsError)
    def handle_experiment_already_exists_error(error):
        return (
            {
                "message": "Bad Request - The experiment name on the registration form "
                "already exists. Please select another and resubmit."
            },
            400,
        )

    @api.errorhandler(ExperimentRegistrationError)
    def handle_experiment_registration_error(error):
        return (
            {
                "message": "Bad Request - The experiment registration form contains "
                "invalid parameters. Please verify and resubmit."
            },
            400,
        )
