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

import datetime
from typing import Optional

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from typing_extensions import TypedDict
from werkzeug.datastructures import FileStorage
from wtforms.fields import StringField, BooleanField, IntegerField
from wtforms.validators import UUID, InputRequired
from wtforms.validators import Optional as OptionalField
from wtforms.validators import Regexp, ValidationError

from dioptra.restapi.app import db
from dioptra.restapi.utils import slugify

from .interface import JobUpdateInterface

#from ..SharedResource import SharedResource

from ..group.model import Group

from ..user.model import User



job_statuses = db.Table(
    "job_statuses", db.Column("status", db.String(255), primary_key=True)
)


class GroupMembership(db.Model):
    """The group memberships table.

    Attributes:
        user_id (int): The ID of the user who is a member of the group.
        group_id (str): The ID of the group to which the user belongs.
        read (bool): Indicates whether the user has read permissions in the group.
        write (bool): Indicates whether the user has write permissions in the group.
        share_read (bool): Indicates whether the user can share read permissions with others in the group.
        share_write (bool): Indicates whether the user can share write permissions with others in the group.
    """

    __tablename__ = "GroupMemberships"

    user_id = db.Column(db.BigInteger(), db.ForeignKey("users.user_id"), primary_key=True)
    group_id = db.Column(db.BigInteger(), db.ForeignKey("Groups.id"), primary_key=True)

    read = db.Column(db.Boolean, default=False)
    write = db.Column(db.Boolean, default=False)
    share_read = db.Column(db.Boolean, default=False)
    share_write = db.Column(db.Boolean, default=False)

    # Define a relationship with User and Group
    user = db.relationship('User', foreign_keys=[user_id])
    group = db.relationship('Group', foreign_keys=[group_id])



    @property
    def user(self):
        """The users that are members of the group."""
        # Define a relationship with SharedPrototypeResource, if needed
        return User.query.filter_by(user_id=self.user_id).all()
    
    @property
    def group(self):
        """The users that are members of the group."""
        # Define a relationship with SharedPrototypeResource, if needed
        return Group.query.filter_by(id=self.group_id).all()


    def update(self, changes: JobUpdateInterface):
        """Updates the record.

        Args:
            changes: A :py:class:`~.interface.JobUpdateInterface` dictionary containing
                record updates.
        """
        for key, val in changes.items():
            setattr(self, key, val)

        return self


class GroupMembershipForm(FlaskForm):
    """Form for creating new group memberships.

    Attributes:
        group_id: The ID of the group to which the user belongs.
        user_id: The ID of the user to add to the group.
        read: Checkbox to indicate read permissions.
        write: Checkbox to indicate write permissions.
        share_read: Checkbox to indicate share read permissions.
        share_write: Checkbox to indicate share write permissions.
    """

    group_id = IntegerField(
        "Group ID",
        validators=[InputRequired()],
        description="The ID of the group to which the user belongs."
    )

    user_id = IntegerField(
        "User ID",
        validators=[InputRequired()],
        description="The ID of the user to add to the group."
    )

    read = BooleanField(
        "Read Permission",
        description="Check to grant read permission for the user in the group.",
        default = False
    )

    write = BooleanField(
        "Write Permission",
        description="Check to grant write permission for the user in the group.",
        default = False
    )

    share_read = BooleanField(
        "Share Read Permission",
        description="Check to allow the user to share read permission with others in the group.",
        default = False
    )

    share_write = BooleanField(
        "Share Write Permission",
        description="Check to allow the user to share write permission with others in the group.",
        default=False
    )

class GroupMembershipFormData(TypedDict, total=False):
    """The data extracted from the group membership submission form.

    Attributes:
        group_id: The ID of the group to which the user belongs.
        user_id: The ID of the user to add to the group.
        read: Indicates whether read permission is granted.
        write: Indicates whether write permission is granted.
        share_read: Indicates whether share read permission is granted.
        share_write: Indicates whether share write permission is granted.
    """

    group_id: int
    user_id: int
    read: bool
    write: bool
    share_read: bool
    share_write: bool