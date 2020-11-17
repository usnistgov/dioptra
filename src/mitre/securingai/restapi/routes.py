from flask import Flask
from flask_restx import Api


def register_routes(api: Api, app: Flask) -> None:
    from .experiment import register_routes as attach_experiment
    from .job import register_routes as attach_job
    from .queue import register_routes as attach_job_queue

    # Add routes
    attach_experiment(api, app)
    attach_job(api, app)
    attach_job_queue(api, app)
