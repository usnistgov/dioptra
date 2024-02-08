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
"""The module defining the task plugin endpoints."""
from __future__ import annotations

import uuid
from typing import Any, cast

import structlog
from flask import current_app, request
from flask_accepts import accepts, responds
from flask_login import login_required
from flask_restx import Namespace, Resource
from injector import inject
from structlog.stdlib import BoundLogger

from dioptra.restapi.utils import as_api_parser, as_parameters_schema_list

from .model import TaskPlugin
from .schema import NameStatusResponseSchema, TaskPluginSchema
from .service import TaskPluginCollectionService, TaskPluginService

LOGGER: BoundLogger = structlog.stdlib.get_logger()

api: Namespace = Namespace(
    "TaskPlugin",
    description="Task plugin registry operations",
)


@api.route("/")
class TaskPluginResource(Resource):
    """Shows a list of all task plugins, and lets you POST to upload new ones."""

    @inject
    def __init__(self, *args, task_plugin_service: TaskPluginService, **kwargs) -> None:
        self._task_plugin_service = task_plugin_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=TaskPluginSchema(many=True), api=api)
    def get(self) -> list[TaskPlugin]:
        """Gets a list of all registered task plugins."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="taskPlugin", request_type="GET"
        )
        log.info("Request received")
        return self._task_plugin_service.get_all(
            s3_collections_list=["dioptra_builtins", "dioptra_custom"],
            bucket=current_app.config["DIOPTRA_PLUGINS_BUCKET"],
            log=log,
        )

    @login_required
    @api.expect(
        as_api_parser(
            api,
            as_parameters_schema_list(
                TaskPluginSchema, operation="load", location="form"
            ),
        )
    )
    @accepts(form_schema=TaskPluginSchema, api=api)
    @responds(schema=TaskPluginSchema, api=api)
    def post(self) -> TaskPlugin:
        """Registers a new task plugin uploaded via the task plugin upload form."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="taskPlugin", request_type="POST"
        )
        parsed_obj = request.parsed_form  # type: ignore
        log.info("Request received")
        return self._task_plugin_service.create(
            task_plugin_name=parsed_obj["task_plugin_name"],
            task_plugin_file=request.files["taskPluginFile"],
            collection=parsed_obj["collection"],
            bucket=current_app.config["DIOPTRA_PLUGINS_BUCKET"],
            log=log,
        )


@api.route("/dioptra_builtins")
class TaskPluginBuiltinsCollectionResource(Resource):
    """Shows a list of all builtin task plugins."""

    @inject
    def __init__(
        self,
        *args,
        task_plugin_collection_service: TaskPluginCollectionService,
        **kwargs,
    ) -> None:
        self._task_plugin_collection_service = task_plugin_collection_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=TaskPluginSchema(many=True), api=api)
    def get(self) -> list[TaskPlugin]:
        """Gets a list of all available builtin task plugins."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="taskPluginBuiltinCollection",
            request_type="GET",
        )
        log.info("Request received")
        return self._task_plugin_collection_service.get_all(
            collection="dioptra_builtins",
            bucket=current_app.config["DIOPTRA_PLUGINS_BUCKET"],
            log=log,
        )


@api.route("/dioptra_builtins/<string:taskPluginName>")
@api.param(
    "taskPluginName",
    "A unique string identifying a task plugin package within dioptra_builtins "
    "collection.",
)
class TaskPluginBuiltinCollectionNameResource(Resource):
    """Shows a single builtin task plugin package."""

    @inject
    def __init__(
        self,
        *args,
        task_plugin_collection_service: TaskPluginCollectionService,
        **kwargs,
    ) -> None:
        self._task_plugin_collection_service = task_plugin_collection_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=TaskPluginSchema, api=api)
    def get(self, taskPluginName: str) -> TaskPlugin:
        """Gets a builtin task plugin by its unique name."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="taskPluginBuiltinCollectionName",
            request_type="GET",
        )
        log.info("Request received")

        task_plugin = self._task_plugin_collection_service.get(
            collection="dioptra_builtins",
            task_plugin_name=taskPluginName,
            raise_error_if_not_found=True,
            bucket=current_app.config["DIOPTRA_PLUGINS_BUCKET"],
            log=log,
        )

        return cast(TaskPlugin, task_plugin)


@api.route("/dioptra_custom")
class TaskPluginCustomCollectionResource(Resource):
    """Shows a list of all custom task plugins."""

    @inject
    def __init__(
        self,
        *args,
        task_plugin_collection_service: TaskPluginCollectionService,
        **kwargs,
    ) -> None:
        self._task_plugin_collection_service = task_plugin_collection_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=TaskPluginSchema(many=True), api=api)
    def get(self) -> list[TaskPlugin]:
        """Gets a list of all registered custom task plugins."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="taskPluginCustomCollection",
            request_type="GET",
        )
        log.info("Request received")
        return self._task_plugin_collection_service.get_all(
            collection="dioptra_custom",
            bucket=current_app.config["DIOPTRA_PLUGINS_BUCKET"],
            raise_error_if_not_found=True,
            log=log,
        )


@api.route("/dioptra_custom/<string:taskPluginName>")
@api.param(
    "taskPluginName",
    "A unique string identifying a task plugin package within dioptra_custom "
    "collection.",
)
class TaskPluginCustomCollectionNameResource(Resource):
    """Shows a single custom task plugin package and lets you delete it."""

    @inject
    def __init__(
        self,
        *args,
        task_plugin_collection_service: TaskPluginCollectionService,
        **kwargs,
    ) -> None:
        self._task_plugin_collection_service = task_plugin_collection_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=TaskPluginSchema, api=api)
    def get(self, taskPluginName: str) -> TaskPlugin:
        """Gets a custom task plugin by its unique name."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="taskPluginCustomCollectionName",
            request_type="GET",
        )
        log.info("Request received")
        task_plugin = self._task_plugin_collection_service.get(
            collection="dioptra_custom",
            task_plugin_name=taskPluginName,
            bucket=current_app.config["DIOPTRA_PLUGINS_BUCKET"],
            raise_error_if_not_found=True,
            log=log,
        )
        return cast(TaskPlugin, task_plugin)

    @login_required
    @responds(schema=NameStatusResponseSchema)
    def delete(self, taskPluginName: str) -> dict[str, Any]:
        """Deletes a custom task plugin by its unique name."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="taskPluginCustomCollectionName",
            task_plugin_name=taskPluginName,
            request_type="DELETE",
        )
        log.info("Request received")
        return self._task_plugin_collection_service.delete(
            collection="dioptra_custom",
            task_plugin_name=taskPluginName,
            bucket=current_app.config["DIOPTRA_PLUGINS_BUCKET"],
            log=log,
        )
