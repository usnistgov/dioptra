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
"""Utility functions to help in building responses from ORM models"""
from typing import Any, Callable, Final, TypedDict, cast
from urllib.parse import urlencode, urlunparse

from marshmallow import Schema

from dioptra.restapi.db import models
from dioptra.restapi.routes import V1_ROOT

ARTIFACTS: Final[str] = "artifacts"
ENTRYPOINTS: Final[str] = "entrypoints"
EXPERIMENTS: Final[str] = "experiments"
GROUPS: Final[str] = "groups"
MODELS: Final[str] = "models"
PLUGINS: Final[str] = "plugins"
PLUGIN_FILES: Final[str] = "files"
PLUGIN_PARAMETER_TYPES: Final[str] = "pluginParameterTypes"
QUEUES: Final[str] = "queues"
TAGS: Final[str] = "tags"
USERS: Final[str] = "users"

# -- Typed Dictionaries --------------------------------------------------------


class GroupRefDict(TypedDict):
    id: int
    name: str
    url: str


class PluginParameterTypeRefDict(TypedDict):
    id: int
    group: GroupRefDict
    url: str
    name: str


class PluginTaskInputParameterDict(TypedDict):
    name: str
    required: bool
    parameter_type: PluginParameterTypeRefDict


class PluginTaskOutputParameterDict(TypedDict):
    name: str
    parameter_type: PluginParameterTypeRefDict


class PluginTaskDict(TypedDict):
    name: str
    input_params: list[PluginTaskInputParameterDict]
    output_params: list[PluginTaskOutputParameterDict]


class PluginWithFilesDict(TypedDict):
    plugin: models.Plugin
    plugin_files: list[models.PluginFile]
    has_draft: bool | None


class PluginFileDict(TypedDict):
    plugin_file: models.PluginFile
    plugin: models.Plugin
    has_draft: bool | None


class ExperimentDict(TypedDict):
    experiment: models.Experiment
    entrypoints: list[models.EntryPoint]
    queue: models.Queue | None
    has_draft: bool | None


class PluginParameterTypeDict(TypedDict):
    plugin_task_parameter_type: models.PluginTaskParameterType
    has_draft: bool | None


class ArtifactDict(TypedDict):
    artifact: models.Artifact
    has_draft: bool | None


class QueueDict(TypedDict):
    queue: models.Queue
    has_draft: bool | None


class EntrypointDict(TypedDict):
    entry_point: models.EntryPoint
    queues: list[models.Queue]
    has_draft: bool | None


class JobDict(TypedDict):
    job: models.Job
    artifacts: list[models.Artifact]
    has_draft: bool | None


class ModelWithVersionDict(TypedDict):
    ml_model: models.MlModel
    version: models.MlModelVersion | None
    has_draft: bool | None


# -- Ref Types -----------------------------------------------------------------


def build_experiment_ref(experiment: models.Experiment) -> dict[str, Any]:
    """Build an ExperimentRef dictionary.

    Args:
        experiment: The experiment object to convert into an ExperimentRef dictionary.

    Returns:
        The ExperimentRef dictionary.
    """
    return {
        "id": experiment.resource_id,
        "name": experiment.name,
        "group": build_group_ref(experiment.resource.owner),
        "url": build_url(f"{EXPERIMENTS}/{experiment.resource_id}"),
    }


def build_experiment_snapshot_ref(experiment: models.Experiment) -> dict[str, Any]:
    """Build an ExperimentSnapshotRef dictionary.

    Args:
        experiment: The experiment object to convert into an ExperimentSnapshotRef
            dictionary.

    Returns:
        The ExperimentSnapshotRef dictionary.
    """
    return {
        "snapshot_id": experiment.resource_snapshot_id,
        "name": experiment.name,
        "group": build_group_ref(experiment.resource.owner),
        "url": build_url(
            f"{EXPERIMENTS}/{experiment.resource_id}/snapshots/"
            f"{experiment.resource_snapshot_id}"
        ),
    }


