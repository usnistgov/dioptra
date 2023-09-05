"""The application's REST controllers for the API."""
from __future__ import annotations

from typing import Any, cast

from functools import wraps

from flask import request
from flask_accepts import accepts
from flask_login import login_required
from flask_restx import Namespace, Resource

from .schemas import (
    ChangePasswordSchema,
    DeleteUserSchema,
    LoginSchema,
    LogoutSchema,
    RegisterUserSchema,
    ShareResourceSchema,
)
from .services import SERVICES

from .models import db, User, Group, Dioptra_Resource

from oso import Oso, NotFoundError, ForbiddenError

oso = Oso()

oso.register_class(User)
oso.register_class(Dioptra_Resource)
oso.register_class(Group)

# Load your policy files.
oso.load_files(["src/proto/main.polar"])


# oso decorator definition
def authorize(action):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            user = SERVICES.user.get_current_user()
            # resource_id = request.headers.get('resource') # Extract resource_id from URL params
            resource_id = request.path.split("/")[-2]  # or using url
            resource = db["resources"][resource_id]

            # Check if the user is allowed to perform the action on the resource
            try:
                oso.authorize(user, action, resource)
                return f(*args, **kwargs)
            except NotFoundError:
                return f"<h1>Whoops!</h1><p>Not Found</p>", 404
            except ForbiddenError:
                return f"<h1>Whoops!</h1><p>Not Allowed</p>", 403

        return wrapped

    return decorator


# -- Endpoint Namespaces --------------------------------------------------------------

auth_api: Namespace = Namespace(
    "Authentication",
    description="Authentication endpoint",
)
user_api: Namespace = Namespace(
    "User",
    description="User endpoint",
)
hello_api: Namespace = Namespace(
    "Hello",
    description="Hello endpoint",
)
test_api: Namespace = Namespace(
    "Test",
    description="Test endpoint",
)
world_api: Namespace = Namespace(
    "World",
    description="World endpoint",
)
foo_api: Namespace = Namespace(
    "Foo",
    description="Foo endpoint",
)

# -- Authentication Resources ---------------------------------------------------------


@auth_api.route("/login")
class LoginResource(Resource):
    @accepts(schema=LoginSchema, api=auth_api)
    def post(self) -> dict[str, Any] | tuple[dict[str, Any], int]:
        """Login to a registered user account."""
        parsed_obj = cast(
            dict[str, Any], request.parsed_obj  # type: ignore[attr-defined]
        )
        username = str(parsed_obj["username"])
        password = str(parsed_obj["password"])
        return SERVICES.auth.login(username=username, password=password)


@auth_api.route("/logout")
class LogoutResource(Resource):
    @login_required
    @accepts(query_params_schema=LogoutSchema, api=auth_api)
    def post(self) -> dict[str, Any]:
        """Logout the current user.

        Must be logged in.
        """
        parsed_query_params = cast(
            dict[str, Any], request.parsed_query_params  # type: ignore[attr-defined]
        )
        everywhere = bool(parsed_query_params["everywhere"])
        return SERVICES.auth.logout(everywhere=everywhere)


# -- User Resource -------------------------------------------------------------------


@user_api.route("/")
class UserResource(Resource):
    @accepts(schema=RegisterUserSchema, api=user_api)
    def post(self) -> dict[str, Any] | tuple[dict[str, Any], int]:
        """Register a new user in the application."""
        parsed_obj = cast(
            dict[str, Any], request.parsed_obj  # type: ignore[attr-defined]
        )
        name = str(parsed_obj["name"])
        password = str(parsed_obj["password"])
        confirm_password = str(parsed_obj["confirm_password"])
        return SERVICES.user.register_new_user(
            name=name, password=password, confirm_password=confirm_password
        )

    @login_required
    @accepts(schema=DeleteUserSchema, api=user_api)
    def delete(self) -> dict[str, Any] | tuple[dict[str, Any], int]:
        """Permanently delete the current user.

        Must be logged in.
        """
        parsed_obj = cast(
            dict[str, Any], request.parsed_obj  # type: ignore[attr-defined]
        )
        password = str(parsed_obj["password"])
        return SERVICES.user.delete_current_user(password=password)


@user_api.route("/password")
class UserPasswordResource(Resource):
    @login_required
    @accepts(schema=ChangePasswordSchema, api=user_api)
    def post(self) -> dict[str, Any] | tuple[dict[str, Any], int]:
        """Change the current user's password.

        Must be logged in.
        """
        parsed_obj = cast(
            dict[str, Any], request.parsed_obj  # type: ignore[attr-defined]
        )
        current_password = str(parsed_obj["current_password"])
        new_password = str(parsed_obj["new_password"])
        return SERVICES.user.change_password(
            current_password=current_password, new_password=new_password
        )


