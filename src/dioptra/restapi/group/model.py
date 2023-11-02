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
"""The data models for the job endpoint objects."""
from __future__ import annotations

from dioptra.restapi.app import db
from dioptra.restapi.group_membership.model import GroupMembership
from dioptra.restapi.user.model import User
from dioptra.restapi.utils import slugify


class Group(db.Model):
    """The Groups table.

    Attributes:
        group_id: The unique identifier of the group.
        name: Human-readable name for the group.
        creator_id: The id for the user that created the group.
        owner_id: The id for the user that owns the group.
        created_on: The time at which the group was created.
        deleted: Whether the group has been deleted.
    """

    __tablename__ = "groups"

    group_id = db.Column(db.BigInteger(), primary_key=True)
    """A UUID that identifies the Resource."""
    name = db.Column(db.String(36))

    creator_id = db.Column(db.BigInteger(), db.ForeignKey("users.user_id"), index=True)
    owner_id = db.Column(db.BigInteger(), db.ForeignKey("users.user_id"), index=True)

    created_on = db.Column(db.DateTime())
    deleted = db.Column(db.Boolean)

    creator = db.relationship("User", foreign_keys=[creator_id])
    owner = db.relationship("User", foreign_keys=[owner_id])

    @classmethod
    def next_id(cls) -> int:
        """Generates the next id in the sequence."""
        group: Group | None = cls.query.order_by(cls.group_id.desc()).first()

        if group is None:
            return 1

        return int(group.id) + 1

    @property
    def users(self):
        """The users that are members of the group."""
        return (
            User.query.join(GroupMembership)
            .filter(GroupMembership.group_id == self.group_id)
            .all()
        )

    def check_membership(self, user: User) -> bool:
        """Check if the user has permission to perform the specified action.

        Args:
            user: The user to check.
            action: The action to check.

        Returns:
            True if the user has permission to perform the action, False otherwise.
        """
        membership = GroupMembership.query.filter_by(
            GroupMembership.user_id == user.user_id,
            GroupMembership.group_id == self.group_id,
        )

        if membership is None:
            return False
        else:
            return True

    # TODO
    def update(self, changes: dict):
        """Updates the record.

        Args:
            changes: A dictionary containing record updates.
        """
        for key, val in changes.items():
            setattr(self, key, val)

        return self