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
"""The module defining the endpoints for Entrypoint resources."""
from __future__ import annotations

import uuid
from typing import cast

import structlog
from flask import request, send_file
from flask_accepts import accepts, responds
from flask_login import login_required
from flask_restx import Namespace, Resource
from injector import inject
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import models
from dioptra.restapi.routes import V1_ENTRYPOINTS_ROUTE
from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.filetypes import FileTypes, plugin_pluginfiles_to_bundle
from dioptra.restapi.v1.queues.schema import QueueRefSchema
from dioptra.restapi.v1.schemas import (
    FileDownloadParametersSchema,
    IdListSchema,
    IdStatusResponseSchema,
)
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
from dioptra.restapi.v1.shared.task_engine_yaml.service import TaskEngineYamlService

from .schema import (
    EntrypointArtifactPluginMutableFieldsSchema,
    EntrypointDraftSchema,
    EntrypointGetQueryParameters,
    EntrypointMutableFieldsSchema,
    EntrypointPageSchema,
    EntrypointPluginMutableFieldsSchema,
    EntrypointPluginSchema,
    EntrypointSchema,
)
from .service import (
    RESOURCE_TYPE,
    SEARCHABLE_FIELDS,
    EntrypointIdArtifactPluginsIdService,
    EntrypointIdArtifactPluginsService,
    EntrypointIdPluginsIdService,
    EntrypointIdPluginsService,
    EntrypointIdQueuesIdService,
    EntrypointIdQueuesService,
    EntrypointIdService,
    EntrypointService,
    EntrypointSnapshotIdService,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()

api: Namespace = Namespace("Entrypoints", description="Entrypoints endpoint")


@api.route("/")
class EntrypointEndpoint(Resource):
    @inject
    def __init__(self, entrypoint_service: EntrypointService, *args, **kwargs) -> None:
        """Initialize the entrypoint resource.

        All arguments are provided via dependency injection.

        Args:
            entrypoint_service: A EntrypointService object.
        """
        self._entrypoint_service = entrypoint_service
        super().__init__(*args, **kwargs)

    @login_required
    @accepts(query_params_schema=EntrypointGetQueryParameters, api=api)
    @responds(schema=EntrypointPageSchema, api=api)
    def get(self):
        """Gets a list of Entrypoint resources matching the filter parameters."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Entrypoint", request_type="GET"
        )

        parsed_query_params = request.parsed_query_params  # noqa: F841
        group_id = parsed_query_params["group_id"]
        search_string = parsed_query_params["search"]
        page_index = parsed_query_params["index"]
        page_length = parsed_query_params["page_length"]
        sort_by_string = parsed_query_params["sort_by"]
        descending = parsed_query_params["descending"]

        entrypoints, total_num_entrypoints = self._entrypoint_service.get(
            group_id=group_id,
            search_string=search_string,
            page_index=page_index,
            page_length=page_length,
            sort_by_string=sort_by_string,
            descending=descending,
            log=log,
        )
        return utils.build_paging_envelope(
            "entrypoints",
            build_fn=utils.build_entrypoint,
            data=entrypoints,
            group_id=group_id,
            draft_type=None,
            query=search_string,
            index=page_index,
            length=page_length,
            total_num_elements=total_num_entrypoints,
            sort_by=sort_by_string,
            descending=descending,
        )

    @login_required
    @accepts(schema=EntrypointSchema, api=api)
    @responds(schema=EntrypointSchema, api=api)
    def post(self):
        """Creates an Entrypoint resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Entrypoint", request_type="POST"
        )
        parsed_obj = request.parsed_obj  # noqa: F841
        entrypoint = self._entrypoint_service.create(
            name=parsed_obj["name"],
            description=parsed_obj["description"],
            task_graph=parsed_obj["task_graph"],
            artifact_graph=parsed_obj.get("artifact_graph", ""),
            parameters=parsed_obj["parameters"],
            artifact_parameters=parsed_obj["artifact_parameters"],
            plugin_ids=parsed_obj["plugin_ids"],
            artifact_plugin_ids=parsed_obj.get("artifact_plugin_ids", []),
            queue_ids=parsed_obj["queue_ids"],
            group_id=int(parsed_obj["group_id"]),
            log=log,
        )
        return utils.build_entrypoint(entrypoint)


