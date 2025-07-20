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
"""The module defining the endpoints for Artifact resources."""

import mimetypes
import shutil
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import unquote

import structlog
from flask import Response, request, send_file
from flask_accepts import accepts, responds
from flask_login import login_required
from flask_restx import Namespace, Resource
from injector import inject
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import models
from dioptra.restapi.errors import QueryParameterValidationError
from dioptra.restapi.routes import V1_ARTIFACTS_ROUTE
from dioptra.restapi.utils import verify_filename_is_safe
from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.filetypes import FileTypes
from dioptra.restapi.v1.shared.job_run_store import JobRunStoreProtocol
from dioptra.restapi.v1.shared.snapshots.controller import (
    generate_resource_snapshots_endpoint,
    generate_resource_snapshots_id_endpoint,
)
from dioptra.sdk.utilities.paths import set_cwd

from .schema import (
    ArtifactContentsGetQueryParameters,
    ArtifactFileSchema,
    ArtifactGetQueryParameters,
    ArtifactMutableFieldsSchema,
    ArtifactPageSchema,
    ArtifactSchema,
)
from .service import (
    RESOURCE_TYPE,
    SEARCHABLE_FIELDS,
    ArtifactIdService,
    ArtifactService,
)
from .snapshot import ArtifactSnapshotIdService

LOGGER: BoundLogger = structlog.stdlib.get_logger()

api: Namespace = Namespace("Artifacts", description="Artifacts endpoint")


@api.route("/")
class ArtifactEndpoint(Resource):
    @inject
    def __init__(self, artifact_service: ArtifactService, *args, **kwargs) -> None:
        """Initialize the artifact resource.

        All arguments are provided via dependency injection.

        Args:
            artifact_service: A ArtifactService object.
        """
        self._artifact_service = artifact_service
        super().__init__(*args, **kwargs)

    @accepts(query_params_schema=ArtifactGetQueryParameters, api=api)
    @responds(schema=ArtifactPageSchema, api=api)
    def get(self):
        """Gets a list of all Artifact resources."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Artifact", request_type="GET"
        )
        parsed_query_params = request.parsed_query_params  # noqa: F841

        group_id = parsed_query_params["group_id"]
        search_string = unquote(parsed_query_params["search"])
        page_index = parsed_query_params["index"]
        page_length = parsed_query_params["page_length"]
        sort_by_string = parsed_query_params["sort_by"]
        descending = parsed_query_params["descending"]

        artifacts, total_num_artifacts = self._artifact_service.get(
            group_id=group_id,
            search_string=search_string,
            page_index=page_index,
            page_length=page_length,
            sort_by_string=sort_by_string,
            descending=descending,
            log=log,
        )
        return utils.build_paging_envelope(
            V1_ARTIFACTS_ROUTE,
            build_fn=utils.build_artifact,
            data=artifacts,
            group_id=group_id,
            query=search_string,
            draft_type=None,
            index=page_index,
            length=page_length,
            total_num_elements=total_num_artifacts,
            sort_by=sort_by_string,
            descending=descending,
        )

    @login_required
    @accepts(schema=ArtifactSchema, api=api)
    @responds(schema=ArtifactSchema, api=api)
    def post(self):
        """Creates an Artifact resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Artifact", request_type="POST"
        )
        log.debug("Request received")
        parsed_obj = request.parsed_obj

        artifact = self._artifact_service.create(
            uri=parsed_obj["artifact_uri"],
            description=parsed_obj["description"],
            group_id=parsed_obj["group_id"],
            job_id=parsed_obj["job_id"],
            plugin_snapshot_id=parsed_obj.get("plugin_snapshot_id"),
            task_id=parsed_obj.get("task_id"),
            log=log,
        )
        return utils.build_artifact(artifact)


