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
"""The server-side functions that perform workflows endpoint operations."""
import json
import tarfile
from collections import defaultdict
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import IO, Any, Final

import jsonschema
import structlog
import toml
from injector import inject
from structlog.stdlib import BoundLogger
from werkzeug.datastructures import FileStorage

from dioptra.restapi.db import db, models
from dioptra.restapi.errors import DioptraError
from dioptra.restapi.v1.entrypoints.service import (
    EntrypointIdService,
    EntrypointNameService,
    EntrypointService,
)
from dioptra.restapi.v1.plugin_parameter_types.service import (
    BuiltinPluginParameterTypeService,
    PluginParameterTypeIdService,
    PluginParameterTypeNameService,
    PluginParameterTypeService,
)
from dioptra.restapi.v1.plugins.service import (
    PluginIdFileService,
    PluginIdService,
    PluginNameService,
    PluginService,
)
from dioptra.sdk.utilities.paths import set_cwd

from .lib import clone_git_repository, package_job_files, views
from .schema import (
    FileTypes,
    ResourceImportResolveNameConflictsStrategy,
    ResourceImportSourceTypes,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()

RESOURCE_TYPE: Final[str] = "workflow"

DIOPTRA_RESOURCES_SCHEMA_PATH: Final[str] = "dioptra-resources.schema.json"


class JobFilesDownloadService(object):
    """The service methods for packaging job files for download."""

    def get(self, job_id: int, file_type: FileTypes, **kwargs) -> IO[bytes]:
        """Get the files needed to run a job and package them for download.

        Args:
            job_id: The identifier of the job.
            file_type: The type of file to package the job files into. Must be one of
                the values in the FileTypes enum.

        Returns:
            The packaged job files returned as a named temporary file.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get job files download", job_id=job_id, file_type=file_type)

        experiment = views.get_experiment(job_id=job_id, logger=log)
        entry_point = views.get_entry_point(job_id=job_id, logger=log)
        entry_point_plugin_files = views.get_entry_point_plugin_files(
            job_id=job_id, logger=log
        )
        job_parameter_values = views.get_job_parameter_values(job_id=job_id, logger=log)
        plugin_parameter_types = views.get_plugin_parameter_types(
            job_id=job_id, logger=log
        )
        return package_job_files(
            job_id=job_id,
            experiment=experiment,
            entry_point=entry_point,
            entry_point_plugin_files=entry_point_plugin_files,
            job_parameter_values=job_parameter_values,
            plugin_parameter_types=plugin_parameter_types,
            file_type=file_type,
            logger=log,
        )


class ResourceImportService(object):
    """The service methods for packaging job files for download."""

    @inject
    def __init__(
        self,
        plugin_service: PluginService,
        plugin_id_service: PluginIdService,
        plugin_name_service: PluginNameService,
        plugin_id_file_service: PluginIdFileService,
        plugin_parameter_type_service: PluginParameterTypeService,
        plugin_parameter_type_id_service: PluginParameterTypeIdService,
        plugin_parameter_type_name_service: PluginParameterTypeNameService,
        builtin_plugin_parameter_type_service: BuiltinPluginParameterTypeService,
        entrypoint_service: EntrypointService,
        entrypoint_id_service: EntrypointIdService,
        entrypoint_name_service: EntrypointNameService,
    ) -> None:
        """Initialize the resource import service.

        All arguments are provided via dependency injection.

        Args:
            plugin_service: A PluginService object,
            plugin_name_service: A PluginNameService object.
            plugin_id_service: A PluginIdService object.
            plugin_id_file_service: A PluginIdFileService object.
            plugin_parameter_type_service: A PluginParameterTypeService object.
            plugin_parameter_type_id_service: A PluginParameterTypeIdService object.
            plugin_parameter_type_name_service: A PluginParameterTypeNameService object.
            builtin_plugin_parameter_type_service: A BuiltinPluginParameterTypeService
                object.
            entrypoint_service: An EntrypointService object.
            entrypoint_id_service: An EntrypointIdService object.
            entrypoint_name_service: An EntrypointNameService object.
        """
        self._plugin_service = plugin_service
        self._plugin_id_service = plugin_id_service
        self._plugin_name_service = plugin_name_service
        self._plugin_id_file_service = plugin_id_file_service
        self._plugin_parameter_type_service = plugin_parameter_type_service
        self._plugin_parameter_type_id_service = plugin_parameter_type_id_service
        self._plugin_parameter_type_name_service = plugin_parameter_type_name_service
        self._builtin_plugin_parameter_type_service = (
            builtin_plugin_parameter_type_service
        )
        self._entrypoint_service = entrypoint_service
        self._entrypoint_id_service = entrypoint_id_service
        self._entrypoint_name_service = entrypoint_name_service

    def import_resources(
        self,
        group_id: int,
        source_type: str,
        git_url: str | None,
        archive_file: FileStorage | None,
        config_path: str,
        resolve_name_conflicts_strategy: str,
        **kwargs,
    ) -> dict[str, Any]:
        """Import resources from a archive file or git repository

        Args:
            group_id: The group to import resources into
            source_type: The source to import from (either "upload" or "git")
            git_url: The url to the git repository if source_type is "git"
            archive_file: The contents of the upload if source_type is "upload"
            resolve_name_conflicts_strategy: The strategy for resolving name conflicts.
                Either "fail" or "overwrite"

        Returns:
            A message summarizing imported resources
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Import resources", group_id=group_id)

        overwrite = (
            resolve_name_conflicts_strategy
            == ResourceImportResolveNameConflictsStrategy.OVERWRITE
        )

        with TemporaryDirectory() as tmp_dir, set_cwd(tmp_dir):
            working_dir = Path(tmp_dir)

            if source_type == ResourceImportSourceTypes.UPLOAD:
                bytes = archive_file.stream.read()
                with tarfile.open(fileobj=BytesIO(bytes), mode="r:*") as tar:
                    tar.extractall(path=working_dir, filter="data")
                hash = str(sha256(bytes).hexdigest())
            elif source_type == ResourceImportSourceTypes.GIT:
                hash = clone_git_repository(git_url, working_dir)

            try:
                config = toml.load(working_dir / config_path)
            except Exception as e:
                raise DioptraError(
                    f"Failed to load resource import config from {config_path}."
                ) from e

            # validate the config file
            with open(
                Path(__file__).resolve().parent / DIOPTRA_RESOURCES_SCHEMA_PATH, "rb"
            ) as f:
                schema = json.load(f)
            jsonschema.validate(config, schema)

            param_types = self._register_plugin_param_types(
                group_id, config.get("plugin_param_types", []), overwrite, log=log
            )
            plugins = self._register_plugins(
                group_id, config.get("plugins", []), param_types, overwrite, log=log
            )
            entrypoints = self._register_entrypoints(
                group_id, config.get("entrypoints", []), plugins, overwrite, log=log
            )

        db.session.commit()

        return {
            "message": "successfully imported",
            "hash": hash,
            "resources": {
                "plugins": list(plugins.keys()),
                "plugin_param_types": list(param_types.keys()),
                "entrypoints": list(entrypoints.keys()),
            },
        }

    def _register_plugin_param_types(
        self,
        group_id: int,
        param_types_config: list[dict[str, Any]],
        overwrite: bool,
        log: BoundLogger,
    ) -> dict[str, models.PluginTaskParameterType]:
        """
        Registers a list of PluginParameterTypes.

        Args:
            group_id: The identifier of the group that will manage imported resources
            param_types_config: A list of dictionaries describing a plugin param types
            overwrite: Whether imported resources should replace existing resources with
                a conflicting name

        Returns:
            A dictionary mapping newly registered PluginParameterType names to the ORM
            object
        """

        param_types = dict()
        for param_type in param_types_config:
            if overwrite:
                existing = self._plugin_parameter_type_name_service.get(
                    param_type["name"], group_id=group_id, log=log
                )
                if existing:
                    self._plugin_parameter_type_id_service.delete(
                        plugin_parameter_type_id=existing.resource_id,
                        log=log,
                    )

            param_type_dict = self._plugin_parameter_type_service.create(
                name=param_type["name"],
                description=param_type.get("description", None),
                structure=param_type.get("structure", None),
                group_id=group_id,
                commit=False,
                log=log,
            )
            param_types[param_type["name"]] = param_type_dict[
                "plugin_task_parameter_type"
            ]

        db.session.flush()

        return param_types

    def _register_plugins(
        self,
        group_id: int,
        plugins_config: list[dict[str, Any]],
        param_types: dict[str, models.PluginTaskParameterType],
        overwrite: bool,
        log: BoundLogger,
    ) -> dict[str, models.PluginTaskParameterType]:
        """
        Registers a list of Plugins and their PluginFiles.

        Args:
            group_id: The identifier of the group that will manage imported resources
            plugins_config: A list of dictionaries describing a plugin and its tasks
            param_types: A dictionary mapping param type name to the ORM object
            overwrite: Whether imported resources should replace existing resources with
                a conflicting name

        Returns:
            A dictionary mapping newly registered Plugin names to the ORM objects
        """

        param_types = param_types.copy()
        builtin_param_types = self._builtin_plugin_parameter_type_service.get(
            group_id=group_id, error_if_not_found=False, log=log
        )
        param_types.update(
            {param_type.name: param_type for param_type in builtin_param_types}
        )

        plugins = {}
        for plugin in plugins_config:
            if overwrite:
                existing = self._plugin_name_service.get(
                    Path(plugin["path"]).stem, group_id=group_id
                )
                if existing:
                    self._plugin_id_service.delete(
                        plugin_id=existing.resource_id,
                        log=log,
                    )

            plugin_dict = self._plugin_service.create(
                name=Path(plugin["path"]).stem,
                description=plugin.get("description", None),
                group_id=group_id,
                commit=False,
                log=log,
            )
            plugins[plugin_dict["plugin"].name] = plugin_dict["plugin"]
            db.session.flush()

            tasks = self._build_tasks(plugin.get("tasks", []), param_types)
            for plugin_file_path in Path(plugin["path"]).rglob("*.py"):
                filename = str(plugin_file_path.relative_to(plugin["path"]))
                contents = plugin_file_path.read_text()

                self._plugin_id_file_service.create(
                    filename,
                    contents=contents,
                    description=None,
                    tasks=tasks[filename],
                    plugin_id=plugin_dict["plugin"].resource_id,
                    commit=False,
                    log=log,
                )

        db.session.flush()

        return plugins

    def _register_entrypoints(
        self,
        group_id: int,
        entrypoints_config: list[dict[str, Any]],
        plugins,
        overwrite: bool,
        log: BoundLogger,
    ) -> dict[str, models.EntryPoint]:
        """
        Registers a list of Entrypoints

        Args:
            group_id: The identifier of the group that will manage imported resources
            entrypoints_config: A list of dictionaries describing entrypoints
            plugins: A dictionary mapping Plugin names to the ORM objects
            overwrite: Whether imported resources should replace existing resources with
                a conflicting name

        Returns:
            A dictionary mapping newly registered Entrypoint names to ORM object
        """

        entrypoints = dict()
        for entrypoint in entrypoints_config:
            if overwrite:
                existing = self._entrypoint_name_service.get(
                    entrypoint["name"], group_id=group_id, log=log
                )
                if existing is not None:
                    self._entrypoint_id_service.delete(
                        entrypoint_id=existing.resource_id
                    )

            contents = Path(entrypoint["path"]).read_text()
            params = [
                {
                    "name": param["name"],
                    "parameter_type": param["type"],
                    "default_value": param.get("default_value", None),
                }
                for param in entrypoint.get("params", [])
            ]
            plugin_ids = [
                plugins[plugin].resource_id for plugin in entrypoint.get("plugins", [])
            ]
            entrypoint_dict = self._entrypoint_service.create(
                name=entrypoint.get("name", Path(entrypoint["path"]).stem),
                description=entrypoint.get("description", None),
                task_graph=contents,
                parameters=params,
                plugin_ids=plugin_ids,
                queue_ids=[],
                group_id=group_id,
                commit=False,
                log=log,
            )
            entrypoints[entrypoint_dict["entry_point"].name] = entrypoint_dict[
                "entry_point"
            ]

        db.session.flush()

        return entrypoints

    def _build_tasks(
        self,
        tasks_config: list[dict[str, Any]],
        param_types: dict[str, models.PluginTaskParameterType],
    ) -> dict[str, list]:
        """
        Builds dictionaries describing plugin tasks from a configuration file

        Args:
            tasks_config: A list of dictionaries describing plugin tasks
            param_types: A dictionary mapping param type name to the ORM object

        Returns:
            A dictionary mapping PluginFile name to a list of tasks
        """

        tasks = defaultdict(list)
        for task in tasks_config:
            tasks[task["filename"]].append(
                {
                    "name": task["name"],
                    "description": task.get("description", None),
                    "input_params": [
                        {
                            "name": param["name"],
                            "parameter_type_id": param_types[param["type"]].resource_id,
                            "required": param.get("required", False),
                        }
                        for param in task["input_params"]
                    ],
                    "output_params": [
                        {
                            "name": param["name"],
                            "parameter_type_id": param_types[param["type"]].resource_id,
                        }
                        for param in task["output_params"]
                    ],
                }
            )
        return tasks
