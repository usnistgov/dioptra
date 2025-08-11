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

from collections import defaultdict
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Final, cast

import jsonschema
import structlog
import tomli as toml
import yaml
from injector import inject
from structlog.stdlib import BoundLogger
from werkzeug.datastructures import FileStorage

from dioptra.restapi.db import db, models
from dioptra.restapi.errors import (
    DioptraError,
    DraftDoesNotExistError,
    DraftResourceModificationsCommitError,
    EntityDoesNotExistError,
    GitError,
    ImportFailedError,
    InvalidYamlError,
)
from dioptra.restapi.utils import read_json_file, verify_filename_is_safe
from dioptra.restapi.v1.entity_types import EntityTypes
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
    get_plugin_task_parameter_types_by_id,
)
from dioptra.restapi.v1.plugins.schema import ALLOWED_PLUGIN_FILENAME_REGEX
from dioptra.restapi.v1.plugins.service import (
    PluginIdFileService,
    PluginIdService,
    PluginNameService,
    PluginService,
)
from dioptra.restapi.v1.shared.io_file_service import IOFileService
from dioptra.restapi.v1.shared.resource_service import (
    ResourceIdService,
    ResourceService,
)
from dioptra.restapi.v1.shared.signature_analysis import get_plugin_signatures
from dioptra.restapi.v1.shared.task_engine_yaml.service import TaskEngineYamlService
from dioptra.sdk.utilities.paths import set_cwd
from dioptra.task_engine.issues import IssueSeverity, IssueType, ValidationIssue

