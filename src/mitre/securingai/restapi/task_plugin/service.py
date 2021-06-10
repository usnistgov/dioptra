# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
"""The server-side functions that perform task plugin endpoint operations."""

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Optional

import structlog
from injector import inject
from structlog.stdlib import BoundLogger
from werkzeug.datastructures import FileStorage

from mitre.securingai.restapi.shared.io_file.service import IOFileService
from mitre.securingai.restapi.shared.s3.service import S3Service

from .errors import TaskPluginAlreadyExistsError
from .model import TaskPlugin, TaskPluginUploadForm, TaskPluginUploadFormData
from .schema import TaskPluginUploadFormSchema

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class TaskPluginService(object):
    @inject
    def __init__(
        self,
        io_file_service: IOFileService,
        s3_service: S3Service,
        task_plugin_upload_form_schema: TaskPluginUploadFormSchema,
    ) -> None:
        self._io_file_service = io_file_service
        self._s3_service = s3_service
        self._task_plugin_upload_form_schema = task_plugin_upload_form_schema

    def create(
        self,
        task_plugin_upload_form_data: TaskPluginUploadFormData,
        bucket: str = "plugins",
        **kwargs,
    ) -> TaskPlugin:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        task_plugin_name: str = task_plugin_upload_form_data["task_plugin_name"]
        task_plugin_file: FileStorage = task_plugin_upload_form_data["task_plugin_file"]
        collection: str = task_plugin_upload_form_data["collection"]

        self._validate_task_plugin_does_not_exist(collection, task_plugin_name, log=log)

        with TemporaryDirectory() as tmpdir:
            self._io_file_service.safe_extract_archive(
                output_dir=tmpdir,
                archive_fileobj=task_plugin_file,
                log=log,
            )

            prefix: Path = Path(collection) / task_plugin_name
            plugin_uri_list: List[str] = self._s3_service.upload_directory(
                directory=tmpdir,
                bucket=bucket,
                prefix=str(prefix),
                include_suffixes=[".py"],
                log=log,
            )

        new_task_plugin: TaskPlugin = TaskPlugin(
            task_plugin_name=task_plugin_name,
            collection=collection,
            modules=[str(Path(x).name) for x in plugin_uri_list],
        )

        log.info(
            "TaskPlugin registration successful",
            task_plugin_name=new_task_plugin.task_plugin_name,
            collection=new_task_plugin.collection,
            modules=new_task_plugin.modules,
        )

        return new_task_plugin

    def delete(
        self, collection: str, task_plugin_name: str, bucket: str = "plugins", **kwargs
    ) -> List[TaskPlugin]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        task_plugin: Optional[TaskPlugin] = self.get_by_name_in_collection(
            collection=collection, task_plugin_name=task_plugin_name, log=log
        )

        if task_plugin is None:
            return []

        prefix: Path = Path(collection) / task_plugin_name
        self._s3_service.delete_prefix(bucket=bucket, prefix=str(prefix), log=log)

        log.info(
            "TaskPlugin deleted",
            collection=collection,
            task_plugin_name=task_plugin_name,
        )

        return [task_plugin]

    def get_all(self, bucket: str = "plugins", **kwargs) -> List[TaskPlugin]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        log.info("Get all task plugins")

        s3_collections_list: List[str] = self._s3_service.list_directories(
            bucket=bucket,
            prefix=self._s3_service.normalize_prefix("/", log=log),
            log=log,
        )

        task_plugins: List[TaskPlugin] = []
        for collection in s3_collections_list:
            task_plugins.extend(self.get_all_in_collection(collection, log=log))

        return task_plugins

    def get_all_in_collection(
        self, collection: str, bucket: str = "plugins", **kwargs
    ) -> List[TaskPlugin]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        log.info("Get all task plugins in collection", collection=collection)

        s3_directories_list: List[str] = self._s3_service.list_directories(
            bucket=bucket,
            prefix=self._s3_service.normalize_prefix(collection, log=log),
            log=log,
        )

        task_plugins_collection: List[TaskPlugin] = []
        for task_plugin_name in s3_directories_list:
            task_plugin: Optional[TaskPlugin] = self.get_by_name_in_collection(
                collection=collection, task_plugin_name=task_plugin_name, log=log
            )

            if task_plugin is not None:
                task_plugins_collection.append(task_plugin)

        return task_plugins_collection

    def get_by_name_in_collection(
        self, collection: str, task_plugin_name: str, bucket: str = "plugins", **kwargs
    ) -> Optional[TaskPlugin]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        log.info(
            "Get task plugin in collection",
            collection=collection,
            task_plugin_name=task_plugin_name,
        )

        prefix = Path(collection) / task_plugin_name
        modules: List[str] = self._s3_service.list_objects(
            bucket=bucket,
            prefix=self._s3_service.normalize_prefix(str(prefix), log=log),
            log=log,
        )

        if not modules:
            return None

        return TaskPlugin(
            task_plugin_name=task_plugin_name,
            collection=collection,
            modules=[str(Path(x).name) for x in modules],
        )

    def extract_data_from_form(
        self, task_plugin_upload_form: TaskPluginUploadForm, **kwargs
    ) -> TaskPluginUploadFormData:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        log.info("Extract data from task plugin upload form")
        data: TaskPluginUploadFormData = self._task_plugin_upload_form_schema.dump(
            task_plugin_upload_form
        )

        return data

    def _validate_task_plugin_does_not_exist(
        self, collection, task_plugin_name, **kwargs
    ) -> None:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        response: Optional[TaskPlugin] = self.get_by_name_in_collection(
            collection=collection, task_plugin_name=task_plugin_name, log=log
        )

        if response is not None:
            raise TaskPluginAlreadyExistsError
