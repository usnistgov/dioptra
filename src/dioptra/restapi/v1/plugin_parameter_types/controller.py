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
"""The module defining the endpoints for PluginParameterType resources."""
import uuid
from typing import cast

import structlog
from flask import request
from flask_accepts import accepts, responds
from flask_login import login_required
from flask_restx import Namespace, Resource
from injector import inject
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import models
from dioptra.restapi.routes import V1_PLUGIN_PARAMETER_TYPES_ROUTE
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
    PluginParameterTypeGetQueryParameters,
    PluginParameterTypeMutableFieldsSchema,
    PluginParameterTypePageSchema,
    PluginParameterTypeSchema,
)
from .service import (
    RESOURCE_TYPE,
    SEARCHABLE_FIELDS,
    PluginParameterTypeIdService,
    PluginParameterTypeService,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()

api: Namespace = Namespace(
    "PluginParameterTypes", description="Plugin Parameter Types endpoint"
)


@api.route("/")
class PluginParameterTypeEndpoint(Resource):
    @inject
    def __init__(
        self, plugin_parameter_type_service: PluginParameterTypeService, *args, **kwargs
    ) -> None:
        """Initialize the plugin parameter type resource.

        All arguments are provided via dependency injection.

        Args:
            plugin_parameter_type_service: A PluginParameterTypeService object.
        """
        self._plugin_parameter_type_service = plugin_parameter_type_service
        super().__init__(*args, **kwargs)

    @login_required
    @accepts(query_params_schema=PluginParameterTypeGetQueryParameters, api=api)
    @responds(schema=PluginParameterTypePageSchema, api=api)
    def get(self):
        """Gets a list of all PluginParameterType resources."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="PluginParameterType",
            request_type="GET",
        )
        parsed_query_params = request.parsed_query_params  # noqa: F841

        group_id = parsed_query_params["group_id"]
        search_string = parsed_query_params["search"]
        page_index = parsed_query_params["index"]
        page_length = parsed_query_params["page_length"]

        (
            plugin_parameter_types,
            total_num_plugin_param_types,
        ) = self._plugin_parameter_type_service.get(
            group_id=group_id,
            search_string=search_string,
            page_index=page_index,
            page_length=page_length,
            log=log,
        )
        return utils.build_paging_envelope(
            V1_PLUGIN_PARAMETER_TYPES_ROUTE,
            build_fn=utils.build_plugin_parameter_type,
            data=plugin_parameter_types,
            group_id=group_id,
            query=search_string,
            draft_type=None,
            index=page_index,
            length=page_length,
            total_num_elements=total_num_plugin_param_types,
        )

    @login_required
    @accepts(schema=PluginParameterTypeSchema, api=api)
    @responds(schema=PluginParameterTypeSchema, api=api)
    def post(self):
        """Creates a PluginParameterType resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="PluginParameterType",
            request_type="POST",
        )
        parsed_obj = request.parsed_obj  # noqa: F841

        plugin_parameter_type = self._plugin_parameter_type_service.create(
            name=parsed_obj["name"],
            structure=parsed_obj["structure"],
            description=parsed_obj["description"],
            group_id=parsed_obj["group_id"],
            log=log,
        )
        return utils.build_plugin_parameter_type(plugin_parameter_type)


@api.route("/<int:id>")
@api.param("id", "ID for the PluginParameterType resource.")
class PluginParameterTypeIdEndpoint(Resource):
    @inject
    def __init__(
        self,
        plugin_parameter_type_id_service: PluginParameterTypeIdService,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the plugin parameter type resource.

        All arguments are provided via dependency injection.

        Args:
            plugin_parameter_type_id_service: A PluginParameterTypeIdService object.
        """
        self._plugin_parameter_type_id_service = plugin_parameter_type_id_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=PluginParameterTypeSchema, api=api)
    def get(self, id: int):
        """Gets a PluginParameterType resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="PluginParameterType",
            request_type="GET",
            id=id,
        )
        plugin_parameter_type = cast(
            models.PluginTaskParameterType,
            self._plugin_parameter_type_id_service.get(
                id, error_if_not_found=True, log=log
            ),
        )
        return utils.build_plugin_parameter_type(plugin_parameter_type)

    @login_required
    @responds(schema=IdStatusResponseSchema, api=api)
    def delete(self, id: int):
        """Deletes a PluginParameterType resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="PluginParameterType",
            request_type="DELETE",
            id=id,
        )
        return self._plugin_parameter_type_id_service.delete(
            plugin_parameter_type_id=id, log=log
        )

    @login_required
    @accepts(schema=PluginParameterTypeMutableFieldsSchema, api=api)
    @responds(schema=PluginParameterTypeSchema, api=api)
    def put(self, id: int):
        """Modifies a PluginParameterType resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="PluginParameterType",
            request_type="PUT",
            id=id,
        )
        parsed_obj = request.parsed_obj  # type: ignore
        plugin_parameter_type = cast(
            models.PluginTaskParameterType,
            self._plugin_parameter_type_id_service.modify(
                id,
                name=parsed_obj["name"],
                structure=parsed_obj["structure"],
                description=parsed_obj["description"],
                error_if_not_found=True,
                log=log,
            ),
        )
        return utils.build_plugin_parameter_type(plugin_parameter_type)


PluginParameterTypeDraftResource = generate_resource_drafts_endpoint(
    api=api,
    resource_name=RESOURCE_TYPE,
    route_prefix=V1_PLUGIN_PARAMETER_TYPES_ROUTE,
    request_schema=PluginParameterTypeSchema,
)

PluginParameterTypeDraftIdResource = generate_resource_drafts_id_endpoint(
    api=api,
    resource_name=RESOURCE_TYPE,
    request_schema=PluginParameterTypeMutableFieldsSchema,
)

PluginParameterTypeIdDraftIdResource = generate_resource_id_draft_endpoint(
    api=api,
    resource_name=RESOURCE_TYPE,
    request_schema=PluginParameterTypeMutableFieldsSchema,
)

PluginParameterTypeSnapshotsResource = generate_resource_snapshots_endpoint(
    api=api,
    resource_model=models.PluginTaskParameterType,
    resource_name=RESOURCE_TYPE,
    route_prefix=V1_PLUGIN_PARAMETER_TYPES_ROUTE,
    searchable_fields=SEARCHABLE_FIELDS,
    page_schema=PluginParameterTypePageSchema,
    build_fn=utils.build_plugin_parameter_type,
)
PluginParameterTypeSnapshotsIdResource = generate_resource_snapshots_id_endpoint(
    api=api,
    resource_model=models.PluginTaskParameterType,
    resource_name=RESOURCE_TYPE,
    response_schema=PluginParameterTypeSchema,
    build_fn=utils.build_plugin_parameter_type,
)

PluginParameterTypeTagsResource = generate_resource_tags_endpoint(
    api=api,
    resource_name=RESOURCE_TYPE,
)
PluginParameterTypeTagsIdResource = generate_resource_tags_id_endpoint(
    api=api,
    resource_name=RESOURCE_TYPE,
)
