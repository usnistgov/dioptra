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
import uuid

import structlog
from flask import request
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource
from injector import inject
from structlog.stdlib import BoundLogger

from dioptra.restapi.utils import as_api_parser, as_parameters_schema_list

from .schema import EchoSchema, EchoSingleFileSchema
from .service import EchoService, EchoSingleFileService

LOGGER: BoundLogger = structlog.stdlib.get_logger()

api: Namespace = Namespace("Echoes", description="Echoes endpoint")


@api.route("/")
class EchoEndpoint(Resource):
    @inject
    def __init__(self, echo_service: EchoService, *args, **kwargs) -> None:
        self._echo_service = echo_service
        super().__init__(*args, **kwargs)

    @api.expect(
        as_api_parser(
            api,
            as_parameters_schema_list(EchoSchema, operation="load", location="form"),
        )
    )
    @accepts(form_schema=EchoSchema, api=api)
    @responds(schema=EchoSchema, api=api)
    def post(self):
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Echo", request_type="POST"
        )
        parsed_obj = request.parsed_form  # noqa: F841

        return self._echo_service.create(
            test_files=request.files.getlist("testFiles"),
            test_string=parsed_obj["test_string"],
            log=log,
        )


@api.route("/singleFile")
class EchoSingleFileEndpoint(Resource):
    @inject
    def __init__(self, echo_service: EchoSingleFileService, *args, **kwargs) -> None:
        self._echo_service = echo_service
        super().__init__(*args, **kwargs)

    @api.expect(
        as_api_parser(
            api,
            as_parameters_schema_list(
                EchoSingleFileSchema, operation="load", location="form"
            ),
        )
    )
    @accepts(form_schema=EchoSingleFileSchema, api=api)
    @responds(schema=EchoSingleFileSchema, api=api)
    def post(self):
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Echo", request_type="POST"
        )
        parsed_obj = request.parsed_form  # noqa: F841

        return self._echo_service.create(
            test_file=request.files.get("testFile"),
            test_string=parsed_obj["test_string"],
            log=log,
        )
