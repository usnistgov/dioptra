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


class GroupMembership(db.Model):
    """The group memberships table.

    Attributes:
        user_id (int): The ID of the user who is a member of the group.
        group_id (str): The ID of the group to which the user belongs.
        read (bool): Indicates whether the user has read permissions in the group.
        write (bool): Indicates whether the user has write permissions in the group.
        share_read (bool): Indicates whether the user can share read permissions with
            others in the group.
        share_write (bool): Indicates whether the user can share write permissions
            with others in the group.
    """

    __tablename__ = "group_memberships"

    user_id = db.Column(
        db.BigInteger(), db.ForeignKey("users.user_id"), primary_key=True
    )
    group_id = db.Column(
        db.BigInteger(), db.ForeignKey("groups.group_id"), primary_key=True
    )

    read = db.Column(db.Boolean, default=False)
    write = db.Column(db.Boolean, default=False)
    share_read = db.Column(db.Boolean, default=False)
    share_write = db.Column(db.Boolean, default=False)

    # is back populates needed?
    user = db.relationship(
        "User",
        foreign_keys=[user_id],
    )
    group = db.relationship("Group", foreign_keys=[group_id])

    def update(self, changes: dict):
        """Updates the record.

        Args:
            changes: A dictionary containing record updates.
        """
        for key, val in changes.items():
            setattr(self, key, val)

        return self