@api.route("/<int:id>")
@api.param("id", "ID for the Entrypoint resource.")
class EntrypointIdEndpoint(Resource):
    @inject
    def __init__(
        self, entrypoint_id_service: EntrypointIdService, *args, **kwargs
    ) -> None:
        """Initialize the entrypoint resource.

        All arguments are provided via dependency injection.

        Args:
            entrypoint_id_service: A EntrypointIdService object.
        """
        self._entrypoint_id_service = entrypoint_id_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=EntrypointSchema, api=api)
    def get(self, id: int):
        """Gets an Entrypoint resource by its unique ID."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="Entrypoint",
            request_type="GET",
            id=id,
        )
        entrypoint = self._entrypoint_id_service.get(id, log=log)
        return utils.build_entrypoint(entrypoint)

    @login_required
    @accepts(schema=EntrypointMutableFieldsSchema, api=api)
    @responds(schema=EntrypointSchema, api=api)
    def put(self, id: int):
        """Modifies an Entrypoint resource by its unique ID."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="Entrypoint",
            request_type="PUT",
            id=id,
        )
        parsed_obj = request.parsed_obj  # type: ignore # noqa: F841
        entrypoint = self._entrypoint_id_service.modify(
            id,
            name=parsed_obj["name"],
            description=parsed_obj["description"],
            task_graph=parsed_obj["task_graph"],
            artifact_graph=parsed_obj.get("artifact_graph", ""),
            parameters=parsed_obj["parameters"],
            artifact_parameters=parsed_obj["artifact_parameters"],
            queue_ids=parsed_obj["queue_ids"],
            log=log,
        )
        return utils.build_entrypoint(entrypoint)

    @login_required
    @responds(schema=IdStatusResponseSchema, api=api)
    def delete(self, id: int):
        """Deletes an Entrypoint resource by its unique ID."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="Entrypoint",
            request_type="DELETE",
            id=id,
        )
        return self._entrypoint_id_service.delete(entrypoint_id=id, log=log)


@api.route("/<int:id>/plugins")
@api.param("id", "ID for the Entrypoint resource.")
class EntrypointIdPluginsEndpoint(Resource):
    @inject
    def __init__(
        self, entrypoint_id_plugins_service: EntrypointIdPluginsService, *args, **kwargs
    ) -> None:
        """Initialize the entrypoint resource.

        All arguments are provided via dependency injection.

        Args:
            entrypoint_id_plugins_service: A EntrypointIdPluginsService object.
        """
        self._entrypoint_id_plugins_service = entrypoint_id_plugins_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=EntrypointPluginSchema(many=True), api=api)
    def get(self, id: int):
        """Retrieves the plugin snapshots for an entrypoint resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Entrypoint", request_type="POST"
        )
        plugins = self._entrypoint_id_plugins_service.get(id, log=log)
        return [utils.build_entrypoint_plugin(plugin) for plugin in plugins]

    @login_required
    @accepts(schema=EntrypointPluginMutableFieldsSchema, api=api)
    @responds(schema=EntrypointPluginSchema(many=True), api=api)
    def post(self, id: int):
        """Appends plugins to an entrypoint resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Entrypoint", request_type="POST"
        )
        parsed_obj = request.parsed_obj  # type: ignore
        plugins = self._entrypoint_id_plugins_service.append(
            id, plugin_ids=parsed_obj["plugin_ids"], log=log
        )
        return [utils.build_entrypoint_plugin(plugin) for plugin in plugins]


@api.route("/<int:id>/snapshots/<int:snapshotId>/config")
@api.param("id", "ID for the entrypoint resource.")
@api.param("snapshotId", "Snapshot ID for the entrypoint resource.")
class EntryPointSnapshotConfigEndpoint(Resource):
    @inject
    def __init__(
        self,
        entrypoint_snapshot_id_service: EntrypointSnapshotIdService,
        yaml_service: TaskEngineYamlService,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the Entrypoint resource.

        All arguments are provided via dependency injection.

        Args:
            entrypoint_snapshot_id_service: A EntrypointSnapshotIdService object.
            yaml_service: A TaskEngineYamlService object
        """
        self._entrypoint_snapshot_id_service = entrypoint_snapshot_id_service
        self._yaml_service = yaml_service
        super().__init__(*args, **kwargs)

    @login_required
    def get(self, id: int, snapshotId: int):
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="EntryPoint",
            request_type="GET",
            id=id,
            snapshotId=snapshotId,
        )
        entry_point = self._entrypoint_snapshot_id_service.get(
            entrypoint_id=id, entrypoint_snapshot_id=snapshotId, log=log
        )
        plugin_files = [
            plugin_plugin_file
            for entry_point_plugin in entry_point.entry_point_plugins
            for plugin_plugin_file in entry_point_plugin.plugin.plugin_plugin_files
        ]
        # this call is part of a HACK fully explained in extract_tasks, which is called
        # internally by build_task_engine_dict, the service call would not be needed
        # if this issue is more permanantly resolved
        types = self._entrypoint_snapshot_id_service.get_group_plugin_parameter_types(
            entry_point.resource.group_id, log=log
        )
        return self._yaml_service.build_dict(
            entry_point=entry_point,  # pyright: ignore
            plugin_plugin_files=plugin_files,  # pyright: ignore
            plugin_parameter_types=types,  # pyright: ignore
            logger=log,
        )


