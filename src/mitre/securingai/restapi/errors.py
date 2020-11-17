from flask_restx import Api


def register_error_handlers(api: Api) -> None:
    from .experiment import register_error_handlers as attach_experiment_error_handlers
    from .job import register_error_handlers as attach_job_error_handlers
    from .queue import register_error_handlers as attach_job_queue_error_handlers

    # Add error handlers
    attach_experiment_error_handlers(api)
    attach_job_error_handlers(api)
    attach_job_queue_error_handlers(api)
