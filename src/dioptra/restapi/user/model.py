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
from typing import Any

from flask_wtf import FlaskForm
from wtforms.fields import EmailField, PasswordField, StringField
from wtforms.validators import Email, EqualTo, InputRequired

from dioptra.restapi.app import db

try:
    from typing import TypedDict

except ImportError:
    from typing_extensions import TypedDict


class User(db.Model):
    """The users table.

    Attributes:
        user_id: An integer identifying a registered user account.
        username: The username for logging into the user account.
        password: The hashed password used for authenticating the user account.
        email_address: The email address associated with the user account.
        created_on: The date and time the user account was created.
        last_modified_on: The date and time the user account was last modified.
        last_login_on: The date and time the user last logged into their account.
        user_expire_on: The date and time the user account is set to expire.
        password_expire_on: The date and time the user's password is set to expire.
        is_deleted: A boolean that indicates if the user account is deleted.
    """

    __tablename__ = "users"

    user_id: int = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True
    )
    username: str = db.Column(db.Text(), nullable=False)
    password: str = db.Column(db.Text(), nullable=False)
    email_address: str = db.Column(db.Text(), nullable=False)
    created_on: datetime.datetime = db.Column(db.DateTime(), nullable=False)
    last_modified_on: datetime.datetime = db.Column(db.DateTime(), nullable=False)
    last_login_on: datetime.datetime = db.Column(db.DateTime(), nullable=False)
    user_expire_on: datetime.datetime = db.Column(db.DateTime(), nullable=False)
    password_expire_on: datetime.datetime = db.Column(db.DateTime(), nullable=False)
    is_deleted: bool = db.Column(db.Boolean(), nullable=False, default=False)

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


class UserRegistrationForm(FlaskForm):
    """The user registration form.

    Attributes:
        username: The username for the user account.
        password: The password to use for for authenticating the new account.
        password_confirm: The password confirmation field, this should exactly
            match the value in `password`.
        email_address: The email address to associate with the user account.
    """

    username = StringField("Username", validators=[InputRequired()])
    password = PasswordField(
        "Password",
        [InputRequired(), EqualTo("password_confirm", message="Passwords must match")],
    )
    password_confirm = PasswordField("Repeat Password", validators=[InputRequired()])
    email_address = EmailField("Email Address", validators=[InputRequired(), Email()])


class UserRegistrationFormData(TypedDict, total=False):
    """The data extracted from the user registration form.

    Attributes:
        username: The username for logging into the user account.
        password: The hashed password used for authenticating the user account.
        email_address: The email address associated with the user account.
    """

    username: str
    password: str
    email_address: str
