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
"""The server-side functions that perform task plugin endpoint operations."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import structlog
from injector import inject
from structlog.stdlib import BoundLogger
from werkzeug.datastructures import FileStorage

from dioptra.restapi.shared.io_file.service import IOFileService
from dioptra.restapi.shared.s3.service import S3Service

from .errors import (
    TaskPluginAlreadyExistsError,
    TaskPluginDoesNotExistError,
    TaskPluginStorageError,
)
from .model import TaskPlugin

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class TaskPluginCollectionService(object):
    """The service methods for managing task plugins within a collection."""

    @inject
    def __init__(
        self,
        s3_service: S3Service,
    ) -> None:
        """Initialize the task plugin service.

        All arguments are provided via dependency injection.

        Args:
            s3_service: The S3 service.
        """
        self._s3_service = s3_service

    def get(
        self,
        collection: str,
        task_plugin_name: str,
        bucket: str = "plugins",
        raise_error_if_not_found: bool = False,
        **kwargs,
    ) -> TaskPlugin | None:
        """Fetch a task plugin by its name within a specific collection.

        Args:
            collection: The collection in which to search for the task plugin.
            task_plugin_name: The name of the task plugin.
            bucket: The S3 bucket from which to fetch the task plugin. Defaults to
                "plugins".
            raise_error_if_not_found: If True, raise an error if the task plugin is not
                found. Defaults to False.

        Returns:
            The task plugin object if found, otherwise None.

        Raises:
            TaskPluginDoesNotExistError: If the task plugin of the name
                task_plugin_name cannot be found in the collection.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        log.info(
            "Get task plugin in collection",
            collection=collection,
            task_plugin_name=task_plugin_name,
        )

        prefix = Path(collection) / task_plugin_name
        modules = self._s3_service.list_objects(
            bucket=bucket,
            prefix=self._s3_service.normalize_prefix(str(prefix), log=log),
            log=log,
        )
        if not modules:
            if raise_error_if_not_found:
                log.error(
                    "TaskPlugin not found",
                    task_plugin_name=task_plugin_name,
                    collection="dioptra_builtins",
                )
                raise TaskPluginDoesNotExistError
            return None

        return TaskPlugin(
            task_plugin_name=task_plugin_name,
            collection=collection,
            modules=[str(Path(x).name) for x in modules],
        )

    def get_all(
        self,
        collection: str,
        bucket: str = "plugins",
        raise_error_if_not_found: bool = False,
        **kwargs,
    ) -> list[TaskPlugin]:
        """Fetch the list of all task plugins in a specific collection.

        Args:
            collection: The collection from which to retrieve task plugins.
            bucket: The S3 bucket from which to fetch task plugins. Defaults to
                "plugins".
            raise_error_if_not_found: If True, raise an error if a task plugin is not
                found. Defaults to False.

        Returns:
            A list of task plugin objects.

        Raises:
            TaskPluginDoesNotExistError: If one of the task plugins cannot be found in
                the collection.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        log.info("Get all task plugins in collection", collection=collection)

        s3_directories_list = self._s3_service.list_directories(
            bucket=bucket,
            prefix=self._s3_service.normalize_prefix(collection, log=log),
            log=log,
        )

        task_plugins_collection = []
        for task_plugin_name in s3_directories_list:
            task_plugin = self.get(
                collection=collection,
                task_plugin_name=task_plugin_name,
                raise_error_if_not_found=raise_error_if_not_found,
                log=log,
            )

            if task_plugin is not None:
                task_plugins_collection.append(task_plugin)

        return task_plugins_collection

    def delete(
        self, collection: str, task_plugin_name: str, bucket: str = "plugins", **kwargs
    ) -> dict[str, Any]:
        """Delete a task plugin.

        Args:
            collection: The collection from which to delete the task plugin.
            task_plugin_name: The name of the task plugin to delete.
            bucket: The S3 bucket from which to delete the task plugin. Defaults to
                "plugins".

        Returns:
            A dictionary reporting the status of the request.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        task_plugin = self.get(
            collection=collection, task_plugin_name=task_plugin_name, log=log
        )

        if task_plugin is None:
            return {
                "status": "Success",
                "collection": collection,
                "taskPluginName": [],
            }

        prefix = Path(collection) / task_plugin_name
        self._s3_service.delete_prefix(
            bucket=bucket,
            prefix=prefix.as_posix(),
            log=log,
        )

        log.info(
            "TaskPlugin deleted",
            collection=collection,
            task_plugin_name=task_plugin_name,
        )

        return {
            "status": "Success",
            "collection": collection,
            "taskPluginName": [task_plugin.task_plugin_name],
        }


