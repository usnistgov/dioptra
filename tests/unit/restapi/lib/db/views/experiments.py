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
from __future__ import annotations

from pathlib import Path

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select, text

from dioptra.restapi.db import models

# CAUTION!!!
# Using __file__ to get a filepath within the tests/ directory is necessary, but DO NOT
# DO THIS in src/dioptra, use importlib.resources instead!
LATEST_EXPERIMENTS_SQL_PATH = Path(__file__).parent / "latest_experiments.sql"
LATEST_EXPERIMENT_ENTRY_POINTS_SQL_PATH = (
    Path(__file__).parent / "latest_experiment_entry_points.sql"
)


def get_latest_experiment(db: SQLAlchemy, resource_id: int) -> models.Experiment | None:
    """Get the latest experiment for a given resource ID.

    Args:
        db: The SQLAlchemy database session.
        resource_id: The ID of the resource.

    Returns:
        The latest experiment for the given resource ID, or None if no experiment is
        found.
    """
    textual_sql = (
        text(LATEST_EXPERIMENTS_SQL_PATH.read_text())
        .columns(
            models.Experiment.resource_snapshot_id,
            models.Experiment.resource_id,
            models.Experiment.resource_type,
        )
        .bindparams(resource_id=resource_id)
    )
    stmt = select(models.Experiment).from_statement(textual_sql)
    return db.session.execute(stmt).scalar()


def get_latest_experiment_entry_points(
    db: SQLAlchemy, experiment_resource_id: int
) -> list[models.EntryPoint]:
    """Get the latest entry points associated with a given experiment.

    Args:
        db: The SQLAlchemy database session.
        experiment_resource_id: The ID of the experiment resource.

    Returns:
        A list of the current entry point resource snapshots associated with the given
        experiment.
    """
    textual_sql = (
        text(LATEST_EXPERIMENT_ENTRY_POINTS_SQL_PATH.read_text())
        .columns(
            models.Experiment.resource_id.label("experiment_resource_id"),
            models.EntryPoint.resource_snapshot_id,
            models.EntryPoint.resource_id,
            models.EntryPoint.resource_type,
        )
        .bindparams(experiment_resource_id=experiment_resource_id)
    )
    stmt = select(models.EntryPoint).from_statement(textual_sql)
    return list(db.session.execute(stmt).scalars())