def build_user_ref(user: models.User) -> dict[str, Any]:
    """Build a UserRef dictionary.

    Args:
        user: The User object to convert into a UserRef dictionary.

    Returns:
        The UserRef dictionary.
    """
    return {
        "id": user.user_id,
        "username": user.username,
        "url": build_url(f"{USERS}/{user.user_id}"),
    }


def build_group_ref(group: models.Group) -> GroupRefDict:
    """Build a GroupRef dictionary.

    Args:
        group: The Group object to convert into a GroupRef dictionary.

    Returns:
        The GroupRef dictionary.
    """
    return {
        "id": group.group_id,
        "name": group.name,
        "url": build_url(f"{GROUPS}/{group.group_id}"),
    }


def build_tag_ref(tag: models.Tag) -> dict[str, Any]:
    """Build a TagRef dictionary.

    Args:
        tag: The Tag object to convert into a TagRef dictionary.

    Returns:
        The TagRef dictionary.
    """
    return {
        "id": tag.tag_id,
        "name": tag.name,
        "group": build_group_ref(tag.owner),
        "url": build_url(f"{TAGS}/{tag.tag_id}"),
    }


def build_tag_ref_list(tags: list[models.Tag]) -> list[dict[str, Any]]:
    """Build a TagRef list.

    Args:
        tag: The list of Tag objects to convert into a TagRef list.

    Returns:
        The TagRef list.
    """
    return [build_tag_ref(tag) for tag in tags]


def build_plugin_ref(plugin: models.Plugin) -> dict[str, Any]:
    """Build a PluginRef dictionary.

    Args:
        plugin: The Plugin object to convert into a PluginRef dictionary.

    Returns:
        The PluginRef dictionary.
    """
    return {
        "id": plugin.resource_id,
        "name": plugin.name,
        "group": build_group_ref(plugin.resource.owner),
        "url": build_url(f"{PLUGINS}/{plugin.resource_id}"),
    }


def build_entrypoint_plugin(plugin_with_files: PluginWithFilesDict) -> dict[str, Any]:
    """Build a PluginFileRef dictionary.

    Args:
        entrypoint: The Entrypoint object
        plugin: The Plugin object to convert into a PluginRef dictionary.

    Returns:
        The PluginFileRef dictionary.
    """
    plugin = plugin_with_files["plugin"]
    plugin_files = plugin_with_files["plugin_files"]

    return {
        "id": plugin.resource_id,
        "snapshot_id": plugin.resource_snapshot_id,
        "name": plugin.name,
        "url": build_url(
            f"{PLUGINS}/{plugin.resource_id}/snapshots/{plugin.resource_snapshot_id}"
        ),
        "files": [
            {
                "id": plugin_file.resource_id,
                "snapshot_id": plugin_file.resource_snapshot_id,
                "filename": plugin_file.filename,
                "url": build_url(
                    f"{PLUGINS}/{plugin.resource_id}/{PLUGIN_FILES}/{plugin_file.resource_id}/"
                    f"snapshots/{plugin_file.resource_snapshot_id}"
                ),
            }
            for plugin_file in plugin_files
        ],
    }


def build_plugin_snapshot_ref(plugin: models.Plugin) -> dict[str, Any]:
    """Build a PluginSnapshotRef dictionary.

    Args:
        plugin: The PluginFile object to convert into a PluginSnapshotRef dictionary.

    Returns:
        The PluginSnapshotRef dictionary.
    """
    return {
        "snapshot_id": plugin.resource_snapshot_id,
        "name": plugin.name,
        "group": build_group_ref(plugin.resource.owner),
        "url": build_url(
            f"{PLUGINS}/{plugin.resource_id}/snapshots/{plugin.resource_snapshot_id}"
        ),
    }


