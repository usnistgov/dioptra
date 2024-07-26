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
"""The module defining the endpoints for Plugin resources."""
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
from dioptra.restapi.routes import V1_PLUGIN_FILES_ROUTE, V1_PLUGINS_ROUTE
from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.schemas import IdStatusResponseSchema
from dioptra.restapi.v1.shared.drafts.controller import (
    generate_nested_resource_drafts_endpoint,
    generate_nested_resource_drafts_id_endpoint,
    generate_nested_resource_id_draft_endpoint,
    generate_resource_drafts_endpoint,
    generate_resource_drafts_id_endpoint,
    generate_resource_id_draft_endpoint,
)
from dioptra.restapi.v1.shared.snapshots.controller import (
    generate_nested_resource_snapshots_endpoint,
    generate_nested_resource_snapshots_id_endpoint,
    generate_resource_snapshots_endpoint,
    generate_resource_snapshots_id_endpoint,
)
from dioptra.restapi.v1.shared.tags.controller import (
    generate_nested_resource_tags_endpoint,
    generate_nested_resource_tags_id_endpoint,
    generate_resource_tags_endpoint,
    generate_resource_tags_id_endpoint,
)

from .schema import (
    PluginFileGetQueryParameters,
    PluginFileMutableFieldsSchema,
    PluginFilePageSchema,
    PluginFileSchema,
    PluginGetQueryParameters,
    PluginMutableFieldsSchema,
    PluginPageSchema,
    PluginSchema,
)
from .service import (
    PLUGIN_FILE_RESOURCE_TYPE,
    PLUGIN_FILE_SEARCHABLE_FIELDS,
    PLUGIN_RESOURCE_TYPE,
    PLUGIN_SEARCHABLE_FIELDS,
    PluginIdFileIdService,
    PluginIdFileService,
    PluginIdService,
    PluginService,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()

api: Namespace = Namespace("Plugins", description="Plugins endpoint")


# WARNING: Do not move the PluginFile Snapshots sub-endpoint definitions.
# They must be declared first because of an issue related interations with the schemas.
PluginFileSnapshotsResource = generate_nested_resource_snapshots_endpoint(
    api=api,
    resource_model=models.PluginFile,
    resource_name=PLUGIN_FILE_RESOURCE_TYPE,
    resource_route=V1_PLUGIN_FILES_ROUTE,
    base_resource_route=V1_PLUGINS_ROUTE,
    searchable_fields=PLUGIN_FILE_SEARCHABLE_FIELDS,
    page_schema=PluginFilePageSchema,
    build_fn=utils.build_plugin_file,
)
PluginFileSnapshotsIdResource = generate_nested_resource_snapshots_id_endpoint(
    api=api,
    resource_model=models.PluginFile,
    resource_name=PLUGIN_FILE_RESOURCE_TYPE,
    resource_route=V1_PLUGIN_FILES_ROUTE,
    response_schema=PluginFileSchema,
    build_fn=utils.build_plugin_file,
)


@api.route("/")
class PluginEndpoint(Resource):
    @inject
    def __init__(self, plugin_service: PluginService, *args, **kwargs) -> None:
        """Initialize the plugin resource.

        All arguments are provided via dependency injection.

        Args:
            plugin_service: A PluginService object.
        """
        self._plugin_service = plugin_service
        super().__init__(*args, **kwargs)

    @login_required
    @accepts(query_params_schema=PluginGetQueryParameters, api=api)
    @responds(schema=PluginPageSchema, api=api)
    def get(self):
        """Gets a list of all Plugin resources."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Plugin", request_type="GET"
        )
        parsed_query_params = request.parsed_query_params  # noqa: F841

        group_id = parsed_query_params["group_id"]
        search_string = parsed_query_params["search"]
        page_index = parsed_query_params["index"]
        page_length = parsed_query_params["page_length"]

        plugins, total_num_plugins = self._plugin_service.get(
            group_id=group_id,
            search_string=search_string,
            page_index=page_index,
            page_length=page_length,
            log=log,
        )
        return utils.build_paging_envelope(
            V1_PLUGINS_ROUTE,
            build_fn=utils.build_plugin,
            data=plugins,
            group_id=group_id,
            query=search_string,
            draft_type=None,
            index=page_index,
            length=page_length,
            total_num_elements=total_num_plugins,
        )

    @login_required
    @accepts(schema=PluginSchema, api=api)
    @responds(schema=PluginSchema, api=api)
    def post(self):
        """Creates a Plugin resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Plugin", request_type="POST"
        )
        parsed_obj = request.parsed_obj  # noqa: F841

        plugin = self._plugin_service.create(
            name=parsed_obj["name"],
            description=parsed_obj["description"],
            group_id=parsed_obj["group_id"],
            log=log,
        )
        return utils.build_plugin(plugin)


