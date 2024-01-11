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


class DioptraResource(db.Model):
    """A registered resource of the application.

    Attributes:
        resource_id: The unique identifier of the resource.
        creator_id: The id of the creator (User) of the resource.
        owner_id: The id of the owner (Group) of the resource.
        created_on: The date and time at which the resource was created.
        last_modified_on: The date and time at which the resource was last modified.
        is_deleted: Whether the resource has been deleted.
    """

    __tablename__ = "dioptra_resources"

    resource_id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), index=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("groups.group_id"), index=True)
    created_on = db.Column(db.DateTime())
    last_modified_on = db.Column(db.DateTime())
    is_deleted = db.Column(db.Boolean, default=False)

    creator = db.relationship("User", foreign_keys=[creator_id])
    owner = db.relationship("Group", foreign_keys=[owner_id])

    @classmethod
    def next_id(cls) -> int:
        """Generates the next id in the sequence."""
        last_resource = cls.query.order_by(cls.resource_id.desc()).first()

        if last_resource is None:
            return 1
        return int(last_resource.resource_id) + 1

    @property
    def is_active(self):
        """Return True if the resource is active, False otherwise."""
        return not self.is_deleted

    def update(self, changes):
        """Updates the record with the given changes.

        Args:
            changes: A dictionary containing record updates.
        """
        for key, value in changes.items():
            setattr(self, key, value)
