"""Add JobSwaps ORM
Address issue #823 to create Job-Swaps ORM
https://github.com/usnistgov/dioptra/issues/823

Revision ID: 4e4b99db9b1d
Revises: ad4f89b2288d
Create Date: 2026-05-11 15:23:39.677010

"""
import sqlalchemy as sa
from alembic import op

SWAPS_TABLE_NAME="job_swaps"

# revision identifiers, used by Alembic.
revision = '4e4b99db9b1d'
down_revision = 'ad4f89b2288d'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(SWAPS_TABLE_NAME,
        sa.Column('job_id', 
                  sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), 
                  nullable=False),
        sa.Column('swap_name', sa.Text(), nullable=False),
        sa.Column('task_alias', sa.Text(), nullable=False),
        sa.Column('plugin_file_resource_snapshot_id', 
                  sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), 
                  nullable=False),
        # FK - constraints to add   
        # EntryPoint-Snapshot        
        sa.ForeignKeyConstraint(['job_id'], 
                                ['jobs.resource_snapshot_id'], 
                                name=op.f('fk_job_swaps_job_id_jobs_resource_snapshot_id')),
        sa.ForeignKeyConstraint(['plugin_file_resource_snapshot_id'], 
                                ['jobs.resource_snapshot_id'], 
                                name=op.f('fk_job_swaps_plugin_file_resource_snapshot_id_plugin_files')),
    )



def downgrade():
    op.drop_table(SWAPS_TABLE_NAME)
