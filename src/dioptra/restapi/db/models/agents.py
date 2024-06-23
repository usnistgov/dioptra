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
from sqlalchemy import Column, ForeignKey, ForeignKeyConstraint, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from dioptra.restapi.db.db import bigint, db, intpk, json_, optionaljson_, text_

from .resources import ResourceSnapshot

# -- Tables (no ORM) -------------------------------------------------------------------

agent_types_table = db.Table(
    "agent_types",
    Column("agent_type", Text(), primary_key=True),
)

# -- ORM Classes -----------------------------------------------------------------------


class Agent(ResourceSnapshot):
    __tablename__ = "agents"

    # Database fields
    resource_snapshot_id: Mapped[intpk] = mapped_column(init=False)
    resource_id: Mapped[bigint] = mapped_column(init=False, nullable=False)
    agent_type: Mapped[text_] = mapped_column(
        ForeignKey("agent_types.agent_type"), nullable=False, index=True
    )
    name: Mapped[text_] = mapped_column(nullable=False, index=True)
    public_key: Mapped[json_] = mapped_column(nullable=False)
    settings: Mapped[optionaljson_] = mapped_column(nullable=True)

    # Additional settings
    __table_args__ = (  # type: ignore[assignment]
        Index(None, "resource_snapshot_id", "resource_id", unique=True),
        Index(None, "resource_id", "agent_type"),
        ForeignKeyConstraint(
            ["resource_snapshot_id", "resource_id"],
            [
                "resource_snapshots.resource_snapshot_id",
                "resource_snapshots.resource_id",
            ],
        ),
    )
    __mapper_args__ = {
        "polymorphic_identity": "agent",
    }
