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
import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dioptra.restapi.db.db import bigint, datetimetz, db, intpk, text_

if TYPE_CHECKING:
    from .groups import Group
    from .resources import Resource, SharedResource
    from .users import User

# -- ORM Classes -----------------------------------------------------------------------


class Tag(db.Model):  # type: ignore[name-defined]
    __tablename__ = "tags"

    # Database fields
    tag_id: Mapped[intpk] = mapped_column(init=False)
    group_id: Mapped[bigint] = mapped_column(
        ForeignKey("groups.group_id"), init=False, nullable=False
    )
    user_id: Mapped[bigint] = mapped_column(
        ForeignKey("users.user_id"), init=False, nullable=False
    )
    name: Mapped[text_] = mapped_column(nullable=False)
    created_on: Mapped[datetimetz] = mapped_column(init=False, nullable=False)
    last_modified_on: Mapped[datetimetz] = mapped_column(init=False, nullable=False)

    # Relationships
    owner: Mapped["Group"] = relationship(back_populates="available_tags")
    creator: Mapped["User"] = relationship(back_populates="created_tags")
    resources: Mapped[list["Resource"]] = relationship(
        init=False, secondary="resource_tags", back_populates="tags"
    )
    shared_resources: Mapped[list["SharedResource"]] = relationship(
        init=False, secondary="shared_resource_tags", back_populates="tags"
    )

    # Additional settings
    __table_args__ = (Index(None, "group_id", "name", unique=True),)

    # Initialize default values using dataclass __post_init__ method
    # https://docs.python.org/3/library/dataclasses.html#dataclasses.__post_init__
    def __post_init__(self) -> None:
        timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        self.created_on = timestamp
        self.last_modified_on = timestamp
