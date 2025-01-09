"""Update entry point parameter types list

Revision ID: 6a75ede23821
Revises: 4b2d781f8bb4
Create Date: 2024-09-10 16:32:40.707231

"""

from typing import Annotated, Optional

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
revision = "6a75ede23821"
down_revision = "4b2d781f8bb4"
branch_labels = None
depends_on = None


# Upgrade and downgrade inserts and deletes
UPGRADE_INSERTS = ["boolean", "integer", "list", "mapping"]
UPGRADE_DELETES = ["path", "uri"]
DOWNGRADE_INSERTS = ["path", "uri"]


# Migration data models
intpk = Annotated[
    int,
    mapped_column(sa.BigInteger().with_variant(sa.Integer, "sqlite"), primary_key=True),
]
text_ = Annotated[str, mapped_column(sa.Text())]
bool_ = Annotated[bool, mapped_column(sa.Boolean())]
optionalstr = Annotated[Optional[str], mapped_column(sa.Text(), nullable=True)]


class UpgradeBase(DeclarativeBase, MappedAsDataclass):
    pass


class DowngradeBase(DeclarativeBase, MappedAsDataclass):
    pass


class EntryPointParameterTypeUpgrade(UpgradeBase):
    __tablename__ = "entry_point_parameter_types"

    parameter_type: Mapped[text_] = mapped_column(primary_key=True)


class EntryPointParameterUpgrade(UpgradeBase):
    __tablename__ = "entry_point_parameters"

    entry_point_resource_snapshot_id: Mapped[intpk] = mapped_column(init=False)
    parameter_number: Mapped[intpk]
    parameter_type: Mapped[text_] = mapped_column(nullable=False)
    name: Mapped[text_] = mapped_column(nullable=False)
    default_value: Mapped[optionalstr]


class EntryPointParameterTypeDowngrade(DowngradeBase):
    __tablename__ = "entry_point_parameter_types"

    parameter_type: Mapped[text_] = mapped_column(primary_key=True)


def upgrade():
    bind = op.get_bind()
    Session = sessionmaker(bind=bind)

    with Session() as session:
        for parameter_type in UPGRADE_INSERTS:
            stmt = sa.select(EntryPointParameterTypeUpgrade).where(
                EntryPointParameterTypeUpgrade.parameter_type == parameter_type
            )

            if session.scalar(stmt) is None:
                session.add(
                    EntryPointParameterTypeUpgrade(parameter_type=parameter_type)
                )

        # Search for any parameters that are of type "path" or "uri" and convert them to
        # "string"
        to_string_params_stmt = sa.select(EntryPointParameterUpgrade).where(
            EntryPointParameterUpgrade.parameter_type.in_(["path", "uri"])
        )

        for entry_point_parameter in session.execute(to_string_params_stmt):
            entry_point_parameter.parameter_type = "string"

        for parameter_type in UPGRADE_DELETES:
            stmt = sa.select(EntryPointParameterTypeUpgrade).where(
                EntryPointParameterTypeUpgrade.parameter_type == parameter_type
            )
            entry_point_parameter_type = session.scalar(stmt)

            if entry_point_parameter_type is not None:
                session.delete(entry_point_parameter_type)

        session.commit()


def downgrade():
    bind = op.get_bind()
    Session = sessionmaker(bind=bind)

    with Session() as session:
        for parameter_type in DOWNGRADE_INSERTS:
            stmt = sa.select(EntryPointParameterTypeDowngrade).where(
                EntryPointParameterTypeDowngrade.parameter_type == parameter_type
            )

            if session.scalar(stmt) is None:
                session.add(
                    EntryPointParameterTypeDowngrade(parameter_type=parameter_type)
                )

        session.commit()
