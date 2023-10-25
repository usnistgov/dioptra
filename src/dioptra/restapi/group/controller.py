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
"""The module defining the job endpoints."""
from __future__ import annotations

import uuid
from typing import List, Optional

import structlog
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource
from injector import inject
from structlog.stdlib import BoundLogger

from dioptra.restapi.utils import as_api_parser

from .errors import GroupDoesNotExistError, GroupSubmissionError
from .model import Group, GroupForm, GroupFormData
from .schema import GroupSchema, group_submit_form_schema
from .service import GroupService

LOGGER: BoundLogger = structlog.stdlib.get_logger()

api: Namespace = Namespace(
    "Group",
    description="Group submission and management operations",
)


@api.route("/")
class GroupResource(Resource):
    """Shows a list of all jobs, and lets you POST to create new jobs."""

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

    @api.expect(as_api_parser(api, group_submit_form_schema))
    @accepts(group_submit_form_schema, api=api)
    @responds(schema=GroupSchema, api=api)
    def post(self) -> Group:
        """Creates a new Group via a group submission form with an attached file."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="group", request_type="POST"
        )  # noqa: F841
        # group_form: GroupForm = GroupForm()

        log.info("Request received")

        # if not group_form.validate_on_submit():
        #     log.error("Form validation failed")
        #     raise GroupSubmissionError

        # log.info("Form validation successful")
        # group_form_data: GroupFormData = self._group_service.extract_data_from_form(
        #     group_form=group_form,
        #     log=log,
        # )

        parsed_obj = request.parsed_obj  # type: ignore
        name = slugify(str(parsed_obj["group_name"]))
        return self._group_service.submit(group_form_data=group_form_data, log=log)
    
    @accepts(group_submit_form_schema, api=api)
    def delete(self) -> bool:
        #need to get id from form, validate it exists, and is not yet deleted then, send to serivce
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="group", request_type="POST"
        )  # noqa: F841

        #group_form: GroupForm = GroupForm()

        log.info("Request received")

        # if not group_form.validate_on_submit():
        #     log.error("Form validation failed")
        #     raise GroupSubmissionError

        # log.info("Form validation successful")
        # group_form_data: GroupFormData = self._group_service.extract_data_from_form(
        #     group_form=group_form,
        #     log=log,
        # )
        parsed_obj = request.parsed_obj  # type: ignore
        group_id = (int(parsed_obj["id"]))
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
