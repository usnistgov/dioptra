"""Retire legacy snapshot URIs after all artifact resources have locations.

Revision ID: c4e1c2004f14
Revises: 65b167004f14
"""

import sqlalchemy as sa
from alembic import context, op
from alembic.util import CommandError

revision = "c4e1c2004f14"
down_revision = "65b167004f14"
branch_labels = None
depends_on = None

_ARTIFACTS = sa.table("artifacts", sa.column("resource_id"))
_LOCATIONS = sa.table(
    "artifact_locations",
    sa.column("artifact_resource_id"),
    sa.column("storage_prefix_id"),
    sa.column("relative_path"),
)
_PREFIXES = sa.table(
    "artifact_storage_prefixes",
    sa.column("storage_prefix_id"),
    sa.column("relative_prefix"),
)


def _begin_sqlite_ddl_transaction() -> None:
    """Keep SQLite DDL and Alembic's revision update in the same transaction."""
    if context.is_offline_mode():
        return

    connection = op.get_bind()
    # SQLite's legacy driver mode does not automatically start a transaction for DDL.
    if (
        connection.dialect.name == "sqlite"
        and not connection.connection.driver_connection.in_transaction
    ):
        connection.exec_driver_sql("BEGIN")


def upgrade() -> None:
    """Remove obsolete URIs after checking that the new schema covers all snapshots.

    Raises:
        CommandError: If the check cannot run or a resource lacks a complete location.
    """
    if context.is_offline_mode():
        raise CommandError(
            "Connect to the database so Dioptra can check existing artifacts."
        )
    _begin_sqlite_ddl_transaction()
    connection = op.get_bind()
    complete_location = (
        sa.select(_LOCATIONS.c.artifact_resource_id)
        .join(
            _PREFIXES, _PREFIXES.c.storage_prefix_id == _LOCATIONS.c.storage_prefix_id
        )
        .where(
            _LOCATIONS.c.artifact_resource_id == _ARTIFACTS.c.resource_id,
            _LOCATIONS.c.relative_path != "",
            _PREFIXES.c.relative_prefix != "",
        )
        .exists()
    )
    if connection.scalar(
        sa.select(sa.exists().where(~complete_location).select_from(_ARTIFACTS))
    ):
        raise CommandError(
            "Upgrade stopped. Some artifacts still use the old storage addresses. "
            "Their addresses have been kept. Leave the API and workers stopped and "
            "back up the database. Ask your administrator to convert those addresses "
            "before running the upgrade again."
        )

    op.drop_column("artifacts", "uri")


def downgrade() -> None:
    """Restore the required URI column on an empty artifacts table.

    Raises:
        CommandError: If the check cannot run or any artifact snapshots exist.
    """
    if context.is_offline_mode():
        raise CommandError(
            "Connect to the database so Dioptra can check existing artifacts."
        )
    _begin_sqlite_ddl_transaction()
    connection = op.get_bind()
    if connection.scalar(
        sa.select(sa.exists().where(_ARTIFACTS.c.resource_id.is_not(None)))
    ):
        raise CommandError(
            "Downgrade stopped. This database contains artifacts, and Dioptra cannot "
            "recreate their old storage addresses. To return to the previous version, "
            "restore the database backup made before the upgrade."
        )

    op.add_column("artifacts", sa.Column("uri", sa.Text(), nullable=False))
