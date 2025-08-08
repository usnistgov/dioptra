"""add alternative_id to MlModel

Revision ID: 17c602b97983
Revises: fa39987673e0
Create Date: 2025-08-08 09:47:00.657872

"""
from alembic import op
import sqlalchemy as sa
from dioptra.restapi.db.custom_types import GUID

# revision identifiers, used by Alembic.
revision = '17c602b97983'
down_revision = 'fa39987673e0'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('ml_models', schema=None) as batch_op:
        batch_op.add_column(sa.Column('alternative_id', GUID(), nullable=False))
        batch_op.create_index(batch_op.f('ix_ml_models_alternative_id'), ['alternative_id'], unique=True)


def downgrade():
    with op.batch_alter_table('ml_models', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_ml_models_alternative_id'))
        batch_op.drop_column('alternative_id')
