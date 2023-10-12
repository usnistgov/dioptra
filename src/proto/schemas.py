"""The application schemas used for serialization and deserialization of data.

Examples:
    >>> login_schema = LoginSchema()
    >>> login_schema.loads('{"username": "user", "password": "password"}')
    {'username': 'user', 'password': 'password'}

    >>> logout_schema = LogoutSchema()
    >>> logout_schema.loads('{"everywhere": true}')
    {'everywhere': True}

    >>> change_password_schema = ChangePasswordSchema()
    >>> change_password_schema.loads(
    ...     '{"currentPassword": "old", "newPassword": "new"}'
    ... )
    {'current_password': 'old', 'new_password': 'new'}

    >>> register_user_schema = RegisterUserSchema()
    >>> register_user_schema.loads(
    ...     '{"name": "a", "password": "b", "confirmPassword": "b"}'
    ... )
    {'name': 'a', 'password': 'b', 'confirm_password': 'b'}

    >>> delete_user_schema = DeleteUserSchema()
    >>> delete_user_schema.loads('{"password": "password"}')
    {'password': 'password'}
"""
from __future__ import annotations

from marshmallow import Schema, fields


class LoginSchema(Schema):
    username = fields.String(
        attribute="username",
        metadata=dict(description="The username for logging into the user account."),
        load_default=lambda: "guest",
    )
    password = fields.String(
        attribute="password",
        metadata=dict(
            description="The password used for authenticating the user account."
        ),
        load_default=lambda: "",
    )


class LogoutSchema(Schema):
    everywhere = fields.Bool(
        attribute="everywhere",
        metadata=dict(description="If True, log out from all devices."),
        load_default=lambda: False,
    )


class ChangePasswordSchema(Schema):
    currentPassword = fields.String(
        attribute="current_password",
        metadata=dict(description="The user's current password."),
        required=True,
    )
    newPassword = fields.String(
        attribute="new_password",
        metadata=dict(description="The new password to replace the current one."),
        required=True,
    )


class RegisterUserSchema(Schema):
    name = fields.String(
        attribute="name",
        metadata=dict(
            description="The username requested by the new user. Must be unique."
        ),
        required=True,
    )
    password = fields.String(
        attribute="password",
        metadata=dict(description="The password for the new user."),
        required=True,
    )
    confirmPassword = fields.String(
        attribute="confirm_password",
        metadata=dict(description="The password confirmation for the new user."),
        required=True,
    )


class DeleteUserSchema(Schema):
    password = fields.String(
        attribute="password",
        metadata=dict(description="The user's current password."),
        required=True,
    )

class SharedPrototypeResourceSchema(Schema):
    id = fields.Integer(
        metadata={"description": "The unique identifier of the shared resource."}
    )
    creator_id = fields.Integer(
        metadata={"description": "The ID of the user that created the shared resource."}
    )
    resource_id = fields.Integer(
        metadata={"description": "The ID of the resource being shared."}
    )
    group_id = fields.Integer(
        metadata={"description": "The ID of the group with which the resource is shared."}
    )
    deleted = fields.Boolean(
        metadata={"description": "Whether the shared resource has been deleted."}
    )
    readable = fields.Boolean(
        metadata={"description": "Whether the shared resource is readable."}
    )
    writable = fields.Boolean(
        metadata={"description": "Whether the shared resource is writable."}
    )

class RevokeSharedPrototypeResourceSchema(Schema):
    id = fields.Integer(
        metadata={"description": "The unique identifier of the shared resource."},
        required=True
    )

class AccessResourceSchema(Schema):
    resource_id = fields.Integer(
        attribute="resource_id",
        metadata=dict(
            description="The resource to be accessed with the group."
        ),
        required=True,
    )
    action_name = fields.String(
        attribute="action_name",
        metadata=dict(description="The action to give the permission to."),
        required=True,
    )


class CreateGroupSchema(Schema):
    """Schema for creating a new group."""

    id = fields.Integer(dump_only=True)
    name = fields.String(
        required=True,
        metadata={"description": "Human-readable name for the group."},
    )
    deleted = fields.Boolean(dump_only=True)

class AddUserToGroupSchema(Schema):
    """Schema for adding a user to a group."""

    user_id = fields.Integer(
        required=True,
        metadata={"description": "The ID of the user to be added to the group."},
    )
    group_id = fields.Integer(
        required=True,
        metadata={"description": "The ID of the group to which the user will be added."},
    )
    read = fields.Boolean(
        required=True,
        metadata={"description": "Whether the user can read the group's resources."},
    )
    write = fields.Boolean(
        required=True,
        metadata={"description": "Whether the user can write to the group's resources."},
    )
    share_read = fields.Boolean(
        required=True,
        metadata={"description": "Whether the user can attach read permissions when sharing a group resource."},
    )
    share_write = fields.Boolean(
        required=True,
        metadata={"description": "Whether the user can attach write permissions when sharing a group resource."},
    )

class DeleteGroupSchema(Schema):
    """Deletes a group"""

    group_id = fields.Integer(
        required=True,
        metadata={"description": "The ID of the group to be deleted."},
    )




if __name__ == "__main__":
    import doctest

    doctest.testmod(verbose=True)
