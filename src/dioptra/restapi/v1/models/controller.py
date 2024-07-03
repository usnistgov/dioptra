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
"""The module defining the endpoints for Model resources."""
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
from dioptra.restapi.routes import V1_MODELS_ROUTE
from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.schemas import IdStatusResponseSchema
from dioptra.restapi.v1.shared.drafts.controller import (
    generate_resource_drafts_endpoint,
    generate_resource_drafts_id_endpoint,
    generate_resource_id_draft_endpoint,
)
from dioptra.restapi.v1.shared.snapshots.controller import (
    generate_resource_snapshots_endpoint,
    generate_resource_snapshots_id_endpoint,
)
from dioptra.restapi.v1.shared.tags.controller import (
    generate_resource_tags_endpoint,
    generate_resource_tags_id_endpoint,
)

from .schema import (
    ModelGetQueryParameters,
    ModelMutableFieldsSchema,
    ModelPageSchema,
    ModelSchema,
    ModelVersionGetQueryParameters,
    ModelVersionMutableFieldsSchema,
    ModelVersionPageSchema,
    ModelVersionSchema,
)
from .service import (
    MODEL_RESOURCE_TYPE,
    MODEL_SEARCHABLE_FIELDS,
    ModelIdService,
    ModelIdVersionsNumberService,
    ModelIdVersionsService,
    ModelService,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()

api: Namespace = Namespace("Models", description="Models endpoint")


@api.route("/")
class ModelEndpoint(Resource):
    @inject
    def __init__(self, model_service: ModelService, *args, **kwargs) -> None:
        """Initialize the model resource.

        All arguments are provided via dependency injection.

        Args:
            model_service: A ModelService object.
        """
        self._model_service = model_service
        super().__init__(*args, **kwargs)

    @login_required
    @accepts(query_params_schema=ModelGetQueryParameters, api=api)
    @responds(schema=ModelPageSchema, api=api)
    def get(self):
        """Gets a list of all Model resources."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Models", request_type="GET"
        )

        parsed_query_params = request.parsed_query_params  # noqa: F841
        group_id = parsed_query_params["group_id"]
        search_string = unquote(parsed_query_params["search"])
        page_index = parsed_query_params["index"]
        page_length = parsed_query_params["page_length"]

        models, total_num_models = self._model_service.get(
            group_id=group_id,
            search_string=search_string,
            page_index=page_index,
            page_length=page_length,
            log=log,
        )
        return utils.build_paging_envelope(
            "models",
            build_fn=utils.build_model,
            data=models,
            group_id=group_id,
            query=search_string,
            draft_type=None,
            index=page_index,
            length=page_length,
            total_num_elements=total_num_models,
        )

    @login_required
    @accepts(schema=ModelSchema, api=api)
    @responds(schema=ModelSchema, api=api)
    def post(self):
        """Creates a Model resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Model", request_type="POST"
        )
        parsed_obj = request.parsed_obj  # noqa: F841
        model = self._model_service.create(
            name=parsed_obj["name"],
            description=parsed_obj["description"],
            group_id=parsed_obj["group_id"],
            log=log,
        )
        return utils.build_model(model)