def build_plugin_file_ref(plugin_file: models.PluginFile) -> dict[str, Any]:
    """Build a PluginRef dictionary.

    Args:
        queue: The Plugin object to convert into a PluginRef dictionary.

    Returns:
        The PluginRef dictionary.
    """
    plugin_id = plugin_file.plugin_id
    return {
        "id": plugin_file.resource_id,
        "plugin": plugin_id,
        "filename": plugin_file.filename,
        "group": build_group_ref(plugin_file.resource.owner),
        "url": build_url(
            f"{PLUGINS}/{plugin_id}/{PLUGIN_FILES}/{plugin_file.resource_id}"
        ),
    }


def build_entrypoint_ref(entrypoint: models.EntryPoint) -> dict[str, Any]:
    """Build a EntrypointRef dictionary.

    Args:
        entrypoint: The Entrypoint object to convert into a EntrypointRef dictionary.

    Returns:
        The EntrypointRef dictionary.
    """
    return {
        "id": entrypoint.resource_id,
        "name": entrypoint.name,
        "group": build_group_ref(entrypoint.resource.owner),
        "url": build_url(f"{ENTRYPOINTS}/{entrypoint.resource_id}"),
    }


def build_entrypoint_snapshot_ref(entrypoint: models.EntryPoint) -> dict[str, Any]:
    """Build a EntrypointSnapshotRef dictionary.

    Args:
        queue: The Entrypoint object to convert into a EntrypointSnapshotRef dictionary.

    Returns:
        The EntrypointSnapshotRef dictionary.
    """
    return {
        "snapshot_id": entrypoint.resource_snapshot_id,
        "name": entrypoint.name,
        "group": build_group_ref(entrypoint.resource.owner),
        "url": build_url(
            f"{ENTRYPOINTS}/{entrypoint.resource_id}"
            f"/snapshots/{entrypoint.resource_snapshot_id}"
        ),
    }


def build_model_ref(model: models.MlModel) -> dict[str, Any]:
    """Build a MlModel dictionary.

    Args:
        model: The Model object to convert into a MlModel dictionary.

    Returns:
        The MlModel dictionary.
    """
    return {
        "id": model.resource_id,
        "name": model.name,
        "group": build_group_ref(model.resource.owner),
        "url": f"{MODELS}/{model.resource_id}",
    }


def build_queue_ref(queue: models.Queue) -> dict[str, Any]:
    """Build a QueueRef dictionary.

    Args:
        queue: The Queue object to convert into a QueueRef dictionary.

    Returns:
        The QueueRef dictionary.
    """
    return {
        "id": queue.resource_id,
        "name": queue.name,
        "group": build_group_ref(queue.resource.owner),
        "url": build_url(f"{QUEUES}/{queue.resource_id}"),
    }


def build_queue_snapshot_ref(queue: models.Queue) -> dict[str, Any]:
    """Build a QueueSnapshotRef dictionary.

    Args:
        queue: The Queue object to convert into a QueueSnapshotRef dictionary.

    Returns:
        The QueueSnapshotRef dictionary.
    """
    return {
        "snapshot_id": queue.resource_snapshot_id,
        "name": queue.name,
        "group": build_group_ref(queue.resource.owner),
        "url": build_url(
            f"{QUEUES}/{queue.resource_id}/snapshots/{queue.resource_snapshot_id}"
        ),
    }


def build_plugin_parameter_type_ref(
    plugin_param_type: models.PluginTaskParameterType,
) -> PluginParameterTypeRefDict:
    """Build a PluginParameterTypeRef dictionary.

    Args:
        plugin_param_type: The Plugin Parameter Type object to convert into a
            PluginParameterTypeRef dictionary.

    Returns:
        The PluginParameterTypeRef dictionary.
    """
    return {
        "id": plugin_param_type.resource_id,
        "name": plugin_param_type.name,
        "group": build_group_ref(plugin_param_type.resource.owner),
        "url": build_url(f"{PLUGIN_PARAMETER_TYPES}/{plugin_param_type.resource_id}"),
    }


def build_artifact_ref(artifact: models.Artifact) -> dict[str, Any]:
    """Build a ArtifactRef dictionary.

    Args:
        artifact: The Artifact object to convert into a ArtifactRef dictionary.

    Returns:
        The ArtifactRef dictionary.
    """
    return {
        "id": artifact.resource_id,
        "artifact_uri": artifact.uri,
        "group": build_group_ref(artifact.resource.owner),
        "url": build_url(f"{ARTIFACTS}/{artifact.resource_id}"),
    }