@api.route("/<int:id>/snapshots/<int:snapshotId>/plugins/bundle")
@api.param("id", "ID for the Entrypoint resource.")
@api.param("snapshotId", "Snapshot ID for the Entrypoint resource.")
class EntryPointSnapshotPluginBundleEndpoint(Resource):
    @inject
    def __init__(
        self,
        entrypoint_snapshot_id_service: EntrypointSnapshotIdService,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the plugin file resource.

        All arguments are provided via dependency injection.

        Args:
            plugin_service: A PluginService object.
        """
        self._entrypoint_snapshot_id_service = entrypoint_snapshot_id_service
        super().__init__(*args, **kwargs)

    @login_required
    @accepts(query_params_schema=FileDownloadParametersSchema, api=api)
    def get(self, id: int, snapshotId: int):
        """Returns a file bundle containing all of the PluginFile resources for an
        EntryPoint Snapshot resource.
        """
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="EntrypointSnapshotPluginsBundle",
            request_type="GET",
            id=id,
        )

        parsed_query_params = request.parsed_query_params  # type: ignore # noqa: F841

        file_type = cast(FileTypes, parsed_query_params["file_type"])

        plugin_files = self._entrypoint_snapshot_id_service.get_plugin_files(
            entrypoint_id=id,
            entrypoint_snapshot_id=snapshotId,
            log=log,
        )
        file = file_type.package(plugin_pluginfiles_to_bundle(plugin_files))
        return send_file(
            path_or_file=file,
            as_attachment=True,
            mimetype=file_type.mimetype,
            download_name=f"plugins_bundle{file_type.suffix}",
        )


@api.route("/<int:id>/plugins/<int:pluginId>")
@api.param("id", "ID for the Entrypoint resource.")
@api.param("pluginId", "ID for the Plugin resource.")
class EntrypointIdPluginsIdEndpoint(Resource):
    @inject
    def __init__(
        self,
        entrypoint_id_plugins_id_service: EntrypointIdPluginsIdService,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the entrypoint resource.

        All arguments are provided via dependency injection.

        Args:
            entrypoint_id_plugins_id_service: A EntrypointIdPluginsService object.
        """
        self._entrypoint_id_plugins_id_service = entrypoint_id_plugins_id_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=EntrypointPluginSchema, api=api)
    def get(self, id: int, pluginId: int):
        """Retrieves a plugin snapshot for an entrypoint resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Entrypoint", request_type="POST"
        )
        plugin = self._entrypoint_id_plugins_id_service.get(id, pluginId, log=log)
        return utils.build_entrypoint_plugin(plugin)

    @login_required
    @responds(schema=IdStatusResponseSchema, api=api)
    def delete(self, id: int, pluginId: int):
        """Removes a plugin from an entrypoint by ID."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="Entrypoint",
            request_type="DELETE",
            id=id,
        )
        return self._entrypoint_id_plugins_id_service.delete(id, pluginId, log=log)


