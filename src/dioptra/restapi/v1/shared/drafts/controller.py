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
"""The module defining the endpoints for Drafts."""
import uuid
from typing import Type, cast

import structlog
from flask import request
from flask_accepts import accepts, responds
from flask_login import login_required
from flask_restx import Namespace, Resource
from injector import ClassAssistedBuilder, inject
from marshmallow import Schema
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import models
from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.schemas import IdStatusResponseSchema

from .schema import (
    DraftExistingResourceSchema,
    DraftGetQueryParameters,
    DraftNewResourceSchema,
    DraftPageSchema,
)
from .service import (
    ResourceDraftsIdService,
    ResourceDraftsService,
    ResourceIdDraftService,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()


def generate_resource_drafts_endpoint(
    api: Namespace,
    resource_name: str,
    route_prefix: str,
    request_schema: Type[Schema],
) -> Resource:
    """
    Generates an Resource class for creating and retrieving Drafts

    Args:
        api: The API namespace
        resource_name: The name of the resource
        request_schema: The request schema type

    Returns:
        The generated Resource class
    """

    @api.route("/drafts/")
    class ResourceDraftsEndpoint(Resource):
        @inject
        def __init__(
            self,
            draft_service: ClassAssistedBuilder[ResourceDraftsService],
            *args,
            **kwargs,
        ) -> None:
            self._draft_service = draft_service.build(resource_type=resource_name)
            super().__init__(*args, **kwargs)

        @login_required
        @accepts(query_params_schema=DraftGetQueryParameters, api=api)
        @responds(schema=DraftPageSchema, api=api)
        def get(self):
            """Gets the Drafts for the resource."""
            log = LOGGER.new(
                request_id=str(uuid.uuid4()), resource="Draft", request_type="GET"
            )
            parsed_query_params = request.parsed_query_params  # noqa: F841

            group_id = parsed_query_params["group_id"]
            page_index = parsed_query_params["index"]
            page_length = parsed_query_params["page_length"]

            drafts, total_num_drafts = self._draft_service.get(
                group_id=group_id,
                page_index=page_index,
                page_length=page_length,
                log=log,
            )
            return utils.build_paging_envelope(
                f"{route_prefix}/drafts",
                build_fn=utils.build_new_resource_draft,
                data=drafts,
                group_id=group_id,
                query=None,
                index=page_index,
                length=page_length,
                total_num_elements=total_num_drafts,
            )

        @login_required
        @accepts(schema=request_schema, api=api)
        @responds(schema=DraftNewResourceSchema, api=api)
        def post(self):
            """Creates a Draft for the resource."""
            log = LOGGER.new(
                request_id=str(uuid.uuid4()), resource="Draft", request_type="POST"
            )
            parsed_obj = request.parsed_obj  # noqa: F841
            draft = self._draft_service.create(parsed_obj, log=log)
            return utils.build_new_resource_draft(draft)

    return ResourceDraftsEndpoint


def generate_resource_drafts_id_endpoint(
    api: Namespace, resource_name: str, request_schema: Type[Schema]
) -> Resource:
    """
    Generates an Resource class for modifying and deleting Drafts

    Args:
        api: The API namespace
        resource_name: The name of the resource
        request_schema: The request schema type

    Returns:
        The generated Resource class
    """

    @api.route("/drafts/<int:draftId>")
    @api.param("draftId", f"ID for the Draft of the {resource_name} resource.")
    class ResourcesDraftsIdEndpoint(Resource):
        @inject
        def __init__(
            self,
            draft_id_service: ClassAssistedBuilder[ResourceDraftsIdService],
            *args,
            **kwargs,
        ) -> None:
            self._draft_id_service = draft_id_service.build(resource_type=resource_name)
            super().__init__(*args, **kwargs)

        @login_required
        @responds(schema=DraftNewResourceSchema, api=api)
        def get(self, draftId: int):
            """Gets a Draft for the resource."""
            log = LOGGER.new(
                request_id=str(uuid.uuid4()), resource="Draft", request_type="GET"
            )
            draft = self._draft_id_service.get(
                draftId, error_if_not_found=True, log=log
            )
            return utils.build_new_resource_draft(cast(models.DraftResource, draft))

        @login_required
        @accepts(schema=request_schema, api=api)
        @responds(schema=DraftNewResourceSchema, api=api)
        def put(self, draftId: int):
            """Modifies a Draft for the resource."""
            log = LOGGER.new(
                request_id=str(uuid.uuid4()), resource="Draft", request_type="POST"
            )
            parsed_obj = request.parsed_obj  # type: ignore
            draft = self._draft_id_service.modify(draftId, payload=parsed_obj, log=log)
            return utils.build_new_resource_draft(cast(models.DraftResource, draft))

        @login_required
        @responds(schema=IdStatusResponseSchema, api=api)
        def delete(self, draftId: int):
            """Deletes a Draft for the resource."""
            log = LOGGER.new(
                request_id=str(uuid.uuid4()), resource="Draft", request_type="DELETE"
            )
            return self._draft_id_service.delete(draftId, log=log)

    return ResourcesDraftsIdEndpoint


def generate_resource_id_draft_endpoint(
    api: Namespace, resource_name: str, request_schema: Type[Schema]
) -> Resource:
    """
    Generates an Resource class for managing the Draft of an existing resource.

    Args:
        api: The API namespace
        resource_name: The name of the resource
        request_schema: The request schema type

    Returns:
        The generated Resource class
    """

    @api.route("/<int:id>/draft")
    @api.param("id", "ID for the resource.")
    class ResourcesIdDraftEndpoint(Resource):
        @inject
        def __init__(
            self,
            id_draft_service: ClassAssistedBuilder[ResourceIdDraftService],
            *args,
            **kwargs,
        ) -> None:
            self._id_draft_service = id_draft_service.build(resource_type=resource_name)
            super().__init__(*args, **kwargs)

        @login_required
        @responds(schema=DraftExistingResourceSchema, api=api)
        def get(self, id: int):
            """Gets the Draft for this resource."""
            log = LOGGER.new(
                request_id=str(uuid.uuid4()), resource="Draft", request_type="GET"
            )
            draft, num_other_drafts = self._id_draft_service.get(
                id, error_if_not_found=True, log=log
            )
            return utils.build_existing_resource_draft(
                cast(models.DraftResource, draft), num_other_drafts
            )

        @login_required
        @accepts(schema=request_schema, api=api)
        @responds(schema=DraftExistingResourceSchema, api=api)
        def post(self, id: int):
            """Creates a Draft for this resource."""
            log = LOGGER.new(
                request_id=str(uuid.uuid4()), resource="Draft", request_type="POST"
            )
            parsed_obj = request.parsed_obj  # type: ignore
            draft, num_other_drafts = self._id_draft_service.create(
                id, payload=parsed_obj, log=log
            )
            return utils.build_existing_resource_draft(
                cast(models.DraftResource, draft), num_other_drafts
            )

        @login_required
        @accepts(schema=request_schema, api=api)
        @responds(schema=DraftExistingResourceSchema, api=api)
        def put(self, id: int):
            """Modifies the Draft for this resource."""
            log = LOGGER.new(
                request_id=str(uuid.uuid4()), resource="Draft", request_type="POST"
            )
            parsed_obj = request.parsed_obj  # type: ignore
            draft, num_other_drafts = self._id_draft_service.modify(
                id, payload=parsed_obj, error_if_not_found=True, log=log
            )
            return utils.build_existing_resource_draft(
                cast(models.DraftResource, draft), num_other_drafts
            )

        @login_required
        @responds(schema=IdStatusResponseSchema, api=api)
        def delete(self, id: int):
            """Deletes the Draft for this resource."""
            log = LOGGER.new(
                request_id=str(uuid.uuid4()), resource="Draft", request_type="DELETE"
            )
            return self._id_draft_service.delete(id, log=log)

    return ResourcesIdDraftEndpoint