# -- Full Types ----------------------------------------------------------------


def build_user(user: models.User) -> dict[str, Any]:
    """Build a User response dictionary.

    Args:
        user: The User object to convert into a User response dictionary.

    Returns:
        The User response dictionary.
    """
    return {
        "id": user.user_id,
        "username": user.username,
        "email": user.email_address,
    }


def build_current_user(user: models.User) -> dict[str, Any]:
    """Build a response dictionary for the current user.

    Args:
        user: The User object representing the current user to convert into a response
            dictionary.

    Returns:
        The response dictionary for the current user.
    """
    return {
        "id": user.user_id,
        "username": user.username,
        "email": user.email_address,
        "groups": [
            build_group_ref(membership.group) for membership in user.group_memberships
        ],
        "created_on": user.created_on,
        "last_modified_on": user.last_modified_on,
        "last_login_on": user.last_login_on,
        "password_expires_on": user.password_expire_on,
    }


def build_group(group: models.Group) -> dict[str, Any]:
    """Build a Group response dictionary.

    Args:
        group: The Group object to convert into a Group response dictionary.

    Returns:
        The Group response dictionary.
    """
    members: dict[int, dict[str, Any]] = {}

    for member in group.members:
        members[member.user_id] = {
            "user": build_user_ref(member.user),
            "group": build_group_ref(group),
            "permissions": {
                "read": member.read,
                "write": member.write,
                "share_read": member.share_read,
                "share_write": member.share_write,
                "owner": False,
                "admin": False,
            },
        }

    for manager in group.managers:
        members[manager.user_id]["permissions"]["owner"] = manager.owner
        members[manager.user_id]["permissions"]["admin"] = manager.admin

    return {
        "id": group.group_id,
        "name": group.name,
        "user": build_user_ref(group.creator),
        "members": list(members.values()),
        "created_on": group.created_on,
        "last_modified_on": group.last_modified_on,
    }


def build_experiment(experiment_dict: ExperimentDict) -> dict[str, Any]:
    """Build an Experiment response dictionary.

    Args:
        experiment: The experiment object to convert into an Experiment response
            dictionary.

    Returns:
        The Experiment response dictionary.
    """
    experiment = experiment_dict["experiment"]
    entrypoints = experiment_dict.get("entrypoints", None)
    has_draft = experiment_dict.get("has_draft", None)

    data = {
        "id": experiment.resource_id,
        "snapshot_id": experiment.resource_snapshot_id,
        "name": experiment.name,
        "description": experiment.description,
        "user": build_user_ref(experiment.creator),
        "group": build_group_ref(experiment.resource.owner),
        "created_on": experiment.resource.created_on,
        "last_modified_on": experiment.resource.last_modified_on,
        "latest_snapshot": experiment.resource.latest_snapshot_id
        == experiment.resource_snapshot_id,
        "tags": [build_tag_ref(tag) for tag in experiment.tags],
    }

    if entrypoints is not None:
        data["entrypoints"] = [
            build_entrypoint_ref(entrypoint) for entrypoint in entrypoints
        ]

    if has_draft is not None:
        data["has_draft"] = has_draft

    return data


def build_tag(tag: models.Tag) -> dict[str, Any]:
    """Build a Tag response dictionary.

    Args:
        queue: The Tag object to convert into a Tag response dictionary.

    Returns:
        The Tag response dictionary.
    """
    return {
        "id": tag.tag_id,
        "name": tag.name,
        "user": build_user_ref(tag.creator),
        "group": build_group_ref(tag.owner),
        "created_on": tag.created_on,
        "last_modified_on": tag.last_modified_on,
    }


