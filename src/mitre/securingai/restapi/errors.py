# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
"""A module for registering the error handlers for the application.

.. |Api| replace:: :py:class:`flask_restx.Api`
"""

from flask_restx import Api


def register_error_handlers(api: Api) -> None:
    """Registers the error handlers with the main application.

    Args:
        api: The main REST |Api| object.
    """
    from .experiment import register_error_handlers as attach_experiment_error_handlers
    from .job import register_error_handlers as attach_job_error_handlers
    from .queue import register_error_handlers as attach_job_queue_error_handlers
    from .task_plugin import (
        register_error_handlers as attach_task_plugin_error_handlers,
    )

    # Add error handlers
    attach_experiment_error_handlers(api)
    attach_job_error_handlers(api)
    attach_job_queue_error_handlers(api)
    attach_task_plugin_error_handlers(api)
