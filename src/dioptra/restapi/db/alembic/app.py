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
"""Construct the database-only Flask context used by migration commands."""

from collections.abc import Mapping

from flask import Flask
from flask_migrate import Migrate

from dioptra.restapi.config import resolve_database_uri
from dioptra.restapi.db import db


def create_migration_app(*, overrides: Mapping[str, object] | None = None) -> Flask:
    """Initialize SQLAlchemy and Flask-Migrate without API settings or clients.

    Resolve the shared database URI, then use the existing complete model metadata
    and batch-rendering option. No API mode or signing key is required.

    Args:
        overrides: Optional mapping containing only ``SQLALCHEMY_DATABASE_URI``,
            as accepted by ``resolve_database_uri``.

    Returns:
        A Flask application configured for database migration commands.

    Raises:
        ValueError: If database URI resolution or validation fails.
    """
    uri = resolve_database_uri(overrides=overrides)
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI=uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    db.init_app(app)
    with app.app_context():
        Migrate(app, db, render_as_batch=True)
    return app
