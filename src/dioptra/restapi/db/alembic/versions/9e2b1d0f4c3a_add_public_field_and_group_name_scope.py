"""Add public field and user-scoped group names

Revision ID: 9e2b1d0f4c3a
Revises: ad4f89b2288d
Create Date: 2026-05-12 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9e2b1d0f4c3a"
down_revision = "ad4f89b2288d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "groups",
        sa.Column("public", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index(
        op.f("ix_groups_user_id_name"),
        "groups",
        ["user_id", "name"],
        unique=True,
    )

    groups_table = sa.table(
        "groups",
        sa.column("group_id", sa.BigInteger()),
        sa.column("public", sa.Boolean()),
    )
    op.execute(groups_table.update().values(public=True))


def downgrade() -> None:
    op.drop_index(op.f("ix_groups_user_id_name"), table_name="groups")
    op.drop_column("groups", "public")
