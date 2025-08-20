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
import structlog
from sqlalchemy import select
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import db, models
from dioptra.restapi.errors import DioptraError, EntityDoesNotExistError
from dioptra.restapi.v1.entity_types import EntityTypes
from dioptra.restapi.v1.entrypoints.service import (
    ENTRYPOINT_RESOURCE_TYPE as ENTRYPOINT_RESOURCE_TYPE,
)
from dioptra.restapi.v1.experiments.service import (
    EXPERIMENT_RESOURCE_TYPE as EXPERIMENT_RESOURCE_TYPE,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()


def get_entry_point(
    job_id: int, logger: BoundLogger | None = None
) -> models.EntryPoint:
    """Run a query to get the entrypoint for a job.

    Args:
        job_id: The ID of the job to get the entrypoint for.
        logger: A structlog logger object to use for logging. A new logger will be
            created if None.

    Returns:
        The entrypoint for the job.
    """
    log = logger or LOGGER.new()  # noqa: F841

    entry_point_stmt = (
        select(models.EntryPoint)
        .join(models.EntryPointJob)
        .where(models.EntryPointJob.job_resource_id == job_id)
    )
    entry_point = db.session.scalar(entry_point_stmt)

    if entry_point is None:
        raise EntityDoesNotExistError(ENTRYPOINT_RESOURCE_TYPE, job_id=job_id)

    return entry_point


def get_experiment(job_id: int, logger: BoundLogger | None = None) -> models.Experiment:
    """Run a query to get the experiment containing the job.

    Args:
        job_id: The ID of the job to get the experiment of.
        logger: A structlog logger object to use for logging. A new logger will be
            created if None.

    Returns:
        The experiment containing the job.
    """
    log = logger or LOGGER.new()  # noqa: F841

    experiment_stmt = (
        select(models.Experiment)
        .join(models.ExperimentJob)
        .where(models.ExperimentJob.job_resource_id == job_id)
    )
    experiment = db.session.scalar(experiment_stmt)

    if experiment is None:
        raise EntityDoesNotExistError(EXPERIMENT_RESOURCE_TYPE, job_id=job_id)

    return experiment


def get_entry_point_plugin_files(
    job_id: int, logger: BoundLogger | None = None
) -> list[models.PluginPluginFile]:
    """Run a query to get the plugin files for an entrypoint.

    Args:
        job_id: The ID of the job to get the plugin files for.
        logger: A structlog logger object to use for logging. A new logger will be
            created if None.

    Returns:
        The plugin files for the entrypoint.
    """
    log = logger or LOGGER.new()  # noqa: F841

    entry_point_resource_snapshot_stmt = (
        select(models.EntryPoint)
        .join(models.EntryPointJob)
        .where(
            models.EntryPointJob.job_resource_id == job_id,
        )
    )
    entry_point = db.session.scalar(entry_point_resource_snapshot_stmt)

    if entry_point is None:
        raise EntityDoesNotExistError(ENTRYPOINT_RESOURCE_TYPE, job_id=job_id)

    plugin_plugin_files = [
        plugin_plugin_file
        for entry_point_plugin in entry_point.entry_point_plugins
        for plugin_plugin_file in entry_point_plugin.plugin.plugin_plugin_files
    ]

    return plugin_plugin_files


def get_plugin_plugin_files_from_plugin_snapshot_ids(
    plugin_snapshot_ids: list[int], logger: BoundLogger | None = None
) -> list[models.PluginPluginFile]:
    """Run a query to get the plugin-plugin files for a list of plugin snapshot IDs.

    Args:
        plugin_snapshot_ids: The list of plugin snapshot IDs to get the plugin-plugin
            files for.
        logger: A structlog logger object to use for logging. A new logger will be
            created if None.

    Returns:
        The plugin-plugin files for the plugin snapshot IDs.

    Raises:
        DioptraError: If two plugin snapshot IDs point to the same resource ID.
    """
    log = logger or LOGGER.new()  # noqa: F841

    plugin_snapshots_stmt = select(models.Plugin).where(
        models.Plugin.resource_snapshot_id.in_(tuple(plugin_snapshot_ids))
    )
    plugins = db.session.scalars(plugin_snapshots_stmt).all()
    plugin_plugin_files: list[models.PluginPluginFile] = []
    plugin_resource_ids_seen: dict[int, int] = {}

    for plugin in plugins:
        if plugin.resource_id in plugin_resource_ids_seen:
            raise DioptraError(
                f"Two plugin snapshot IDs, {plugin.resource_snapshot_id} and "
                f"{plugin_resource_ids_seen[plugin.resource_id]}, point to the "
                f"same resource ID {plugin.resource_id}. Only one snapshot ID "
                "per resource ID is allowed."
            )

        plugin_resource_ids_seen[plugin.resource_id] = plugin.resource_snapshot_id

        for plugin_plugin_file in plugin.plugin_plugin_files:
            plugin_plugin_files.append(plugin_plugin_file)

    return plugin_plugin_files


def get_job_parameter_values(
    job_id: int, logger: BoundLogger | None = None
) -> list[models.EntryPointParameterValue]:
    """Run a query to get the parameter values for the job.

    Args:
        job_id: The ID of the job to get the parameter values for.
        logger: A structlog logger object to use for logging. A new logger will be
            created if None.

    Returns:
        The parameter values for the job.
    """
    log = logger or LOGGER.new()  # noqa: F841

    entry_point_param_values_stmt = select(models.EntryPointParameterValue).where(
        models.EntryPointParameterValue.job_resource_id == job_id,
    )
    return list(db.session.scalars(entry_point_param_values_stmt).unique().all())


def get_plugin_parameter_types(
    job_id: int | None = None,
    group_id: int | None = None,
    logger: BoundLogger | None = None,
) -> list[models.PluginTaskParameterType]:
    """Run a query to get the plugin task parameter types.

    This function retrieves the plugin task parameter types for a job or group. It
    requires either a job ID or a group ID to be provided, but not both.

    Args:
        job_id: The ID of the job to get the plugin task parameter types for.
            Must be provided if group_id is None. Defaults to None.
        group_id: The ID of the group to get the plugin task parameter types for.
            Must be provided if job_id is None. Defaults to None.
        logger: A structlog logger object to use for logging. A new logger will be
            created if None.

    Returns:
        The plugin task parameter types for the entrypoint.

    Raises:
        DioptraError: If both job_id and group_id are provided, or if both are None.
    """
    log = logger or LOGGER.new()  # noqa: F841

    if job_id is not None and group_id is not None:
        raise DioptraError(
            "Either a job or group identifier must be provided, not both"
        )

    if job_id:
        return _get_plugin_parameter_types_for_job_id(job_id=job_id, logger=log)

    if group_id:
        return _get_plugin_parameter_types_for_group_id(group_id=group_id, logger=log)

    raise DioptraError(
        "A job or group identifier must be provided, both cannot be None"
    )


def _get_plugin_parameter_types_for_group_id(
    group_id: int, logger: BoundLogger | None = None
) -> list[models.PluginTaskParameterType]:
    """Run a query to get the plugin task parameter types for the group.

    Args:
        group_id: The ID of the group to get the plugin task parameter types for.
        logger: A structlog logger object to use for logging. A new logger will be
            created if None.

    Returns:
        The plugin files for the entrypoint.
    """
    log = logger or LOGGER.new()  # noqa: F841

    plugin_parameter_types_stmt = (
        select(models.PluginTaskParameterType)
        .join(models.Resource)
        .where(
            models.Resource.is_deleted == False,  # noqa: E712
            models.Resource.group_id == group_id,
            models.Resource.latest_snapshot_id
            == models.PluginTaskParameterType.resource_snapshot_id,
        )
    )
    return list(db.session.scalars(plugin_parameter_types_stmt).all())


def _get_plugin_parameter_types_for_job_id(
    job_id: int, logger: BoundLogger | None = None
) -> list[models.PluginTaskParameterType]:
    """Run a query to get the plugin task parameter types for the job.

    Args:
        job_id: The ID of the job to get the plugin task parameter types for.
        logger: A structlog logger object to use for logging. A new logger will be
            created if None.

    Returns:
        The plugin files for the entrypoint.
    """
    log = logger or LOGGER.new()  # noqa: F841

    group_id_stmt = select(models.Resource.group_id).where(
        models.Resource.resource_id == job_id
    )
    plugin_parameter_types_stmt = (
        select(models.PluginTaskParameterType)
        .join(models.Resource)
        .where(
            models.Resource.is_deleted == False,  # noqa: E712
            models.Resource.group_id == group_id_stmt.scalar_subquery(),
            models.Resource.latest_snapshot_id
            == models.PluginTaskParameterType.resource_snapshot_id,
        )
    )
    return list(db.session.scalars(plugin_parameter_types_stmt).all())


def get_resource(
    resource_id: int, logger: BoundLogger | None = None
) -> models.Resource | None:
    """Run a query to get a resource

    Args:
        resource_id: The identifier of the Resource
        logger: A structlog logger object to use for logging. A new logger will be
            created if None.

    Returns:
        The retrieved Resource ORM object
    """
    log = logger or LOGGER.new()  # noqa: F841

    resource_stmt = select(models.Resource).where(
        models.Resource.resource_id == resource_id,
        models.Resource.is_deleted == False,  # noqa: E712
    )
    return db.session.scalar(resource_stmt)


def get_resource_snapshot(
    resource_type: str, snapshot_id: int, logger: BoundLogger | None = None
) -> models.ResourceSnapshot:
    """Run a query to get the latest snapshot for a resource

    Args:
        resource_type: The type of Resource.
        snapshot_id: The ID of snapshot to retrieve
        logger: A structlog logger object to use for logging. A new logger will be
            created if None.

    Returns:
        The resource snapshot
    """
    log = logger or LOGGER.new()  # noqa: F841

    snapshot_model = {
        "artifact": models.Artifact,
        "entry_point": models.EntryPoint,
        "experiment": models.Experiment,
        "ml_model": models.MlModel,
        "plugin": models.Plugin,
        "plugin_file": models.PluginFile,
        "plugin_task_parameter_type": models.PluginTaskParameterType,
        "queue": models.Queue,
    }.get(resource_type, None)

    if snapshot_model is None:
        raise DioptraError(f"Invalid resource type: {resource_type}")

    snapshot_stmt = (
        select(snapshot_model)
        .join(models.Resource)
        .where(
            snapshot_model.resource_snapshot_id == snapshot_id,
            models.Resource.is_deleted == False,  # noqa: E712
        )
    )
    snapshot = db.session.scalar(snapshot_stmt)

    if snapshot is None:
        raise EntityDoesNotExistError(
            EntityTypes.get_from_string(resource_type), snapshot_id=snapshot_id
        )

    return snapshot


def get_draft_resource(
    draft_id: int, logger: BoundLogger | None = None
) -> models.DraftResource | None:
    """Run a query to get the draft of a resource

    Args:
        draft_id: The identifier of the DraftResource
        logger: A structlog logger object to use for logging. A new logger will be
            created if None.

    Returns:
        The retrieved DraftResource ORM object
    """
    log = logger or LOGGER.new()  # noqa: F841

    draft_stmt = select(models.DraftResource).where(
        models.DraftResource.draft_resource_id == draft_id
    )
    return db.session.scalar(draft_stmt)
