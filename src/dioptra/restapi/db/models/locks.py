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

from sqlalchemy import Column, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dioptra.restapi.db.db import datetimetz, db, intpk, text_

if TYPE_CHECKING:
    from .groups import Group
    from .resources import Resource
    from .users import User

# -- Tables (no ORM) -------------------------------------------------------------------

user_lock_types_table = db.Table(
    "user_lock_types",
    Column("user_lock_type", Text(), primary_key=True),
)
group_lock_types_table = db.Table(
    "group_lock_types",
    Column("group_lock_type", Text(), primary_key=True),
)
resource_lock_types_table = db.Table(
    "resource_lock_types",
    Column("resource_lock_type", Text(), primary_key=True),
)

# -- ORM Classes -----------------------------------------------------------------------


class UserLock(db.Model):  # type: ignore[name-defined]
    __tablename__ = "user_locks"

    # Database fields
    user_id: Mapped[intpk] = mapped_column(ForeignKey("users.user_id"), init=False)
    user_lock_type: Mapped[text_] = mapped_column(
        ForeignKey("user_lock_types.user_lock_type"), primary_key=True
    )
    created_on: Mapped[datetimetz] = mapped_column(init=False, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="locks")

    # Initialize default values using dataclass __post_init__ method
    # https://docs.python.org/3/library/dataclasses.html#dataclasses.__post_init__
    def __post_init__(self) -> None:
        timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        self.created_on = timestamp


class GroupLock(db.Model):  # type: ignore[name-defined]
    __tablename__ = "group_locks"

    # Database fields
    group_id: Mapped[intpk] = mapped_column(ForeignKey("groups.group_id"), init=False)
    group_lock_type: Mapped[text_] = mapped_column(
        ForeignKey("group_lock_types.group_lock_type"), primary_key=True
    )
    created_on: Mapped[datetimetz] = mapped_column(init=False, nullable=False)

    # Relationships
    group: Mapped["Group"] = relationship("Group", back_populates="locks")

    # Initialize default values using dataclass __post_init__ method
    # https://docs.python.org/3/library/dataclasses.html#dataclasses.__post_init__
    def __post_init__(self) -> None:
        timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        self.created_on = timestamp


class ResourceLock(db.Model):  # type: ignore[name-defined]
    __tablename__ = "resource_locks"

    # Database fields
    resource_id: Mapped[intpk] = mapped_column(
        ForeignKey("resources.resource_id"), init=False
    )
    resource_lock_type: Mapped[text_] = mapped_column(
        ForeignKey("resource_lock_types.resource_lock_type"), primary_key=True
    )
    created_on: Mapped[datetimetz] = mapped_column(init=False, nullable=False)

    # Relationships
    resource: Mapped["Resource"] = relationship("Resource", back_populates="locks")

    # Initialize default values using dataclass __post_init__ method
    # https://docs.python.org/3/library/dataclasses.html#dataclasses.__post_init__
    def __post_init__(self) -> None:
        timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        self.created_on = timestamp
