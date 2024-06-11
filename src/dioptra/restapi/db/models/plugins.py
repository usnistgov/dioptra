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
from sqlalchemy import ForeignKey, ForeignKeyConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dioptra.restapi.db.db import bigint, db, intpk, optionaljson_, optionalstr, text_

from .resources import ResourceSnapshot

# -- ORM Classes -----------------------------------------------------------------------


class Plugin(ResourceSnapshot):
    __tablename__ = "plugins"

    # Database fields
    resource_snapshot_id: Mapped[intpk] = mapped_column(init=False)
    resource_id: Mapped[bigint] = mapped_column(init=False, nullable=False, index=True)
    name: Mapped[text_] = mapped_column(nullable=False, index=True)

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
        "polymorphic_identity": "plugin",
    }


class PluginFile(ResourceSnapshot):
    __tablename__ = "plugin_files"

    # Database fields
    resource_snapshot_id: Mapped[intpk] = mapped_column(init=False)
    resource_id: Mapped[bigint] = mapped_column(init=False, nullable=False, index=True)
    filename: Mapped[text_] = mapped_column(nullable=False, index=True)
    contents: Mapped[optionalstr]

    # Relationships
    tasks: Mapped[list["PluginTask"]] = relationship(init=False, back_populates="file")

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
        "polymorphic_identity": "plugin_file",
    }


class PluginTask(db.Model):  # type: ignore[name-defined]
    __tablename__ = "plugin_tasks"

    # Database fields
    plugin_file_resource_snapshot_id: Mapped[intpk] = mapped_column(
        ForeignKey("plugin_files.resource_snapshot_id"), init=False
    )
    plugin_task_name: Mapped[text_] = mapped_column(primary_key=True)

    # Relationships
    file: Mapped["PluginFile"] = relationship(back_populates="tasks")
    input_parameters: Mapped[list["PluginTaskInputParameter"]] = relationship(
        back_populates="task"
    )
    output_parameters: Mapped[list["PluginTaskOutputParameter"]] = relationship(
        back_populates="task"
    )


class PluginTaskParameterType(ResourceSnapshot):
    __tablename__ = "plugin_task_parameter_types"

    # Database fields
    resource_snapshot_id: Mapped[intpk] = mapped_column(init=False)
    resource_id: Mapped[bigint] = mapped_column(init=False, nullable=False, index=True)
    name: Mapped[text_] = mapped_column(nullable=False, index=True)
    structure: Mapped[optionaljson_] = mapped_column(nullable=True)

    # Relationships
    input_parameters: Mapped[list["PluginTaskInputParameter"]] = relationship(
        init=False, back_populates="parameter_type"
    )
    output_parameters: Mapped[list["PluginTaskOutputParameter"]] = relationship(
        init=False, back_populates="parameter_type"
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
        "polymorphic_identity": "plugin_task_parameter_type",
    }


class PluginTaskInputParameter(db.Model):  # type: ignore[name-defined]
    __tablename__ = "plugin_task_input_parameters"

    # Database fields
    plugin_file_resource_snapshot_id: Mapped[intpk] = mapped_column(init=False)
    plugin_task_name: Mapped[text_] = mapped_column(init=False, primary_key=True)
    parameter_number: Mapped[intpk]
    plugin_task_parameter_type_resource_snapshot_id: Mapped[bigint] = mapped_column(
        ForeignKey("plugin_task_parameter_types.resource_snapshot_id"),
        init=False,
        nullable=False,
        index=True,
    )
    name: Mapped[text_] = mapped_column(nullable=False)

    # Relationships
    task: Mapped["PluginTask"] = relationship(
        init=False, back_populates="input_parameters"
    )
    parameter_type: Mapped["PluginTaskParameterType"] = relationship(
        back_populates="input_parameters"
    )

    # Additional settings
    __table_args__ = (
        Index(
            None, "plugin_file_resource_snapshot_id", "plugin_task_name", unique=True
        ),
        ForeignKeyConstraint(
            ["plugin_file_resource_snapshot_id", "plugin_task_name"],
            [
                "plugin_tasks.plugin_file_resource_snapshot_id",
                "plugin_tasks.plugin_task_name",
            ],
        ),
    )


class PluginTaskOutputParameter(db.Model):  # type: ignore[name-defined]
    __tablename__ = "plugin_task_output_parameters"

    # Database fields
    plugin_file_resource_snapshot_id: Mapped[intpk] = mapped_column(init=False)
    plugin_task_name: Mapped[text_] = mapped_column(init=False, primary_key=True)
    parameter_number: Mapped[intpk]
    plugin_task_parameter_type_resource_snapshot_id: Mapped[bigint] = mapped_column(
        ForeignKey("plugin_task_parameter_types.resource_snapshot_id"),
        init=False,
        nullable=False,
        index=True,
    )
    name: Mapped[text_] = mapped_column(nullable=False)

    # Relationships
    task: Mapped["PluginTask"] = relationship(
        init=False, back_populates="output_parameters"
    )
    parameter_type: Mapped["PluginTaskParameterType"] = relationship(
        back_populates="output_parameters"
    )

    # Additional settings
    __table_args__ = (
        Index(
            None, "plugin_file_resource_snapshot_id", "plugin_task_name", unique=True
        ),
        ForeignKeyConstraint(
            ["plugin_file_resource_snapshot_id", "plugin_task_name"],
            [
                "plugin_tasks.plugin_file_resource_snapshot_id",
                "plugin_tasks.plugin_task_name",
            ],
        ),
    )
