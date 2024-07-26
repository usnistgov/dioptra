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

from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Nullable,
    Text,
    UniqueConstraint,
    and_,
    func,
    select,
)
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from dioptra.restapi.db.db import (
    bigint,
    datetimetz,
    db,
    intpk,
    json_,
    optionalbigint,
    optionalstr,
    text_,
)

from .constants import resource_lock_types
from .locks import ResourceLock

if TYPE_CHECKING:
    from .groups import Group
    from .tags import Tag
    from .users import User

# -- Tables (no ORM) -------------------------------------------------------------------

resource_types_table = db.Table(
    "resource_types",
    Column("resource_type", Text(), primary_key=True),
)
resource_dependencies_table = db.Table(
    "resource_dependencies",
    Column(
        "parent_resource_id",
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
    ),
    Column(
        "child_resource_id",
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
    ),
    Column(
        "parent_resource_type",
        Text(),
        nullable=False,
    ),
    Column(
        "child_resource_type",
        Text(),
        nullable=False,
    ),
    Index(None, "child_resource_id", "parent_resource_id"),
    Index(None, "parent_resource_type", "child_resource_type"),
    ForeignKeyConstraint(
        ["parent_resource_type", "child_resource_type"],
        [
            "resource_dependency_types.parent_resource_type",
            "resource_dependency_types.child_resource_type",
        ],
    ),
    ForeignKeyConstraint(
        ["parent_resource_id", "parent_resource_type"],
        [
            "resources.resource_id",
            "resources.resource_type",
        ],
    ),
    ForeignKeyConstraint(
        ["child_resource_id", "child_resource_type"],
        [
            "resources.resource_id",
            "resources.resource_type",
        ],
    ),
)
resource_dependency_types_table = db.Table(
    "resource_dependency_types",
    Column(
        "parent_resource_type",
        Text(),
        ForeignKey("resource_types.resource_type"),
        primary_key=True,
    ),
    Column(
        "child_resource_type",
        Text(),
        ForeignKey("resource_types.resource_type"),
        primary_key=True,
    ),
)
resource_tags_table = db.Table(
    "resource_tags",
    Column(
        "resource_id",
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("resources.resource_id"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("tags.tag_id"),
        primary_key=True,
    ),
)
shared_resource_tags_table = db.Table(
    "shared_resource_tags",
    Column(
        "shared_resource_id",
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("shared_resources.shared_resource_id"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("tags.tag_id"),
        primary_key=True,
    ),
)

# -- ORM Classes -----------------------------------------------------------------------


class DraftResource(db.Model):  # type: ignore[name-defined]
    __tablename__ = "draft_resources"

    # Database fields
    draft_resource_id: Mapped[intpk] = mapped_column(init=False)
    group_id: Mapped[bigint] = mapped_column(
        ForeignKey("groups.group_id"), init=False, nullable=False
    )
    resource_type: Mapped[text_] = mapped_column(
        ForeignKey("resource_types.resource_type"), nullable=False
    )
    user_id: Mapped[bigint] = mapped_column(
        ForeignKey("users.user_id"), init=False, nullable=False, index=True
    )
    payload: Mapped[json_] = mapped_column(nullable=False)
    created_on: Mapped[datetimetz] = mapped_column(init=False, nullable=False)
    last_modified_on: Mapped[datetimetz] = mapped_column(init=False, nullable=False)

    # Relationships
    target_owner: Mapped["Group"] = relationship(
        back_populates="draft_resources", lazy="joined"
    )
    creator: Mapped["User"] = relationship(
        back_populates="created_drafts", lazy="joined"
    )

    # Additional settings
    __table_args__ = (Index(None, "group_id", "resource_type", "user_id"),)

    # Initialize default values using dataclass __post_init__ method
    # https://docs.python.org/3/library/dataclasses.html#dataclasses.__post_init__
    def __post_init__(self) -> None:
        timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        self.created_on = timestamp
        self.last_modified_on = timestamp


class ResourceSnapshot(db.Model):  # type: ignore[name-defined]
    __tablename__ = "resource_snapshots"

    # Database fields
    resource_snapshot_id: Mapped[intpk] = mapped_column(init=False)
    resource_id: Mapped[bigint] = mapped_column(init=False, nullable=False)
    resource_type: Mapped[text_] = mapped_column(
        ForeignKey("resource_types.resource_type"),
        init=False,
        nullable=False,
        index=True,
    )
    user_id: Mapped[bigint] = mapped_column(
        ForeignKey("users.user_id"), init=False, nullable=False
    )
    description: Mapped[optionalstr] = mapped_column(index=True)
    created_on: Mapped[datetimetz] = mapped_column(init=False, nullable=False)

    # Relationships
    resource: Mapped["Resource"] = relationship(
        back_populates="versions", lazy="joined"
    )
    creator: Mapped["User"] = relationship(
        back_populates="created_snapshots", lazy="joined"
    )

    # Proxy relationships
    parents: AssociationProxy[list["Resource"]] = association_proxy(
        "resource", "parents", init=False
    )
    children: AssociationProxy[list["Resource"]] = association_proxy(
        "resource", "children", init=False
    )
    tags: AssociationProxy[list["Resource"]] = association_proxy(
        "resource", "tags", init=False
    )

    # Additional settings
    __table_args__ = (
        Index(
            None, "resource_snapshot_id", "resource_id", "resource_type", unique=True
        ),
        Index(None, "resource_id", "created_on"),
        ForeignKeyConstraint(
            ["resource_id", "resource_type"],
            ["resources.resource_id", "resources.resource_type"],
        ),
        UniqueConstraint("resource_snapshot_id", "resource_id"),
    )
    __mapper_args__ = {
        "polymorphic_identity": "resource_snapshot",
        "polymorphic_on": "resource_type",
    }

    # Initialize default values using dataclass __post_init__ method
    # https://docs.python.org/3/library/dataclasses.html#dataclasses.__post_init__
    def __post_init__(self) -> None:
        timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        self.created_on = timestamp


class Resource(db.Model):  # type: ignore[name-defined]
    __tablename__ = "resources"

    # Database fields
    resource_id: Mapped[intpk] = mapped_column(init=False)
    group_id: Mapped[bigint] = mapped_column(
        ForeignKey("groups.group_id"), init=False, nullable=False
    )
    resource_type: Mapped[text_] = mapped_column(
        ForeignKey("resource_types.resource_type"), nullable=False, index=True
    )
    created_on: Mapped[datetimetz] = mapped_column(init=False, nullable=False)

    # Derived fields (read-only)
    last_modified_on: Mapped[datetimetz] = column_property(
        select(func.max(ResourceSnapshot.created_on))
        .where(ResourceSnapshot.resource_id == resource_id)
        .correlate_except(ResourceSnapshot)
        .scalar_subquery()
    )
    is_deleted: Mapped[bool] = column_property(
        select(ResourceLock.resource_id)
        .where(
            ResourceLock.resource_id == resource_id,
            ResourceLock.resource_lock_type == resource_lock_types.DELETE,
        )
        .correlate_except(ResourceLock)
        .exists()
    )
    is_readonly: Mapped[bool] = column_property(
        select(ResourceLock.resource_id)
        .where(
            ResourceLock.resource_id == resource_id,
            ResourceLock.resource_lock_type == resource_lock_types.READONLY,
        )
        .correlate_except(ResourceLock)
        .exists()
    )
    latest_snapshot_id: Mapped[optionalbigint] = column_property(
        Nullable(
            select(ResourceSnapshot.resource_snapshot_id)
            .where(ResourceSnapshot.resource_id == resource_id)
            .order_by(ResourceSnapshot.created_on.desc())
            .limit(1)
            .correlate_except(ResourceSnapshot)
            .scalar_subquery()
        )
    )

    # Relationships
    owner: Mapped["Group"] = relationship(back_populates="resources", lazy="joined")
    parents: Mapped[list["Resource"]] = relationship(
        init=False,
        secondary="resource_dependencies",
        back_populates="children",
        primaryjoin=and_(
            resource_id == resource_dependencies_table.c.child_resource_id,
            resource_type == resource_dependencies_table.c.child_resource_type,
        ),
        secondaryjoin=and_(
            resource_id == resource_dependencies_table.c.parent_resource_id,
            resource_type == resource_dependencies_table.c.parent_resource_type,
        ),
    )
    children: Mapped[list["Resource"]] = relationship(
        init=False,
        secondary="resource_dependencies",
        back_populates="parents",
        primaryjoin=and_(
            resource_id == resource_dependencies_table.c.parent_resource_id,
            resource_type == resource_dependencies_table.c.parent_resource_type,
        ),
        secondaryjoin=and_(
            resource_id == resource_dependencies_table.c.child_resource_id,
            resource_type == resource_dependencies_table.c.child_resource_type,
        ),
    )
    locks: Mapped[list["ResourceLock"]] = relationship(
        init=False, back_populates="resource"
    )
    shares: Mapped[list["SharedResource"]] = relationship(
        init=False, back_populates="resource"
    )
    versions: Mapped[list["ResourceSnapshot"]] = relationship(
        init=False, back_populates="resource"
    )
    tags: Mapped[list["Tag"]] = relationship(
        init=False, secondary="resource_tags", back_populates="resources"
    )

    # Additional settings
    __table_args__ = (
        Index(None, "resource_id", "resource_type", unique=True),
        Index(None, "group_id", "resource_type"),
    )

    # Initialize default values using dataclass __post_init__ method
    # https://docs.python.org/3/library/dataclasses.html#dataclasses.__post_init__
    def __post_init__(self) -> None:
        timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        self.created_on = timestamp


class SharedResource(db.Model):  # type: ignore[name-defined]
    __tablename__ = "shared_resources"

    # Database fields
    shared_resource_id: Mapped[intpk] = mapped_column(init=False)
    resource_id: Mapped[bigint] = mapped_column(
        ForeignKey("resources.resource_id"), init=False, nullable=False, index=True
    )
    group_id: Mapped[bigint] = mapped_column(
        ForeignKey("groups.group_id"), init=False, nullable=False
    )
    user_id: Mapped[bigint] = mapped_column(
        ForeignKey("users.user_id"), init=False, nullable=False
    )
    read: Mapped[bool] = mapped_column(nullable=False)
    write: Mapped[bool] = mapped_column(nullable=False)
    created_on: Mapped[datetimetz] = mapped_column(init=False, nullable=False)

    # Relationships
    resource: Mapped["Resource"] = relationship(back_populates="shares", lazy="joined")
    recipient: Mapped["Group"] = relationship(
        back_populates="received_shares", lazy="joined"
    )
    creator: Mapped["User"] = relationship(
        back_populates="created_shares", lazy="joined"
    )
    tags: Mapped[list["Tag"]] = relationship(
        init=False, secondary="shared_resource_tags", back_populates="shared_resources"
    )

    # Additional settings
    __table_args__ = (Index(None, "group_id", "resource_id"),)

    # Initialize default values using dataclass __post_init__ method
    # https://docs.python.org/3/library/dataclasses.html#dataclasses.__post_init__
    def __post_init__(self) -> None:
        timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        self.created_on = timestamp


draft_resource_json_resource_id = Index(
    "ix_draft_resources_payload_resource_id",
    DraftResource.payload["resource_id"].as_string().cast(Integer),
)
