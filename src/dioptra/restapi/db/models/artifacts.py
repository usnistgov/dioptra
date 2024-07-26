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
from sqlalchemy import ForeignKeyConstraint, Index, and_, select
from sqlalchemy.orm import Mapped, column_property, mapped_column

from dioptra.restapi.db.db import bigint, intpk, text_

from .resources import Resource, ResourceSnapshot, resource_dependencies_table

# -- ORM Classes -----------------------------------------------------------------------


class Artifact(ResourceSnapshot):
    __tablename__ = "artifacts"

    # Database fields
    resource_snapshot_id: Mapped[intpk] = mapped_column(init=False)
    resource_id: Mapped[bigint] = mapped_column(init=False, nullable=False, index=True)
    uri: Mapped[text_] = mapped_column(nullable=False)

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
        "polymorphic_identity": "artifact",
    }
