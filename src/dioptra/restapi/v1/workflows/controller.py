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
from flask import request, send_file
from flask_accepts import accepts, responds
from flask_login import login_required
from flask_restx import Namespace, Resource
from injector import inject
from structlog.stdlib import BoundLogger

from dioptra.restapi.utils import as_api_parser, as_parameters_schema_list
from dioptra.restapi.v1.schemas import IdStatusResponseSchema

from .schema import (
    FileTypes,
    JobFilesDownloadQueryParametersSchema,
    ResourceImportSchema,
    SignatureAnalysisOutputSchema,
    SignatureAnalysisSchema,
    ValidateEntrypointRequestSchema,
    ValidateEntrypointResponseSchema,
)
from .service import (
    DraftCommitService,
    JobFilesDownloadService,
    ResourceImportService,
    SignatureAnalysisService,
    ValidateEntrypointService,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()

api: Namespace = Namespace("Workflows", description="Workflows endpoint")


@api.route("/jobFilesDownload")
class JobFilesDownloadEndpoint(Resource):
    @inject
    def __init__(
        self, job_files_download_service: JobFilesDownloadService, *args, **kwargs
    ) -> None:
        """Initialize the workflow resource.

        All arguments are provided via dependency injection.

        Args:
            job_files_download_service: A JobFilesDownloadService object.
        """
        self._job_files_download_service = job_files_download_service
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
        mimetype = {
            FileTypes.TAR_GZ: "application/gzip",
            FileTypes.ZIP: "application/zip",
        }
        download_name = {
            FileTypes.TAR_GZ: "job_files.tar.gz",
            FileTypes.ZIP: "job_files.zip",
        }
        parsed_query_params = request.parsed_query_params  # noqa: F841
        job_files_download_package = self._job_files_download_service.get(
            job_id=parsed_query_params["job_id"],
            file_type=parsed_query_params["file_type"],
            log=log,
        )
        return send_file(
            path_or_file=job_files_download_package.name,
            as_attachment=True,
            mimetype=mimetype[parsed_query_params["file_type"]],
            download_name=download_name[parsed_query_params["file_type"]],
        )


@api.route("/pluginTaskSignatureAnalysis")
class SignatureAnalysisEndpoint(Resource):
    @inject
    def __init__(
        self, signature_analysis_service: SignatureAnalysisService, *args, **kwargs
    ) -> None:
        """Initialize the workflow resource.

        All arguments are provided via dependency injection.

        Args:
            signature_analysis_service: A SignatureAnalysisService object.
        """
        self._signature_analysis_service = signature_analysis_service
        super().__init__(*args, **kwargs)

    @login_required
    @accepts(schema=SignatureAnalysisSchema, api=api)
    @responds(schema=SignatureAnalysisOutputSchema, api=api)
    def post(self):
        """Download a compressed file archive containing the files needed to execute a submitted job."""  # noqa: B950
        log = LOGGER.new(  # noqa: F841
            request_id=str(uuid.uuid4()),
            resource="SignatureAnalysis",
            request_type="POST",
        )
        parsed_obj = request.parsed_obj
        return self._signature_analysis_service.post(
            python_code=parsed_obj["python_code"],
        )


@api.route("/resourceImport")
class ResourceImport(Resource):
    @inject
    def __init__(
        self, resource_import_service: ResourceImportService, *args, **kwargs
    ) -> None:
        """Initialize the workflow resource.

        All arguments are provided via dependency injection.

        Args:
            resource_import_service: A ResourceImportService object.
        """
        self._resource_import_service = resource_import_service
        super().__init__(*args, **kwargs)

    @login_required
    @api.expect(
        as_api_parser(
            api,
            as_parameters_schema_list(
                ResourceImportSchema, operation="load", location="form"
            ),
        )
    )
    @accepts(form_schema=ResourceImportSchema, api=api)
    def post(self):
        """Import resources from an external source."""  # noqa: B950
        log = LOGGER.new(  # noqa: F841
            request_id=str(uuid.uuid4()), resource="ResourceImport", request_type="POST"
        )
        parsed_form = request.parsed_form

        return self._resource_import_service.import_resources(
            group_id=parsed_form["group_id"],
            source_type=parsed_form["source_type"],
            git_url=parsed_form.get("git_url", None),
            archive_file=request.files.get("archiveFile", None),
            files=request.files.getlist("files", None),
            config_path=parsed_form["config_path"],
            resolve_name_conflicts_strategy=parsed_form[
                "resolve_name_conflicts_strategy"
            ],
            log=log,
        )


@api.route("/draftCommit/<int:id>")
@api.param("id", "ID for the Draft resource.")
class DraftCommitEndpoint(Resource):
    @inject
    def __init__(
        self, draft_commit_service: DraftCommitService, *args, **kwargs
    ) -> None:
        """Initialize the workflow resource.

        All arguments are provided via dependency injection.

        Args:
            draft_commit_service: A DraftCommitService object.
        """
        self._draft_commit_service = draft_commit_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=IdStatusResponseSchema, api=api)
    def post(self, id: int):
        """Commit a draft as a new resource"""  # noqa: B950
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="DraftCommit", request_type="POST"
        )  # noqa: F841
        return self._draft_commit_service.commit_draft(draft_id=id, log=log)


@api.route("/validateEntrypoint")
class ValidateEntrypointEndpoint(Resource):
    @inject
    def __init__(
        self, validate_entrypoint_service: ValidateEntrypointService, *args, **kwargs
    ) -> None:
        """Initialize the workflow resource.

        All arguments are provided via dependency injection.

        Args:
            entrypoint_validate_service: An EntrypointValidateService object.
        """
        self._validate_entrypoint_service = validate_entrypoint_service
        super().__init__(*args, **kwargs)

    @login_required
    @accepts(schema=ValidateEntrypointRequestSchema, api=api)
    @responds(schema=ValidateEntrypointResponseSchema, api=api)
    def post(self):
        """Validates the proposed inputs for an entrypoint."""  # noqa: B950
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="ValidateEntrypoint",
            request_type="POST",
        )
        parsed_obj = request.parsed_obj  # pyright: ignore
        group_id = parsed_obj["group_id"]
        task_graph = parsed_obj["task_graph"]
        plugin_snapshot_ids = parsed_obj["plugin_snapshot_ids"]
        parameters = parsed_obj["parameters"]
        return self._validate_entrypoint_service.validate(
            group_id=group_id,
            task_graph=task_graph,
            plugin_snapshot_ids=plugin_snapshot_ids,
            entrypoint_parameters=parameters,
            log=log,
        )
