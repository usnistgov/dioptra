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

import structlog
from flask import request
from flask_accepts import accepts
from flask_login import login_required
from flask_restx import Namespace, Resource
from injector import inject
from structlog.stdlib import BoundLogger

from .schema import JobFilesDownloadQueryParametersSchema

LOGGER: BoundLogger = structlog.stdlib.get_logger()

api: Namespace = Namespace("Workflows", description="Workflows endpoint")


@api.route("/jobFilesDownload")
class JobFilesDownloadEndpoint(Resource):
    @inject
    def __init__(self, *args, **kwargs) -> None:
        """Initialize the workflow resource.

        All arguments are provided via dependency injection.
        """
        super().__init__(*args, **kwargs)

    @login_required
    @accepts(query_params_schema=JobFilesDownloadQueryParametersSchema, api=api)
    def get(self):
        """Download a compressed file archive containing the files needed to execute a submitted job."""  # noqa: B950
        log = LOGGER.new(  # noqa: F841
            request_id=str(uuid.uuid4()),
            resource="JobFilesDownload",
            request_type="GET",
        )
        parsed_query_params = request.parsed_query_params  # noqa: F841
