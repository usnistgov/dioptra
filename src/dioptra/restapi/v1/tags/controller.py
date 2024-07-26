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
"""The module defining the endpoints for Tag resources."""
from __future__ import annotations

import uuid
from typing import cast
from urllib.parse import unquote

import structlog
from flask import request
from flask_accepts import accepts, responds
from flask_login import login_required
from flask_restx import Namespace, Resource
from injector import inject
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import models
from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.schemas import IdStatusResponseSchema, ResourceUrlsPageSchema

from .schema import (
    TagGetQueryParameters,
    TagMutableFieldsSchema,
    TagPageSchema,
    TagResourceQueryParameters,
    TagSchema,
)
from .service import TagIdResourcesService, TagIdService, TagService

LOGGER: BoundLogger = structlog.stdlib.get_logger()

api: Namespace = Namespace("Tags", description="Tags endpoint")


@api.route("/")
class TagEndpoint(Resource):
    @inject
    def __init__(self, tag_service: TagService, *args, **kwargs) -> None:
        """Initialize the tag resource.

        All arguments are provided via dependency injection.

        Args:
            tag_service: A TagService object.
        """
        self._tag_service = tag_service
        super().__init__(*args, **kwargs)

    @login_required
    @accepts(query_params_schema=TagGetQueryParameters, api=api)
    @responds(schema=TagPageSchema, api=api)
    def get(self):
        """Gets a list of all Tags."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Tag", request_type="GET"
        )
        parsed_query_params = request.parsed_query_params  # noqa: F841

        group_id = parsed_query_params["group_id"]
        search_string = unquote(parsed_query_params["search"])
        page_index = parsed_query_params["index"]
        page_length = parsed_query_params["page_length"]

        tags, total_num_tags = self._tag_service.get(
            group_id=group_id,
            search_string=search_string,
            page_index=page_index,
            page_length=page_length,
            log=log,
        )
        return utils.build_paging_envelope(
            "tags",
            build_fn=utils.build_tag,
            data=tags,
            group_id=group_id,
            query=search_string,
            draft_type=None,
            index=page_index,
            length=page_length,
            total_num_elements=total_num_tags,
        )

    @login_required
    @accepts(schema=TagSchema, api=api)
    @responds(schema=TagSchema, api=api)
    def post(self):
        """Creates a Tag."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Tag", request_type="POST"
        )
        parsed_obj = request.parsed_obj  # noqa: F841

        tag = self._tag_service.create(
            name=str(parsed_obj["name"]),
            group_id=int(parsed_obj["group_id"]),
            log=log,
        )
        return utils.build_tag(tag)


@api.route("/<int:id>")
@api.param("id", "ID for the Tag.")
class TagIdEndpoint(Resource):
    @inject
    def __init__(self, tag_id_service: TagIdService, *args, **kwargs) -> None:
        """Initialize the tag resource.

        All arguments are provided via dependency injection.

        Args:
            tag_id_service: A TagIdService object.
        """
        self._tag_id_service = tag_id_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=TagSchema, api=api)
    def get(self, id: int):
        """Gets a Tag."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Tag", request_type="GET", id=id
        )
        tag = cast(
            models.Tag,
            self._tag_id_service.get(id, error_if_not_found=True, log=log),
        )
        return utils.build_tag(tag)

    @login_required
    @responds(schema=IdStatusResponseSchema, api=api)
    def delete(self, id: int):
        """Deletes a Tag."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Tag", request_type="DELETE", id=id
        )
        return self._tag_id_service.delete(tag_id=id, error_if_not_found=True, log=log)

    @login_required
    @accepts(schema=TagMutableFieldsSchema, api=api)
    @responds(schema=TagSchema, api=api)
    def put(self, id: int):
        """Modifies a Tag."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Tag", request_type="PUT", id=id
        )
        log.debug("Request received")
        parsed_obj = request.parsed_obj  # type: ignore
        tag = cast(
            models.Tag,
            self._tag_id_service.modify(
                id,
                name=parsed_obj["name"],
                error_if_not_found=True,
                log=log,
            ),
        )
        return utils.build_tag(tag)


@api.route("/<int:id>/resources/")
@api.param("id", "ID for the Tag.")
class TagIdResourceEndpoint(Resource):
    @inject
    def __init__(
        self, tag_id_resources_service: TagIdResourcesService, *args, **kwargs
    ) -> None:
        """Initialize the tag resource.

        All arguments are provided via dependency injection.

        Args:
            tag_id_resources_service: A TagService object.
        """
        self._tag_id_resources_service = tag_id_resources_service
        super().__init__(*args, **kwargs)

    @login_required
    @accepts(query_params_schema=TagResourceQueryParameters, api=api)
    @responds(schema=ResourceUrlsPageSchema, api=api)
    def get(self, id: int):
        """Gets all Resources labeled with this Tag."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Tag", request_type="GET", id=id
        )
        parsed_query_params = request.parsed_query_params  # type: ignore # noqa: F841

        resource_type = parsed_query_params["resource_type"]
        page_index = parsed_query_params["index"]
        page_length = parsed_query_params["page_length"]

        resources, total_num_resources = cast(
            tuple[list[models.Resource], int],
            self._tag_id_resources_service.get(
                id,
                resource_type=resource_type,
                page_index=page_index,
                page_length=page_length,
                error_if_not_found=True,
                log=log,
            ),
        )
        return utils.build_paging_envelope(
            f"tags/{id}/resources",
            build_fn=utils.build_resource_url,
            data=resources,
            group_id=None,
            query=None,
            draft_type=None,
            index=page_index,
            length=page_length,
            total_num_elements=total_num_resources,
        )