@api.route("/<int:id>/snapshots/<int:snapshotId>/artifactPlugins/bundle")
@api.param("id", "ID for the Entrypoint resource.")
@api.param("snapshotId", "Snapshot ID for the Entrypoint resource.")
class EntryPointSnapshotArtifactBundleEndpoint(Resource):
    @inject
    def __init__(
        self,
        entrypoint_snapshot_id_service: EntrypointSnapshotIdService,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the plugin file resource.

        All arguments are provided via dependency injection.

        Args:
            plugin_service: A PluginService object.
        """
        self._entrypoint_snapshot_id_service = entrypoint_snapshot_id_service
        super().__init__(*args, **kwargs)

    @login_required
    @accepts(query_params_schema=FileDownloadParametersSchema, api=api)
    def get(self, id: int, snapshotId: int):
        """Returns a file bundle containing all of the ArtifactPlugin PluginFile
        resources for an EntryPoint Snapshot resource.
        """
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="EntryPointSnapshotArtifactBundleEndpoint",
            request_type="GET",
            id=id,
        )
        parsed_query_params = request.parsed_query_params  # type: ignore # noqa: F841

        file_type = cast(FileTypes, parsed_query_params.get("file_type"))

        plugin_files = self._entrypoint_snapshot_id_service.get_artifact_plugin_files(
            entrypoint_id=id,
            entrypoint_snapshot_id=snapshotId,
            log=log,
        )

        file = file_type.package(plugin_pluginfiles_to_bundle(plugin_files))
        return send_file(
            path_or_file=file,
            as_attachment=True,
            mimetype=file_type.mimetype,
            download_name=f"artifact_serialize_bundle{file_type.suffix}",
        )


@api.route("/<int:id>/artifactPlugins")
@api.param("id", "ID for the Entrypoint resource.")
class EntrypointIdArtifactPluginsEndpoint(Resource):
    @inject
    def __init__(
        self,
        entrypoint_id_artifact_plugins_service: EntrypointIdArtifactPluginsService,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the entrypoint resource.

        All arguments are provided via dependency injection.

        Args:
            entrypoint_id_artifact_plugins_service: An
                EntrypointIdArtifactPluginsService object.
        """
        self._entrypoint_id_artifact_plugins_service = (
            entrypoint_id_artifact_plugins_service
        )
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=EntrypointPluginSchema(many=True), api=api)
    def get(self, id: int):
        """Retrieves the artifact plugin snapshots for an entrypoint resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Entrypoint", request_type="POST"
        )
        artifact_plugins = self._entrypoint_id_artifact_plugins_service.get(id, log=log)
        return [
            utils.build_entrypoint_plugin(artifact_plugin)
            for artifact_plugin in artifact_plugins
        ]

    @login_required
    @accepts(schema=EntrypointArtifactPluginMutableFieldsSchema, api=api)
    @responds(schema=EntrypointPluginSchema(many=True), api=api)
    def post(self, id: int):
        """Appends artifact plugins to an entrypoint resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Entrypoint", request_type="POST"
        )
        parsed_obj = request.parsed_obj  # type: ignore
        artifact_plugins = self._entrypoint_id_artifact_plugins_service.append(
            id, artifact_plugin_ids=parsed_obj["artifact_plugin_ids"], log=log
        )
        return [
            utils.build_entrypoint_plugin(artifact_plugin)
            for artifact_plugin in artifact_plugins
        ]


