"""add metrics table

Revision ID: ad4f89b2288d
Revises: 06e8176155bf
Create Date: 2025-08-26 10:25:55.222239

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'ad4f89b2288d'
down_revision = '06e8176155bf'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('job_metrics',
        sa.Column('job_resource_id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('value', sa.Float(), nullable=True),
        sa.Column('step', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), nullable=False),
        sa.Column('timestamp', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), nullable=False),
        sa.ForeignKeyConstraint(['job_resource_id'], ['resources.resource_id'], name=op.f('fk_job_metrics_job_resource_id_resources')),
        sa.PrimaryKeyConstraint('job_resource_id', 'name', 'timestamp', name=op.f('pk_job_metrics'))
    )


def downgrade():
    op.drop_table('job_metrics')
