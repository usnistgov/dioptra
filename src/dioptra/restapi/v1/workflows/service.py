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
import jsonschema
import tarfile
from collections import defaultdict
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import IO, Any, Final

import structlog
import toml
from injector import inject
from structlog.stdlib import BoundLogger
from werkzeug.datastructures import FileStorage

from dioptra.restapi.db import db
from dioptra.restapi.v1.entrypoints.service import EntrypointService
from dioptra.restapi.v1.plugin_parameter_types.service import (
    BuiltinPluginParameterTypeService,
    PluginParameterTypeService,
)
from dioptra.restapi.v1.plugins.service import PluginIdFileService, PluginService
from dioptra.sdk.utilities.paths import set_cwd

from .lib import clone_git_repository, package_job_files, views
from .schema import (
    FileTypes,
    ResourceImportSourceTypes,
    ResourceImportResolveNameConflictsStrategy,
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
        return package_job_files(
            job_id=job_id,
            experiment=experiment,
            entry_point=entry_point,
            entry_point_plugin_files=entry_point_plugin_files,
            job_parameter_values=job_parameter_values,
            file_type=file_type,
            logger=log,
        )


class ResourceImportService(object):
    """The service methods for packaging job files for download."""

    @inject
    def __init__(
        self,
        plugin_service: PluginService,
        plugin_id_file_service: PluginIdFileService,
        plugin_parameter_type_service: PluginParameterTypeService,
        builtin_plugin_parameter_type_service: BuiltinPluginParameterTypeService,
        entrypoint_service: EntrypointService,
    ) -> None:
        """Initialize the resource import service.

        All arguments are provided via dependency injection.

        Args:
            plugin_name_service: A PluginNameService object.
            plugin_id_file_service: A PluginIdFileService object.
            plugin_parameter_type_service: A PluginParameterTypeService object.
            builtin_plugin_parameter_type_service: A BuiltinPluginParameterTypeService object.
            entrypoint_service: A EntrypointService object.
        """
        self._plugin_service = plugin_service
        self._plugin_id_file_service = plugin_id_file_service
        self._plugin_parameter_type_service = plugin_parameter_type_service
        self._builtin_plugin_parameter_type_service = (
            builtin_plugin_parameter_type_service
        )
        self._entrypoint_service = entrypoint_service

    def import_resources(
        self,
        group_id: int,
        source_type: str,
        git_url: str | None,
        archive_file: FileStorage | None,
        config_path: str,
        read_only: bool,
        resolve_name_conflicts_strategy: str,
        **kwargs,
    ) -> dict[str, Any]:
        """Import resources from a archive file or git repository

        Args:
            group_id: The group to import resources into
            source_type: The source to import from (either "upload" or "git")
            git_url: The url to the git repository if source_type is "git"
            archive_file: The contents of the upload if source_type is "upload"
            read_only: Whether to apply a readonly lock to all imported resources
            resolve_name_conflicts_strategy: The strategy for resolving name conflicts.
                Either "fail" or "overwrite"

        Returns:
            A message summarizing imported resources
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Import resources", group_id=group_id)

        replace_existing = (
            resolve_name_conflicts_strategy
            == ResourceImportResolveNameConflictsStrategy.OVERWRITE
        )

        with TemporaryDirectory() as tmp_dir, set_cwd(tmp_dir):
            working_dir = Path(tmp_dir)

            if source_type == ResourceImportSourceTypes.UPLOAD:
                bytes = archive_file.stream.read()
                with tarfile.open(fileobj=BytesIO(bytes), mode="r:*") as tar:
                    tar.extractall(path=working_dir, filter="data")
                hash = sha256(bytes).hexdigest()
            elif source_type == ResourceImportSourceTypes.GIT:
                hash = clone_git_repository(git_url, working_dir)

            log.info(hash=hash, paths=list(working_dir.glob("*")))

            config = toml.load(working_dir / config_path)

            # validate the config file
            with open(
                Path(__file__).resolve().parent / DIOPTRA_RESOURCES_SCHEMA_PATH, "rb"
            ) as f:
                schema = json.load(f)
            jsonschema.validate(config, schema)

            # register new plugin param types
            param_types = {
                param_type["name"]: self._plugin_parameter_type_service.create(
                    name=param_type["name"],
                    description=param_type.get("description", None),
                    structure=param_type.get("structure", None),
                    group_id=group_id,
                    replace_existing=replace_existing,
                    commit=False,
                    log=log,
                )
                for param_type in config.get("plugin_param_types", [])
            }
            # retrieve built-ins
            param_types.update(
                {
                    param_type.name: param_type
                    for param_type in self._builtin_plugin_parameter_type_service.get(
                        group_id=group_id, error_if_not_found=False, log=log
                    )
                }
            )
            db.session.flush()

            # register new plugins
            plugin_ids = {}
            for plugin in config.get("plugins", []):
                plugin_dict = self._plugin_service.create(
                    name=Path(plugin["path"]).stem,
                    description=plugin.get("description", None),
                    group_id=group_id,
                    replace_existing=replace_existing,
                    commit=False,
                    log=log,
                )
                db.session.flush()
                plugin_ids[plugin_dict["plugin"].name] = plugin_dict[
                    "plugin"
                ].resource_id

                tasks = _build_tasks(plugin.get("tasks", []), param_types)
                for plugin_file_path in Path(plugin["path"]).rglob("*.py"):
                    filename = str(plugin_file_path.relative_to(plugin["path"]))
                    contents = plugin_file_path.read_text()

                    plugin_file_dict = self._plugin_id_file_service.create(
                        filename,
                        contents=contents,
                        description=None,
                        tasks=tasks[filename],
                        plugin_id=plugin_dict["plugin"].resource_id,
                        commit=False,
                        log=log,
                    )

            # register new entrypoints
            for entrypoint in config.get("entrypoints", []):
                contents = Path(entrypoint["path"]).read_text()
                params = [
                    {
                        "name": param["name"],
                        "parameter_type": param["type"],
                        "default_value": param.get("default_value", None),
                    }
                    for param in entrypoint.get("params", [])
                ]
                self._entrypoint_service.create(
                    name=entrypoint.get("name", Path(entrypoint["path"]).stem),
                    description=entrypoint.get("description", None),
                    task_graph=contents,
                    parameters=params,
                    plugin_ids=[
                        plugin_ids[plugin] for plugin in entrypoint.get("plugins", [])
                    ],
                    queue_ids=[],
                    group_id=group_id,
                    replace_existing=replace_existing,
                    commit=False,
                    log=log,
                )

        db.session.commit()

        return {"message": "successfully imported"}


def _build_tasks(tasks_config, param_types):
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