def build_entrypoint(entrypoint_dict: EntrypointDict) -> dict[str, Any]:
    entrypoint = entrypoint_dict["entry_point"]
    queues = entrypoint_dict.get("queues", None)
    has_draft = entrypoint_dict.get("has_draft", None)

    plugins_dict = {
        entry_point_plugin_file.plugin.resource_id: PluginWithFilesDict(
            plugin=entry_point_plugin_file.plugin, plugin_files=[], has_draft=False
        )
        for entry_point_plugin_file in entrypoint.entry_point_plugin_files
    }
    for entry_point_plugin_file in entrypoint.entry_point_plugin_files:
        resource_id = entry_point_plugin_file.plugin.resource_id
        plugin_file = entry_point_plugin_file.plugin_file
        plugins_dict[resource_id]["plugin_files"].append(plugin_file)
    plugins = list(plugins_dict.values())

    data = {
        "id": entrypoint.resource_id,
        "snapshot_id": entrypoint.resource_snapshot_id,
        "name": entrypoint.name,
        "description": entrypoint.description,
        "task_graph": entrypoint.task_graph,
        "user": build_user_ref(entrypoint.creator),
        "group": build_group_ref(entrypoint.resource.owner),
        "created_on": entrypoint.resource.created_on,
        "last_modified_on": entrypoint.resource.last_modified_on,
        "latest_snapshot": entrypoint.resource.latest_snapshot_id
        == entrypoint.resource_snapshot_id,
        "tags": [build_tag_ref(tag) for tag in entrypoint.tags],
        "parameters": [
            {
                "name": param.name,
                "default_value": param.default_value,
                "parameter_type": param.parameter_type,
            }
            for param in entrypoint.parameters
        ],
        "plugins": [build_entrypoint_plugin(plugin) for plugin in plugins],
    }

    if queues is not None:
        data["queues"] = [build_queue_ref(queue) for queue in queues]

    if has_draft is not None:
        data["has_draft"] = has_draft

    return data


def build_job(job_dict: JobDict) -> dict[str, Any]:
    """Build a Job response dictionary.

    Args:
        job: The Job object to convert into a job response dictionary.

    Returns:
        The Job response dictionary.
    """
    job = job_dict["job"]
    artifacts = job_dict.get("artifacts", None)
    has_draft = job_dict.get("has_draft", None)

    data = {
        "id": job.resource_id,
        "snapshot_id": job.resource_snapshot_id,
        "description": job.description,
        "status": job.status,
        "values": {
            param.parameter.name: param.value
            for param in job.entry_point_job.entry_point_parameter_values
        },
        "timeout": job.timeout,
        "user": build_user_ref(job.creator),
        "group": build_group_ref(job.resource.owner),
        "queue": build_queue_snapshot_ref(job.queue_job.queue),
        "experiment": build_experiment_snapshot_ref(job.experiment_job.experiment),
        "entrypoint": build_entrypoint_snapshot_ref(job.entry_point_job.entry_point),
        "created_on": job.resource.created_on,
        "last_modified_on": job.resource.last_modified_on,
        "latest_snapshot": job.resource.latest_snapshot_id == job.resource_snapshot_id,
        "tags": [build_tag_ref(tag) for tag in job.tags],
    }

    if artifacts is not None:
        data["artifacts"] = [build_artifact_ref(artifact) for artifact in artifacts]

    if has_draft is not None:
        data["has_draft"] = has_draft

    return data


