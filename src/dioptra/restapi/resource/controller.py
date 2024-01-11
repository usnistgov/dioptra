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
"""The module defining the group endpoints."""
from __future__ import annotations

import uuid
from typing import Any, List, cast

import structlog
from flask import request
from flask_accepts import accepts, responds
from flask_login import login_required
from flask_restx import Namespace, Resource
from injector import inject
from structlog.stdlib import BoundLogger

from .model import DioptraResource
from .schema import DioptraResourceSchema, IdStatusResponseSchema
from .service import DioptraResourceService

LOGGER: BoundLogger = structlog.stdlib.get_logger()

api: Namespace = Namespace(
    "DioptraResource",
    description="Dioptra Resource submission and management operations",
)


@api.route("/")
class DioptraResourceResource(Resource):
    """Shows a list of all Dioptra Resources, and lets you POST to create new
    Dioptra Resources."""

    @inject
    def __init__(
        self,
        *args,
        dioptra_resource_service: DioptraResourceService,
        **kwargs,
    ) -> None:
        self._dioptra_resource_service = dioptra_resource_service
        super().__init__(*args, **kwargs)

    @responds(schema=DioptraResourceSchema(many=True), api=api)
    def get(self) -> List[DioptraResource]:
        """Gets a list of all Dioptra Resources."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="dioptra_resource",
            request_type="GET",
        )  # noqa: F841
        log.info("Request received")
        return self._dioptra_resource_service.get_all(log=log)

    @login_required
    @accepts(schema=DioptraResourceSchema, api=api)
    @responds(schema=DioptraResourceSchema, api=api)
    def post(self) -> DioptraResource:
        """Registers a new Dioptra Resource"""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="dioptra_resource",
            request_type="POST",
        )  # noqa: F841

        log.info("Request received")

        parsed_obj = request.parsed_obj  # type: ignore
        owner_id = int(parsed_obj["owner_id"])
        creator_id = int(parsed_obj["creator_id"])

        return self._dioptra_resource_service.create(
            owner_id=owner_id, creator_id=creator_id, log=log
        )


@api.route("/<int:resourceId>")
@api.param("resourceId", "An integer specifying a resource's ID.")
class DioptraResourceIdResource(Resource):
    """Shows a single Dioptra Resource."""

    @inject
    def __init__(
        self,
        *args,
        dioptra_resource_service: DioptraResourceService,
        **kwargs,
    ) -> None:
        self._dioptra_resource_service = dioptra_resource_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=DioptraResourceSchema, api=api)
    def get(self, resourceId: int) -> DioptraResource:
        """Gets a Dioptra Resource by its unique identifier."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="dioptra_resource_id",
            request_type="GET",
        )  # noqa: F841
        log.info("Request received", resource_id=resourceId)
        resource = self._dioptra_resource_service.get(resourceId, log=log)

        return cast(DioptraResource, resource)

    @login_required
    @responds(schema=IdStatusResponseSchema, api=api)
    def delete(self, resourceId: int) -> dict[str, Any]:
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="dioptra_resource",
            request_type="POST",
        )  # noqa: F841

        log.info("Request received")

        return self._dioptra_resource_service.delete(resource_id=resourceId)
