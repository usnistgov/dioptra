"""change plugin tasks type

Revision ID: 5d023000488a
Revises: 06e8176155bf
Create Date: 2025-08-25 16:09:51.335509

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5d023000488a'
down_revision = '06e8176155bf'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('plugin_tasks', schema=None) as batch_op:
        batch_op.alter_column('type',
               existing_type=sa.VARCHAR(),
               type_=sa.Text(),
               existing_nullable=False)


def downgrade():
    with op.batch_alter_table('plugin_tasks', schema=None) as batch_op:
        batch_op.alter_column('type',
               existing_type=sa.Text(),
               type_=sa.VARCHAR(),
               existing_nullable=False)
