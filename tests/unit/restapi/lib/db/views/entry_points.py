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
LATEST_ENTRY_POINTS_SQL_PATH = Path(__file__).parent / "latest_entry_points.sql"
LATEST_ENTRY_POINT_QUEUES_SQL_PATH = (
    Path(__file__).parent / "latest_entry_point_queues.sql"
)


def get_latest_entry_point(
    db: SQLAlchemy, resource_id: int
) -> models.EntryPoint | None:
    """Get the latest entry point for a given resource ID.

    Args:
        db: The SQLAlchemy database session.
        resource_id: The ID of the resource.

    Returns:
        The latest entry point for the given resource ID, or None if no entry point is
        found.
    """
    textual_sql = (
        text(LATEST_ENTRY_POINTS_SQL_PATH.read_text())
        .columns(
            models.EntryPoint.resource_snapshot_id,
            models.EntryPoint.resource_id,
            models.EntryPoint.resource_type,
        )
        .bindparams(resource_id=resource_id)
    )
    stmt = select(models.EntryPoint).from_statement(textual_sql)
    return db.session.execute(stmt).scalar()


def get_latest_entry_point_queues(
    db: SQLAlchemy, entry_point_resource_id: int
) -> list[models.Queue]:
    """Get the latest queues associated with a given entry point.

    Args:
        db: The SQLAlchemy database session.
        entry_point_resource_id: The ID of the entry point.

    Returns:
        A list of the current queue resource snapshots associated with the given entry
        point.
    """
    textual_sql = (
        text(LATEST_ENTRY_POINT_QUEUES_SQL_PATH.read_text())
        .columns(
            models.EntryPoint.resource_id.label("entry_point_resource_id"),
            models.Queue.resource_snapshot_id,
            models.Queue.resource_id,
            models.Queue.resource_type,
        )
        .bindparams(entry_point_resource_id=entry_point_resource_id)
    )
    stmt = select(models.Queue).from_statement(textual_sql)
    return list(db.session.execute(stmt).scalars())
