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
"""The module defining the endpoints for Entrypoint resources."""
from __future__ import annotations

import uuid

import structlog
from flask import request
from flask_accepts import accepts, responds
from flask_login import login_required
from flask_restx import Namespace, Resource
from structlog.stdlib import BoundLogger

from dioptra.restapi.v1.schemas import IdStatusResponseSchema

from .schema import (
    EntrypointGetQueryParameters,
    EntrypointMutableFieldsSchema,
    EntrypointPageSchema,
    EntrypointSchema,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()

api: Namespace = Namespace("Entrypoints", description="Entrypoints endpoint")


@api.route("/")
class EntrypointEndpoint(Resource):
    @login_required
    @accepts(query_params_schema=EntrypointGetQueryParameters, api=api)
    @responds(schema=EntrypointPageSchema, api=api)
    def get(self):
        """Gets a list of Entrypoint resources matching the filter parameters."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Entrypoint", request_type="GET"
        )
        log.debug("Request received")
        """
        index = request.args.get("index", 0, type=int)
        page_length = request.args.get("pageLength", 20, type=int)

        data = self._entrypoint_service.get_page(
            index=index, page_length=page_length, log=log
        )

        is_complete = True if Entrypoint.query.count() <= index + page_length else False

        return Page(
            data=data,
            index=index,
            is_complete=is_complete,
            endpoint="v1/entrypoint",
            page_length=page_length,
        )"""

    @login_required
    @accepts(schema=EntrypointSchema, api=api)
    @responds(schema=EntrypointSchema, api=api)
    def post(self):
        """Creates an Entrypoint resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Entrypoint", request_type="POST"
        )
        log.debug("Request received")
        parsed_obj = request.parsed_obj  # noqa: F841
        # return self._entrypoint_service.create(
        #    parsed_obj["name"],
        #    parsed_obj["task_graph"],
        #    parsed_obj["parameters"],
        #    log=log,
        # )


@api.route("/<int:id>")
@api.param("id", "ID for the Entrypoint resource.")
class EntrypointIdEndpoint(Resource):
    @login_required
    @responds(schema=EntrypointSchema, api=api)
    def get(self, id: int):
        """Gets an Entrypoint resource by its unique ID."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="Entrypoint",
            request_type="GET",
            id=id,
        )
        log.debug("Request received")
        # return self._entrypoint_service.get(id, error_if_not_found=True, log=log)

    @login_required
    @responds(schema=IdStatusResponseSchema, api=api)
    def delete(self, id: int):
        """Deletes an Entrypoint resource by its unique ID."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="Entrypoint",
            request_type="DELETE",
            id=id,
        )
        log.debug("Request received")
        # return self._entrypoint_service.delete(id)

    @login_required
    @accepts(schema=EntrypointMutableFieldsSchema, api=api)
    @responds(schema=EntrypointSchema, api=api)
    def put(self, id: int):
        """Modifies an Entrypoint resource by its unique ID."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="Entrypoint",
            request_type="PUT",
            id=id,
        )
        log.debug("Request received")
        parsed_obj = request.parsed_obj  # type: ignore # noqa: F841
        # return self._entrypoint_service.edit(
        #    parsed_obj["name"],
        #    parsed_obj["task_graph"],
        #    parsed_obj["parameters"],)
        #    log=log,
        # )
