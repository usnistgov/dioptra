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
from typing import List, Optional

import structlog
from flask import current_app, jsonify
from flask.wrappers import Response
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource
from injector import inject
from structlog.stdlib import BoundLogger

from dioptra.restapi.utils import as_api_parser

from .errors import TaskPluginDoesNotExistError, TaskPluginUploadError
from .model import TaskPlugin, TaskPluginUploadForm, TaskPluginUploadFormData
from .schema import TaskPluginSchema, TaskPluginUploadSchema
from .service import TaskPluginService

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

    @responds(schema=TaskPluginSchema(many=True), api=api)
    def get(self) -> List[TaskPlugin]:
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

    @api.expect(as_api_parser(api, TaskPluginUploadSchema))
    @accepts(TaskPluginUploadSchema, api=api)
    @responds(schema=TaskPluginSchema, api=api)
    def post(self) -> TaskPlugin:
        """Registers a new task plugin uploaded via the task plugin upload form."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="taskPlugin", request_type="POST"
        )
        task_plugin_upload_form: TaskPluginUploadForm = TaskPluginUploadForm()

        log.info("Request received")

        if not task_plugin_upload_form.validate_on_submit():
            log.error("Form validation failed")
            raise TaskPluginUploadError

        log.info("Form validation successful")
        task_plugin_upload_form_data: TaskPluginUploadFormData = (
            self._task_plugin_service.extract_data_from_form(
                task_plugin_upload_form=task_plugin_upload_form, log=log
            )
        )
        return self._task_plugin_service.create(
            task_plugin_upload_form_data=task_plugin_upload_form_data,
            bucket=current_app.config["DIOPTRA_PLUGINS_BUCKET"],
            log=log,
        )


@api.route("/dioptra_builtins")
class TaskPluginBuiltinsCollectionResource(Resource):
    """Shows a list of all builtin task plugins."""

    @inject
    def __init__(self, *args, task_plugin_service: TaskPluginService, **kwargs) -> None:
        self._task_plugin_service = task_plugin_service
        super().__init__(*args, **kwargs)

    @responds(schema=TaskPluginSchema(many=True), api=api)
    def get(self) -> List[TaskPlugin]:
        """Gets a list of all available builtin task plugins."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="taskPluginBuiltinCollection",
            request_type="GET",
        )
        log.info("Request received")
        return self._task_plugin_service.get_all_in_collection(
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
    def __init__(self, *args, task_plugin_service: TaskPluginService, **kwargs) -> None:
        self._task_plugin_service = task_plugin_service
        super().__init__(*args, **kwargs)

    @responds(schema=TaskPluginSchema, api=api)
    def get(self, taskPluginName: str) -> TaskPlugin:
        """Gets a builtin task plugin by its unique name."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="taskPluginBuiltinCollectionName",
            request_type="GET",
        )
        log.info("Request received")

        task_plugin: Optional[
            TaskPlugin
        ] = self._task_plugin_service.get_by_name_in_collection(
            collection="dioptra_builtins",
            task_plugin_name=taskPluginName,
            bucket=current_app.config["DIOPTRA_PLUGINS_BUCKET"],
            log=log,
        )

        if task_plugin is None:
            log.error(
                "TaskPlugin not found",
                task_plugin_name=taskPluginName,
                collection="dioptra_builtins",
            )
            raise TaskPluginDoesNotExistError

        return task_plugin


@api.route("/dioptra_custom")
class TaskPluginCustomCollectionResource(Resource):
    """Shows a list of all custom task plugins."""

    @inject
    def __init__(self, *args, task_plugin_service: TaskPluginService, **kwargs) -> None:
        self._task_plugin_service = task_plugin_service
        super().__init__(*args, **kwargs)

    @responds(schema=TaskPluginSchema(many=True), api=api)
    def get(self) -> List[TaskPlugin]:
        """Gets a list of all registered custom task plugins."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="taskPluginCustomCollection",
            request_type="GET",
        )
        log.info("Request received")
        return self._task_plugin_service.get_all_in_collection(
            collection="dioptra_custom",
            bucket=current_app.config["DIOPTRA_PLUGINS_BUCKET"],
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
    def __init__(self, *args, task_plugin_service: TaskPluginService, **kwargs) -> None:
        self._task_plugin_service = task_plugin_service
        super().__init__(*args, **kwargs)

    @responds(schema=TaskPluginSchema, api=api)
    def get(self, taskPluginName: str) -> TaskPlugin:
        """Gets a custom task plugin by its unique name."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="taskPluginCustomCollectionName",
            request_type="GET",
        )
        log.info("Request received")

        task_plugin: Optional[
            TaskPlugin
        ] = self._task_plugin_service.get_by_name_in_collection(
            collection="dioptra_custom",
            task_plugin_name=taskPluginName,
            bucket=current_app.config["DIOPTRA_PLUGINS_BUCKET"],
            log=log,
        )

        if task_plugin is None:
            log.error(
                "TaskPlugin not found",
                task_plugin_name=taskPluginName,
                collection="dioptra_custom",
            )
            raise TaskPluginDoesNotExistError

        return task_plugin

    def delete(self, taskPluginName: str) -> Response:
        """Deletes a custom task plugin by its unique name."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="taskPluginCustomCollectionName",
            task_plugin_name=taskPluginName,
            request_type="DELETE",
        )
        log.info("Request received")

        task_plugins: List[TaskPlugin] = self._task_plugin_service.delete(
            collection="dioptra_custom",
            task_plugin_name=taskPluginName,
            bucket=current_app.config["DIOPTRA_PLUGINS_BUCKET"],
            log=log,
        )
        name: List[str] = [x.task_plugin_name for x in task_plugins]

        return jsonify(  # type: ignore
            dict(status="Success", collection="dioptra_custom", taskPluginName=name)
        )