@api.route("/<int:id>")
@api.param("id", "ID for the Plugin resource.")
class PluginIdEndpoint(Resource):
    @inject
    def __init__(self, plugin_id_service: PluginIdService, *args, **kwargs) -> None:
        """Initialize the plugin resource.

        All arguments are provided via dependency injection.

        Args:
            plugin_id_service: A PluginIdService object.
        """
        self._plugin_id_service = plugin_id_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=PluginSchema, api=api)
    def get(self, id: int):
        """Gets a Plugin resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Plugin", request_type="GET", id=id
        )
        plugin = cast(
            models.Plugin,
            self._plugin_id_service.get(id, error_if_not_found=True, log=log),
        )
        return utils.build_plugin(plugin)

    @login_required
    @responds(schema=IdStatusResponseSchema, api=api)
    def delete(self, id: int):
        """Deletes a Plugin resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="Plugin",
            request_type="DELETE",
            id=id,
        )
        return self._plugin_id_service.delete(plugin_id=id, log=log)

    @login_required
    @accepts(schema=PluginMutableFieldsSchema, api=api)
    @responds(schema=PluginSchema, api=api)
    def put(self, id: int):
        """Modifies a Plugin resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Plugin", request_type="PUT", id=id
        )
        parsed_obj = request.parsed_obj  # type: ignore # noqa: F841
        plugin = cast(
            models.Plugin,
            self._plugin_id_service.modify(
                id,
                name=parsed_obj["name"],
                description=parsed_obj["description"],
                error_if_not_found=True,
                log=log,
            ),
        )
        return utils.build_plugin(plugin)


@api.route("/<int:id>/files")
@api.param("id", "ID for the Plugin resource.")
class PluginIdFilesEndpoint(Resource):
    @inject
    def __init__(
        self, plugin_id_file_service: PluginIdFileService, *args, **kwargs
    ) -> None:
        """Initialize the plugin file resource.

        All arguments are provided via dependency injection.

        Args:
            plugin_service: A PluginService object.
        """
        self._plugin_id_file_service = plugin_id_file_service
        super().__init__(*args, **kwargs)

    @login_required
    @accepts(query_params_schema=PluginFileGetQueryParameters, api=api)
    @responds(schema=PluginFilePageSchema, api=api)
    def get(self, id: int):
        """Gets a list of all PluginFile resources for a Plugin resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="PluginFile",
            request_type="GET",
            id=id,
        )
        parsed_query_params = request.parsed_query_params  # type: ignore # noqa: F841

        search_string = parsed_query_params["search"]
        page_index = parsed_query_params["index"]
        page_length = parsed_query_params["page_length"]

        plugin_files, total_num_plugin_files = self._plugin_id_file_service.get(
            plugin_id=id,
            search_string=search_string,
            page_index=page_index,
            page_length=page_length,
            log=log,
        )

        return utils.build_paging_envelope(
            f"plugins/{id}/files",
            utils.build_plugin_file,
            plugin_files,
            group_id=None,
            query=search_string,
            draft_type=None,
            index=page_index,
            length=page_length,
            total_num_elements=total_num_plugin_files,
        )

    @login_required
    @responds(schema=IdStatusResponseSchema, api=api)
    def delete(self, id: int):
        """Deletes all PluginFile resources associated with a Plugin resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="PluginFile",
            request_type="DELETE",
            id=id,
        )
        return self._plugin_id_file_service.delete(plugin_id=id, log=log)

    @login_required
    @accepts(schema=PluginFileSchema(exclude=["groupId"]), api=api)
    @responds(schema=PluginFileSchema, api=api)
    def post(self, id: int):
        """Creates a PluginFile resource associated with a Plugin resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="PluginFile", request_type="POST"
        )
        parsed_obj = request.parsed_obj  # type: ignore # noqa: F841

        plugin_file = self._plugin_id_file_service.create(
            filename=parsed_obj["filename"],
            contents=parsed_obj["contents"],
            description=parsed_obj["description"],
            tasks=parsed_obj["tasks"],
            plugin_id=id,
            log=log,
        )
        return utils.build_plugin_file(plugin_file)