@user_api.route("/shareread")
class ShareResource(Resource):
    @login_required
    @accepts(schema=ShareResourceSchema, api=user_api)
    def post(self) -> str:
        """Give user the read permission on a given resource"""
        parsed_obj = cast(
            dict[str, Any], request.parsed_obj  # type: ignore[attr-defined]
        )
        user = SERVICES.user.get_current_user()
        resource = db["resources"][parsed_obj["resource_name"]]
        try:
            oso.authorize(user, "share-read", resource)
            share_with = db["groups"][parsed_obj["group_name"]]
            resource.share_read(share_with)

            return f"<h1>A Repo</h1><p>read perms granted</p>"
        except ForbiddenError:
            return f"<h1>Whoops!</h1><p>Not Found</p>", 403


@user_api.route("/revokeshareread")
class RevokeShareResource(Resource):
    @login_required
    @accepts(schema=ShareResourceSchema, api=user_api)
    def post(self) -> str:
        """Give user the read permission on a given resource"""
        parsed_obj = cast(
            dict[str, Any], request.parsed_obj  # type: ignore[attr-defined]
        )
        user = SERVICES.user.get_current_user()
        resource = db["resources"][parsed_obj["resource_name"]]
        try:
            oso.authorize(user, "share-read", resource)
            share_with = db["groups"][parsed_obj["group_name"]]
            resource.unshare(share_with)

            return f"<h1>A Repo</h1><p>read perms revoked</p>"
        except ForbiddenError:
            return f"<h1>Whoops!</h1><p>Not Found</p>", 403


# -- Hello Resource -------------------------------------------------------------------


@hello_api.route("/")
class HelloResource(Resource):
    @authorize("read")
    def get(self) -> str:
        """Responds "Hello, World!"."""
        return SERVICES.hello.say_hello_world()

    @authorize("update")
    def post(self) -> str:
        """Responds "Hello, World!"."""
        return SERVICES.hello.say_hello_world()

    @authorize("create")
    def put(self) -> str:
        """Responds "Hello, World!"."""
        return SERVICES.hello.say_hello_world()


# -- Test Resource --------------------------------------------------------------------


@test_api.route("/")
class TestResource(Resource):
    @login_required
    @authorize("read")
    def get(self) -> str:
        """Responds with the server's secret key.

        Must be logged in.
        """
        return SERVICES.test.reveal_secret_key()

    @login_required
    @authorize("update")
    def post(self) -> str:
        """Responds with the server's secret key.

        Must be logged in.
        """
        return SERVICES.test.reveal_secret_key()

    @login_required
    @authorize("create")
    def put(self) -> str:
        """Responds with the server's secret key.

        Must be logged in.
        """
        return SERVICES.test.reveal_secret_key()


# testing with path variables
@test_api.route("/<name>")
class TestPluginResource(Resource):
    @login_required
    def get(self) -> str:
        """Responds with the server's secret key.

        Must be logged in.
        """
        resource = db["resources"]["test"]
        user = SERVICES.user
        try:
            oso.authorize(user, "read", resource)
            return SERVICES.test.reveal_secret_key()
        except NotFoundError:
            return f"<h1>Whoops!</h1><p>Not Found</p>", 404

    @login_required
    def post(self) -> str:
        """Responds with the server's secret key.

        Must be logged in.
        """
        resource = db["resources"]["test"]
        user = SERVICES.user
        try:
            oso.authorize(user, "write", resource)
            return SERVICES.test.reveal_secret_key()
        except NotFoundError:
            return f"<h1>Whoops!</h1><p>Not Found</p>", 404

    @login_required
    @authorize("write")
    def put(self, name) -> str:
        """Responds with the server's secret key.

        Must be logged in.
        """
        return SERVICES.test.reveal_secret_key()


# -- World Resource -------------------------------------------------------------------


@world_api.route("/")
class WorldResource(Resource):
    @login_required
    @authorize("read")
    def get(self) -> dict[str, Any]:
        """Responds with the user's information.

        Must be logged in.
        """
        return SERVICES.world.show_user_info()

    @login_required
    @authorize("update")
    def post(self) -> dict[str, Any]:
        """Responds with the user's information.

        Must be logged in.
        """
        return SERVICES.world.show_user_info()

    @login_required
    @authorize("create")
    def put(self) -> dict[str, Any]:
        """Responds with the user's information.

        Must be logged in.
        """
        return SERVICES.world.show_user_info()


# -- Foo Resource ---------------------------------------------------------------------


@foo_api.route("/")
class FooResource(Resource):
    @login_required
    def get(self) -> str:
        """Responds with "bar".

        Must be logged in.
        """
        return SERVICES.foo.say_bar()

    @login_required
    def post(self):
        """Echoes the JSON payload in the request.

        Must be logged in.
        """
        return SERVICES.foo.echo_request(request)

    @login_required
    def put(self) -> str:
        """Responds with "bar".

        Must be logged in.
        """
        return SERVICES.foo.say_bar()
