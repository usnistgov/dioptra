# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
"""A module for registering the endpoint routes with the main application.

.. |Api| replace:: :py:class:`flask_restx.Api`
.. |Flask| replace:: :py:class:`flask.Flask`
"""

from flask import Flask
from flask_restx import Api


def register_routes(api: Api, app: Flask) -> None:
    """Registers the endpoint routes with the main application.

    Args:
        api: The main REST |Api| object.
        app: The main |Flask| application.
    """
    from .experiment import register_routes as attach_experiment
    from .job import register_routes as attach_job
    from .queue import register_routes as attach_job_queue
    from .task_plugin import register_routes as attach_task_plugin

    # Add routes
    attach_experiment(api, app)
    attach_job(api, app)
    attach_job_queue(api, app)
    attach_task_plugin(api, app)