@api.route("/<int:id>/files/<int:fileId>")
@api.param("id", "ID for the Plugin resource.")
@api.param("fileId", "ID for the PluginFile resource.")
class PluginIdFileIdEndpoint(Resource):
    @inject
    def __init__(
        self, plugin_file_id_service: PluginIdFileIdService, *args, **kwargs
    ) -> None:
        """Initialize the plugin file id resource.

        All arguments are provided via dependency injection.

        Args:
            plugin_file_id_service: PluginIdFileIdService
        """
        self._plugin_file_id_service = plugin_file_id_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=PluginFileSchema, api=api)
    def get(self, id: int, fileId: int):
        """Gets a PluginFile resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="PluginFile",
            request_type="GET",
            id=id,
        )
        plugin_file = cast(
            models.PluginFile,
            self._plugin_file_id_service.get(
                id, plugin_file_id=fileId, error_if_not_found=True, log=log
            ),
        )
        return utils.build_plugin_file(plugin_file)

    @login_required
    @responds(schema=IdStatusResponseSchema, api=api)
    def delete(self, id: int, fileId: int):
        """Deletes a PluginFile resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="PluginFile",
            request_type="DELETE",
            id=id,
        )
        return self._plugin_file_id_service.delete(id, plugin_file_id=fileId, log=log)

    @login_required
    @accepts(schema=PluginFileMutableFieldsSchema, api=api)
    @responds(schema=PluginFileSchema, api=api)
    def put(self, id: int, fileId: int):
        """Modifies a PluginFile resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="PluginFile",
            request_type="PUT",
            id=id,
        )
        parsed_obj = request.parsed_obj  # type: ignore # noqa: F841
        plugin_file = cast(
            models.PluginFile,
            self._plugin_file_id_service.modify(
                id,
                plugin_file_id=fileId,
                filename=parsed_obj["filename"],
                contents=parsed_obj["contents"],
                tasks=parsed_obj["tasks"],
                description=parsed_obj["description"],
                error_if_not_found=True,
                log=log,
            ),
        )
        return utils.build_plugin_file(plugin_file)


PluginDraftResource = generate_resource_drafts_endpoint(
    api,
    resource_name=PLUGIN_RESOURCE_TYPE,
    route_prefix=V1_PLUGINS_ROUTE,
    request_schema=PluginSchema,
)
PluginDraftIdResource = generate_resource_drafts_id_endpoint(
    api,
    resource_name=PLUGIN_RESOURCE_TYPE,
    request_schema=PluginMutableFieldsSchema,
)
PluginIdDraftResource = generate_resource_id_draft_endpoint(
    api,
    resource_name=PLUGIN_RESOURCE_TYPE,
    request_schema=PluginMutableFieldsSchema,
)

PluginFileDraftResource = generate_nested_resource_drafts_endpoint(
    api,
    resource_name=PLUGIN_FILE_RESOURCE_TYPE,
    resource_route=V1_PLUGIN_FILES_ROUTE,
    base_resource_route=V1_PLUGINS_ROUTE,
    request_schema=PluginFileSchema(exclude=["groupId"]),
)
PluginFileDraftIdResource = generate_nested_resource_drafts_id_endpoint(
    api,
    resource_name=PLUGIN_FILE_RESOURCE_TYPE,
    resource_route=V1_PLUGIN_FILES_ROUTE,
    request_schema=PluginFileSchema(exclude=["groupId"]),
)
PluginFileIdDraftResource = generate_nested_resource_id_draft_endpoint(
    api,
    resource_name=PLUGIN_FILE_RESOURCE_TYPE,
    resource_route=V1_PLUGIN_FILES_ROUTE,
    request_schema=PluginFileSchema(exclude=["groupId"]),
)

PluginSnapshotsResource = generate_resource_snapshots_endpoint(
    api=api,
    resource_model=models.Plugin,
    resource_name=PLUGIN_RESOURCE_TYPE,
    route_prefix=V1_PLUGINS_ROUTE,
    searchable_fields=PLUGIN_SEARCHABLE_FIELDS,
    page_schema=PluginPageSchema,
    build_fn=utils.build_plugin,
)
PluginSnapshotsIdResource = generate_resource_snapshots_id_endpoint(
    api=api,
    resource_model=models.Plugin,
    resource_name=PLUGIN_RESOURCE_TYPE,
    response_schema=PluginSchema,
    build_fn=utils.build_plugin,
)

PluginTagsResource = generate_resource_tags_endpoint(
    api=api,
    resource_name=PLUGIN_RESOURCE_TYPE,
)
PluginTagsIdResource = generate_resource_tags_id_endpoint(
    api=api,
    resource_name=PLUGIN_RESOURCE_TYPE,
)
PluginFileTagsIdResource = generate_nested_resource_tags_endpoint(
    api=api,
    resource_name=PLUGIN_FILE_RESOURCE_TYPE,
    resource_route=V1_PLUGIN_FILES_ROUTE,
    base_resource_name=PLUGIN_RESOURCE_TYPE,
)
PluginFileTagsIdResource = generate_nested_resource_tags_id_endpoint(
    api=api,
    resource_name=PLUGIN_FILE_RESOURCE_TYPE,
    resource_route=V1_PLUGIN_FILES_ROUTE,
    base_resource_name=PLUGIN_RESOURCE_TYPE,
)
