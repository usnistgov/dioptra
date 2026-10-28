"""Make usernames unique, including those belonging to deleted users.

Revision ID: c217b6f8a904
Revises: 30e74c5564b3

Existing duplicate usernames must be resolved before applying this migration.
"""

import logging

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c217b6f8a904"
down_revision = "30e74c5564b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    users = sa.table("users", sa.column("username", sa.Text()))
    duplicate = op.get_bind().execute(
        sa.select(users.c.username)
        .group_by(users.c.username)
        .having(sa.func.count() > 1)
        .limit(1)
    ).first()
    if duplicate is not None:
        message = (
            "Cannot apply migration c217b6f8a904: duplicate usernames exist in "
            "the users table. Modify usernames so every user has a unique "
            "username, including deleted users, then rerun dioptra-db autoupgrade."
        )
        logging.getLogger("alembic").error(message)
        raise RuntimeError(message)

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_users_username"))
        batch_op.create_index(
            batch_op.f("ix_users_username"), ["username"], unique=True
        )


def downgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_users_username"))
        batch_op.create_index(
            batch_op.f("ix_users_username"), ["username"], unique=False
        )
