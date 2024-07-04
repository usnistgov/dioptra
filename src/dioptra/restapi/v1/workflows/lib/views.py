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

from ..errors import JobEntryPointDoesNotExistError

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
        log.debug(
            "The job's entrypoint does not exist",
            job_id=job_id,
        )
        raise JobEntryPointDoesNotExistError

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
        log.debug(
            "The experiment associated with the job does not exist",
            job_id=job_id,
        )
        raise JobEntryPointDoesNotExistError

    return experiment


def get_entry_point_plugin_files(
    job_id: int, logger: BoundLogger | None = None
) -> list[models.EntryPointPluginFile]:
    """Run a query to get the plugin files for an entrypoint.

    Args:
        job_id: The ID of the job to get the plugin files for.
        logger: A structlog logger object to use for logging. A new logger will be
            created if None.

    Returns:
        The plugin files for the entrypoint.
    """
    log = logger or LOGGER.new()  # noqa: F841

    entry_point_resource_snapshot_id_stmt = (
        select(models.EntryPoint.resource_snapshot_id)
        .join(models.EntryPointJob)
        .where(
            models.EntryPointJob.job_resource_id == job_id,
        )
    )
    entry_point_plugin_files_stmt = select(models.EntryPointPluginFile).where(
        models.EntryPointPluginFile.entry_point_resource_snapshot_id
        == entry_point_resource_snapshot_id_stmt.scalar_subquery(),
    )
    return list(db.session.scalars(entry_point_plugin_files_stmt).unique().all())


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
