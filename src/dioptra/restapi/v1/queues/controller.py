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
from dioptra.restapi.routes import V1_QUEUES_ROUTE
from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.schemas import IdStatusResponseSchema
from dioptra.restapi.v1.shared.drafts.controller import (
    generate_resource_drafts_endpoint,
    generate_resource_drafts_id_endpoint,
    generate_resource_id_draft_endpoint,
)
from dioptra.restapi.v1.shared.snapshots.controller import (
    generate_resource_snapshots_endpoint,
    generate_resource_snapshots_id_endpoint,
)
from dioptra.restapi.v1.shared.tags.controller import (
    generate_resource_tags_endpoint,
    generate_resource_tags_id_endpoint,
)

from .schema import (
    QueueGetQueryParameters,
    QueueMutableFieldsSchema,
    QueuePageSchema,
    QueueSchema,
)
from .service import RESOURCE_TYPE, SEARCHABLE_FIELDS, QueueIdService, QueueService

LOGGER: BoundLogger = structlog.stdlib.get_logger()

api: Namespace = Namespace("Queues", description="Queues endpoint")


@api.route("/")
class QueueEndpoint(Resource):
    @inject
    def __init__(self, queue_service: QueueService, *args, **kwargs) -> None:
        """Initialize the queue resource.

        All arguments are provided via dependency injection.

        Args:
            queue_service: A QueueService object.
        """
        self._queue_service = queue_service
        super().__init__(*args, **kwargs)

    @login_required
    @accepts(query_params_schema=QueueGetQueryParameters, api=api)
    @responds(schema=QueuePageSchema, api=api)
    def get(self):
        """Gets a list of all Queue resources."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Queue", request_type="GET"
        )
        parsed_query_params = request.parsed_query_params  # noqa: F841

        group_id = parsed_query_params["group_id"]
        search_string = unquote(parsed_query_params["search"])
        page_index = parsed_query_params["index"]
        page_length = parsed_query_params["page_length"]

        queues, total_num_queues = self._queue_service.get(
            group_id=group_id,
            search_string=search_string,
            page_index=page_index,
            page_length=page_length,
            log=log,
        )
        return utils.build_paging_envelope(
            V1_QUEUES_ROUTE,
            build_fn=utils.build_queue,
            data=queues,
            group_id=group_id,
            query=search_string,
            draft_type=None,
            index=page_index,
            length=page_length,
            total_num_elements=total_num_queues,
        )

    @login_required
    @accepts(schema=QueueSchema, api=api)
    @responds(schema=QueueSchema, api=api)
    def post(self):
        """Creates a Queue resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Queue", request_type="POST"
        )
        parsed_obj = request.parsed_obj  # noqa: F841

        queue = self._queue_service.create(
            name=parsed_obj["name"],
            description=parsed_obj["description"],
            group_id=parsed_obj["group_id"],
            log=log,
        )
        return utils.build_queue(queue)


@api.route("/<int:id>")
@api.param("id", "ID for the Queue resource.")
class QueueIdEndpoint(Resource):
    @inject
    def __init__(self, queue_id_service: QueueIdService, *args, **kwargs) -> None:
        """Initialize the queue resource.

        All arguments are provided via dependency injection.

        Args:
            queue_id_service: A QueueIdService object.
        """
        self._queue_id_service = queue_id_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=QueueSchema, api=api)
    def get(self, id: int):
        """Gets a Queue resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Queue", request_type="GET", id=id
        )
        queue = cast(
            models.Queue,
            self._queue_id_service.get(id, error_if_not_found=True, log=log),
        )
        return utils.build_queue(queue)

    @login_required
    @responds(schema=IdStatusResponseSchema, api=api)
    def delete(self, id: int):
        """Deletes a Queue resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Queue", request_type="DELETE", id=id
        )
        return self._queue_id_service.delete(queue_id=id, log=log)

    @login_required
    @accepts(schema=QueueMutableFieldsSchema, api=api)
    @responds(schema=QueueSchema, api=api)
    def put(self, id: int):
        """Modifies a Queue resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Queue", request_type="PUT", id=id
        )
        parsed_obj = request.parsed_obj  # type: ignore
        queue = cast(
            models.Queue,
            self._queue_id_service.modify(
                id,
                name=parsed_obj["name"],
                description=parsed_obj["description"],
                error_if_not_found=True,
                log=log,
            ),
        )
        return utils.build_queue(queue)


QueueDraftResource = generate_resource_drafts_endpoint(
    api,
    resource_name=RESOURCE_TYPE,
    route_prefix=V1_QUEUES_ROUTE,
    request_schema=QueueSchema,
)
QueueDraftIdResource = generate_resource_drafts_id_endpoint(
    api,
    resource_name=RESOURCE_TYPE,
    request_schema=QueueMutableFieldsSchema,
)
QueueIdDraftResource = generate_resource_id_draft_endpoint(
    api,
    resource_name=RESOURCE_TYPE,
    request_schema=QueueMutableFieldsSchema,
)

QueueSnapshotsResource = generate_resource_snapshots_endpoint(
    api=api,
    resource_model=models.Queue,
    resource_name=RESOURCE_TYPE,
    route_prefix=V1_QUEUES_ROUTE,
    searchable_fields=SEARCHABLE_FIELDS,
    page_schema=QueuePageSchema,
    build_fn=utils.build_queue,
)
QueueSnapshotsIdResource = generate_resource_snapshots_id_endpoint(
    api=api,
    resource_model=models.Queue,
    resource_name=RESOURCE_TYPE,
    response_schema=QueueSchema,
    build_fn=utils.build_queue,
)

QueueTagsResource = generate_resource_tags_endpoint(
    api=api,
    resource_name=RESOURCE_TYPE,
)
QueueTagsIdResource = generate_resource_tags_id_endpoint(
    api=api,
    resource_name=RESOURCE_TYPE,
)
