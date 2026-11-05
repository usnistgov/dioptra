"""Remove ML model registry and its resource metadata, preserving artifacts.

Revision ID: 484286c49669
Revises: e64f9b2a7130
Create Date: 2026-11-03 16:26:00.963036

Registry data is permanently deleted. Downgrade restores only the empty schema
and resource ontology, not the deleted models, versions or associations.
"""

import sqlalchemy as sa
from alembic import op

revision = "484286c49669"
down_revision = "e64f9b2a7130"
branch_labels = None
depends_on = None

MODEL_TYPES = ("ml_model", "ml_model_version")
resource_types = sa.table("resource_types", sa.column("resource_type", sa.Text()))
dependency_types = sa.table(
    "resource_dependency_types",
    sa.column("parent_resource_type", sa.Text()),
    sa.column("child_resource_type", sa.Text()),
)


def upgrade() -> None:
    # Use migration-local SQL tables: the application no longer maps these types.
    connection = op.get_bind()
    resources = sa.table(
        "resources", sa.column("resource_id"), sa.column("resource_type")
    )
    model_ids = sa.select(resources.c.resource_id).where(
        resources.c.resource_type.in_(MODEL_TYPES)
    )
    shares = sa.table(
        "shared_resources", sa.column("shared_resource_id"), sa.column("resource_id")
    )
    share_tags = sa.table("shared_resource_tags", sa.column("shared_resource_id"))
    connection.execute(
        share_tags.delete().where(
            share_tags.c.shared_resource_id.in_(
                sa.select(shares.c.shared_resource_id).where(
                    shares.c.resource_id.in_(model_ids)
                )
            )
        )
    )
    for name in ("shared_resources", "resource_tags", "resource_locks"):
        table = sa.table(name, sa.column("resource_id"))
        connection.execute(table.delete().where(table.c.resource_id.in_(model_ids)))

    dependencies = sa.table(
        "resource_dependencies",
        sa.column("parent_resource_id"),
        sa.column("child_resource_id"),
    )
    connection.execute(
        dependencies.delete().where(
            sa.or_(
                dependencies.c.parent_resource_id.in_(model_ids),
                dependencies.c.child_resource_id.in_(model_ids),
            )
        )
    )
    drafts = sa.table("draft_resources", sa.column("resource_type"))
    connection.execute(drafts.delete().where(drafts.c.resource_type.in_(MODEL_TYPES)))

    # Drop the subclasses before deleting their base snapshots. Artifacts are
    # referenced by versions, but are independent resources and must survive.
    op.drop_table("ml_model_versions")
    op.drop_table("ml_models")
    snapshots = sa.table("resource_snapshots", sa.column("resource_id"))
    connection.execute(snapshots.delete().where(snapshots.c.resource_id.in_(model_ids)))
    connection.execute(
        resources.delete().where(resources.c.resource_type.in_(MODEL_TYPES))
    )
    connection.execute(
        dependency_types.delete().where(
            sa.or_(
                dependency_types.c.parent_resource_type.in_(MODEL_TYPES),
                dependency_types.c.child_resource_type.in_(MODEL_TYPES),
            )
        )
    )
    connection.execute(
        resource_types.delete().where(resource_types.c.resource_type.in_(MODEL_TYPES))
    )


def downgrade() -> None:
    # Recreate empty registry tables; deleted data cannot be recovered.
    op.bulk_insert(resource_types, [{"resource_type": name} for name in MODEL_TYPES])
    op.bulk_insert(
        dependency_types,
        [
            {
                "parent_resource_type": "ml_model",
                "child_resource_type": "ml_model_version",
            }
        ],
    )
    bigint = sa.BigInteger().with_variant(sa.Integer(), "sqlite")
    op.create_table(
        "ml_models",
        sa.Column("resource_snapshot_id", bigint, nullable=False),
        sa.Column("resource_id", bigint, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["resource_snapshot_id", "resource_id"],
            [
                "resource_snapshots.resource_snapshot_id",
                "resource_snapshots.resource_id",
            ],
            name=op.f("fk_ml_models_resource_snapshot_id_resource_snapshots"),
        ),
        sa.PrimaryKeyConstraint("resource_snapshot_id", name=op.f("pk_ml_models")),
        sa.UniqueConstraint(
            "resource_snapshot_id",
            "resource_id",
            name=op.f("uq_ml_models_resource_snapshot_id"),
        ),
    )
    op.create_index(
        op.f("ix_ml_models_resource_snapshot_id"),
        "ml_models",
        ["resource_snapshot_id", "resource_id"],
        unique=True,
    )
    op.create_index(op.f("ix_ml_models_resource_id"), "ml_models", ["resource_id"])
    op.create_table(
        "ml_model_versions",
        sa.Column("resource_snapshot_id", bigint, nullable=False),
        sa.Column("resource_id", bigint, nullable=False),
        sa.Column("artifact_resource_snapshot_id", bigint, nullable=False),
        sa.Column("version_number", bigint, nullable=False),
        sa.ForeignKeyConstraint(
            ["artifact_resource_snapshot_id"],
            ["artifacts.resource_snapshot_id"],
            name=op.f("fk_ml_model_versions_artifact_resource_snapshot_id_artifacts"),
        ),
        sa.ForeignKeyConstraint(
            ["resource_snapshot_id", "resource_id"],
            [
                "resource_snapshots.resource_snapshot_id",
                "resource_snapshots.resource_id",
            ],
            name=op.f("fk_ml_model_versions_resource_snapshot_id_resource_snapshots"),
        ),
        sa.PrimaryKeyConstraint(
            "resource_snapshot_id", name=op.f("pk_ml_model_versions")
        ),
        sa.UniqueConstraint(
            "resource_snapshot_id",
            "resource_id",
            name=op.f("uq_ml_model_versions_resource_snapshot_id"),
        ),
    )
    op.create_index(
        op.f("ix_ml_model_versions_resource_snapshot_id"),
        "ml_model_versions",
        ["resource_snapshot_id", "resource_id", "artifact_resource_snapshot_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_ml_model_versions_resource_id"), "ml_model_versions", ["resource_id"]
    )
