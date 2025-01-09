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
LATEST_ARTIFACTS_SQL_PATH = Path(__file__).parent / "latest_artifacts.sql"


def get_latest_artifact(db: SQLAlchemy, resource_id: int) -> models.Artifact | None:
    """Get the latest artifact for a given resource ID.

    Args:
        db: The SQLAlchemy database session.
        resource_id: The ID of the resource.

    Returns:
        The latest artifact for the given resource ID, or None if no artifact is found.
    """
    textual_sql = (
        text(LATEST_ARTIFACTS_SQL_PATH.read_text())
        .columns(
            models.Artifact.resource_snapshot_id,
            models.Artifact.resource_id,
            models.Artifact.resource_type,
        )
        .bindparams(resource_id=resource_id)
    )
    stmt = select(models.Artifact).from_statement(textual_sql)
    return db.session.execute(stmt).scalar()
