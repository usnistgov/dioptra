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
"""The module defining the endpoints for Workflow resources."""
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
from dioptra.restapi.routes import V1_WORKFLOWS_ROUTE
from dioptra.restapi.v1 import utils

from .schema import WorkflowGetQueryParameters, WorkflowPageSchema, WorkflowSchema
from .service import WorkflowIdService, WorkflowService

LOGGER: BoundLogger = structlog.stdlib.get_logger()

api: Namespace = Namespace("Workflows", description="Workflows endpoint")


@api.route("/")
class WorkflowEndpoint(Resource):
    @inject
    def __init__(self, workflow_service: WorkflowService, *args, **kwargs) -> None:
        """Initialize the workflow resource.

        All arguments are provided via dependency injection.

        Args:
            workflow_service: A WorkflowService object.
        """
        self._workflow_service = workflow_service
        super().__init__(*args, **kwargs)

    @login_required
    @accepts(query_params_schema=WorkflowGetQueryParameters, api=api)
    @responds(schema=WorkflowPageSchema, api=api)
    def get(self):
        """Gets a list of all Workflow resources."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Workflow", request_type="GET"
        )
        parsed_query_params = request.parsed_query_params  # noqa: F841

        group_id = parsed_query_params["group_id"]
        search_string = unquote(parsed_query_params["search"])
        page_index = parsed_query_params["index"]
        page_length = parsed_query_params["page_length"]

        workflows, total_num_workflows = self._workflow_service.get(
            group_id=group_id,
            search_string=search_string,
            page_index=page_index,
            page_length=page_length,
            log=log,
        )
        return utils.build_paging_envelope(
            V1_WORKFLOWS_ROUTE,
            build_fn=utils.build_workflow,
            data=workflows,
            group_id=group_id,
            query=search_string,
            draft_type=None,
            index=page_index,
            length=page_length,
            total_num_elements=total_num_workflows,
        )


@api.route("/<int:id>")
@api.param("id", "ID for the Workflow resource.")
class WorkflowIdEndpoint(Resource):
    @inject
    def __init__(self, workflow_id_service: WorkflowIdService, *args, **kwargs) -> None:
        """Initialize the workflow id resource.

        All arguments are provided via dependency injection.

        Args:
            workflow_id_service: A WorkflowIdService object.
        """
        self._workflow_id_service = workflow_id_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=WorkflowSchema, api=api)
    def get(self, id: int):
        """Gets a Workflow resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Workflow", request_type="GET", id=id
        )
        workflow = cast(
            models.Workflow,
            self._workflow_id_service.get(id, error_if_not_found=True, log=log),
        )
        return utils.build_workflow(workflow)
