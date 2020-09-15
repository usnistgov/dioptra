from flask_restx import Api


class JobDoesNotExistError(Exception):
    pass


class JobSubmissionError(Exception):
    pass


class JobWorkflowUploadError(Exception):
    pass


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
