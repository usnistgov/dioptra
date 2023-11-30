"""The application services layer.

The services should be accessed using the SERVICES variable.

Examples:
    >>> SERVICES.hello.say_hello_world()
    'Hello, World!'

    >>> SERVICES.foo.say_bar()
    'bar'

    >>> password = "password123"
    >>> hashed_password = SERVICES.password.hash(password)
    >>> SERVICES.password.verify(password, hashed_password)
    True

    >>> db["users"].get("1", "None")
    'None'
    >>> new_user = "new_user"
    >>> new_password = "new_pass"
    >>> SERVICES.user.register_new_user(new_user, new_password, new_password)
    {'status': 200, 'message': 'User new_user registration successful'}
    >>> db["users"].get("1")  # doctest: +ELLIPSIS
    User(id=1, alternative_id='...', name='new_user', password='...', deleted=False)
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Union, cast

import flask
from flask import Request, current_app, has_request_context, session
from flask_login import current_user, login_user, logout_user
from passlib.context import CryptContext

from .models import User, db


class HelloService(object):
    """The service methods accessed via the /api/hello endpoint."""

    def say_hello_world(self) -> str:
        """Return the greeting message "Hello, World!".

        Returns:
            A string containing the greeting message.
        """
        return "Hello, World!"


class TestService(object):
    """The service methods accessed via the /api/test endpoint."""

    def reveal_secret_key(self) -> str:
        """Return the secret key set on the environment variable SECRET_KEY.

        Returns:
            A string containing the secret key.
        """
        return cast(str, current_app.config["SECRET_KEY"])


class WorldService(object):
    """The service methods accessed via the /api/world endpoint."""

    def show_user_info(self) -> dict[str, Any]:
        """Serialize the user model's information in the JSON format.

        Returns:
            A response object containing the serialized user model's information.
        """
        return cast(User, current_user).to_json()


class FooService(object):
    """The service methods accessed via the /api/foo endpoint."""

    def echo_request(self, request: Request) -> Any | None:
        """Echo the request's JSON payload.

        Args:
            request: A request object containing the JSON payload.

        Returns:
            A dictionary containing the JSON payload. If no JSON payload is found,
            returns an "unknown input" message and a 400 status code.
        """
        if request.content_type != "application/json":
            return {"message": "unknown input"}, 400

        return request.json

    def say_bar(self) -> str:
        """Return the message "bar".

        Returns:
            A string containing the message "bar".
        """
        return "bar"


class PasswordService(object):
    """The service methods used to hash and verify passwords."""

    def __init__(self, context: CryptContext) -> None:
        """Initialize the password service.

        Args:
            context: Helper for hashing & verifying passwords using multiple algorithms.
                See the passlib documentation for full list of configuration options.
        """
        self._context = context

    def hash(self, password: str) -> str:
        """Hash the given password.

        Args:
            password: A string containing the password to be hashed.

        Returns:
            A string containing the hashed password.
        """
        return cast(str, self._context.hash(password))

    def verify(self, password: str, hashed_password: str) -> bool:
        """Verify the given password against the given hashed password.

        Args:
            password: A string containing the password to be verified.
            hashed_password: A string containing the hashed password to be verified
                against.

        Returns:
            A boolean indicating whether the given password matches the given hashed
            password.
        """
        return cast(bool, self._context.verify(password, hashed_password))


class UserService(object):
    """The service methods used to register and manage users."""

    def __init__(self, password_service: PasswordService) -> None:
        """Initialize the user service.

        Args:
            password_service: A PasswordService object.
        """
        self._password_service = password_service

    def authenticate_user(self, name: str, password: str) -> User | None:
        """Authenticate the user with the given name and password.

        Args:
            name: A string containing the name of the user to be authenticated.
            password: A string containing the password of the user to be
                authenticated.

        Returns:
            A user object if the user is authenticated, otherwise None.
        """
        for user in (
            x for x in db["users"].values() if x.name == name and not x.deleted
        ):
            # All users in the local user database have passwords, but the
            # "password" attribute is optional to support user objects
            # corresponding to OIDC users, for which we have no password.
            assert user.password

            if self._password_service.verify(
                password=password, hashed_password=user.password
            ):
                return user

            break

        return None

    def change_password(
        self, current_password: str, new_password: str
    ) -> dict[str, Any] | tuple[dict[str, Any], int]:
        """Change the current user's password.

        Args:
            name: The user making the password change request.
            current_password: The user's current password.
            new_password: The user's new password, to replace the current one after
                authentication.

        Returns:
            A dictionary containing the password change success message if the password
            change is successful, otherwise a tuple containing a dictionary with the
            password change failure message and a 403 status code.
        """
        if not self._password_service.verify(
            password=current_password, hashed_password=current_user.password
        ):
            return {"status": 403, "message": "Password Change Failed"}, 403

        current_user.password = self._password_service.hash(password=new_password)
        current_user.alternative_id = uuid.uuid4().hex
        return {"status": 200, "message": "Password Change Successful"}

    def delete_current_user(
        self, password: str
    ) -> dict[str, Any] | tuple[dict[str, Any], int]:
        """Permanently deletes the current user.

        Args:
            password: The current user's password.

        Returns:
            A dictionary containing the delete user success message if the user is
            deleted successfully, otherwise a tuple containing a dictionary with the
            delete user failure message and a 403 status code.
        """
        if not self._password_service.verify(
            password=password, hashed_password=current_user.password
        ):
            return {
                "status": 403,
                "message": "Unable to delete current user, password check failed.",
            }, 403

        current_user.deleted = True
        return {"status": 200, "message": "Current user deleted successfully."}

    def load_user(self, user_id: str) -> User | None:
        """Load the user associated with a provided id.

        Args:
            user_id: A string identifying the user to be loaded.

        Returns:
            A user object if the user is found, otherwise None.
        """
        user = None

        if has_request_context():
            # Check for an OIDC user; make up a corresponding User object if
            # possible.  We use the ID token; in this case we have no need of
            # the user_id parameter to this method.  We can't "look up" a user
            # by ID; we have no database of OIDC users to consult.  (That means
            # the "remember me" functionality can't work with OIDC users.)
            if flask.g.oidc.user_loggedin:
                user = self.create_user_from_id_token(session["oidc_auth_token"])

        if not user:
            # Not an OIDC user; try to locate a local user
            for db_user in db["users"].values():
                if db_user.is_active and db_user.get_id() == user_id:
                    user = db_user
                    break

        return user

    def create_user_from_id_token(self, id_token: Mapping[str, Any]) -> User:
        """
        Create a User object corresponding to an OIDC ID token.

        Args:
            id_token: An OIDC ID token, as created by flask-oidc.  (A dict)

        Returns:
            A User object
        """
        # The token structure assumed here is derived from an Okta ID
        # token.

        user = User(
            # id is not applicable; presumably would be a db primary key if
            # these users were stored in a db somewhere.  But OIDC users won't
            # be.
            id=0,
            # OP (OIDC Provider, e.g. Okta) identifies a user via a "sub"
            # (subject) claim.
            alternative_id=id_token["userinfo"]["sub"],
            name=id_token["userinfo"]["name"],
            deleted=False,
            # password is not applicable since we don't authenticate OIDC
            # users.  That is OP's job.
            password=None,
        )

        return user

    def register_new_user(
        self, name: str, password: str, confirm_password: str
    ) -> dict[str, Any] | tuple[dict[str, Any], int]:
        """Register a new user.

        Args:
            name: The username requested by the new user. Must be unique.
            password: The password for the new user.
            confirm_password: The password confirmation for the new user.

        Returns:
            A dictionary containing the registration success message if the registration
            is successful, otherwise a tuple containing a dictionary with the
            registration failure message and a 403 status code.
        """
        if password != confirm_password:
            return {
                "status": 403,
                "message": "The password and confirmation password did not match.",
            }, 403

        if (
            len(
                [
                    x.name
                    for x in db["users"].values()
                    if x.name == name and not x.deleted
                ]
            )
            > 0
        ):
            return {
                "status": 403,
                "message": f"The username {name} is not available.",
            }, 403

        new_id = max([0, *[x.id for x in db["users"].values()]]) + 1

        db["users"][f"{new_id}"] = User(
            id=new_id,
            alternative_id=uuid.uuid4().hex,
            name=name,
            password=SERVICES.password.hash(password),
            deleted=False,
        )
        return {"status": 200, "message": f"User {name} registration successful"}


class AuthService(object):
    """The service methods accessed via the /api/auth endpoint."""

    def __init__(self, user_service: UserService) -> None:
        """Initialize the auth service.

        Args:
            user_service: A UserService object.
        """
        self._user_service = user_service

    def login(
        self, username: str, password: str
    ) -> dict[str, Any] | tuple[dict[str, Any], int]:
        """Login the user with the given username and password.  Used only for
        "proactive" login of a local user.  Not used for OIDC logins.

        Args:
            username: The username for logging into the user account.
            password: The password for authenticating the user account.

        Returns:
            A response object containing the login success message if the user is
            logged in successfully, otherwise a tuple containing the login failure
            message and a 401 status code.
        """
        user = self._user_service.authenticate_user(name=username, password=password)

        if not user:
            return (
                {"status": 401, "message": "Username or Password Error"},
                401,
            )

        login_user(user)
        return {"status": 200, "message": "login success"}

    def logout(
        self, everywhere: bool
    ) -> Optional[Union[dict[str, Any], flask.Response]]:
        """Log the current user out.  Applicable to both local and OIDC users.

        Args:
            everywhere: If True, log out from all devices by regenerating the current
                user's alternative id.  Not applicable to OIDC users.  This is
                a no-op if there is no authenticated user.

        Returns:
            A response (dict or flask response), or None if not called in the
                context of a flask http request, or if there is no
                authenticated user to log out.
        """

        resp: Optional[Union[dict[str, Any], flask.Response]] = None
        if has_request_context() and current_user.is_authenticated:
            if everywhere:
                # If current_user is an OIDC user, it is a temporary object, so
                # changing anything is pointless.  But it doesn't hurt.
                current_user.alternative_id = uuid.uuid4().hex

            # does stuff with the session, so requires request context.
            logout_user()

            if flask.g.oidc.user_loggedin:
                # If an OIDC-authenticated user, invoke the OIDC logout
                # endpoint.  This will do things like clear OIDC session keys.
                #
                # Any particular place we should return (redirect) to here,
                # after logout?
                resp = flask.g.oidc.logout()

            else:
                resp = {"status": 200, "message": "logout success"}

        return resp


@dataclass
class AppServices(object):
    """The application services layer.

    Attributes:
        hello: A HelloService object.
        test: A TestService object.
        world: A WorldService object.
        foo: A FooService object.
        password: A PasswordService object.
        user: A UserService object.
        auth: An AuthService object.
    """

    hello: HelloService
    test: TestService
    world: WorldService
    foo: FooService
    password: PasswordService
    user: UserService
    auth: AuthService


def _bootstrap_services() -> AppServices:
    """Bootstrap the application services using dependency injection.

    Returns:
        An object containing the application services.
    """
    hello = HelloService()
    test = TestService()
    world = WorldService()
    foo = FooService()
    password = PasswordService(
        context=CryptContext(
            schemes=["pbkdf2_sha256"],
            pbkdf2_sha256__default_rounds=30000,
        ),
    )
    user = UserService(password_service=password)
    auth = AuthService(user_service=user)

    return AppServices(
        hello=hello,
        test=test,
        world=world,
        foo=foo,
        password=password,
        user=user,
        auth=auth,
    )


SERVICES = _bootstrap_services()

if __name__ == "__main__":
    import doctest

    doctest.testmod(verbose=True)