class TaskPluginService(object):
    """The service methods for uploading and listing all task plugins."""

    @inject
    def __init__(
        self,
        task_plugin_collection_service: TaskPluginCollectionService,
        io_file_service: IOFileService,
        s3_service: S3Service,
    ) -> None:
        """Initialize the task plugin service.

        All arguments are provided via dependency injection.

        Args:
            task_plugin_collection_service: The task plugin collection service.
            io_file_service: The IO file service.
            s3_service: The S3 service.
        """
        self._task_plugin_collection_service = task_plugin_collection_service
        self._io_file_service = io_file_service
        self._s3_service = s3_service

    def create(
        self,
        task_plugin_name: str,
        task_plugin_file: FileStorage,
        collection: str,
        bucket: str = "plugins",
        **kwargs,
    ) -> TaskPlugin:
        """Create a new task plugin.

        Args:
            task_plugin_name: The name of the task plugin.
            task_plugin_file: The file containing the task plugin.
            collection: The collection to which the task plugin belongs.
            bucket: The S3 bucket to store the task plugin. Defaults to "plugins".

        Returns:
            The newly created task plugin object.

        Raises:
            TaskPluginAlreadyExistsError: If a task plugin with the same name already
                exists in the collection.
            TaskPluginStorageError: If there is an error storing the task plugin in the
                backend storage.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        response = self._task_plugin_collection_service.get(
            collection=collection, task_plugin_name=task_plugin_name, log=log
        )

        if response is not None:
            raise TaskPluginAlreadyExistsError

        with TemporaryDirectory() as tmpdir:
            self._io_file_service.safe_extract_archive(
                output_dir=tmpdir,
                # FileStorage proxies its stream, but does so via __getattr__
                # override, which is opaque to mypy (we want to use FileStorage
                # as if it were an IO stream, but mypy can't tell that is
                # correct).  Passing the wrapped stream directly provides a
                # clearer type to mypy.
                archive_fileobj=task_plugin_file.stream,
                log=log,
            )

            prefix: Path = Path(collection) / task_plugin_name
            plugin_uri_list = self._s3_service.upload_directory(
                directory=tmpdir,
                bucket=bucket,
                prefix=prefix.as_posix(),
                include_suffixes=[".py"],
                log=log,
            )

        if plugin_uri_list is None:
            raise TaskPluginStorageError

        new_task_plugin = TaskPlugin(
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

    def get_all(
        self,
        s3_collections_list: list[str],
        bucket: str = "plugins",
        raise_error_if_not_found: bool = False,
        **kwargs,
    ) -> list[TaskPlugin]:
        """Fetch the list of all task plugins from multiple collections.

        Args:
            s3_collections_list: A list of collections to retrieve task plugins from.
            bucket: The S3 bucket from which to fetch task plugins. Defaults to
                "plugins".
            raise_error_if_not_found: If True, raise an error if a task plugin is not
                found. Defaults to False.
        Returns:
            A list of task plugin objects.

        Raises:
            TaskPluginDoesNotExistError: If one of the task plugins cannot be found in
                the collection.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        log.info("Get all task plugins")

        task_plugins = []

        for collection in s3_collections_list:
            task_plugins.extend(
                self._task_plugin_collection_service.get_all(
                    collection,
                    bucket=bucket,
                    raise_error_if_not_found=raise_error_if_not_found,
                    log=log,
                )
            )

        return task_plugins
