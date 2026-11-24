"""Add immutable artifact locations alongside the legacy snapshot URIs.

Revision ID: 65b167004f14
Revises: e64f9b2a7130
"""

import sqlalchemy as sa
from alembic import context, op

revision = "65b167004f14"
down_revision = "e64f9b2a7130"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add the offline reconciliation tables without modifying artifact snapshots."""
    _begin_sqlite_ddl_transaction()
    id_type = sa.BigInteger().with_variant(sa.Integer(), "sqlite")
    op.create_table(
        "artifact_storage_prefixes",
        sa.Column("storage_prefix_id", id_type, nullable=False),
        sa.Column("relative_prefix", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint(
            "storage_prefix_id", name=op.f("pk_artifact_storage_prefixes")
        ),
        sa.UniqueConstraint(
            "relative_prefix", name=op.f("uq_artifact_storage_prefixes_relative_prefix")
        ),
    )
    op.create_table(
        "artifact_locations",
        sa.Column("artifact_resource_id", id_type, nullable=False, autoincrement=False),
        sa.Column(
            "artifact_resource_type",
            sa.Text(),
            nullable=False,
            server_default="artifact",
        ),
        sa.Column("storage_prefix_id", id_type, nullable=False),
        sa.Column("relative_path", sa.Text(), nullable=False),
        sa.CheckConstraint(
            "artifact_resource_type = 'artifact'",
            name=op.f("ck_artifact_locations_artifact_type"),
        ),
        sa.PrimaryKeyConstraint(
            "artifact_resource_id", name=op.f("pk_artifact_locations")
        ),
        sa.ForeignKeyConstraint(
            ["artifact_resource_id", "artifact_resource_type"],
            ["resources.resource_id", "resources.resource_type"],
            name=op.f("fk_artifact_locations_artifact_resource_id_resources"),
        ),
        sa.ForeignKeyConstraint(
            ["storage_prefix_id"],
            ["artifact_storage_prefixes.storage_prefix_id"],
            name=op.f(
                "fk_artifact_locations_storage_prefix_id_artifact_storage_prefixes"
            ),
        ),
    )
    op.create_index(
        op.f("ix_artifact_locations_storage_prefix_id"),
        "artifact_locations",
        ["storage_prefix_id"],
    )


def downgrade() -> None:
    """Drop the reconciliation tables while preserving the legacy URI column."""
    _begin_sqlite_ddl_transaction()
    op.drop_table("artifact_locations")
    op.drop_table("artifact_storage_prefixes")


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
