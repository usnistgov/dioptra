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
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from dioptra.restapi.db.db import (
    datetimetz,
    db,
    guid,
    intpk,
    optionaldatetimetz,
    optionalstr,
    text_,
)

from .constants import user_lock_types
from .locks import UserLock

if TYPE_CHECKING:
    from .groups import Group, GroupManager, GroupMember
    from .resources import DraftResource, ResourceSnapshot, SharedResource
    from .tags import Tag

# -- ORM Classes -----------------------------------------------------------------------


class User(db.Model):  # type: ignore[name-defined]
    __tablename__ = "users"

    # Database fields
    user_id: Mapped[intpk] = mapped_column(init=False)
    alternative_id: Mapped[guid] = mapped_column(
        init=False, nullable=False, unique=True, index=True
    )
    username: Mapped[text_] = mapped_column(nullable=False, index=True)
    password: Mapped[optionalstr]
    email_address: Mapped[text_] = mapped_column(nullable=False, index=True)
    created_on: Mapped[datetimetz] = mapped_column(init=False, nullable=False)
    last_modified_on: Mapped[datetimetz] = mapped_column(init=False, nullable=False)
    last_login_on: Mapped[optionaldatetimetz] = mapped_column(init=False, nullable=True)
    password_expire_on: Mapped[datetimetz] = mapped_column(init=False, nullable=False)

    # Derived fields (read-only)
    is_deleted: Mapped[bool] = column_property(
        select(UserLock.user_id)
        .where(
            UserLock.user_id == user_id,
            UserLock.user_lock_type == user_lock_types.DELETE,
        )
        .correlate_except(UserLock)
        .exists()
    )

    # Relationships
    group_memberships: Mapped[list["GroupMember"]] = relationship(
        init=False, back_populates="user"
    )
    group_managerships: Mapped[list["GroupManager"]] = relationship(
        init=False, back_populates="user"
    )
    created_drafts: Mapped[list["DraftResource"]] = relationship(
        init=False, viewonly=True
    )
    created_groups: Mapped[list["Group"]] = relationship(init=False, viewonly=True)
    created_shares: Mapped[list["SharedResource"]] = relationship(
        init=False, viewonly=True
    )
    created_snapshots: Mapped[list["ResourceSnapshot"]] = relationship(
        init=False, viewonly=True
    )
    created_tags: Mapped[list["Tag"]] = relationship(init=False, viewonly=True)
    locks: Mapped[list["UserLock"]] = relationship(init=False, back_populates="user")

    # Initialize default values using dataclass __post_init__ method
    # https://docs.python.org/3/library/dataclasses.html#dataclasses.__post_init__
    def __post_init__(self) -> None:
        timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        self.alternative_id = uuid.uuid4()
        self.created_on = timestamp
        self.last_modified_on = timestamp
        self.last_login_on = None
        self.password_expire_on = timestamp + datetime.timedelta(days=365)

    @property
    def is_authenticated(self) -> bool:
        """Return True if the user is authenticated, False otherwise."""
        return self.is_active

    @property
    def is_active(self) -> bool:
        """Return True if the user account is active, False otherwise."""
        return not self.is_deleted

    @property
    def is_anonymous(self) -> bool:
        """Return True if the user is registered, False otherwise."""
        return False

    def get_id(self) -> str:
        """Get the user's session identifier.

        Returns:
            The user's identifier as a string.
        """
        return str(self.alternative_id)
