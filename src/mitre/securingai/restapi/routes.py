from flask import Flask
from flask_restx import Api


def register_routes(api: Api, app: Flask) -> None:
    from .job import register_routes as attach_job

    # Add routes
    attach_job(api, app)
