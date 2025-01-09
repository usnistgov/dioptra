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
"""The module defining the endpoints for Group resources."""
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
from dioptra.restapi.v1.schemas import IdStatusResponseSchema

from .schema import (
    GroupGetQueryParameters,
    GroupMemberMutableFieldsSchema,
    GroupMemberSchema,
    GroupMutableFieldsSchema,
    GroupPageSchema,
    GroupSchema,
)
from .service import GroupIdService, GroupService

LOGGER: BoundLogger = structlog.stdlib.get_logger()

api: Namespace = Namespace("Groups", description="Groups endpoint")


@api.route("/")
class GroupEndpoint(Resource):
    @inject
    def __init__(self, group_service: GroupService, *args, **kwargs) -> None:
        """Initialize the group service

        All arguments are provided via dependency injection.

        Args:
            group_service: A GroupService object.
        """
        self._group_service = group_service
        super().__init__(*args, **kwargs)

    @login_required
    @accepts(query_params_schema=GroupGetQueryParameters, api=api)
    @responds(schema=GroupPageSchema, api=api)
    def get(self):
        """Gets a list of all Group resources."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Group", request_type="GET"
        )
        parsed_query_params = request.parsed_query_params  # noqa: F841

        search_string = unquote(parsed_query_params["search"])
        page_index = parsed_query_params["index"]
        page_length = parsed_query_params["page_length"]

        groups, total_num_groups = self._group_service.get(
            search_string=search_string,
            page_index=page_index,
            page_length=page_length,
            log=log,
        )
        return utils.build_paging_envelope(
            "groups",
            build_fn=utils.build_group,
            data=groups,
            group_id=None,
            query=search_string,
            draft_type=None,
            index=page_index,
            length=page_length,
            total_num_elements=total_num_groups,
        )

    @login_required
    @accepts(schema=GroupSchema, api=api)
    @responds(schema=GroupSchema, api=api)
    def _post(self):
        """Creates a Group resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Group", request_type="POST"
        )
        parsed_obj = request.parsed_obj  # noqa: F841

        group = self._group_service.create(name=parsed_obj["name"], log=log)
        return utils.build_group(group)


@api.route("/<int:id>")
@api.param("id", "ID for the Group resource.")
class GroupIdEndpoint(Resource):
    @inject
    def __init__(self, group_id_service: GroupIdService, *args, **kwargs) -> None:
        """Initialize the group service

        All arguments are provided via dependency injection.

        Args:
            group_service: A GroupService object.
        """
        self._group_id_service = group_id_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=GroupSchema, api=api)
    def get(self, id: int):
        """Gets a Group resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Group", request_type="GET", id=id
        )
        group = cast(
            models.Group,
            self._group_id_service.get(id, error_if_not_found=True, log=log),
        )
        return utils.build_group(group)

    @login_required
    @responds(schema=IdStatusResponseSchema, api=api)
    def _delete(self, id: int):
        """Deletes a Group resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Group", request_type="DELETE", id=id
        )
        return self._group_id_service.delete(id, log=log)

    @login_required
    @accepts(schema=GroupMutableFieldsSchema, api=api)
    @responds(schema=GroupSchema, api=api)
    def _put(self, id: int):
        """Modifies a Group resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Group", request_type="PUT", id=id
        )
        parsed_obj = request.parsed_obj  # type: ignore # noqa: F841
        group = cast(
            models.Group,
            self._group_id_service.modify(
                id, name=parsed_obj["name"], error_if_not_found=True, log=log
            ),
        )
        return utils.build_group(group)


# @api.route("/<int:id>/members")
@api.param("id", "ID for the Group resource.")
class GroupIdMembersEndpoint(Resource):
    @login_required
    @responds(schema=GroupMemberSchema(many=True), api=api)
    def get(self, id: int):
        """Gets a list of Member's Group Permissions."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="GroupMember",
            request_type="GET",
            id=id,
        )
        log.debug("Request received")

    @login_required
    @accepts(schema=GroupMemberSchema, api=api)
    @responds(schema=GroupMemberSchema, api=api)
    def post(self, id: int):
        """Adds a Member to the Group with default permissions."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="GroupMember",
            request_type="POST",
            id=id,
        )
        log.debug("Request received")
        parsed_obj = request.parsed_obj  # type: ignore # noqa: F841

    @login_required
    @accepts(schema=GroupMemberSchema(many=True), api=api)
    @responds(schema=GroupMemberSchema(many=True), api=api)
    def put(self, id: int):
        """Modifies all Group Members' permissions."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="GroupMember",
            request_type="POST",
            id=id,
        )
        log.debug("Request received")
        parsed_obj = request.parsed_obj  # type: ignore # noqa: F841


# @api.route("/<int:id>/members/<int:user_id>")
@api.param("id", "ID for the Group resource.")
@api.param("user_id", "ID for the User resource.")
class GroupIdMembersUserIdEndpoint(Resource):
    @login_required
    @responds(schema=GroupMemberSchema, api=api)
    def get(self, id: int, user_id: int):
        """Gets a Member's Group permissions."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="GroupMember",
            request_type="GET",
            id=id,
        )
        log.debug("Request received")

    @login_required
    @responds(schema=IdStatusResponseSchema, api=api)
    def delete(self, id: int, user_id: int):
        """Removes a Member from the Group."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="GroupMember",
            request_type="DELETE",
            id=id,
        )
        log.debug("Request received")

    @login_required
    @accepts(schema=GroupMemberMutableFieldsSchema, api=api)
    @responds(schema=GroupMemberSchema, api=api)
    def patch(self, id: int, user_id: int):
        """Modifies a Member's Group permissions."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="GroupMember",
            request_type="PATCH",
            id=id,
        )
        log.debug("Request received")
        parsed_obj = request.parsed_obj  # type: ignore # noqa: F841