@api.route("/<int:id>")
@api.param("id", "ID for the Model resource.")
class ModelIdEndpoint(Resource):
    @inject
    def __init__(self, model_id_service: ModelIdService, *args, **kwargs) -> None:
        """Initialize the model resource.

        All arguments are provided via dependency injection.

        Args:
            model_id_service: A ModelIdService object.
        """
        self._model_id_service = model_id_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=ModelSchema, api=api)
    def get(self, id: int):
        """Gets a Model resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Model", request_type="GET", id=id
        )
        model = cast(
            models.MlModel,
            self._model_id_service.get(id, error_if_not_found=True, log=log),
        )
        return utils.build_model(model)

    @login_required
    @responds(schema=IdStatusResponseSchema, api=api)
    def delete(self, id: int):
        """Deletes a Model resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Model", request_type="DELETE", id=id
        )
        return self._model_id_service.delete(model_id=id, log=log)

    @login_required
    @accepts(schema=ModelMutableFieldsSchema, api=api)
    @responds(schema=ModelSchema, api=api)
    def put(self, id: int):
        """Modifies a Model resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Model", request_type="PUT", id=id
        )
        parsed_obj = request.parsed_obj  # type: ignore # noqa: F841
        model = cast(
            models.MlModel,
            self._model_id_service.modify(
                id,
                name=parsed_obj["name"],
                description=parsed_obj["description"],
                error_if_not_found=True,
                log=log,
            ),
        )
        return utils.build_model(model)


@api.route("/<int:id>/versions")
@api.param("id", "ID for the Models resource.")
class ModelIdVersionsEndpoint(Resource):
    @inject
    def __init__(
        self, model_id_versions_service: ModelIdVersionsService, *args, **kwargs
    ) -> None:
        """Initialize the model resource.

        All arguments are provided via dependency injection.

        Args:
            model_id_versions_service: A ModelIdVersionsService object.
        """
        self._model_id_versions_service = model_id_versions_service
        super().__init__(*args, **kwargs)

    @login_required
    @accepts(query_params_schema=ModelVersionGetQueryParameters, api=api)
    @responds(schema=ModelVersionPageSchema, api=api)
    def get(self, id: int):
        """Gets a list of versions of this Model resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Model", request_type="GET"
        )

        parsed_query_params = request.parsed_query_params  # type: ignore
        search_string = unquote(parsed_query_params["search"])
        page_index = parsed_query_params["index"]
        page_length = parsed_query_params["page_length"]

        versions, total_num_versions = cast(
            tuple[list[utils.ModelWithVersionDict], int],
            self._model_id_versions_service.get(
                model_id=id,
                search_string=search_string,
                page_index=page_index,
                page_length=page_length,
                error_if_not_found=True,
                log=log,
            ),
        )
        return utils.build_paging_envelope(
            f"models/{id}/versions",
            build_fn=utils.build_model_version,
            data=versions,
            group_id=None,
            query=search_string,
            draft_type=None,
            index=page_index,
            length=page_length,
            total_num_elements=total_num_versions,
        )

    @login_required
    @accepts(schema=ModelVersionSchema, api=api)
    @responds(schema=ModelVersionSchema, api=api)
    def post(self, id: int):
        """Creates a new version of the model resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Model", request_type="POST"
        )
        parsed_obj = request.parsed_obj  # type: ignore
        model = self._model_id_versions_service.create(
            id,
            description=parsed_obj["description"],
            artifact_id=parsed_obj["artifact_id"],
            log=log,
        )
        return utils.build_model_version(model)


@api.route("/<int:id>/versions/<int:versionNumber>")
@api.param("id", "ID for the Model resource.")
@api.param("versionNumber", "Version number for the Model resource.")
class ModelIdVersionsNumberEndpoint(Resource):
    @inject
    def __init__(
        self,
        model_id_versions_number_service: ModelIdVersionsNumberService,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the model resource.

        All arguments are provided via dependency injection.

        Args:
            model_id_versions_number_service: A ModelIdVersionsNumberService object.
        """
        self._model_id_versions_number_service = model_id_versions_number_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=ModelVersionSchema, api=api)
    def get(self, id: int, versionNumber: int):
        """Gets a specific version of a model by version number."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Models", request_type="GET"
        )
        model = cast(
            utils.ModelWithVersionDict,
            self._model_id_versions_number_service.get(
                id, version_number=versionNumber, error_if_not_found=True, log=log
            ),
        )
        return utils.build_model_version(model)

    @login_required
    @accepts(schema=ModelVersionMutableFieldsSchema, api=api)
    @responds(schema=ModelVersionSchema, api=api)
    def put(self, id: int, versionNumber: int):
        """Modifies specific version of the model resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Model", request_type="POST"
        )
        parsed_obj = request.parsed_obj  # type: ignore
        model = cast(
            utils.ModelWithVersionDict,
            self._model_id_versions_number_service.modify(
                id,
                versionNumber,
                description=parsed_obj["description"],
                error_if_not_found=True,
                log=log,
            ),
        )
        return utils.build_model_version(model)


ModelDraftResource = generate_resource_drafts_endpoint(
    api,
    resource_name=MODEL_RESOURCE_TYPE,
    route_prefix=V1_MODELS_ROUTE,
    request_schema=ModelSchema,
)
ModelDraftIdResource = generate_resource_drafts_id_endpoint(
    api,
    resource_name=MODEL_RESOURCE_TYPE,
    request_schema=ModelSchema(exclude=["groupId"]),
)
ModelIdDraftResource = generate_resource_id_draft_endpoint(
    api,
    resource_name=MODEL_RESOURCE_TYPE,
    request_schema=ModelSchema(exclude=["groupId"]),
)

ModelSnapshotsResource = generate_resource_snapshots_endpoint(
    api=api,
    resource_model=models.MlModel,
    resource_name=MODEL_RESOURCE_TYPE,
    route_prefix=V1_MODELS_ROUTE,
    searchable_fields=MODEL_SEARCHABLE_FIELDS,
    page_schema=ModelPageSchema,
    build_fn=utils.build_model,
)
ModelSnapshotsIdResource = generate_resource_snapshots_id_endpoint(
    api=api,
    resource_model=models.MlModel,
    resource_name=MODEL_RESOURCE_TYPE,
    response_schema=ModelSchema,
    build_fn=utils.build_model,
)

ModelTagsResource = generate_resource_tags_endpoint(
    api=api,
    resource_name=MODEL_RESOURCE_TYPE,
)
ModelTagsIdResource = generate_resource_tags_id_endpoint(
    api=api,
    resource_name=MODEL_RESOURCE_TYPE,
)
