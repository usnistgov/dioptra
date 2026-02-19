"""Up/Down-grade resource snapshot types as delete/insert 'resource_snapshot' [GH-Issue #474]

Revision ID: 0ca6eca33569
Revises: f1d231f7ef15
Create Date: 2024-12-12 00:47:23.575103

"""

from typing import Annotated

import sqlalchemy as sa
from alembic import op
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
    sessionmaker,
)

# revision identifiers, used by Alembic.
revision = "0ca6eca33569"
down_revision = "f1d231f7ef15"
branch_labels = None
depends_on = None


text_ = Annotated[str, mapped_column(sa.Text())]


# The data to up/down-grade
ENUM_TABLE = "resource_types"
TABLE_ENTRY = "resource_snapshot"


class UpgradeBase(DeclarativeBase, MappedAsDataclass):
    pass


class DowngradeBase(DeclarativeBase, MappedAsDataclass):
    pass


class ResourceTypeUpgrade(UpgradeBase):
    __tablename__ = ENUM_TABLE
    resource_type: Mapped[text_] = mapped_column(primary_key=True)


class ResourceTypeDowngrade(DowngradeBase):
    __tablename__ = ENUM_TABLE
    resource_type: Mapped[text_] = mapped_column(primary_key=True)


def upgrade():
    """Alembic Upgrade Hook-Point that deletes the entry from
    resource_types table with value 'resource_snapshot'
    """
    bind = op.get_bind()
    Session = sessionmaker(bind=bind)

    with Session() as session:
        stmt = sa.select(ResourceTypeUpgrade).where(
            ResourceTypeUpgrade.resource_type == TABLE_ENTRY
        )
        resource_snapshot_type = session.scalar(stmt)

        if resource_snapshot_type is not None:
            session.delete(resource_snapshot_type)

        session.commit()


def downgrade():
    """Alembic Downgrade Hook-Point that reinstates the entry to
    resource_types table with value 'resource_snapshot'
    """
    bind = op.get_bind()
    Session = sessionmaker(bind=bind)

    with Session() as session:
        stmt = sa.select(ResourceTypeUpgrade).where(
            ResourceTypeUpgrade.resource_type == TABLE_ENTRY
        )
        resource_snapshot_type = session.scalar(stmt)

        if resource_snapshot_type is None:
            session.add(ResourceTypeUpgrade(resource_type=TABLE_ENTRY))

        session.commit()
