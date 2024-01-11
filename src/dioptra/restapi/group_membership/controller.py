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
"""The module defining the group membership endpoints."""
from __future__ import annotations

import uuid
from typing import Any

import structlog
from flask import request
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource
from injector import inject
from structlog.stdlib import BoundLogger

from .model import GroupMembership
from .schema import GroupMembershipSchema, IdStatusResponseSchema
from .service import GroupMembershipService

LOGGER: BoundLogger = structlog.stdlib.get_logger()

api: Namespace = Namespace(
    "GroupMembership",
    description="Add users to groups",
)


@api.route("/")
class GroupMembershipResource(Resource):
    """Manage group memberships."""

    @inject
    def __init__(
        self,
        *args,
        group_membership_service: GroupMembershipService,
        **kwargs,
    ) -> None:
        self._group_membership_service = group_membership_service
        super().__init__(*args, **kwargs)

    @responds(schema=GroupMembershipSchema(many=True), api=api)
    def get(self) -> list[GroupMembership]:
        """Get a list of all group memberships."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="group_membership",
            request_type="GET",
        )
        log.info("Request received")
        return self._group_membership_service.get_all(log=log)

    @accepts(schema=GroupMembershipSchema, api=api)
    @responds(schema=GroupMembershipSchema, api=api)
    def post(self) -> GroupMembership:
        """Create a new group membership using a group membership submission form."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="group_membership",
            request_type="POST",
        )

        log.info("Request received")

        parsed_obj = request.parsed_obj  # type: ignore
        group_id = int(parsed_obj["group_id"])
        user_id = int(parsed_obj["user_id"])
        read = bool(parsed_obj["read"])
        write = bool(parsed_obj["write"])
        share_read = bool(parsed_obj["share_read"])
        share_write = bool(parsed_obj["share_write"])

        return self._group_membership_service.create(
            group_id, user_id, read, write, share_read, share_write, log=log
        )

    @accepts(schema=GroupMembershipSchema, api=api)
    @responds(schema=IdStatusResponseSchema, api=api)
    def delete(self) -> dict[str, Any]:
        """Delete a group membership."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="group_membership",
            request_type="DELETE",
        )

        log.info("Request received")

        parsed_obj = request.parsed_obj  # type: ignore
        group_id = int(parsed_obj["group_id"])
        user_id = int(parsed_obj["user_id"])
        return self._group_membership_service.delete(group_id, user_id, log=log)
