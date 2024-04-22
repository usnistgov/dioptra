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
"""The module defining the endpoints for Queue resources."""
from __future__ import annotations

import uuid

import structlog
from flask import request
from flask_accepts import accepts, responds
from flask_login import login_required
from flask_restx import Namespace, Resource
from structlog.stdlib import BoundLogger

from dioptra.restapi.v1.schemas import IdStatusResponseSchema
from dioptra.restapi.v1.tags.controller import ResourceTagEndpoint

from .schema import (
    QueueGetQueryParameters,
    QueueMutableFieldsSchema,
    QueuePageSchema,
    QueueSchema,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()

api: Namespace = Namespace("Queues", description="Queues endpoint")


@api.route("/<int:id>/tags")
class QueueTagsEndpoint(ResourceTagEndpoint):
    """Tagging functionality"""

    # @inject
    # def __init__(self, *args, queue_service: QueueService, **kwargs) -> None:
    # self._queue_service = queue_service
    # self._resource_name = "Queue"
    # super().__init__(*args, **kwargs)


@api.route("/")
class QueueEndpoint(Resource):
    @login_required
    @accepts(query_params_schema=QueueGetQueryParameters, api=api)
    @responds(schema=QueuePageSchema, api=api)
    def get(self):
        """Gets a list of all Queue resources."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Queue", request_type="GET"
        )
        log.debug("Request received")
        parsed_query_params = request.parsed_query_params  # noqa: F841

    @login_required
    @accepts(schema=QueueSchema, api=api)
    @responds(schema=QueueSchema, api=api)
    def post(self):
        """Creates a Queue resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Queue", request_type="POST"
        )
        log.debug("Request received")
        parsed_obj = request.parsed_obj  # noqa: F841


@api.route("/<int:id>")
@api.param("id", "ID for the Queue resource.")
class QueueIdEndpoint(Resource):
    @login_required
    @responds(schema=QueueSchema, api=api)
    def get(self, id: int):
        """Gets a Queue resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Queue", request_type="GET", id=id
        )
        log.debug("Request received")

    @login_required
    @responds(schema=IdStatusResponseSchema, api=api)
    def delete(self, id: int):
        """Deletes a Queue resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Queue", request_type="DELETE", id=id
        )
        log.debug("Request received")

    @login_required
    @accepts(schema=QueueMutableFieldsSchema, api=api)
    @responds(schema=QueueSchema, api=api)
    def put(self, id: int):
        """Modifies a Queue resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Queue", request_type="PUT", id=id
        )
        log.debug("Request received")
        parsed_obj = request.parsed_obj  # type: ignore # noqa: F841
