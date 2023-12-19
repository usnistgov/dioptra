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


class JobSubmissionError(Exception):
    """The job submission form contains invalid parameters."""


class JobWorkflowUploadError(Exception):
    """The service for storing the uploaded workfile file is unavailable."""


class JobStatusIncorrectError(Exception):
    """The job status failed validation."""


class InvalidExperimentDescriptionError(Exception):
    """The experiment description failed validation."""


def register_error_handlers(api: Api) -> None:
    @api.errorhandler(JobDoesNotExistError)
    def handle_job_does_not_exist_error(error):
        return {"message": "Not Found - The requested job does not exist"}, 404

    @api.errorhandler(JobSubmissionError)
    def handle_job_submission_error(error):
        return (
            {
                "message": "Bad Request - The job submission form contains "
                "invalid parameters. Please verify and resubmit."
            },
            400,
        )

    @api.errorhandler(JobWorkflowUploadError)
    def handle_job_workflow_upload_error(error):
        return (
            {
                "message": "Service Unavailable - Unable to store the "
                "workflow file after upload. Please try again "
                "later."
            },
            503,
        )

    @api.errorhandler(InvalidExperimentDescriptionError)
    def handle_invalid_experiment_description_error(error):
        return {"message": "The experiment description is invalid!"}, 400

    @api.errorhandler(JobStatusIncorrectError)
    def handle_job_status_incorrect_error(error):
        return {
            "message": "The job status is invalid! Must be one of"
            "['queued', 'started', 'deferred', 'finished', 'failed']"
        }, 400
