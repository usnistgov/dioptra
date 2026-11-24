# This Software (Dioptra) is being made available as a public service by the
# National Institute of Standards and Technology (NIST), an Agency of the United
# States Department of Commerce. This software was developed in part by employees of
# NIST and in part by NIST contractors. Copyright in portions of this software that
# were developed by NIST contractors has been licensed or assigned to NIST. Pursuant
# to Title 17 United States Code Section 105, works of NIST employees are not
# subject to copyright protection in the United States. However, NIST may hold
# international copyright in software created by its employees and domestic
# copyright (or licensing rights) in portions of software that were assigned or
# licensed to NIST. To the extent that NIST holds copyright in this software, it is
# being made available under the Creative Commons Attribution 4.0 International
# license (CC BY 4.0). The disclaimers of the CC BY 4.0 license apply to all parts
# of the software developed or licensed by NIST.
#
# ACCESS THE FULL CC BY 4.0 LICENSE HERE:
# https://creativecommons.org/licenses/by/4.0/legalcode

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    and_,
    select,
)
from sqlalchemy.orm import Mapped, column_property, foreign, mapped_column, relationship

from dioptra.restapi.db.db import bigint, bool_, db, intpk, optionalbigint, text_

from .plugins import ArtifactTask, PluginPluginFile
from .resources import Resource, ResourceSnapshot, resource_dependencies_table

# -- ORM Classes -----------------------------------------------------------------------


class ArtifactStoragePrefix(db.Model):  # type: ignore[name-defined]
    """Store the producing run's immutable prefix under the deployment artifact base.

    Attributes:
        storage_prefix_id: Database identifier shared by locations for this run.
        relative_prefix: Canonical run directory relative to the deployment base.
    """

    __tablename__ = "artifact_storage_prefixes"

    # Database fields
    storage_prefix_id: Mapped[intpk] = mapped_column(init=False)
    relative_prefix: Mapped[text_] = mapped_column(nullable=False, unique=True)


class ArtifactLocation(db.Model):  # type: ignore[name-defined]
    """Store the location shared by every snapshot of one artifact resource.

    Attributes:
        artifact_resource_id: Resource identifier shared by the artifact snapshots.
        artifact_resource_type: Discriminator enforcing that the resource is an artifact.
        storage_prefix_id: Identifier of the producing run's saved prefix.
        relative_path: Canonical file or directory path under that prefix.
        storage_prefix: Producing prefix shared by artifacts from the same run.
    """

    __tablename__ = "artifact_locations"

    # Database fields
    artifact_resource_id: Mapped[intpk] = mapped_column(init=False, autoincrement=False)
    artifact_resource_type: Mapped[text_] = mapped_column(
        init=False, server_default="artifact"
    )
    storage_prefix_id: Mapped[bigint] = mapped_column(
        ForeignKey("artifact_storage_prefixes.storage_prefix_id"),
        nullable=False,
        index=True,
    )
    relative_path: Mapped[text_] = mapped_column(nullable=False)

    # Relationships
    storage_prefix: Mapped[ArtifactStoragePrefix] = relationship(
        init=False, lazy="joined"
    )

    # Additional settings
    __table_args__ = (
        CheckConstraint("artifact_resource_type = 'artifact'", name="artifact_type"),
        ForeignKeyConstraint(
            ["artifact_resource_id", "artifact_resource_type"],
            ["resources.resource_id", "resources.resource_type"],
        ),
    )


class Artifact(ResourceSnapshot):
    __tablename__ = "artifacts"

    # Database fields
    resource_snapshot_id: Mapped[intpk] = mapped_column(init=False)
    resource_id: Mapped[bigint] = mapped_column(init=False, nullable=False, index=True)
    is_dir: Mapped[bool_] = mapped_column(nullable=False)
    file_size: Mapped[optionalbigint] = mapped_column(nullable=True)

    plugin_snapshot_id: Mapped[bigint] = mapped_column(init=False, nullable=True)
    plugin_file_id: Mapped[bigint] = mapped_column(init=False, nullable=True)
    task_name: Mapped[text_] = mapped_column(init=False, nullable=True)

    # Derived fields (read-only)
    job_id: Mapped[bigint] = column_property(
        select(Resource.resource_id)
        .join(
            resource_dependencies_table,
            and_(
                Resource.resource_id
                == resource_dependencies_table.c.parent_resource_id,
                resource_dependencies_table.c.child_resource_id == resource_id,
            ),
        )
        .limit(1)
        .correlate_except(Resource)
        .scalar_subquery()
    )

    # Relationships
    location: Mapped[ArtifactLocation | None] = relationship(
        primaryjoin=lambda: (
            Artifact.resource_id == foreign(ArtifactLocation.artifact_resource_id)
        ),
        default=None,
        lazy="joined",
    )
    task: Mapped["ArtifactTask"] = relationship(init=False)
    plugin_plugin_file: Mapped["PluginPluginFile"] = relationship(
        init=False, overlaps="task"
    )

    # Additional settings
    __table_args__ = (  # type: ignore[assignment]
        Index(None, "resource_snapshot_id", "resource_id", unique=True),
        ForeignKeyConstraint(
            ["resource_snapshot_id", "resource_id"],
            [
                "resource_snapshots.resource_snapshot_id",
                "resource_snapshots.resource_id",
            ],
        ),
        ForeignKeyConstraint(
            ["plugin_file_id", "task_name"],
            [
                "plugin_tasks.plugin_file_resource_snapshot_id",
                "plugin_tasks.plugin_task_name",
            ],
        ),
        ForeignKeyConstraint(
            ["plugin_snapshot_id", "plugin_file_id"],
            [
                "plugin_plugin_files.plugin_resource_snapshot_id",
                "plugin_plugin_files.plugin_file_resource_snapshot_id",
            ],
        ),
    )
    __mapper_args__ = {
        "polymorphic_identity": "artifact",
    }