@api.route("/<int:id>/artifactPlugins/<int:artifactPluginId>")
@api.param("id", "ID for the Entrypoint resource.")
@api.param("artifactPluginId", "ID for the Artifact Plugin resource.")
class EntrypointIdArtifactPluginIdEndpoint(Resource):
    @inject
    def __init__(
        self,
        entrypoint_id_artifact_plugin_id_service: EntrypointIdArtifactPluginsIdService,  # noqa: B950
        *args,
        **kwargs,
    ) -> None:
        """Initialize the entrypoint resource.

        All arguments are provided via dependency injection.

        Args:
            entrypoint_id_artifact_plugin_id_service:
                An EntrypointIdArtifactPluginsIdService object.
        """
        self._entrypoint_id_artifact_plugin_id_service = (
            entrypoint_id_artifact_plugin_id_service
        )
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=EntrypointPluginSchema, api=api)
    def get(self, id: int, artifactPluginId: int):
        """Retrieves a artifact plugin snapshot for an entrypoint resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Entrypoint", request_type="POST"
        )
        artifact_plugin = self._entrypoint_id_artifact_plugin_id_service.get(
            id, artifactPluginId, log=log
        )
        return utils.build_entrypoint_plugin(artifact_plugin)

    @login_required
    @responds(schema=IdStatusResponseSchema, api=api)
    def delete(self, id: int, artifactPluginId: int):
        """Removes a artifact plugin from an entrypoint by ID."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="Entrypoint",
            request_type="DELETE",
            id=id,
        )
        return self._entrypoint_id_artifact_plugin_id_service.delete(
            id, artifactPluginId, log=log
        )


@api.route("/<int:id>/snapshots/<int:snapshotId>/artifactPlugins")
@api.param("id", "ID for the Entrypoint resource.")
@api.param("snapshotId", "Snapshot ID for the Entrypoint snapshot.")
class EntrypointSnapshotIdArtifactPluginsEndpoint(Resource):
    @inject
    def __init__(
        self,
        entrypoint_snapshot_service: EntrypointSnapshotIdService,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the entrypoint resource.

        All arguments are provided via dependency injection.

        Args:
            entrypoint_snapshot_service: An EntrypointSnapshotIdService object.
        """
        self._entrypoint_snapshot_service = entrypoint_snapshot_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=EntrypointPluginSchema(many=True), api=api)
    def get(self, id: int, snapshotId: int):
        """Retrieves the artifact plugin snapshots for an entrypoint resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Entrypoint", request_type="POST"
        )
        entry_point = self._entrypoint_snapshot_service.get(
            entrypoint_id=id, entrypoint_snapshot_id=snapshotId, log=log
        )
        return [
            utils.build_entrypoint_plugin(
                utils.PluginWithFilesDict(
                    plugin=artifact_plugin.plugin,
                    plugin_files=[file for file in artifact_plugin.plugin.plugin_files],
                    has_draft=False,
                )
            )
            for artifact_plugin in entry_point.entry_point_artifact_plugins
        ]


