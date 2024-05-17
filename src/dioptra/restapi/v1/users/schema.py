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
"""The schemas for serializing/deserializing User resources."""
from marshmallow import Schema, fields

from dioptra.restapi.v1.groups.schema import GroupRefSchema
from dioptra.restapi.v1.schemas import (
    BasePageSchema,
    PagingQueryParametersSchema,
    SearchQueryParametersSchema,
)


class UserRefSchema(Schema):
    """The reference schema for the data stored in a User resource."""

    id = fields.Integer(
        attribute="id",
        metadata=dict(description="ID for the User resource."),
        dump_only=True,
    )
    username = fields.String(
        attribute="username",
        metadata=dict(description="Username of the User resource."),
    )
    url = fields.Url(
        attribute="url",
        metadata=dict(description="URL for accessing the full User resource."),
        relative=True,
    )


class UserMutableFieldsSchema(Schema):
    """The schema for the mutable data fields in a User resource."""

    username = fields.String(
        attribute="username", metadata=dict(description="Username of the User.")
    )
    email = fields.String(
        attribute="email", metadata=dict(description="Email of the User.")
    )


class UserSchema(UserMutableFieldsSchema):
    """The schema for a User that is not the logged-in User."""

    password = fields.String(
        attribute="password",
        metadata=dict(description="Password for the User resource."),
        load_only=True,
    )
    confirmPassword = fields.String(
        attribute="confirm_password",
        metadata=dict(
            description="The password confirmation when creating a new user account."
        ),
        load_only=True,
    )
    id = fields.Integer(
        attribute="id",
        metadata=dict(description="ID for the User resource."),
        dump_only=True,
    )


class UserCurrentSchema(UserSchema):
    """The schema for the currently logged-in User."""

    groups = fields.Nested(
        GroupRefSchema,
        attribute="groups",
        metadata=dict(description="A list of Groups the User is a part of."),
        many=True,
        dump_only=True,
    )
    createdOn = fields.DateTime(
        attribute="created_on",
        metadata=dict(
            description="Timestamp when the User resource was created.",
            dump_only=True,
        ),
    )
    lastModifiedOn = fields.DateTime(
        attribute="last_modified_on",
        metadata=dict(
            description="Timestamp when the User resource was last modified."
        ),
        dump_only=True,
    )
    lastLoginOn = fields.DateTime(
        attribute="last_login_on",
        metadata=dict(
            description="Timestamp when the User resource was last logged in."
        ),
        dump_only=True,
    )
    passwordExpiresOn = fields.DateTime(
        attribute="password_expires_on",
        metadata=dict(
            description="Timestamp when the User resource password expires on."
        ),
        dump_only=True,
    )


class UserPasswordSchema(Schema):
    """The schema for changing a User's password."""

    oldPassword = fields.String(
        attribute="old_password",
        metadata=dict(description="Old password for the User resource."),
    )
    newPassword = fields.String(
        attribute="new_password",
        metadata=dict(description="New password for the User resource."),
    )
    confirmNewPassword = fields.String(
        attribute="confirm_new_password",
        metadata=dict(
            description="The new password confirmation when changing a password."
        ),
        load_only=True,
    )


class UserDeleteSchema(Schema):
    """The schema for deleting a User."""

    password = fields.String(
        attribute="password",
        metadata=dict(description="The users current password."),
    )


class UserPageSchema(BasePageSchema):
    """The paged schema for the data stored in a User resource."""

    data = fields.Nested(
        UserSchema,
        many=True,
        metadata=dict(description="List of User resources in the current page."),
    )


class UserGetQueryParameters(
    PagingQueryParametersSchema,
    SearchQueryParametersSchema,
):
    """The query parameters for the GET method of the /users endpoint."""
