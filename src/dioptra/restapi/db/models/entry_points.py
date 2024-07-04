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
from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, ForeignKeyConstraint, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dioptra.restapi.db.db import bigint, db, intpk, optionalstr, text_

from .resources import ResourceSnapshot

if TYPE_CHECKING:
    from .jobs import EntryPointJob
    from .plugins import Plugin, PluginFile
    from .resources import Resource


# -- Tables (no ORM) -------------------------------------------------------------------

entry_point_parameter_types_table = db.Table(
    "entry_point_parameter_types",
    Column("parameter_type", Text(), primary_key=True),
)

# -- ORM Classes -----------------------------------------------------------------------


class EntryPoint(ResourceSnapshot):
    __tablename__ = "entry_points"

    # Database fields
    resource_snapshot_id: Mapped[intpk] = mapped_column(init=False)
    resource_id: Mapped[bigint] = mapped_column(init=False, nullable=False, index=True)
    name: Mapped[text_] = mapped_column(nullable=False, index=True)
    task_graph: Mapped[text_] = mapped_column(nullable=False)

    # Relationships
    parameters: Mapped[list["EntryPointParameter"]] = relationship(
        back_populates="entry_point"
    )
    entry_point_jobs: Mapped[list["EntryPointJob"]] = relationship(
        init=False, viewonly=True
    )
    entry_point_plugin_files: Mapped[list["EntryPointPluginFile"]] = relationship(
        init=False, back_populates="entry_point"
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
    )
    __mapper_args__ = {
        "polymorphic_identity": "entry_point",
    }


class EntryPointParameter(db.Model):  # type: ignore[name-defined]
    __tablename__ = "entry_point_parameters"

    # Database fields
    entry_point_resource_snapshot_id: Mapped[intpk] = mapped_column(
        ForeignKey("entry_points.resource_snapshot_id"), init=False
    )
    parameter_number: Mapped[intpk]
    parameter_type: Mapped[text_] = mapped_column(
        ForeignKey("entry_point_parameter_types.parameter_type"),
        nullable=False,
        index=True,
    )
    name: Mapped[text_] = mapped_column(nullable=False)
    default_value: Mapped[optionalstr]

    # Relationships
    entry_point: Mapped["EntryPoint"] = relationship(
        init=False, back_populates="parameters"
    )
    values: Mapped[list["EntryPointParameterValue"]] = relationship(
        init=False, viewonly=True
    )

    __table_args__ = (
        Index(None, "entry_point_resource_snapshot_id", "name", unique=True),
    )


class EntryPointParameterValue(db.Model):  # type: ignore[name-defined]
    __tablename__ = "entry_point_parameter_values"

    # Database fields
    job_resource_id: Mapped[intpk] = mapped_column(
        ForeignKey("resources.resource_id"), init=False
    )
    entry_point_resource_snapshot_id: Mapped[intpk] = mapped_column(init=False)
    parameter_number: Mapped[intpk] = mapped_column(init=False)
    value: Mapped[optionalstr]

    # Relationships
    job_resource: Mapped["Resource"] = relationship()
    parameter: Mapped["EntryPointParameter"] = relationship(
        back_populates="values", lazy="joined"
    )
    entry_point_job: Mapped["EntryPointJob"] = relationship(
        init=False,
        back_populates="entry_point_parameter_values",
        overlaps="job_resource,parameter,values",
    )

    # Additional settings
    __table_args__ = (
        Index(None, "job_resource_id", "parameter_number", unique=True),
        ForeignKeyConstraint(
            ["entry_point_resource_snapshot_id", "parameter_number"],
            [
                "entry_point_parameters.entry_point_resource_snapshot_id",
                "entry_point_parameters.parameter_number",
            ],
        ),
        ForeignKeyConstraint(
            ["entry_point_resource_snapshot_id", "job_resource_id"],
            [
                "entry_point_jobs.entry_point_resource_snapshot_id",
                "entry_point_jobs.job_resource_id",
            ],
        ),
    )


class EntryPointPluginFile(db.Model):  # type: ignore[name-defined]
    __tablename__ = "entry_point_plugin_files"

    # Database fields
    entry_point_resource_snapshot_id: Mapped[intpk] = mapped_column(
        ForeignKey("entry_points.resource_snapshot_id"), init=False
    )
    plugin_resource_snapshot_id: Mapped[intpk] = mapped_column(
        ForeignKey("plugins.resource_snapshot_id"), init=False
    )
    plugin_file_resource_snapshot_id: Mapped[intpk] = mapped_column(
        ForeignKey("plugin_files.resource_snapshot_id"), init=False
    )

    # Relationships
    entry_point: Mapped["EntryPoint"] = relationship(
        back_populates="entry_point_plugin_files", lazy="joined"
    )
    plugin: Mapped["Plugin"] = relationship(lazy="joined")
    plugin_file: Mapped["PluginFile"] = relationship(lazy="joined")
