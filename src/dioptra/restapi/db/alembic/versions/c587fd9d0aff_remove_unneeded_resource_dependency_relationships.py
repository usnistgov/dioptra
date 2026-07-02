"""remove unneeded resource dependency relationships

Revision ID: c587fd9d0aff
Revises: ad4f89b2288d
Create Date: 2026-04-14 13:40:15.520745

"""

from typing import Annotated

import sqlalchemy as sa
from alembic import op
from sqlalchemy import insert, literal_column, select, union_all
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
    sessionmaker,
)

# revision identifiers, used by Alembic.
revision = "c587fd9d0aff"
down_revision = "ad4f89b2288d"
branch_labels = None
depends_on = None

# Migration data models
intpk = Annotated[
    int,
    mapped_column(sa.BigInteger().with_variant(sa.Integer, "sqlite"), primary_key=True),
]
text_ = Annotated[str, mapped_column(sa.Text())]


class UpgradeBase(DeclarativeBase, MappedAsDataclass):
    pass


class DowngradeBase(DeclarativeBase, MappedAsDataclass):
    pass


# Model classes
class ResourceDependencyType(UpgradeBase):
    __tablename__ = "resource_dependency_types"
    parent_resource_type: Mapped[str] = mapped_column(primary_key=True)
    child_resource_type: Mapped[str] = mapped_column(primary_key=True)


class ResourceDependency(UpgradeBase):
    __tablename__ = "resource_dependencies"
    parent_resource_id: Mapped[int] = mapped_column(primary_key=True)
    child_resource_id: Mapped[int] = mapped_column(primary_key=True)
    parent_resource_type: Mapped[str] = mapped_column(primary_key=True)
    child_resource_type: Mapped[str] = mapped_column(primary_key=True)


class PluginPluginFile(UpgradeBase):
    __tablename__ = "plugin_plugin_files"
    plugin_resource_snapshot_id: Mapped[int] = mapped_column(primary_key=True)
    plugin_file_resource_snapshot_id: Mapped[int] = mapped_column(primary_key=True)


class EntryPointPlugin(UpgradeBase):
    __tablename__ = "entry_point_plugins"
    entry_point_resource_snapshot_id: Mapped[int] = mapped_column(primary_key=True)
    plugin_resource_snapshot_id: Mapped[int] = mapped_column(primary_key=True)


class EntryPointArtifactPlugin(UpgradeBase):
    __tablename__ = "entry_point_artifact_plugins"
    entry_point_resource_snapshot_id: Mapped[int] = mapped_column(primary_key=True)
    plugin_resource_snapshot_id: Mapped[int] = mapped_column(primary_key=True)


class ResourceSnapshot(UpgradeBase):
    __tablename__ = "resource_snapshots"
    resource_snapshot_id: Mapped[int] = mapped_column(primary_key=True)
    resource_id: Mapped[int] = mapped_column(primary_key=True)
    resource_type: Mapped[str] = mapped_column(primary_key=True)


def upgrade() -> None:
    """Remove redundant relationships from resource_dependencies."""
    bind = op.get_bind()
    session = sessionmaker(bind=bind)()

    dependency_types = [
        ("plugin", "plugin_file"),
        ("entry_point", "plugin"),
        ("job", "job"),
    ]

    for parent_resource_type, child_resource_type in dependency_types:
        # Delete relationship entries before dependency types due to FK constraints.
        session.query(ResourceDependency).filter(
            ResourceDependency.parent_resource_type == parent_resource_type,
            ResourceDependency.child_resource_type == child_resource_type,
        ).delete()

        dep_type = (
            session.query(ResourceDependencyType)
            .filter(
                ResourceDependencyType.parent_resource_type == parent_resource_type,
                ResourceDependencyType.child_resource_type == child_resource_type,
            )
            .first()
        )
        if dep_type:
            session.delete(dep_type)

    session.commit()


def downgrade() -> None:
    """Recreate removed resource dependency relationships where possible."""
    bind = op.get_bind()
    session = sessionmaker(bind=bind)()

    for parent_resource_type, child_resource_type in [
        ("plugin", "plugin_file"),
        ("entry_point", "plugin"),
        ("job", "job"),
    ]:
        session.merge(
            ResourceDependencyType(
                parent_resource_type=parent_resource_type,
                child_resource_type=child_resource_type,
            )
        )

    # Use existing model class tables to create aliases
    pg_plugin_files = PluginPluginFile.__table__
    entry_point_plugins = EntryPointPlugin.__table__
    entry_point_artifact_plugins = EntryPointArtifactPlugin.__table__
    resource_snapshots = ResourceSnapshot.__table__

    rs_plugin_parent = resource_snapshots.alias("rs_plugin_parent")
    rs_plugin_child = resource_snapshots.alias("rs_plugin_child")
    plugin_plugin_file_select = (
        select(
            rs_plugin_parent.c.resource_id.label("parent_resource_id"),
            rs_plugin_child.c.resource_id.label("child_resource_id"),
            literal_column("'plugin'").label("parent_resource_type"),
            literal_column("'plugin_file'").label("child_resource_type"),
        )
        .distinct()
        .select_from(pg_plugin_files)
        .join(
            rs_plugin_parent,
            rs_plugin_parent.c.resource_snapshot_id
            == pg_plugin_files.c.plugin_resource_snapshot_id,
        )
        .join(
            rs_plugin_child,
            rs_plugin_child.c.resource_snapshot_id
            == pg_plugin_files.c.plugin_file_resource_snapshot_id,
        )
    )

    entry_point_plugin_associations = union_all(
        select(
            entry_point_plugins.c.entry_point_resource_snapshot_id,
            entry_point_plugins.c.plugin_resource_snapshot_id,
        ),
        select(
            entry_point_artifact_plugins.c.entry_point_resource_snapshot_id,
            entry_point_artifact_plugins.c.plugin_resource_snapshot_id,
        ),
    ).subquery()
    rs_entry_point_parent = resource_snapshots.alias("rs_entry_point_parent")
    rs_entry_point_child = resource_snapshots.alias("rs_entry_point_child")
    entry_point_plugin_select = (
        select(
            rs_entry_point_parent.c.resource_id.label("parent_resource_id"),
            rs_entry_point_child.c.resource_id.label("child_resource_id"),
            literal_column("'entry_point'").label("parent_resource_type"),
            literal_column("'plugin'").label("child_resource_type"),
        )
        .select_from(entry_point_plugin_associations)
        .join(
            rs_entry_point_parent,
            rs_entry_point_parent.c.resource_snapshot_id
            == entry_point_plugin_associations.c.entry_point_resource_snapshot_id,
        )
        .join(
            rs_entry_point_child,
            rs_entry_point_child.c.resource_snapshot_id
            == entry_point_plugin_associations.c.plugin_resource_snapshot_id,
        )
        .distinct()
    )

    insert_stmt = insert(ResourceDependency).from_select(
        [
            "parent_resource_id",
            "child_resource_id",
            "parent_resource_type",
            "child_resource_type",
        ],
        union_all(plugin_plugin_file_select, entry_point_plugin_select),
    )
    session.execute(insert_stmt)

    session.commit()