def build_model(model_dict: ModelWithVersionDict) -> dict[str, Any]:
    """Build a Model response dictionary for the latest version.

    Args:
        model: The Model object to convert into a Model response dictionary.

    Returns:
        The Model response dictionary.
    """
    model = model_dict["ml_model"]
    version = model_dict.get("version", None)
    has_draft = model_dict.get("has_draft", None)

    latest_version = build_model_version(model_dict) if version is not None else None
    latest_version_number = version.version_number if version is not None else 0

    # WARNING: this assumes versions cannot be deleted and that no details of
    # the version # are needed in constructing the ref type. If either of these
    # assumptions change, the service and controller layers will need to be
    # updated to return the MlModelVersion # ORM objects.
    versions = [
        {
            "version_number": version_number,
            "url": build_url(f"{MODELS}/{model.resource_id}/versions/{version_number}"),
        }
        for version_number in range(1, latest_version_number + 1)
    ]

    data = {
        "id": model.resource_id,
        "snapshot_id": model.resource_snapshot_id,
        "name": model.name,
        "description": model.description,
        "user": build_user_ref(model.creator),
        "group": build_group_ref(model.resource.owner),
        "created_on": model.resource.created_on,
        "last_modified_on": model.resource.last_modified_on,
        "latest_snapshot": model.resource.latest_snapshot_id
        == model.resource_snapshot_id,
        "tags": [build_tag_ref(tag) for tag in model.tags],
        "latest_version": latest_version,
        "versions": versions,
    }

    if has_draft is not None:
        data["has_draft"] = has_draft

    return data


def build_model_version(model_dict: ModelWithVersionDict) -> dict[str, Any]:
    """Build a ModelVersion response dictionary.

    Args:
        model: The ModelVersion object to convert into a ModelVersion response
            dictionary.

    Returns:
        The ModelVersion response dictionary.
    """
    model = model_dict["ml_model"]
    version = cast(models.MlModelVersion, model_dict["version"])
    return {
        "model": build_model_ref(model),
        "description": version.description,
        "version_number": version.version_number,
        "artifact": build_artifact_ref(version.artifact),
        "created_on": version.resource.created_on,
    }


def build_artifact(artifact_dict: ArtifactDict) -> dict[str, Any]:
    artifact = artifact_dict["artifact"]
    has_draft = artifact_dict.get("has_draft")

    data = {
        "id": artifact.resource_id,
        "snapshot_id": artifact.resource_snapshot_id,
        "uri": artifact.uri,
        "description": artifact.description,
        "user": build_user_ref(artifact.creator),
        "group": build_group_ref(artifact.resource.owner),
        "created_on": artifact.resource.created_on,
        "last_modified_on": artifact.resource.last_modified_on,
        "latest_snapshot": artifact.resource.latest_snapshot_id
        == artifact.resource_snapshot_id,
        "tags": [build_tag_ref(tag) for tag in artifact.tags],
    }

    if has_draft is not None:
        data["has_draft"] = has_draft

    return data


def build_queue(queue_dict: QueueDict) -> dict[str, Any]:
    """Build a Queue response dictionary.

    Args:
        queue: The Queue object to convert into a Queue response dictionary.

    Returns:
        The Queue response dictionary.
    """
    queue = queue_dict["queue"]
    has_draft = queue_dict.get("has_draft", None)

    data = {
        "id": queue.resource_id,
        "snapshot_id": queue.resource_snapshot_id,
        "name": queue.name,
        "description": queue.description,
        "user": build_user_ref(queue.creator),
        "group": build_group_ref(queue.resource.owner),
        "created_on": queue.resource.created_on,
        "last_modified_on": queue.resource.last_modified_on,
        "latest_snapshot": queue.resource.latest_snapshot_id
        == queue.resource_snapshot_id,
        "tags": [build_tag_ref(tag) for tag in queue.tags],
    }

    if has_draft is not None:
        data["has_draft"] = has_draft

    return data


def build_plugin(plugin_with_files: PluginWithFilesDict) -> dict[str, Any]:
    """Build a Plugin response dictionary.

    Args:
        queue: The Plugin object to convert into a Plugin response dictionary.

    Returns:
        The Plugin response dictionary.
    """
    plugin = plugin_with_files["plugin"]
    plugin_files = plugin_with_files.get("plugin_files", None)
    has_draft = plugin_with_files.get("has_draft", None)

    data = {
        "id": plugin.resource_id,
        "snapshot_id": plugin.resource_snapshot_id,
        "name": plugin.name,
        "description": plugin.description,
        "user": build_user_ref(plugin.creator),
        "group": build_group_ref(plugin.resource.owner),
        "created_on": plugin.resource.created_on,
        "last_modified_on": plugin.resource.last_modified_on,
        "latest_snapshot": plugin.resource.latest_snapshot_id
        == plugin.resource_snapshot_id,
        "tags": [build_tag_ref(tag) for tag in plugin.tags],
    }

    if plugin_files is not None:
        data["files"] = [
            build_plugin_file_ref(plugin_file) for plugin_file in plugin_files
        ]

    if has_draft is not None:
        data["has_draft"] = has_draft

    return data


