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
from typing import IO, Any, Callable, Final, Generator, cast

import jsonschema
import structlog
import tomli as toml
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
from dioptra.restapi.v1.utils import PluginParameterTypeDict
from dioptra.sdk.utilities.paths import set_cwd
from dioptra.task_engine.issues import IssueSeverity, IssueType, ValidationIssue

from .lib import views
from .lib.clone_git_repository import clone_git_repository
from .lib.package_job_files import package_job_files
from .schema import (
    FileTypes,
    ResourceImportResolveNameConflictsStrategy,
    ResourceImportSourceTypes,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()

RESOURCE_TYPE: Final[str] = "workflow"

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


class JobFilesDownloadService(object):
    """The service methods for packaging job files for download."""

    @inject
    def __init__(
        self,
        task_engine_yaml_service: TaskEngineYamlService,
    ) -> None:
        """Initialize the job files download service.

        All arguments are provided via dependency injection.

        Args:
            task_engine_yaml_service: A TaskEngineYamlService object.
        """
        self._task_engine_yaml_service = task_engine_yaml_service

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

        task_engine_yaml = self._task_engine_yaml_service.build_yaml(
            entry_point=entry_point,  # pyright: ignore
            plugin_plugin_files=entry_point_plugin_files,  # pyright: ignore
            plugin_parameter_types=plugin_parameter_types,  # pyright: ignore
            logger=log,
        )

        return package_job_files(
            job_id=job_id,
            experiment=experiment,
            entry_point_name=entry_point.name,
            task_engine_yaml=task_engine_yaml,
            entry_point_plugin_files=entry_point_plugin_files,
            job_parameter_values=job_parameter_values,
            file_type=file_type,
            logger=log,
        )


class SignatureAnalysisService(object):
    """The service methods for performing signature analysis on a file."""

    @inject
    def __init__(
        self,
        plugin_parameter_type_service: PluginParameterTypeService,
    ) -> None:
        """Initialize the job files download service.

        All arguments are provided via dependency injection.

        Args:
            plugin_parameter_type_service: A PluginParameterTypeService object.
        """
        self._plugin_parameter_type_service = plugin_parameter_type_service

    def post(
        self, group_id: int, python_code: str, **kwargs
    ) -> dict[str, list[dict[str, Any]]]:
        """Perform signature analysis on a file.

        Args:
            filename: The name of the file.
            python_code: The contents of the file.

        Returns:
            A dictionary containing the signature analysis.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.info(
            "Performing signature analysis",
            python_source=python_code,
        )
        endpoint_analyses = [
            _create_endpoint_analysis_dict(
                group_id, signature, self._plugin_parameter_type_service, log
            )
            for signature in get_plugin_signatures(python_source=python_code)
        ]
        return {"tasks": endpoint_analyses}


def _create_endpoint_analysis_dict(
    group_id: int,
    signature: dict[str, Any],
    plugin_parameter_type_service: PluginParameterTypeService,
    log: BoundLogger,
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
                "proposed_types": match_name_and_structure(
                    suggested_type["suggestion"],
                    suggested_type["structure"],
                    group_id=group_id,
                    plugin_parameter_type_service=plugin_parameter_type_service,
                    log=log,
                ),
            }
            for suggested_type in signature["suggested_types"]
        ],
    }


def match_name_and_structure(
    type_name_suggestion: str,
    type_name_structure: dict | None,
    group_id: int,
    plugin_parameter_type_service: PluginParameterTypeService,
    log: BoundLogger,
):
    log.debug(f"Matching name for expanded_a: {type_name_suggestion}")
    expanded_a, ids_a = _expand_string_or_dict(
        type_name_suggestion, group_id, plugin_parameter_type_service, log=log
    )
    log.debug(f"Matching structure for expanded_b: {type_name_structure}")
    expanded_b, ids_b = _expand_string_or_dict(
        type_name_structure, group_id, plugin_parameter_type_service, log=log
    )
    log.debug(f"Expanded type from RESTAPI: {expanded_a}")
    log.debug(f"Expanded type derived from annotation: {expanded_b}")

    if expanded_a == expanded_b:
        return ids_a
    return []


def _get_registered_type_expanded_structure(
    type_name_suggestion: str,
    group_id: int,
    plugin_parameter_type_service: PluginParameterTypeService,
    log: BoundLogger,
) -> tuple[dict[str, Any] | None, list[int]]:
    """This function looks up the fully expanded type structure given
    a parameter
    """

    expanded_structure = None
    type_ids = []

    log.debug(f"Looking up type for {type_name_suggestion} in RESTAPI.")

    # using our GET query language to ensure that we get an exact match
    # on the type name. there should be one result because type
    # names are unique within a group.

    for types, _num_types in _get_all_from_paged_service(
        plugin_parameter_type_service.get,
        group_id=group_id,
        search_string=f'"{type_name_suggestion}"',
        sort_by_string="name",
        descending=True,
    ):
        found_type: PluginParameterTypeDict
        for found_type in types:
            if found_type["plugin_task_parameter_type"].name == type_name_suggestion:
                log.debug(
                    f"Structure associated with type "
                    f"{type_name_suggestion} in RESTAPI: "
                    f"{found_type['plugin_task_parameter_type'].structure}"
                )

                if isinstance(found_type["plugin_task_parameter_type"].structure, dict):
                    expanded_structure = _expand_structure(
                        structure=found_type["plugin_task_parameter_type"].structure,
                        group_id=group_id,
                        plugin_parameter_type_service=plugin_parameter_type_service,
                        log=log,
                    )
                    type_ids.append(
                        found_type["plugin_task_parameter_type"].resource_id
                    )
                if found_type["plugin_task_parameter_type"].structure is None:
                    expanded_structure = None
                    type_ids.append(
                        found_type["plugin_task_parameter_type"].resource_id
                    )

    return expanded_structure, type_ids


def _get_all_from_paged_service(
    fn: Callable[..., tuple[list[Any], int]], per_page: int = 10, **kwargs
) -> Generator[tuple[list[Any], int], None, None]:
    current_page = 0
    max_pages = 1

    while current_page < max_pages:
        things, num_things = fn(
            page_index=current_page * per_page, page_length=per_page, **kwargs
        )

        current_page += 1
        max_pages = num_things // per_page + 1

        yield things, num_things


def _expand_structure(
    structure: dict[str, Any],
    group_id: int,
    plugin_parameter_type_service: PluginParameterTypeService,
    log: BoundLogger,
) -> dict[str, Any]:
    """Takes a dictionary structure, and looks up all the named types
    in it and expands if they have a non-null type structure.
    """
    expanded = {}
    log.debug(f"Request to expand structure: {structure}")
    for key in structure:
        types = structure[key]

        new_value: list | dict | str | None = None

        if key == "union" or key == "tuple":
            log.debug(f"Calling expand on union/tuple: {types}")

            new_value = [
                _expand_string_or_dict(
                    t,
                    group_id=group_id,
                    plugin_parameter_type_service=plugin_parameter_type_service,
                    log=log,
                )[0]
                for t in types
            ]

        if key == "mapping":
            mapping_key_type = types[0]
            mapping_value_type = types[1]
            log.debug(f"Calling expand on mapping: {mapping_value_type}")

            mapping_value_type, ids = _expand_string_or_dict(
                mapping_value_type,
                group_id=group_id,
                plugin_parameter_type_service=plugin_parameter_type_service,
                log=log,
            )
            new_value = [mapping_key_type, mapping_value_type]

        if key == "list":
            # types should just be a string here
            list_of = types
            log.debug(f"Calling expand on list: {list_of}")

            new_value, ids = _expand_string_or_dict(
                list_of,
                group_id=group_id,
                plugin_parameter_type_service=plugin_parameter_type_service,
                log=log,
            )

        log.debug(f"Added to dictionary - {key}:{new_value}")
        expanded[key] = new_value

    log.debug(f"Finished expanding structure - {expanded}")
    return expanded


def _expand_string_or_dict(
    to_expand: str | dict | None,
    group_id: int,
    plugin_parameter_type_service: PluginParameterTypeService,
    log: BoundLogger,
) -> tuple[str | dict | None | list, list[int]]:

    if to_expand is None:
        return None, []

    log.debug(f"Expanding a string or dictionary: {to_expand}")

    if isinstance(to_expand, dict):
        return (
            _expand_structure(
                structure=to_expand,
                group_id=group_id,
                plugin_parameter_type_service=plugin_parameter_type_service,
                log=log,
            ),
            [],
        )
    elif isinstance(to_expand, str):
        lookup_structure, ids = _get_registered_type_expanded_structure(
            type_name_suggestion=to_expand,
            group_id=group_id,
            plugin_parameter_type_service=plugin_parameter_type_service,
            log=log,
        )
        return lookup_structure, ids


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
                    group_id, config.get("entrypoints", []), plugins, overwrite, log=log
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
            try:
                verify_filename_is_safe(file.filename)
            except ValueError as e:
                raise ImportFailedError(
                    "Failed to read uploaded files", reason=str(e)
                ) from e

            # The _sort_by_filename sorting key already checks whether filename is None,
            # so here we can just assert that it's not None to make mypy happy.
            assert file.filename is not None
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
                    plugin_dict["plugin"].resource_id,
                    filename=filename,
                    contents=contents,
                    description=None,
                    tasks=tasks[filename],
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

            try:
                contents = Path(entrypoint["path"]).read_text()
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

            for param in entrypoint.get("params", []):
                if param["type"] not in VALID_ENTRYPOINT_PARAM_TYPES:
                    raise ImportFailedError(
                        "Invalid entrypoint parameter type provided.",
                        reason=f"Found '{param['type']}' but must be one of "
                        f"{VALID_ENTRYPOINT_PARAM_TYPES}.",
                    )

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
            try:
                input_params = [
                    {
                        "name": param["name"],
                        "parameter_type_id": param_types[param["type"]].resource_id,
                        "required": param.get("required", False),
                    }
                    for param in task["input_params"]
                ]
            except KeyError as e:
                raise ImportFailedError(
                    "Plugin task input parameter type not found.",
                    reason=f"Parameter type named {e} not does not exist and "
                    "is not defined in provided toml config.",
                ) from e

            try:
                output_params = [
                    {
                        "name": param["name"],
                        "parameter_type_id": param_types[param["type"]].resource_id,
                    }
                    for param in task["output_params"]
                ]
            except KeyError as e:
                raise ImportFailedError(
                    "Plugin task output parameter type not found.",
                    reason=f"Parameter type named {e} not does not exist and "
                    "is not defined in provided toml config.",
                ) from e

            tasks[task["filename"]].append(
                {
                    "name": task["name"],
                    "description": task.get("description", None),
                    "input_params": input_params,
                    "output_params": output_params,
                }
            )
        return tasks


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
                    draft.resource_type, resource_id=draft.payload["resource_id"]
                )

            # if the underlying resource was modified since the draft was created,
            # raise an error with the information necessary to reconcile the draft.
            if draft.payload["resource_snapshot_id"] != resource.latest_snapshot_id:
                base_snapshot = views.get_resource_snapshot(
                    draft.resource_type, draft.payload["resource_snapshot_id"]
                )
                if base_snapshot is None:
                    raise EntityDoesNotExistError(
                        draft.resource_type,
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
                    resource_type=draft.resource_type,
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
class EntryPointDataAdapter(object):
    task_graph: str
    parameters: list[EntryPointParameterDataAdapter]


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
        plugin_snapshot_ids: list[int],
        entrypoint_parameters: list[dict[str, Any]],
        **kwargs,
    ) -> dict[str, Any]:
        """Validate the proposed inputs to an entrypoint resource.

        Args:
            group_id: The ID of the group validating the entrypoint resource.
            task_graph: The proposed task graph for the entrypoint resource.
            plugin_snapshot_ids: A list of identifiers for the plugin snapshots that
                will be attached to the Entrypoint resource.
            entrypoint_parameters: The proposed list of parameters for the entrypoint
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
            plugin_ids=plugin_snapshot_ids,
            entrypoint_parameters=entrypoint_parameters,
        )

        entrypoint = EntryPointDataAdapter(
            task_graph=task_graph,
            parameters=[
                EntryPointParameterDataAdapter(
                    parameter_type=param["parameter_type"],
                    name=param["name"],
                    default_value=param["default_value"],
                )
                for param in entrypoint_parameters
            ],
        )
        plugin_plugin_files = views.get_plugin_plugin_files_from_plugin_snapshot_ids(
            plugin_snapshot_ids=plugin_snapshot_ids, logger=log
        )
        plugin_parameter_types = views.get_plugin_parameter_types(
            group_id=group_id, logger=log
        )
        try:
            task_engine_dict = self._task_engine_yaml_service.build_dict(
                entry_point=entrypoint,
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