from .lib import views
from .lib.clone_git_repository import clone_git_repository
from .schema import (
    ResourceImportResolveNameConflictsStrategy,
    ResourceImportSourceTypes,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()

RESOURCE_TYPE: Final[EntityTypes] = EntityTypes.WORKFLOW

DIOPTRA_RESOURCES_SCHEMA: Final[dict] = read_json_file(
    "dioptra.restapi.v1.workflows", "dioptra-resources.schema.json"
)

VALID_ENTRYPOINT_PARAM_TYPES: Final[set[str]] = {
    "string",
    "float",
    "integer",
    "boolean",
    "list",
    "mapping",
}


class SignatureAnalysisService(object):
    """The service methods for performing signature analysis on a file."""

    def post(self, python_code: str, **kwargs) -> dict[str, list[dict[str, Any]]]:
        """Perform signature analysis on a file.

        Args:
            filename: The name of the file.
            python_code: The contents of the file.

        Returns:
            A dictionary containing the signature analysis.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug(
            "Performing signature analysis",
            python_source=python_code,
        )
        endpoint_analyses = [
            _create_endpoint_analysis_dict(signature)
            for signature in get_plugin_signatures(python_source=python_code)
        ]
        return {"tasks": endpoint_analyses}


def _create_endpoint_analysis_dict(
    signature: dict[str, Any],
) -> dict[str, Any]:
    """Create an endpoint analysis dictionary from a signature analysis.
    Args:
        signature: The signature analysis.
    Returns:
        The endpoint analysis dictionary.
    """
    return {
        "name": signature["name"],
        "inputs": signature["inputs"],
        "outputs": signature["outputs"],
        "missing_types": [
            {
                "description": suggested_type["type_annotation"],
                "name": suggested_type["suggestion"],
            }
            for suggested_type in signature["suggested_types"]
        ],
    }


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
        io_file_service: IOFileService,
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
            io_file_service: An IOFileService object.
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
        self._io_file_service = io_file_service

    def import_resources(
        self,
        group_id: int,
        source_type: str,
        git_url: str | None,
        archive_file: FileStorage | None,
        files: list[FileStorage] | None,
        config_path: str,
        resolve_name_conflicts_strategy: str,
        **kwargs,
    ) -> dict[str, Any]:
        """Import resources from a archive file or git repository

        Args:
            group_id: The group to import resources into
            source_type: The source to import from (either "upload" or "git")
            git_url: The url to the git repository if source_type is "git"
            archive_file: The contents of the upload if source_type is "upload_archive"
            files: The contents of the upload if source_type is "upload_files"
            config_path: The path to the toml configuration file in the import source.
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

            if source_type == ResourceImportSourceTypes.UPLOAD_ARCHIVE:
                hash: str = self._read_from_archive(archive_file, working_dir)
            elif source_type == ResourceImportSourceTypes.UPLOAD_FILES:
                hash = self._read_from_files(files, working_dir)
            elif source_type == ResourceImportSourceTypes.GIT:
                hash = self._read_from_git(git_url, working_dir)

            config = self._load_config_file(working_dir / config_path)

            # all resources are relative to the config file directory
            with set_cwd((working_dir / config_path).parent):
                param_types = self._register_plugin_param_types(
                    group_id, config.get("plugin_param_types", []), overwrite, log=log
                )
                plugins = self._register_plugins(
                    group_id, config.get("plugins", []), param_types, overwrite, log=log
                )
                entrypoints = self._register_entrypoints(
                    group_id,
                    config.get("entrypoints", []),
                    plugins,
                    param_types,
                    overwrite,
                    log=log,
                )

        db.session.commit()

        return {
            "message": "successfully imported",
            "hash": hash,
            "resources": {
                "plugins": {
                    plugin.name: plugin.resource_id for plugin in plugins.values()
                },
                "plugin_param_types": {
                    param_type.name: param_type.resource_id
                    for param_type in param_types.values()
                },
                "entrypoints": {
                    entrypoint.name: entrypoint.resource_id
                    for entrypoint in entrypoints.values()
                },
            },
        }

    def _read_from_archive(self, archive_file: FileStorage, destination: Path) -> str:
        """
        Reads resources from an archive file.

        Args:
            archive_file: A FileStorage object containing the uploaded archive.
            destination: The path to extract the archive to.

        Returns:
            The hash of the uploaded file.

        Raises:
            ImportFailedError: If the archive cannot be read and unpacked for any reason
        """

        bytes = archive_file.stream.read()
        try:
            self._io_file_service.safe_extract_archive(
                destination, archive_fileobj=BytesIO(bytes), preserve_paths=True
            )
        except Exception as e:
            raise ImportFailedError("Failed to read uploaded tarfile") from e

        return str(sha256(bytes).hexdigest())

    def _read_from_files(self, files: list[FileStorage], destination: Path) -> str:
        """
        Reads resources from a multi-file upload.

        Args:
            files: A list of FileStorage objects containing the uploaded files.
            destination: The path to save the files to.

        Returns:
            The hash of the uploaded files.

        Raises:
            ImportFailedError: If the archive cannot be read and unpacked for any reason
        """

        def _sort_by_filename(x: FileStorage) -> Path:
            if (filename := x.filename) is None:
                raise DioptraError(
                    f"Malformed multi-file upload, filename not found: {x.name}"
                )

            return Path(filename).resolve()

        hash = sha256()
        for file in sorted(files, key=_sort_by_filename):
            # The _sort_by_filename sorting key already checks whether filename is None,
            # so here we can just assert that it's not None to make mypy happy.
            assert file.filename is not None
            try:
                verify_filename_is_safe(file.filename)
            except ValueError as e:
                raise ImportFailedError(
                    "Failed to read uploaded files", reason=str(e)
                ) from e
            Path(file.filename).parent.mkdir(parents=True, exist_ok=True)

            bytes = file.stream.read()
            with open(destination / file.filename, "wb") as f:
                f.write(bytes)
            hash.update(bytes)

        return str(hash.hexdigest())

    def _read_from_git(self, git_url: str, destination: Path) -> str:
        """
        Reads resources from a git repo.

        Args:
            git_url: A url to the git repository
            destination: The path to clone the repo to.

        Returns:
            The latest git commit hash.

        Raises:
            ImportFailedError: If the archive cannot be read and unpacked for any reason
        """

        try:
            return clone_git_repository(git_url, destination)
        except Exception as e:
            raise GitError(f"Failed to clone repository: {git_url}") from e

    def _load_config_file(self, config_path: Path) -> dict[str, Any]:
        """
        Loads and validates the dioptra toml config

        Args:
            config_path: The path to the config file

        Returns:
            A dictionary containing the configuration
        """

        try:
            with open(config_path, "rb") as f:
                config = toml.load(f)
        except toml.TOMLDecodeError as e:
            raise ImportFailedError(
                f"Failed to load resource import config from {config_path}.",
                reason=f"Could not decode config: {e}",
            ) from e
        except FileNotFoundError as e:
            raise ImportFailedError(
                f"Failed to load resource import config from {config_path}.",
                reason="File not found.",
            ) from e
        except Exception as e:
            raise ImportFailedError(
                f"Failed to load resource import config from {config_path}."
            ) from e

        try:
            jsonschema.validate(config, DIOPTRA_RESOURCES_SCHEMA)
        except jsonschema.ValidationError as e:
            raise ImportFailedError(
                f"Failed to validate config file from {config_path}.",
                reason=str(e),
            ) from e

        return config

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

        param_types = {}
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

            task_config = plugin.get("tasks", {})
            function_tasks = ResourceImportService._build_tasks(
                tasks_config=task_config.get("functions", []),
                param_types=param_types,
                is_function_task=True,
            )
            artifact_tasks = ResourceImportService._build_tasks(
                tasks_config=task_config.get("artifacts", []),
                param_types=param_types,
                is_function_task=False,
            )
            for plugin_file_path in Path(plugin["path"]).rglob("[!.]*.py"):
                filename = str(plugin_file_path.relative_to(plugin["path"]))
                if not ALLOWED_PLUGIN_FILENAME_REGEX.fullmatch(filename):
                    raise ImportFailedError(
                        f"Failed to read plugin file from {filename}",
                        reason="File is not a valid python filename.",
                    )
                try:
                    contents = plugin_file_path.read_text()
                except FileNotFoundError as e:
                    raise ImportFailedError(
                        f"Failed to read plugin file from {plugin_file_path}",
                        reason="File not found.",
                    ) from e
                except Exception as e:
                    raise ImportFailedError(
                        f"Failed to read plugin file from {plugin_file_path}",
                        reason=str(e),
                    ) from e

                self._plugin_id_file_service.create(
                    plugin_id=plugin_dict["plugin"].resource_id,
                    filename=filename,
                    contents=contents,
                    description=None,
                    function_tasks=function_tasks[filename],
                    artifact_tasks=artifact_tasks[filename],
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
        param_types,
        overwrite: bool,
        log: BoundLogger,
    ) -> dict[str, models.EntryPoint]:
        """
        Registers a list of Entrypoints

        Args:
            group_id: The identifier of the group that will manage imported resources
            entrypoints_config: A list of dictionaries describing entrypoints
            plugins: A dictionary mapping Plugin names to the ORM objects
            param_types: A dictionary mapping param type name to the ORM object
            overwrite: Whether imported resources should replace existing resources with
                a conflicting name

        Returns:
            A dictionary mapping newly registered Entrypoint names to ORM object
        """

        param_types = param_types.copy()
        builtin_param_types = self._builtin_plugin_parameter_type_service.get(
            group_id=group_id, error_if_not_found=False, log=log
        )
        param_types.update(
            {param_type.name: param_type for param_type in builtin_param_types}
        )

        entrypoints = {}
        for entrypoint in entrypoints_config:
            if overwrite:
                existing = self._entrypoint_name_service.get(
                    entrypoint["name"], group_id=group_id, log=log
                )
                if existing is not None:
                    self._entrypoint_id_service.delete(
                        entrypoint_id=existing.resource_id
                    )

            try:
                contents = yaml.safe_load(Path(entrypoint["path"]).read_text())
            except FileNotFoundError as e:
                raise ImportFailedError(
                    f"Failed to read entrypoint file from {entrypoint['path']}",
                    reason="File not found.",
                ) from e
            except Exception as e:
                raise ImportFailedError(
                    f"Failed to read entrypoint file from {entrypoint['path']}",
                    reason=str(e),
                ) from e

            params = ResourceImportService._build_entrypoint_params_list(
                entrypoint.get("params", [])
            )

            artifact_params = ResourceImportService._build_artifacts_params_list(
                entrypoint.get("artifact_params", []), param_types
            )
            plugin_ids = [
                plugins[plugin].resource_id for plugin in entrypoint.get("plugins", [])
            ]
            artifact_plugin_ids = [
                plugins[plugin].resource_id
                for plugin in entrypoint.get("artifact_plugins", [])
            ]
            entrypoint_dict = self._entrypoint_service.create(
                name=entrypoint.get("name", Path(entrypoint["path"]).stem),
                description=entrypoint.get("description", None),
                task_graph=yaml.dump(contents.get("graph", None)),
                artifact_graph=yaml.dump(contents.get("artifacts", None)),
                parameters=params,
                artifact_parameters=artifact_params,
                plugin_ids=plugin_ids,
                artifact_plugin_ids=artifact_plugin_ids,
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

    @staticmethod
    def _build_tasks(
        tasks_config: list[dict[str, Any]],
        param_types: dict[str, models.PluginTaskParameterType],
        is_function_task: bool,
    ) -> dict[str, list]:
        """
        Builds dictionaries describing plugin tasks from a configuration file

        Args:
            tasks_config: A list of dictionaries describing plugin tasks
            param_types: A dictionary mapping param type name to the ORM object
            is_function_task: True if the task is a function task, false otherwise

        Returns:
            A dictionary mapping PluginFile name to a list of tasks
        """

        tasks = defaultdict(list)
        for task in tasks_config:
            entry = {
                "name": task["name"],
                "description": task.get("description", None),
                "output_params": ResourceImportService._build_params_list(
                    task["output_params"], param_types, include_required=False
                ),
            }
            if is_function_task:
                entry["input_params"] = ResourceImportService._build_params_list(
                    task["input_params"], param_types, include_required=True
                )
            tasks[task["filename"]].append(entry)
        return tasks

    @staticmethod
    def _build_entrypoint_params_list(
        entrypoint_params: list[dict[str, Any]],
    ):
        """
        Verifies the param types are valid and and constructs a list of dictionaries in
        the structure expected by the Entrypoint ORM object.

        Args:
            params: A list of dictionaries describing task parameters

        Raises:
            ImportFailedError: If a parameter type is not valid
        """
        for param in entrypoint_params:
            if param["type"] not in VALID_ENTRYPOINT_PARAM_TYPES:
                raise ImportFailedError(
                    "Invalid entrypoint parameter type provided.",
                    reason=f"Found '{param['type']}' but must be one of "
                    f"{VALID_ENTRYPOINT_PARAM_TYPES}.",
                )

        return [
            {
                "name": param["name"],
                "parameter_type": param["type"],
                "default_value": param.get("default_value", None),
            }
            for param in entrypoint_params
        ]

    @staticmethod
    def _build_params_list(
        params: list[dict[str, Any]],
        param_types: dict[str, models.PluginTaskParameterType],
        include_required: bool = False,
    ):
        """
        Looks up the plugin parameter types specified in the config and constructs a
        list of dictionaries in the structure expected by the Entrypoint ORM object.

        Args:
            params: A list of dictionaries describing task parameters
            param_types: A dictionary mapping param type name to the ORM object
            include_required: Whether to include the 'required' field

        Raises:
            ImportFailedError: If a plugin parameter type cannot be found
        """
        try:
            return [
                {
                    "name": param["name"],
                    "parameter_type_id": param_types[param["type"]].resource_id,
                    **(
                        {"required": param.get("required", False)}
                        if include_required
                        else {}
                    ),
                }
                for param in params
            ]
        except KeyError as e:
            raise ImportFailedError(
                "Plugin parameter type specified in task parameters not found.",
                reason=f"Parameter type named {e} not does not exist and "
                "is not defined in provided toml config.",
            ) from e

    @staticmethod
    def _build_artifacts_params_list(
        artifact_params: list[dict[str, Any]],
        param_types: dict[str, models.PluginTaskParameterType],
    ):
        """
        Looks up the plugin parameter types specified in the config and constructs a
        list of dictionaries in the structure expected by the Entrypoint ORM object.

        Args:
            artifact_params: A list of dictionaries describing artifact parameters
            param_types: A dictionary mapping param type name to the ORM object

        Raises:
            ImportFailedError: If a plugin parameter type cannot be found
        """
        try:
            return [
                {
                    "name": artifact["name"],
                    "output_params": [
                        {
                            "name": param["name"],
                            "parameter_type_id": param_types[param["type"]].resource_id,
                        }
                        for param in artifact["output_params"]
                    ],
                }
                for artifact in artifact_params
            ]
        except KeyError as e:
            raise ImportFailedError(
                "Plugin parameter type specified in artifact parameters not found.",
                reason=f"Parameter type named {e} not does not exist and "
                "is not defined in provided toml config.",
            ) from e


class DraftCommitService(object):
    """The service methods for commiting a Draft as a new ResourceSnapshot."""

    @inject
    def __init__(
        self,
        resource_service: ResourceService,
        resource_id_service: ResourceIdService,
    ) -> None:
        """Initialize the draft commit service.

        All arguments are provided via dependency injection.
        All arguments are provided via dependency injection.

        Args:
            resource_service: A ResourceService object.
            resource_id_service: A ResourceIdService object.
        """
        self._resource_service = resource_service
        self._resource_id_service = resource_id_service

    def commit_draft(self, draft_id: int, **kwargs) -> dict:
        """Commit the Draft as a new ResourceSnapshot

        Args:
            draft_id: The identifier of the draft.

        Returns:
            The packaged job files returned as a named temporary file.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("commit draft", draft_id=draft_id)

        draft = views.get_draft_resource(draft_id, logger=log)
        if draft is None:
            raise DraftDoesNotExistError(draft_resource_id=draft_id)

        if draft.payload["resource_id"] is None:
            resource_ids = (
                [draft.payload["base_resource_id"]]
                if draft.payload["base_resource_id"] is not None
                else []
            )

            resource_dict = self._resource_service.create(
                *resource_ids,
                resource_type=draft.resource_type,
                resource_data=draft.payload["resource_data"],
                group_id=draft.group_id,
                commit=False,
                log=log,
            )
        else:  # the draft contains modifications to an existing resource
            resource = views.get_resource(draft.payload["resource_id"])
            if resource is None:
                raise EntityDoesNotExistError(
                    EntityTypes.get_from_string(draft.resource_type),
                    resource_id=draft.payload["resource_id"],
                )

            # if the underlying resource was modified since the draft was created,
            # raise an error with the information necessary to reconcile the draft.
            if draft.payload["resource_snapshot_id"] != resource.latest_snapshot_id:
                base_snapshot = views.get_resource_snapshot(
                    draft.resource_type, draft.payload["resource_snapshot_id"]
                )
                if base_snapshot is None:
                    raise EntityDoesNotExistError(
                        EntityTypes.get_from_string(draft.resource_type),
                        snapshot_id=draft.payload["resource_snapshot_id"],
                    )

                curr_snapshot = views.get_resource_snapshot(
                    draft.resource_type, cast(int, resource.latest_snapshot_id)
                )
                if curr_snapshot is None:
                    raise EntityDoesNotExistError(
                        draft.resource_type, resource_id=draft.payload["resource_id"]
                    )

                raise DraftResourceModificationsCommitError(
                    resource_type=EntityTypes.get_from_string(draft.resource_type),
                    resource_id=draft.payload["resource_id"],
                    draft=draft,
                    base_snapshot=base_snapshot,
                    curr_snapshot=curr_snapshot,
                )

            resource_ids = [draft.payload["resource_id"]]
            if draft.payload["base_resource_id"] is not None:
                resource_ids = [draft.payload["base_resource_id"]] + resource_ids

            resource_dict = self._resource_id_service.modify(
                *resource_ids,
                resource_type=draft.resource_type,
                resource_data=draft.payload["resource_data"],
                group_id=draft.group_id,
                commit=False,
                log=log,
            )

        db.session.delete(draft)

        db.session.commit()

        resource_ids = [resource_dict[draft.resource_type].resource_id]
        if draft.payload["base_resource_id"] is not None:
            resource_ids = [draft.payload["base_resource_id"]] + resource_ids
        return {"status": "Success", "id": resource_ids}


@dataclass
class EntryPointParameterDataAdapter(object):
    parameter_type: str
    name: str
    default_value: str | None


@dataclass
class TaskOutputParameterDataAdapter(object):
    parameter_number: int
    name: str
    parameter_type: models.PluginTaskParameterType


@dataclass
class EntryPointArtifactDataAdapter(object):
    name: str
    output_parameters: list[TaskOutputParameterDataAdapter]


@dataclass
class EntryPointDataAdapter(object):
    task_graph: str
    artifact_graph: str
    parameters: list[EntryPointParameterDataAdapter]
    artifact_parameters: list[EntryPointArtifactDataAdapter]


class ValidateEntrypointService(object):
    """The service for validating the inputs to an entrypoint resource."""

    @inject
    def __init__(
        self,
        task_engine_yaml_service: TaskEngineYamlService,
    ) -> None:
        """Initialize the entrypoint service.

        All arguments are provided via dependency injection.

        Args:
            task_engine_yaml_service: A TaskEngineYamlService object.
        """
        self._task_engine_yaml_service = task_engine_yaml_service

    def validate(
        self,
        group_id: int,
        task_graph: str,
        artifact_graph: str,
        plugin_snapshot_ids: list[int],
        entrypoint_parameters: list[dict[str, Any]],
        entrypoint_artifacts: list[dict[str, Any]],
        **kwargs,
    ) -> dict[str, Any]:
        """Validate the proposed inputs to an entrypoint resource.

        Args:
            group_id: The ID of the group validating the entrypoint resource.
            task_graph: The proposed task graph for the entrypoint resource.
            artifact_graph: The proposed artifact graph for the entrypoint resource.
            plugin_snapshot_ids: A list of identifiers for the plugin snapshots that
                will be attached to the Entrypoint resource.
            entrypoint_parameters: The proposed list of parameters for the entrypoint
                resource.
            entrypoint_artifacts: The proposed list of Artifacts for the entrypoint
                resource.

        Returns:
            A dictionary containing the validation result. The dictionary contains two
            keys:
                - "schema_valid": A boolean indicating whether the schema is valid.
                - "schema_issues": A list of issues found in the schema, if any.

        Raises:
            DioptraError: If two or more plugin_snapshot_ids point at the same
                resource_id.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug(
            "Validating input for an entrypoint resource",
            task_graph=task_graph,
            artifact_graph=artifact_graph,
            plugin_ids=plugin_snapshot_ids,
            entrypoint_parameters=entrypoint_parameters,
            entrypoint_artifacts=entrypoint_artifacts,
        )

        type_ids = [
            parameter["parameter_type_id"]
            for artifact in entrypoint_artifacts
            for parameter in artifact["output_parameters"]
        ]
        id_type_map = get_plugin_task_parameter_types_by_id(ids=type_ids, log=log)
        entrypoint = EntryPointDataAdapter(
            task_graph=task_graph,
            artifact_graph=artifact_graph,
            parameters=[
                EntryPointParameterDataAdapter(
                    parameter_type=param["parameter_type"],
                    name=param["name"],
                    default_value=param["default_value"],
                )
                for param in entrypoint_parameters
            ],
            artifact_parameters=[
                EntryPointArtifactDataAdapter(
                    name=artifact["name"],
                    output_parameters=[
                        TaskOutputParameterDataAdapter(
                            name=param["name"],
                            parameter_number=p,
                            parameter_type=id_type_map[param["parameter_type_id"]],
                        )
                        for p, param in enumerate(entrypoint_parameters)
                    ],
                )
                for artifact in entrypoint_artifacts
            ],
        )
        plugin_parameter_types = views.get_plugin_parameter_types(
            group_id=group_id, logger=log
        )
        plugin_plugin_files = views.get_plugin_plugin_files_from_plugin_snapshot_ids(
            plugin_snapshot_ids=plugin_snapshot_ids, logger=log
        )
        try:
            task_engine_dict = self._task_engine_yaml_service.build_dict(
                entry_point=entrypoint,  # pyright: ignore
                plugin_plugin_files=plugin_plugin_files,  # pyright: ignore
                plugin_parameter_types=plugin_parameter_types,  # pyright: ignore
                logger=log,
            )
        except InvalidYamlError as e:
            return {
                "schema_valid": False,
                "schema_issues": [
                    ValidationIssue(
                        type_=IssueType.SYNTAX,
                        severity=IssueSeverity.ERROR,
                        message=str(e),
                    )
                ],
            }

        issues = self._task_engine_yaml_service.validate(
            task_engine_dict=task_engine_dict
        )

        if issues:
            return {"schema_valid": False, "schema_issues": issues}

        return {"schema_valid": True, "schema_issues": []}
