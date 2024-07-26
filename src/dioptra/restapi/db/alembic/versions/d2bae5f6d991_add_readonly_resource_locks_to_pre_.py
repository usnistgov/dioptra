"""Add 'readonly' resource locks to pre-existing built-in parameter types

Revision ID: d2bae5f6d991
Revises: 10f9e72e72aa
Create Date: 2024-06-28 12:30:13.685590

"""

import datetime
from typing import Annotated, Any, Optional

import sqlalchemy as sa
from alembic import op
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    column_property,
    mapped_column,
    relationship,
    sessionmaker,
)

from dioptra.restapi.db.custom_types import TZDateTime

# revision identifiers, used by Alembic.
revision = "d2bae5f6d991"
down_revision = "10f9e72e72aa"
branch_labels = None
depends_on = None


# Declare list of allowed simple built-in parameter types
BUILTIN_PARAMETER_TYPES = ["any", "number", "integer", "string", "boolean", "null"]


# Migration data models
bigint = Annotated[
    int, mapped_column(sa.BigInteger().with_variant(sa.Integer, "sqlite"))
]
intpk = Annotated[
    int,
    mapped_column(sa.BigInteger().with_variant(sa.Integer, "sqlite"), primary_key=True),
]
text_ = Annotated[str, mapped_column(sa.Text())]
bool_ = Annotated[bool, mapped_column(sa.Boolean())]
datetimetz = Annotated[datetime.datetime, mapped_column(TZDateTime())]
optionalbigint = Annotated[
    Optional[int],
    mapped_column(sa.BigInteger().with_variant(sa.Integer, "sqlite"), nullable=True),
]
optionaljson_ = Annotated[Optional[dict[str, Any]], mapped_column(sa.JSON)]
optionalstr = Annotated[Optional[str], mapped_column(sa.Text(), nullable=True)]


class UpgradeBase(DeclarativeBase, MappedAsDataclass):
    pass


class GroupUpgrade(UpgradeBase):
    __tablename__ = "groups"

    # Database fields
    group_id: Mapped[intpk] = mapped_column(init=False)
    name: Mapped[text_] = mapped_column(nullable=False)
    user_id: Mapped[bigint] = mapped_column(nullable=False)


class ResourceSnapshotUpgrade(UpgradeBase):
    __tablename__ = "resource_snapshots"

    # Database fields
    resource_snapshot_id: Mapped[intpk] = mapped_column(init=False)
    resource_id: Mapped[bigint] = mapped_column(nullable=False)
    resource_type: Mapped[text_] = mapped_column(nullable=False)
    user_id: Mapped[bigint] = mapped_column(nullable=False)
    description: Mapped[optionalstr] = mapped_column()
    created_on: Mapped[datetimetz] = mapped_column(init=False, nullable=False)

    # Initialize default values using dataclass __post_init__ method
    # https://docs.python.org/3/library/dataclasses.html#dataclasses.__post_init__
    def __post_init__(self) -> None:
        timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        self.created_on = timestamp


class ResourceLockUpgrade(UpgradeBase):
    __tablename__ = "resource_locks"

    # Database fields
    resource_id: Mapped[intpk] = mapped_column(sa.ForeignKey("resources.resource_id"))
    resource_lock_type: Mapped[text_] = mapped_column(primary_key=True)
    created_on: Mapped[datetimetz] = mapped_column(init=False, nullable=False)

    # Relationships
    resource: Mapped["ResourceUpgrade"] = relationship(
        init=False, back_populates="locks"
    )

    # Initialize default values using dataclass __post_init__ method
    # https://docs.python.org/3/library/dataclasses.html#dataclasses.__post_init__
    def __post_init__(self) -> None:
        timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        self.created_on = timestamp


class ResourceUpgrade(UpgradeBase):
    __tablename__ = "resources"

    # Database fields
    resource_id: Mapped[intpk] = mapped_column(init=False)
    group_id: Mapped[bigint] = mapped_column(nullable=False)
    resource_type: Mapped[text_] = mapped_column(nullable=False)
    created_on: Mapped[datetimetz] = mapped_column(init=False, nullable=False)

    # Derived fields (read-only)
    is_deleted: Mapped[bool] = column_property(
        sa.select(ResourceLockUpgrade.resource_id)
        .where(
            ResourceLockUpgrade.resource_id == resource_id,
            ResourceLockUpgrade.resource_lock_type == "delete",
        )
        .correlate_except(ResourceLockUpgrade)
        .exists()
    )
    is_readonly: Mapped[bool] = column_property(
        sa.select(ResourceLockUpgrade.resource_id)
        .where(
            ResourceLockUpgrade.resource_id == resource_id,
            ResourceLockUpgrade.resource_lock_type == "readonly",
        )
        .correlate_except(ResourceLockUpgrade)
        .exists()
    )
    latest_snapshot_id: Mapped[optionalbigint] = column_property(
        sa.Nullable(
            sa.select(ResourceSnapshotUpgrade.resource_snapshot_id)
            .where(ResourceSnapshotUpgrade.resource_id == resource_id)
            .order_by(ResourceSnapshotUpgrade.created_on.desc())
            .limit(1)
            .correlate_except(ResourceSnapshotUpgrade)
            .scalar_subquery()
        )
    )

    # Relationships
    locks: Mapped[list["ResourceLockUpgrade"]] = relationship(
        init=False, back_populates="resource"
    )

    # Initialize default values using dataclass __post_init__ method
    # https://docs.python.org/3/library/dataclasses.html#dataclasses.__post_init__
    def __post_init__(self) -> None:
        timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        self.created_on = timestamp


