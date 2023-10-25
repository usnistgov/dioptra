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
"""
from __future__ import annotations

from marshmallow import Schema, fields


class UserSchema(Schema):
    """The schema for the data stored in an |User| object."""

    userId = fields.Integer(
        attribute="user_id",
        metadata=dict(description="An integer identifying a registered user account."),
        dump_only=True,
    )
    username = fields.String(
        attribute="username",
        metadata=dict(description="The username of the user account."),
    )
    emailAddress = fields.Email(
        attribute="email_address",
        metadata=dict(
            description="The email address associated with the user account."
        ),
    )
    password = fields.String(
        attribute="password",
        metadata=dict(description="The password for the user account."),
        load_only=True,
    )
    confirmPassword = fields.String(
        attribute="confirm_password",
        metadata=dict(
            description="The password confirmation when creating a new user account."
        ),
        load_only=True,
    )
    createdOn = fields.DateTime(
        attribute="created_on",
        metadata=dict(description="The date and time the user account was created."),
        dump_only=True,
    )
    lastModifiedOn = fields.DateTime(
        attribute="last_modified_on",
        metadata=dict(
            description="The date and time the user account was last modified."
        ),
        dump_only=True,
    )
    lastLoginOn = fields.DateTime(
        attribute="last_login_on",
        metadata=dict(
            description="The date and time the user last logged into their account."
        ),
        dump_only=True,
    )
    passwordExpireOn = fields.DateTime(
        attribute="password_expire_on",
        metadata=dict(
            description="The date and time the user's password is set to expire."
        ),
        dump_only=True,
    )


class ChangePasswordUserSchema(Schema):
    """The required fields for changing the password of a user account."""

    userId = fields.Integer(
        attribute="user_id",
        metadata=dict(description="The account's unique id."),
    )
    currentPassword = fields.String(
        attribute="current_password",
        metadata=dict(description="The account's current password."),
    )
    newPassword = fields.String(
        attribute="new_password",
        metadata=dict(description="The new password to replace the current one."),
    )


class ChangePasswordCurrentUserSchema(Schema):
    """The required fields for changing the password of the current user account."""

    currentPassword = fields.String(
        attribute="current_password",
        metadata=dict(description="The account's current password."),
    )
    newPassword = fields.String(
        attribute="new_password",
        metadata=dict(description="The new password to replace the current one."),
    )


class DeleteCurrentUserSchema(Schema):
    """The required fields for deleting a user account."""

    password = fields.String(
        attribute="password",
        metadata=dict(description="The user's current password."),
    )


class UsernameStatusResponseSchema(Schema):
    """A simple response for reporting a status for one or more objects."""

    status = fields.String(
        attribute="status",
        metadata=dict(description="The status of the request."),
    )
    username = fields.List(
        fields.String(),
        attribute="username",
        metadata=dict(
            description="A list of usernames identifying the affected object(s)."
        ),
    )
