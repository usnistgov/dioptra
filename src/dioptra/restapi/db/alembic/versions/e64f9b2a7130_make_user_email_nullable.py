"""Make the unused user email address nullable, preserving existing values.

Revision ID: e64f9b2a7130
Revises: c217b6f8a904
"""

import sqlalchemy as sa
from alembic import op

revision = "e64f9b2a7130"
down_revision = "c217b6f8a904"
branch_labels = None
depends_on = None


def _set_email_nullable(nullable: bool) -> None:
    connection = op.get_bind()
    if connection.dialect.name != "sqlite":
        op.alter_column(
            "users", "email_address", existing_type=sa.Text(), nullable=nullable
        )
        return

    # SQLite rebuilds the table; disable foreign keys outside a transaction so
    # references to existing users survive the temporary removal of the table.
    with op.get_context().autocommit_block():
        foreign_keys = connection.exec_driver_sql("PRAGMA foreign_keys").scalar()
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        try:
            with op.batch_alter_table("users", schema=None) as batch_op:
                batch_op.alter_column(
                    "email_address", existing_type=sa.Text(), nullable=nullable
                )
        finally:
            connection.exec_driver_sql(f"PRAGMA foreign_keys={int(bool(foreign_keys))}")


def upgrade() -> None:
    _set_email_nullable(True)


def downgrade() -> None:
    users = sa.table("users", sa.column("email_address", sa.Text()))
    if op.get_bind().scalar(
        sa.select(sa.exists().where(users.c.email_address.is_(None)))
    ):
        raise RuntimeError(
            "Cannot make users.email_address non-nullable while NULL values exist. "
            "Populate those values before downgrading."
        )
    _set_email_nullable(False)