class PluginTaskParameterTypeUpgrade(UpgradeBase):
    __tablename__ = "plugin_task_parameter_types"

    # Database fields
    resource_snapshot_id: Mapped[intpk]
    resource_id: Mapped[bigint] = mapped_column(nullable=False)
    name: Mapped[text_] = mapped_column(nullable=False)
    structure: Mapped[optionaljson_] = mapped_column(nullable=True)


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    bind = op.get_bind()
    Session = sessionmaker(bind=bind)

    with Session() as session:
        # Search for built-in simple types that are in the database already and haven't
        # been marked as deleted and don't have a "readonly" lock set. Set a "readonly"
        # lock on any records found that match this criteria.
        param_types_no_readonly_locks_stmt = (
            sa.select(PluginTaskParameterTypeUpgrade.resource_id)
            .join(
                ResourceUpgrade,
                PluginTaskParameterTypeUpgrade.resource_id
                == ResourceUpgrade.resource_id,
            )
            .where(
                PluginTaskParameterTypeUpgrade.name.in_(BUILTIN_PARAMETER_TYPES),
                ResourceUpgrade.is_deleted == False,  # noqa: E712
                ResourceUpgrade.is_readonly == False,  # noqa: E712
                ResourceUpgrade.latest_snapshot_id
                == PluginTaskParameterTypeUpgrade.resource_snapshot_id,
            )
        )

        for resource_id in session.scalars(param_types_no_readonly_locks_stmt):
            resource_lock = ResourceLockUpgrade(
                resource_id=resource_id, resource_lock_type="readonly"
            )
            session.add(resource_lock)

        # Get information about the default public group.
        public_group = session.scalar(
            sa.select(GroupUpgrade).where(GroupUpgrade.name == "public")
        )

        # If the public group already exists, then get a list of the built-in simple
        # types that are already registered in the public group. Figure out which
        # built-in types are still missing, register them, and mark them as readonly.
        if public_group:
            existing_builtin_param_types_stmt = (
                sa.select(PluginTaskParameterTypeUpgrade.name)
                .join(
                    ResourceUpgrade,
                    PluginTaskParameterTypeUpgrade.resource_id
                    == ResourceUpgrade.resource_id,
                )
                .where(
                    PluginTaskParameterTypeUpgrade.name.in_(BUILTIN_PARAMETER_TYPES),
                    ResourceUpgrade.group_id == public_group.group_id,
                    ResourceUpgrade.is_deleted == False,  # noqa: E712
                    ResourceUpgrade.latest_snapshot_id
                    == PluginTaskParameterTypeUpgrade.resource_snapshot_id,
                )
            )
            existing_builtin_param_types = list(
                session.scalars(existing_builtin_param_types_stmt).all()
            )
            missing_builtin_param_types = [
                x
                for x in BUILTIN_PARAMETER_TYPES
                if x not in set(existing_builtin_param_types)
            ]

            for builtin_type in missing_builtin_param_types:
                resource = ResourceUpgrade(
                    group_id=public_group.group_id,
                    resource_type="plugin_task_parameter_type",
                )
                session.add(resource)
                session.flush()
                resource_snapshot = ResourceSnapshotUpgrade(
                    resource_id=resource.resource_id,
                    resource_type="plugin_task_parameter_type",
                    user_id=public_group.user_id,
                    description=None,
                )
                session.add(resource_snapshot)
                session.flush()
                param_type = PluginTaskParameterTypeUpgrade(
                    resource_snapshot_id=resource_snapshot.resource_snapshot_id,
                    resource_id=resource.resource_id,
                    name=builtin_type,
                    structure=None,
                )
                resource_lock = ResourceLockUpgrade(
                    resource_id=resource.resource_id, resource_lock_type="readonly"
                )
                session.add(param_type)
                session.add(resource_lock)
                session.flush()

        session.commit()


def downgrade():
    # No downgrade necessary, the readonly locks are simply ignored and hidden when
    # using previous commits.
    pass
