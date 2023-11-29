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
from typing import Any, List, Optional

import structlog
from flask import request
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource
from injector import inject
from structlog.stdlib import BoundLogger

from dioptra.restapi.utils import slugify

from .errors import GroupDoesNotExistError
from .model import Group
from .schema import GroupSchema
from .service import GroupService

LOGGER: BoundLogger = structlog.stdlib.get_logger()

api: Namespace = Namespace(
    "Group",
    description="Group submission and management operations",
)


@api.route("/")
class GroupResource(Resource):
    """Shows a list of all Group, and lets you POST to create new groups."""

    @inject
    def __init__(
        self,
        *args,
        group_service: GroupService,
        **kwargs,
    ) -> None:
        self._group_service = group_service
        super().__init__(*args, **kwargs)

    @responds(schema=GroupSchema(many=True), api=api)
    def get(self) -> List[Group]:
        """Gets a list of all groups."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="group", request_type="GET"
        )  # noqa: F841
        log.info("Request received")
        return self._group_service.get_all(log=log)

    @accepts(GroupSchema, api=api)
    @responds(schema=GroupSchema, api=api)
    def post(self) -> Group:
        """Creates a new Group via a group submission form with an attached file."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="group", request_type="POST"
        )  # noqa: F841

        log.info("Request received")

        parsed_obj = request.parsed_obj  # type: ignore
        name = slugify(str(parsed_obj["group_name"]))
        return self._group_service.submit(name=name, log=log)

    @accepts(GroupSchema, api=api)
    def delete(self) -> dict[str, Any]:
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="group", request_type="POST"
        )  # noqa: F841

        log.info("Request received")

        parsed_obj = request.parsed_obj  # type: ignore
        group_id = int(parsed_obj["id"])
        return self._group_service.delete(id=group_id)


@api.route("/<int:groupId>")
@api.param("groupId", "A string specifying a group's UUID.")
class GroupIdResource(Resource):
    """Shows a single job."""

    @inject
    def __init__(self, *args, _service: GroupService, **kwargs) -> None:
        self._group_service = _service
        super().__init__(*args, **kwargs)

    @responds(schema=GroupSchema, api=api)
    def get(self, groupId: int) -> Group:
        """Gets a group by its unique identifier."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="groupId", request_type="GET"
        )  # noqa: F841
        log.info("Request received", group_id=groupId)
        group: Optional[Group] = self._group_service.get_by_id(groupId, log=log)

        if group is None:
            log.error("Group not found", group_id=groupId)
            raise GroupDoesNotExistError

        return group