def build_plugin_file(plugin_file_with_plugin: PluginFileDict) -> dict[str, Any]:
    plugin_file = plugin_file_with_plugin["plugin_file"]
    plugin = plugin_file_with_plugin.get("plugin", None)
    has_draft = plugin_file_with_plugin.get("has_draft", None)

    data = {
        "id": plugin_file.resource_id,
        "snapshot_id": plugin_file.resource_snapshot_id,
        "filename": plugin_file.filename,
        "description": plugin_file.description,
        "user": build_user_ref(plugin_file.creator),
        "group": build_group_ref(plugin_file.resource.owner),
        "created_on": plugin_file.resource.created_on,
        "last_modified_on": plugin_file.resource.last_modified_on,
        "latest_snapshot": plugin_file.resource.latest_snapshot_id
        == plugin_file.resource_snapshot_id,
        "contents": plugin_file.contents,
        "tasks": [build_plugin_task(task) for task in plugin_file.tasks],
        "tags": [build_tag_ref(tag) for tag in plugin_file.tags],
    }

    if plugin is not None:
        data["plugin"] = build_plugin_ref(plugin)

    if has_draft is not None:
        data["has_draft"] = has_draft

    return data


def build_plugin_task(plugin_task: models.PluginTask) -> PluginTaskDict:
    input_params: list[PluginTaskInputParameterDict] = []
    for input_parameter in plugin_task.input_parameters:
        input_params.append(
            PluginTaskInputParameterDict(
                name=input_parameter.name,
                required=input_parameter.required,
                parameter_type=build_plugin_parameter_type_ref(
                    input_parameter.parameter_type
                ),
            )
        )

    output_params: list[PluginTaskOutputParameterDict] = []
    for output_parameter in plugin_task.output_parameters:
        output_params.append(
            PluginTaskOutputParameterDict(
                name=output_parameter.name,
                parameter_type=build_plugin_parameter_type_ref(
                    output_parameter.parameter_type
                ),
            )
        )

    return PluginTaskDict(
        name=plugin_task.plugin_task_name,
        input_params=input_params,
        output_params=output_params,
    )


def build_plugin_parameter_type(
    plugin_parameter_type_dict: PluginParameterTypeDict,
) -> dict[str, Any]:
    """Build a Plugin Parameter Type response dictionary.

    Args:
        plugin_parameter_type: The Plugin Parameter Type object to convert
            into a Plugin Parameter Type response dictionary.

    Returns:
        The Plugin Parameter Type response dictionary.
    """
    plugin_parameter_type = plugin_parameter_type_dict["plugin_task_parameter_type"]
    has_draft = plugin_parameter_type_dict["has_draft"]

    data = {
        "id": plugin_parameter_type.resource_id,
        "snapshot_id": plugin_parameter_type.resource_snapshot_id,
        "name": plugin_parameter_type.name,
        "structure": plugin_parameter_type.structure,
        "description": plugin_parameter_type.description,
        "user": build_user_ref(plugin_parameter_type.creator),
        "group": build_group_ref(plugin_parameter_type.resource.owner),
        "created_on": plugin_parameter_type.resource.created_on,
        "last_modified_on": plugin_parameter_type.resource.last_modified_on,
        "latest_snapshot": plugin_parameter_type.resource.latest_snapshot_id
        == plugin_parameter_type.resource_snapshot_id,
        "tags": [build_tag_ref(tag) for tag in plugin_parameter_type.tags],
    }

    if has_draft is not None:
        data["has_draft"] = has_draft

    return data