@api.route("/<int:id>")
@api.param("id", "ID for the Artifact resource.")
class ArtifactIdEndpoint(Resource):
    @inject
    def __init__(self, artifact_id_service: ArtifactIdService, *args, **kwargs) -> None:
        """Initialize the artifact_id resource.

        All arguments are provided via dependency injection.

        Args:
            artifact_id_service: A ArtifactIdService object.
        """
        self._artifact_id_service = artifact_id_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=ArtifactSchema, api=api)
    def get(self, id: int):
        """Gets an Artifact resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Artifact", request_type="GET", id=id
        )

        artifact = self._artifact_id_service.get(id, log=log)
        return utils.build_artifact(artifact)

    @login_required
    @accepts(schema=ArtifactMutableFieldsSchema, api=api)
    @responds(schema=ArtifactSchema, api=api)
    def put(self, id: int):
        """Modifies an Artifact resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Artifact", request_type="PUT", id=id
        )
        parsed_obj = request.parsed_obj  # type: ignore
        artifact = self._artifact_id_service.modify(
            id,
            description=parsed_obj["description"],
            plugin_snapshot_id=parsed_obj.get("plugin_snapshot_id"),
            task_id=parsed_obj.get("task_id"),
            log=log,
        )
        return utils.build_artifact(artifact)


@api.route("/<int:id>/files")
@api.param("id", "ID for the Artifact resource.")
class ArtifactIdFilesEndpoint(Resource):
    @inject
    def __init__(self, artifact_id_service: ArtifactIdService, *args, **kwargs) -> None:
        """Initialize the artifact files contents resource.

        All arguments are provided via dependency injection.

        Args:
            artifact_id_contents_service: An ArtifactIdContentsService object.
        """
        self._artifact_id_service = artifact_id_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=ArtifactFileSchema(many=True), api=api)
    def get(self, id: int):
        """Gets a list of all files associated with an Artifact resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Artifact", request_type="GET", id=id
        )

        listing = self._artifact_id_service.get_listing(
            artifact_id=id,
            log=log,
        )
        return utils.build_artifact_files(artifact_id=id, files=listing)


@api.route("/<int:id>/contents")
@api.param("id", "ID for the Artifact resource.")
class ArtifactIdContentsEndpoint(Resource):
    @inject
    def __init__(
        self,
        artifact_id_service: ArtifactIdService,
        job_run_store: JobRunStoreProtocol,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the artifact id contents resource.

        All arguments are provided via dependency injection.

        Args:
            artifact_id_contents_service: A ArtifactIdContentsService object.
        """
        self._artifact_id_service = artifact_id_service
        self._job_run_store = job_run_store
        super().__init__(*args, **kwargs)

    @login_required
    @accepts(query_params_schema=ArtifactContentsGetQueryParameters, api=api)
    @responds(schema=ArtifactFileSchema(many=True), api=api)
    def get(self, id: int):
        """
        Downloads the contents of an Artifact resource.

        Args:
            id: the resource id of the artifact

        Returns:
            A list of the files associated with artifact.
        """
        return _handle_artifact_contents(
            job_run_store=self._job_run_store,
            artifact=self._artifact_id_service.get(artifact_id=id)["artifact"],
            log=LOGGER.new(
                request_id=str(uuid.uuid4()),
                resource="Artifact",
                request_type="GET",
                id=id,
            ),
        )


