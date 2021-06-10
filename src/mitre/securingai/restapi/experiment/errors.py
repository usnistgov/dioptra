# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
"""Error handlers for the experiment endpoints."""

from flask_restx import Api


class ExperimentAlreadyExistsError(Exception):
    """The experiment name already exists."""


class ExperimentMLFlowTrackingAlreadyExistsError(Exception):
    """The experiment name already exists on the MLFlow Tracking backend."""


class ExperimentDoesNotExistError(Exception):
    """The requested experiment does not exist."""


class ExperimentMLFlowTrackingDoesNotExistError(Exception):
    """The requested experiment is in our database but is not in MLFlow Tracking."""


class ExperimentMLFlowTrackingRegistrationError(Exception):
    """Experiment registration to the MLFlow Tracking backend has failed."""


class ExperimentRegistrationError(Exception):
    """The experiment registration form contains invalid parameters."""


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

    @api.errorhandler(ExperimentMLFlowTrackingAlreadyExistsError)
    def handle_mlflow_tracking_experiment_already_exists_error(error):
        return (
            {
                "message": "Bad Request - The experiment name on the registration form "
                "already exists on the MLFlow Tracking backend. Please select another "
                "and resubmit."
            },
            400,
        )

    @api.errorhandler(ExperimentMLFlowTrackingDoesNotExistError)
    def handle_mlflow_tracking_experiment_does_not_exist_error(error):
        return (
            {
                "message": "Bad Gateway - The requested experiment exists in "
                "our database but cannot be found on the MLFlow Tracking backend. "
                "If this happens more than once, please file a bug report."
            },
            502,
        )

    @api.errorhandler(ExperimentMLFlowTrackingRegistrationError)
    def handle_mlflow_tracking_experiment_registration_error(error):
        return (
            {
                "message": "Bad Gateway - Experiment registration to the MLFlow "
                "Tracking backend has failed. If this happens more than once, please "
                "file a bug report."
            },
            502,
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
