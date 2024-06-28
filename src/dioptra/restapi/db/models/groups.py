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

from sqlalchemy import ForeignKey, select
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from dioptra.restapi.db.db import bigint, datetimetz, db, intpk, text_

from .constants import group_lock_types
from .locks import GroupLock

if TYPE_CHECKING:
    from .resources import DraftResource, Resource, SharedResource
    from .tags import Tag
    from .users import User

# -- ORM Classes -----------------------------------------------------------------------


class Group(db.Model):  # type: ignore[name-defined]
    __tablename__ = "groups"

    # Database fields
    group_id: Mapped[intpk] = mapped_column(init=False)
    name: Mapped[text_] = mapped_column(nullable=False)
    user_id: Mapped[bigint] = mapped_column(
        ForeignKey("users.user_id"), init=False, nullable=False, index=True
    )
    created_on: Mapped[datetimetz] = mapped_column(init=False, nullable=False)
    last_modified_on: Mapped[datetimetz] = mapped_column(init=False, nullable=False)

    # Derived fields (read-only)
    is_deleted: Mapped[bool] = column_property(
        select(GroupLock.group_id)
        .where(
            GroupLock.group_id == group_id,
            GroupLock.group_lock_type == group_lock_types.DELETE,
        )
        .correlate_except(GroupLock)
        .exists()
    )

    # Relationships
    creator: Mapped["User"] = relationship(back_populates="created_groups")
    members: Mapped[list["GroupMember"]] = relationship(
        init=False, back_populates="group"
    )
    managers: Mapped[list["GroupManager"]] = relationship(
        init=False, back_populates="group"
    )
    draft_resources: Mapped[list["DraftResource"]] = relationship(
        init=False, viewonly=True
    )
    locks: Mapped[list["GroupLock"]] = relationship(init=False, back_populates="group")
    resources: Mapped[list["Resource"]] = relationship(init=False, viewonly=True)
    received_shares: Mapped[list["SharedResource"]] = relationship(
        init=False, viewonly=True
    )
    available_tags: Mapped[list["Tag"]] = relationship(init=False, viewonly=True)

    # Initialize default values using dataclass __post_init__ method
    # https://docs.python.org/3/library/dataclasses.html#dataclasses.__post_init__
    def __post_init__(self) -> None:
        timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        self.created_on = timestamp
        self.last_modified_on = timestamp


class GroupMember(db.Model):  # type: ignore[name-defined]
    __tablename__ = "group_members"

    # Database fields
    user_id: Mapped[intpk] = mapped_column(ForeignKey("users.user_id"), init=False)
    group_id: Mapped[intpk] = mapped_column(ForeignKey("groups.group_id"), init=False)
    read: Mapped[bool]
    write: Mapped[bool]
    share_read: Mapped[bool]
    share_write: Mapped[bool]

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="group_memberships", lazy="joined"
    )
    group: Mapped["Group"] = relationship(init=False, back_populates="members")


class GroupManager(db.Model):  # type: ignore[name-defined]
    __tablename__ = "group_managers"

    # Database fields
    user_id: Mapped[intpk] = mapped_column(ForeignKey("users.user_id"), init=False)
    group_id: Mapped[intpk] = mapped_column(ForeignKey("groups.group_id"), init=False)
    owner: Mapped[bool]
    admin: Mapped[bool]

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="group_managerships", lazy="joined"
    )
    group: Mapped["Group"] = relationship(init=False, back_populates="managers")