@api.route("/<int:id>/snapshots/<int:snapshotId>/contents")
@api.param("id", "Snapshot ID for the Artifact resource.")
@api.param("snapshotId", "Snapshot ID for the Artifact resource.")
class ArtifactSnapshotIdContentsEndpoint(Resource):
    @inject
    def __init__(
        self,
        artifact_snapshot_id_service: ArtifactSnapshotIdService,
        job_run_store: JobRunStoreProtocol,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the artifact id contents resource.

        All arguments are provided via dependency injection.

        Args:
            artifact_id_contents_service: A ArtifactIdContentsService object.
        """
        self._artifact_snapshot_id_service = artifact_snapshot_id_service
        self._job_run_store = job_run_store
        super().__init__(*args, **kwargs)

    @login_required
    @accepts(query_params_schema=ArtifactContentsGetQueryParameters, api=api)
    @responds(schema=ArtifactFileSchema(many=True), api=api)
    def get(self, id: int, snapshotId: int):
        """
        Downloads the contents of an Artifact snapshot.

        Args:
            id: the resource id of the artifact
            snapshotId: the snapshot resource id of the artifact

        Returns:
            A list of the files associated with artifact.
        """
        return _handle_artifact_contents(
            job_run_store=self._job_run_store,
            artifact=self._artifact_snapshot_id_service.get(
                artifact_id=id, artifact_snapshot_id=snapshotId
            ),
            log=LOGGER.new(
                request_id=str(uuid.uuid4()),
                resource="Artifact",
                request_type="GET",
                id=id,
                snapshotId=snapshotId,
            ),
        )


ArtifactSnapshotsResource = generate_resource_snapshots_endpoint(
    api=api,
    resource_model=models.Artifact,
    resource_name=RESOURCE_TYPE,
    route_prefix=V1_ARTIFACTS_ROUTE,
    searchable_fields=SEARCHABLE_FIELDS,
    page_schema=ArtifactPageSchema,
    build_fn=utils.build_artifact,
)
ArtifactSnapshotsIdResource = generate_resource_snapshots_id_endpoint(
    api=api,
    resource_model=models.Artifact,
    resource_name=RESOURCE_TYPE,
    response_schema=ArtifactSchema,
    build_fn=utils.build_artifact,
)


def _handle_artifact_contents(
    job_run_store: JobRunStoreProtocol, artifact: models.Artifact, log: BoundLogger
) -> Response:
    parsed_query_params = request.parsed_query_params  # type: ignore # noqa: F841

    path: str | None = parsed_query_params.get("path")
    if path:
        # validate the path
        try:
            verify_filename_is_safe(path)
        except ValueError as e:
            log.error("Query Parameter validation failed.", error=e)
            raise QueryParameterValidationError(
                RESOURCE_TYPE, constraint="invalid path query parameter"
            ) from None

    file_type: FileTypes | None = parsed_query_params.get("file_type")

    if not artifact.is_dir and path is not None:
        raise QueryParameterValidationError(
            RESOURCE_TYPE,
            constraint="path query parameter may not be provided for a file",
        )
    if not artifact.is_dir and file_type is not None:
        raise QueryParameterValidationError(
            RESOURCE_TYPE,
            constraint="file_type query parameter may not be provided for a file",
        )

    with TemporaryDirectory() as tmp_dir, set_cwd(tmp_dir):
        mimetype, result = _download_artifacts(
            job_run_store=job_run_store,
            tmp_dir=tmp_dir,
            artifact=artifact,
            path=path,
            file_type=file_type,
        )
        return send_file(
            path_or_file=result,
            mimetype=mimetype,
            as_attachment=False,
            download_name=result.name,
        )


def _download_artifacts(
    job_run_store: JobRunStoreProtocol,
    tmp_dir: str,
    artifact: models.Artifact,
    path: str | None,
    file_type: FileTypes | None,
) -> tuple[str, Path]:
    """
    A helper function for downloading the artifact(s) and preparing them for
    download
    """
    result = job_run_store.download_artifacts(
        artifact_uri=artifact.uri, path=path, destination=Path(tmp_dir)
    )
    if result.is_dir():
        if file_type is None:
            file_type = FileTypes.TAR_GZ

        archive = shutil.make_archive(
            result.name,
            format=file_type.format,
            root_dir=result.parent,
            base_dir=result.name,
        )

        return (file_type.mimetype, Path(archive))
    else:
        mimetype, _ = mimetypes.guess_type(result)
        if mimetype is None:
            mimetype = "application/octet-stream"
        return (mimetype, result)
