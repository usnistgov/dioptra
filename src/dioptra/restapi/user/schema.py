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
"""The schemas for serializing/deserializing the user endpoint objects.

.. |User| replace:: :py:class:`~.model.User`
.. |UserRegistrationForm| replace:: :py:class:`~.model.UserRegistrationForm`
"""
from __future__ import annotations

from typing import Any

from marshmallow import Schema, fields, pre_dump

from .model import User, UserRegistrationForm


class UserSchema(Schema):
    """The schema for the data stored in an |User| object.

    Attributes:
        userId: An integer identifying a registered user account.
        username: The username for logging into the user account.
        emailAddress: The email address associated with the user account.
        createdOn: The date and time the user account was created.
        lastModifiedOn: The date and time the user account was last modified.
        lastLoginOn: The date and time the user last logged into their account.
        userExpireOn: The date and time the user account is set to expire.
        passwordExpireOn: The date and time the user's password is set to expire.
    """

    __model__ = User

    userId = fields.Integer(
        attribute="user_id",
        metadata=dict(description="An integer identifying a registered user account."),
    )
    username = fields.String(
        attribute="username",
        metadata=dict(description="The username for logging into the user account."),
    )
    emailAddress = fields.Email(
        attribute="email_address",
        metadata=dict(
            description="The email address associated with the user account."
        ),
    )
    createdOn = fields.DateTime(
        attribute="created_on",
        metadata=dict(description="The date and time the user account was created."),
    )
    lastModifiedOn = fields.DateTime(
        attribute="last_modified_on",
        metadata=dict(
            description="The date and time the user account was last modified."
        ),
    )
    lastLoginOn = fields.DateTime(
        attribute="last_login_on",
        metadata=dict(
            description="The date and time the user last logged into their account."
        ),
    )
    userExpireOn = fields.DateTime(
        attribute="user_expire_on",
        metadata=dict(
            description="The date and time the user account is set to expire."
        ),
    )
    passwordExpireOn = fields.DateTime(
        attribute="password_expire_on",
        metadata=dict(
            description="The date and time the user's password is set to expire."
        ),
    )


class UserRegistrationFormSchema(Schema):
    """The schema for the information stored in an user registration form.

    Attributes:
        username: The username for logging into the user account. Must be unique.
        password: The password used for authenticating the user account.
        email_address: The email address associated with the user account.
    """

    username = fields.String(
        attribute="username",
        required=True,
        metadata=dict(
            description=(
                "The username for logging into the user account. Must be unique."
            ),
        ),
    )
    password = fields.String(
        attribute="password",
        required=True,
        metadata=dict(
            description="The password used for authenticating the user account."
        ),
    )
    email_address = fields.Email(
        attribute="email_address",
        required=True,
        metadata=dict(
            description="The email address associated with the user account."
        ),
    )

    @pre_dump
    def extract_data_from_form(
        self, data: UserRegistrationForm, many: bool, **kwargs
    ) -> dict[str, Any]:
        """Extracts data from the |UserRegistrationForm| for validation."""

        return {
            "username": data.username.data,
            "password": data.password.data,
            "email_address": data.email_address.data,
        }


UserRegistrationSchema = [
    dict(
        name="username",
        type=str,
        location="form",
        required=True,
        help="The username for logging into the user account. Must be unique.",
    ),
    dict(
        name="password",
        type=str,
        location="form",
        required=True,
        help="The password used for authenticating the user account.",
    ),
    dict(
        name="password_confirm",
        type=str,
        location="form",
        required=True,
        help=(
            "The password confirmation field, this should exactly match the value in "
            "password."
        ),
    ),
    dict(
        name="email_address",
        type=str,
        location="form",
        required=True,
        help="The email address associated with the user account.",
    ),
]
