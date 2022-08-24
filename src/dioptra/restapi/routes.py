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
"""A module for registering the endpoint routes with the main application.

.. |Api| replace:: :py:class:`flask_restx.Api`
.. |Flask| replace:: :py:class:`flask.Flask`
"""
from __future__ import annotations

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
    from .user import register_routes as attach_user

    # Add routes
    attach_experiment(api, app)
    attach_job(api, app)
    attach_job_queue(api, app)
    attach_task_plugin(api, app)
    attach_user(api, app)