def build_resource_draft(
    draft: models.DraftResource,
    draft_schema: type[Schema] | Schema,
    num_other_drafts: int | None = None,
) -> dict[str, Any]:
    """Build a Draft response dictionary for a resource.

    Args:
        draft: The Draft object to convert into a Draft response dictionary.

    Returns:
        The Draft response dictionary.
    """

    if isinstance(draft_schema, Schema):
        schema = draft_schema
    else:
        schema = draft_schema()
    payload = schema.dump(draft.payload["resource_data"])

    metadata = dict()
    if num_other_drafts is not None:
        metadata["num_other_drafts"] = num_other_drafts
    return {
        "id": draft.draft_resource_id,
        "resource_id": draft.payload.get("resource_id", None),
        "resource_snapshot_id": draft.payload.get("resource_snapshot_id", None),
        "payload": payload,
        "resource_type": draft.resource_type,
        "user": build_user_ref(draft.creator),
        "group": build_group_ref(draft.target_owner),
        "created_on": draft.created_on,
        "last_modified_on": draft.last_modified_on,
        "metadata": metadata,
    }


def build_resource_url(resource: models.Resource):
    return build_url(f"{resource.resource_type}/{resource.resource_id}")


# -- Paging --------------------------------------------------------------------


def build_paging_envelope(
    route_prefix: str,
    build_fn: Callable,
    data: list[Any],
    group_id: int | None,
    query: str | None,
    draft_type: str | None,
    index: int,
    length: int,
    total_num_elements: int,
) -> dict[str, Any]:
    """Build the paging envelope for a response.

    Args:
        route_prefix: The prefix of the route, forms the URL path in the paging url.
        build_fn: The function for converting an ORM object into a response dictionary.
            This dictionary is then wrapped in the paging envelope and set as the "data"
            field.
        data: The list of ORM objects to wrap in the paging envelope.
        query: The optional search query string.
        draft_type: The type of drafts to return.
        index: The index of the current page.
        length: The number of results to return per page.
        total_num_elements: The total number of elements in the collection.

    Returns:
        The paging envelope for the response.
    """
    has_prev = index > 0
    has_next = total_num_elements > index + length
    is_complete = not has_next

    paged_data = {
        "index": index,
        "is_complete": is_complete,
        "total_num_results": total_num_elements,
        "first": build_paging_url(
            route_prefix,
            group_id=group_id,
            search=query,
            draft_type=draft_type,
            index=0,
            length=length,
        ),
        "data": [build_fn(x) for x in data],
    }

    if has_prev:
        prev_index = max(index - length, 0)
        prev_url = build_paging_url(
            route_prefix,
            group_id=group_id,
            search=query,
            draft_type=draft_type,
            index=prev_index,
            length=length,
        )
        paged_data["prev"] = prev_url

    if has_next:
        next_index = index + length
        next_url = build_paging_url(
            route_prefix,
            group_id=group_id,
            search=query,
            draft_type=draft_type,
            index=next_index,
            length=length,
        )
        paged_data["next"] = next_url

    return paged_data


def build_paging_url(
    route_prefix: str,
    group_id: int | None,
    search: str | None,
    draft_type: str | None,
    index: int,
    length: int,
) -> str:
    """Build a URL for a paged resource endpoint.

    Args:
        resource_type: The prefix of the route to paginate, forms the URL path.
        search: The optional search query string.
        draft_type: The type of drafts to return.
        index: The index of the current page.
        length: The number of results to return per page.

    Returns:
        A quoted URL string for the paged resource endpoint.
    """
    query_params: dict[str, Any] = {"index": index, "pageLength": length}

    if group_id:
        query_params["groupId"] = group_id

    if search:
        query_params["search"] = search

    if draft_type:
        query_params["draft_type"] = draft_type

    return build_url(route_prefix, query_params)


def build_url(route_prefix: str, query_params: dict[str, str] | None = None) -> str:
    query_params = query_params or {}

    return urlunparse(
        ("", "", f"/{V1_ROOT}/{route_prefix}", "", urlencode(query_params), "")
    )
