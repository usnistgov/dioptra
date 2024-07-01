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
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final, cast

import structlog
import yaml
from injector import inject
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import db, models
from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.plugins.service import PluginIdFileService, PluginIdService

from .schema import FileTypes

LOGGER: BoundLogger = structlog.stdlib.get_logger()

RESOURCE_TYPE: Final[str] = "workflow"


class JobFilesDownloadService(object):
    @inject
    def __init__(
        self,
        plugin_id_service: PluginIdService,
        plugin_id_files_service: PluginIdFileService,
        plugin_files_export_service: "PluginFilesExportService",
        task_engine_yaml_service: "TaskEngineYamlService",
    ) -> None:
        """Initialize the queue service.

        All arguments are provided via dependency injection.
        """
        self._plugin_id_service = plugin_id_service
        self._plugin_id_files_service = plugin_id_files_service
        self._plugin_files_export_service = plugin_files_export_service
        self._task_engine_yaml_service = task_engine_yaml_service

    def get(self, job_id: int, file_type: FileTypes, **kwargs):
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get job files download", job_id=job_id, file_type=file_type)

        plugin_ids: list[int] = []

        with TemporaryDirectory() as tmp_dir:
            tmp_dir_path = Path(tmp_dir)
            plugin_dirs: list[Path] = []
            for plugin_id in plugin_ids:
                plugin_with_files_dict = cast(
                    utils.PluginWithFilesDict,
                    self._plugin_id_service.get(plugin_id, error_if_not_found=True),
                )
                plugin_dirs.append(
                    self._plugin_files_export_service.get(
                        plugin_with_files_dict, tmp_dir=tmp_dir_path
                    )
                )

            task_yaml_path = self._task_engine_yaml_service.get(tmp_dir=tmp_dir_path)

            with tarfile.open(plugin_path.with_suffix(".tar.gz"), "w:gz") as tar:
                tar.add(plugin_path, arcname=plugin.name)


class PluginFilesExportService(object):
    def get(
        self, plugin_with_files_dict: utils.PluginWithFilesDict, tmp_dir: Path
    ) -> Path:
        plugin = plugin_with_files_dict["plugin"]
        plugin_files = plugin_with_files_dict["plugin_files"]

        plugin_path = tmp_dir / plugin.name
        plugin_path.mkdir(parents=True)
        for plugin_file in plugin_files:
            (plugin_path / plugin_file.filename).parent.mkdir(
                parents=True, exist_ok=True
            )
            if plugin_file.contents:
                (plugin_path / plugin_file.filename).write_text(plugin_file.contents)

            else:
                (plugin_path / plugin_file.filename).touch(exist_ok=True)

        return plugin_path


class TaskEngineYamlService(object):
    def get(self, tmp_dir: Path) -> Path:
        task_engine_dict = {
            "types": self.extract_types(),
            "parameters": self.extract_parameters(),
            "tasks": self.extract_tasks(),
            "graph": self.extract_graph(),
        }

        task_yaml_path = tmp_dir / f"{entrypoint.name}.yml"

        with task_yaml_path.open("wt") as f:
            yaml.dump(task_engine_dict, f, default_flow_style=False, indent=2)

        return task_yaml_path

    def extract_types(self):
        types = {
            param.parameter_type.name: param.parameter_type.structure
            for file in files
            for task in file.tasks
            for param in task.input_parameters + task.output_parameters
            if param.parameter_type.name not in BUILTIN_TYPES
        }

    def extract_parameters(self):
        parameters = {
            param.name: param.default_value for param in entrypoint.parameters
        }

    def extract_tasks(self):
        tasks = {
            task.plugin_task_name: {
                "plugin": ".".join(
                    [plugin.name, Path(file.filename).stem, task.plugin_task_name]
                ),
                "inputs": [
                    {"name": param.name, "type": param.parameter_type.name}
                    for param in task.input_parameters
                ],
                "outputs": [
                    {param.name: param.parameter_type.name}
                    for param in task.output_parameters
                ],
            }
            for file in files
            for task in file.tasks
        }

    def extract_graph(self):
        return entrypoint.task_graph
