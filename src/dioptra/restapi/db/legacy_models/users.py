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
"""The data models for the user endpoint objects."""
from __future__ import annotations

import datetime
import uuid
from typing import Any

from dioptra.restapi.db.custom_types import GUID
from dioptra.restapi.db.db import db


class User(db.Model):
    """The users table.

    Attributes:
        user_id: An integer identifying a registered user account.
        alternative_id: A UUID as a 32-character lowercase hexadecimal string that
            serves as the user's alternative identifier. The alternative_id is
            changed when the user's password is changed or the user revokes all
            active sessions via a full logout.
        username: The username for logging into the user account.
        password: The hashed password used for authenticating the user account.
        email_address: The email address associated with the user account.
        created_on: The date and time the user account was created.
        last_modified_on: The date and time the user account was last modified.
        last_login_on: The date and time the user last logged into their account.
        password_expire_on: The date and time the user's password is set to expire.
        is_deleted: A boolean that indicates if the user account is deleted.
    """

    __tablename__ = "legacy_users"

    user_id: int = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True
    )
    alternative_id: uuid.UUID = db.Column(
        GUID(), nullable=False, unique=True, default=uuid.uuid4
    )
    username: str = db.Column(db.Text(), nullable=False)
    password: str = db.Column(db.Text(), nullable=False)
    email_address: str = db.Column(db.Text(), nullable=False)
    created_on: datetime.datetime = db.Column(db.DateTime(), nullable=False)
    last_modified_on: datetime.datetime = db.Column(db.DateTime(), nullable=False)
    last_login_on: datetime.datetime = db.Column(db.DateTime(), nullable=False)
    password_expire_on: datetime.datetime = db.Column(db.DateTime(), nullable=False)
    is_deleted: bool = db.Column(db.Boolean(), nullable=False, default=False)

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

    def update(self, changes: dict[str, Any]):
        """Updates the record.

        Args:
            changes: A :py:class:`~.interface.ExperimentUpdateInterface` dictionary
                containing record updates.
        """
        self.last_modified_on = datetime.datetime.now()

        for key, val in changes.items():
            setattr(self, key, val)

        return self
