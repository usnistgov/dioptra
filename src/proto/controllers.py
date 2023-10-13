"""The application's REST controllers for the API."""
from __future__ import annotations

from typing import Any, cast

from functools import wraps

from flask import request, current_app
from flask_accepts import accepts
from flask_login import login_required, current_user
from flask_restx import Namespace, Resource

from .schemas import (
    ChangePasswordSchema,
    DeleteUserSchema,
    LoginSchema,
    LogoutSchema,
    RegisterUserSchema,
    SharedPrototypeResourceSchema,
    RevokeSharedPrototypeResourceSchema,
    AccessResourceSchema,
    CreateGroupSchema,
    AddUserToGroupSchema,
    DeleteGroupSchema
)
from .services import SERVICES

from .models import db

from oso import NotFoundError, ForbiddenError


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
                current_app.oso.authorize(user, action, resource)
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
group_api: Namespace = Namespace(
    "Groups",
    description="Groups endpoint",
)
sharing_api: Namespace = Namespace(
    "Shared",
    description="Shared Resource endpoint",
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

# -- Sharing Resource -----------------------------------------------------------------
@sharing_api.route("/")
class InteractSharedResource(Resource):
    @login_required
    @accepts(schema=AccessResourceSchema, api= sharing_api)
    def get(self) -> str:
        """Read a shared resource"""
        parsed_obj = cast(
            dict[str, Any], request.parsed_obj  # type: ignore[attr-defined]
        )

        resource_id = str(parsed_obj["resource_id"])
        action = str(parsed_obj["action_name"])
        user = current_user
        resource = db["shared_resources"][resource_id]

        try:
            current_app.oso.authorize(user, action, resource)

            return f"<h1>Shared Resource</h1><p>read</p>"
        except ForbiddenError:
            return f"<h1>Whoops!</h1><p>Not Found</p>", 403


@sharing_api.route("/share")
class SharedResource(Resource):
    @login_required
    @accepts(schema=SharedPrototypeResourceSchema, api=sharing_api)
    def post(self) -> str:
        """Shares a given resource with a group."""
        parsed_obj = cast(
            dict[str, Any], request.parsed_obj  # type: ignore[attr-defined]
        )

        creator_id =  SERVICES.user.get_current_user().id
        resource_id = str(parsed_obj["resource_id"])
        group_id = int(parsed_obj["group_id"])
        readable = bool(parsed_obj["readable"])
        writable = bool(parsed_obj["writable"])

        user = db["users"]["1"]#SERVICES.user.get_current_user()
        resource = db["resources"]["2"]
        print(resource)
        print(user)
        try:
            if readable:
                current_app.oso.authorize(user, "share_read", resource)
            if writable:
                current_app.oso.authorize(current_user, "share_write", resource)
            
            SERVICES.shared_resource.create(
                creator_id=creator_id,
                resource_id=resource_id,
                group_id=group_id,
                readable=readable,
                writable=writable
            )
            return f"<h1>A Repo</h1><p>perms granted</p>"
        except ForbiddenError:
            return f"<h1>Whoops!</h1><p>Not Found</p>", 403

    @login_required
    @accepts(schema=RevokeSharedPrototypeResourceSchema, api=sharing_api)
    def delete(self) -> str:
        """Revokes the share on a given resource from a group"""
        parsed_obj = cast(
            dict[str, Any], request.parsed_obj  # type: ignore[attr-defined]
        )

        shared_resource_id = str(parsed_obj["id"])

        user = SERVICES.user.get_current_user()
        resource = db["shared_resources"][shared_resource_id]
        try:
            current_app.oso.authorize(user, "share_read", resource)
            current_app.oso.authorize(user, "share_write", resource)
            
            SERVICES.shared_resource.delete(
                resource_id=db["shared_resources"][shared_resource_id],
            )
            return f"<h1>A Repo</h1><p>perms granted</p>"
        except ForbiddenError:
            return f"<h1>Whoops!</h1><p>Not Found</p>", 403

# -- Group Resource -------------------------------------------------------------------

@group_api.route("/")
class ManageGroup(Resource):
    @login_required
    @accepts(schema= CreateGroupSchema, api=group_api)
    def post(self):
        """Creates a new group, responds with the success of the creation."""
        parsed_obj = cast(
            dict[str, Any], request.parsed_obj  # type: ignore[attr-defined]
        )
        name = str(parsed_obj["name"])
        creator_id= SERVICES.user.get_current_user().id
        owner_id= SERVICES.user.get_current_user().id
        return SERVICES.group.create(
            name=name, creator_id=creator_id, owner_id=owner_id
        )

    @login_required
    @accepts(schema=AddUserToGroupSchema, api=group_api)
    def put(self):
        """Adds a user to a group, responds with the success of the add."""
        parsed_obj = cast(
            dict[str, Any],
            request.parsed_obj  # type: ignore[attr-defined]
        )
        user_id = int(parsed_obj["user_id"])
        group_id = int(parsed_obj["group_id"])
        read = bool(parsed_obj["read"])
        write = bool(parsed_obj["write"])
        share_read = bool(parsed_obj["share_read"])
        share_write = bool(parsed_obj["share_write"])

        # Call the service to add the user to the group
        result = SERVICES.group.add_member(
            user_id=user_id,
            group_id=group_id,
            read=read,
            write=write,
            share_read=share_read,
            share_write=share_write,
        )

        return result
    
    @login_required
    @accepts(schema=DeleteGroupSchema, api=group_api)
    def delete(self):
        """Deletes a group, responds with the success of the deletion."""
        parsed_obj = cast(
            dict[str, Any],
            request.parsed_obj  # type: ignore[attr-defined]
        )
        group_id = str(parsed_obj["group_id"])

        result = SERVICES.group.delete_group(group_id=group_id)

        return result
        
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
    def get(self) -> str:
        """Responds with the server's secret key.

        Must be logged in.
        """
        resource = db["resources"]["2"]

        # Check if the user is allowed to perform the action on the resource
        try:
            current_app.oso.authorize(current_user, "read", resource)
            return SERVICES.test.reveal_secret_key()
        except NotFoundError:
            return f"<h1>Whoops!</h1><p>Not Found</p>", 404
        

    @login_required
    @authorize("update")
    def post(self) -> str:
        """Responds with the server's secret key.

        Must be logged in.
        """
        resource = db["resources"]["2"]

        try:
            current_app.oso.authorize(current_user, "write", resource)
            return SERVICES.test.reveal_secret_key()
        except NotFoundError:
            return f"<h1>Whoops!</h1><p>Not Found</p>", 404

    @login_required
    @authorize("create")
    def put(self) -> str:
        """Responds with the server's secret key.

        Must be logged in.
        """
        return SERVICES.test.reveal_secret_key()


# -- World Resource -------------------------------------------------------------------


@world_api.route("/")
class WorldResource(Resource):
    @login_required
    def get(self) -> dict[str, Any]:
        """Responds with the user's information.

        Must be logged in.
        """
        # resource_id = request.headers.get('resource') #pip  Extract resource_id from URL params
        #resource_id = request.path.split("/")[-2]  # or using url
        resource = db["resources"]["1"]

        # Check if the user is allowed to perform the action on the resource
        try:
            current_app.oso.authorize(current_user, "read", resource)
            return SERVICES.world.show_user_info()
        except NotFoundError:
            return f"<h1>Whoops!</h1><p>Not Found</p>", 404
        except ForbiddenError:
            return f"<h1>Whoops!</h1><p>Not Allowed</p>", 403
        
    @login_required
    @authorize("update")
    def post(self) -> dict[str, Any]:
        """Responds with the user's information.

        Must be logged in.
        """
        resource = db["resources"]["1"]

        # Check if the user is allowed to perform the action on the resource
        try:
            current_app.oso.authorize(current_user, "write", resource)
            return SERVICES.world.show_user_info()
        except NotFoundError:
            return f"<h1>Whoops!</h1><p>Not Found</p>", 404
        except ForbiddenError:
            return f"<h1>Whoops!</h1><p>Not Allowed</p>", 403

    @login_required
    @authorize("create")
    def put(self) -> dict[str, Any]:
        """Responds with the user's information.

        Must be logged in.
        """
        resource = db["resources"]["1"]

        # Check if the user is allowed to perform the action on the resource
        try:
            current_app.oso.authorize(current_user, "write", resource)
            return SERVICES.world.show_user_info()
        except NotFoundError:
            return f"<h1>Whoops!</h1><p>Not Found</p>", 404
        except ForbiddenError:
            return f"<h1>Whoops!</h1><p>Not Allowed</p>", 403


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
