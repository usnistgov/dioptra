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


class LoginReactiveSchema(Schema):
    """
    Schema used for flask-login views, which can be triggered in a "reactive"
    style where a user-agent tries to access a protected endpoint, and
    flask-login automatically redirects to a login view.  When
    auto-redirecting, flask-login adds a "next" query param to allow the view
    to redirect the user-agent back to the endpoint they came from.
    """

    next = fields.Url(relative=True, require_tld=False)


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


if __name__ == "__main__":
    import doctest

    doctest.testmod(verbose=True)
