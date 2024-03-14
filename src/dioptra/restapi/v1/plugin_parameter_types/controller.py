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
"""The module defining the endpoints for PluginParameterType resources."""
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
    PluginParameterTypeGetQueryParameters,
    PluginParameterTypeMutableFieldsSchema,
    PluginParameterTypePageSchema,
    PluginParameterTypeSchema,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()

api: Namespace = Namespace(
    "PluginParameterTypes", description="Plugin Parameter Types endpoint"
)


@api.route("/")
class PluginParameterTypeEndpoint(Resource):
    @login_required
    @accepts(query_params_schema=PluginParameterTypeGetQueryParameters, api=api)
    @responds(schema=PluginParameterTypePageSchema, api=api)
    def get(self):
        """Gets a list of all PluginParameterType resources."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="PluginParameterTypes",
            request_type="GET",
        )
        log.debug("Request received")
        parsed_query_params = request.parsed_query_params  # noqa: F841

    @login_required
    @accepts(schema=PluginParameterTypeSchema, api=api)
    @responds(schema=PluginParameterTypeSchema, api=api)
    def post(self):
        """Creates a PluginParameterType resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="PluginParameterTypes",
            request_type="POST",
        )
        log.debug("Request received")
        parsed_obj = request.parsed_obj  # noqa: F841


@api.route("/<int:id>")
@api.param("id", "ID for the PluginParameterType resource.")
class PluginParameterTypeIdEndpoint(Resource):
    @login_required
    @responds(schema=IdStatusResponseSchema, api=api)
    def delete(self, id: int):
        """Deletes a PluginParameterType resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="PluginParameterType",
            request_type="DELETE",
            id=id,
        )
        log.debug("Request received")

    @login_required
    @accepts(schema=PluginParameterTypeMutableFieldsSchema, api=api)
    @responds(schema=PluginParameterTypeSchema, api=api)
    def put(self, id: int):
        """Modifies a PluginParameterType resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="PluginParameterType",
            request_type="PUT",
            id=id,
        )
        log.debug("Request received")
        parsed_obj = request.parsed_obj  # type: ignore # noqa: F841
