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
"""Error handlers for the queue endpoints."""
from __future__ import annotations

from flask_restx import Api


class QueueAlreadyExistsError(Exception):
    """The queue name already exists."""


class QueueDoesNotExistError(Exception):
    """The requested queue does not exist."""


class QueueLockedError(Exception):
    """The requested queue is locked."""


def register_error_handlers(api: Api) -> None:
    @api.errorhandler(QueueDoesNotExistError)
    def handle_queue_does_not_exist_error(error):
        return {"message": "Not Found - The requested queue does not exist"}, 404

    @api.errorhandler(QueueLockedError)
    def handle_queue_locked_error(error):
        return {"message": "Forbidden - The requested queue is locked."}, 403

    @api.errorhandler(QueueAlreadyExistsError)
    def handle_queue_already_exists_error(error):
        return (
            {
                "message": "Bad Request - The queue name on the registration form "
                "already exists. Please select another and resubmit."
            },
            400,
        )