@api.route("/<int:id>/queues")
@api.param("id", "ID for the Entrypoint resource.")
class EntrypointIdQueuesEndpoint(Resource):
    @inject
    def __init__(
        self, entrypoint_id_queues_service: EntrypointIdQueuesService, *args, **kwargs
    ) -> None:
        self._entrypoint_id_queues_service = entrypoint_id_queues_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=QueueRefSchema(many=True), api=api)
    def get(self, id: int):
        """Gets the list of Queues for the resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Entrypoint", request_type="GET"
        )
        queues = self._entrypoint_id_queues_service.get(id, log=log)
        return [utils.build_queue_ref(queue) for queue in queues]

    @login_required
    @accepts(schema=IdListSchema, api=api)
    @responds(schema=QueueRefSchema(many=True), api=api)
    def post(self, id: int):
        """Appends one or more Queues to the resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Entrypoint", request_type="POST"
        )
        parsed_obj = request.parsed_obj  # type: ignore
        queues = cast(
            list[models.Queue],
            self._entrypoint_id_queues_service.append(
                id, queue_ids=parsed_obj["ids"], log=log
            ),
        )
        return [utils.build_queue_ref(queue) for queue in queues]

    @login_required
    @accepts(schema=IdListSchema, api=api)
    @responds(schema=QueueRefSchema(many=True), api=api)
    def put(self, id: int):
        """Replaces one or more Queues to the resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Entrypoint", request_type="POST"
        )
        parsed_obj = request.parsed_obj  # type: ignore
        queues = self._entrypoint_id_queues_service.modify(
            id, queue_ids=parsed_obj["ids"], error_if_not_found=True, log=log
        )
        return [utils.build_queue_ref(queue) for queue in queues]

    @login_required
    @responds(schema=IdStatusResponseSchema, api=api)
    def delete(self, id: int):
        """Removes all Queues from the resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Entrypoint", request_type="DELETE"
        )
        return self._entrypoint_id_queues_service.delete(
            id, error_if_not_found=True, log=log
        )


@api.route("/<int:id>/queues/<int:queueId>")
@api.param("id", "ID for the Entrypoint resource.")
@api.param("queueId", "ID for the Queue resource.")
class EntrypointIdQueuesId(Resource):
    @inject
    def __init__(
        self,
        entrypoint_id_queues_id_service: EntrypointIdQueuesIdService,
        *args,
        **kwargs,
    ) -> None:
        self._entrypoint_id_queues_id_service = entrypoint_id_queues_id_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=IdStatusResponseSchema, api=api)
    def delete(self, id: int, queueId):
        """Removes a Queue from the Entrypoint resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Entrypoint", request_type="GET"
        )
        return self._entrypoint_id_queues_id_service.delete(id, queueId, log=log)


EntrypointDraftResource = generate_resource_drafts_endpoint(
    api,
    resource_name=RESOURCE_TYPE,
    route_prefix=V1_ENTRYPOINTS_ROUTE,
    request_schema=EntrypointDraftSchema,
)
EntrypointDraftIdResource = generate_resource_drafts_id_endpoint(
    api,
    resource_name=RESOURCE_TYPE,
    request_schema=EntrypointDraftSchema(exclude=["groupId"]),
)
EntrypointIdDraftResource = generate_resource_id_draft_endpoint(
    api,
    resource_name=RESOURCE_TYPE,
    request_schema=EntrypointDraftSchema(exclude=["groupId", "pluginIds"]),
)

EntrypointSnapshotsResource = generate_resource_snapshots_endpoint(
    api=api,
    resource_model=models.EntryPoint,
    resource_name=RESOURCE_TYPE,
    route_prefix=V1_ENTRYPOINTS_ROUTE,
    searchable_fields=SEARCHABLE_FIELDS,
    page_schema=EntrypointPageSchema,
    build_fn=utils.build_entrypoint,
)
EntrypointSnapshotsIdResource = generate_resource_snapshots_id_endpoint(
    api=api,
    resource_model=models.EntryPoint,
    resource_name=RESOURCE_TYPE,
    response_schema=EntrypointSchema,
    build_fn=utils.build_entrypoint,
)

EntrypointTagsResource = generate_resource_tags_endpoint(
    api=api,
    resource_name=RESOURCE_TYPE,
)
EntrypointTagsIdResource = generate_resource_tags_id_endpoint(
    api=api,
    resource_name=RESOURCE_TYPE,
)
