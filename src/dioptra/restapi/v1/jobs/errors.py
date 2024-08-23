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
"""Error handlers for the job endpoints."""
from __future__ import annotations

from flask_restx import Api


class JobDoesNotExistError(Exception):
    """The requested job does not exist."""


class JobInvalidStatusTransitionError(Exception):
    """The requested status transition is invalid."""


class JobInvalidParameterNameError(Exception):
    """The requested job parameter name is invalid."""


class JobMlflowRunAlreadySetError(Exception):
    """The requested job already has an mlflow run id set."""


class ExperimentJobDoesNotExistError(Exception):
    """The requested experiment job does not exist."""


class EntryPointNotRegisteredToExperimentError(Exception):
    """The requested entry point is not registered to the provided experiment."""


class QueueNotRegisteredToEntryPointError(Exception):
    """The requested queue is not registered to the provided entry point."""


def register_error_handlers(api: Api) -> None:
    @api.errorhandler(JobDoesNotExistError)
    def handle_job_does_not_exist_error(error):
        return {"message": "Not Found - The requested job does not exist"}, 404

    @api.errorhandler(JobInvalidStatusTransitionError)
    def handle_job_invalid_status_transition_error(error):
        return {
            "message": "Bad Request - The requested job status update is invalid"
        }, 400

    @api.errorhandler(JobInvalidParameterNameError)
    def handle_job_invalid_parameter_name_error(error):
        return {
            "message": "Bad Request - A provided job parameter name does not match any "
            "entrypoint parameters"
        }, 400

    @api.errorhandler(JobMlflowRunAlreadySetError)
    def handle_job_mlflow_run_already_set_error(error):
        return {
            "message": "Bad Request - The requested job already has an mlflow run id "
            "set. It may not be changed."
        }, 400

    @api.errorhandler(ExperimentJobDoesNotExistError)
    def handle_experiment_job_does_not_exist_error(error):
        return {
            "message": "Not Found - The requested experiment job does not exist"
        }, 404

    @api.errorhandler(EntryPointNotRegisteredToExperimentError)
    def handle_entry_point_not_registered_to_experiment_error(error):
        return {
            "message": "Bad Request - The requested entry point is not registered to "
            "the provided experiment"
        }, 400

    @api.errorhandler(QueueNotRegisteredToEntryPointError)
    def handle_queue_not_registered_to_entry_point_error(error):
        return {
            "message": "Bad Request - The requested queue is not registered to the "
            "provided entry point"
        }, 400
