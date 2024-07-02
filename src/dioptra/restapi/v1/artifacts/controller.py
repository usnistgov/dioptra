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
from __future__ import annotations

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
from dioptra.restapi.routes import V1_ARTIFACTS_ROUTE
from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.shared.snapshots.controller import (
    generate_resource_snapshots_endpoint,
    generate_resource_snapshots_id_endpoint,
)

from .schema import (
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

    @login_required
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

        artifacts, total_num_artifacts = self._artifact_service.get(
            group_id=group_id,
            search_string=search_string,
            page_index=page_index,
            page_length=page_length,
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
        parsed_obj = request.parsed_obj  # noqa: F841

        artifact = self._artifact_service.create(
            uri=parsed_obj["uri"],
            description=parsed_obj["description"],
            group_id=parsed_obj["group_id"],
            job_id=parsed_obj["job_id"],
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
        artifact = cast(
            models.Artifact,
            self._artifact_id_service.get(id, error_if_not_found=True, log=log),
        )
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
        artifact = cast(
            models.Artifact,
            self._artifact_id_service.modify(
                id,
                description=parsed_obj["description"],
                error_if_not_found=True,
                log=log,
            ),
        )
        return utils.build_artifact(artifact)


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
