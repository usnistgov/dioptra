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
"""The module defining the endpoints for User resources."""
from __future__ import annotations

from flask_accepts import accepts, responds
from flask_login import login_required
from flask_restx import Namespace, Resource

from dioptra.restapi.v1.schemas import IdStatusResponseSchema

from .schema import (
    UserCurrentSchema,
    UserGetQueryParameters,
    UserMutableFieldsSchema,
    UserPageSchema,
    UserPasswordSchema,
    UserSchema,
)

api: Namespace = Namespace("Users", description="Users endpoint")


@api.route("/")
class UserEndpoint(Resource):

    @login_required
    @accepts(query_params_schema=UserGetQueryParameters, api=api)
    @responds(schema=UserPageSchema, api=api)
    def get(self):
        """Gets a list of all User resources."""

    @login_required
    @accepts(schema=UserSchema, api=api)
    @responds(schema=UserCurrentSchema, api=api)
    def post(self):
        """Creates a User resource."""
        ...


@api.route("/<int:id>")
@api.param("id", "ID for the User resource.")
class UserIdEndpoint(Resource):

    @login_required
    @responds(schema=UserSchema, api=api)
    def get(self, id: int):
        """Gets the User with the provided ID."""


@api.route("/current")
class UserCurrentEndpoint(Resource):

    @login_required
    @responds(schema=UserCurrentSchema, api=api)
    def get(self):
        """Gets the Current User."""

    @login_required
    @responds(schema=IdStatusResponseSchema, api=api)
    def delete(self):
        """Deletes a Current User."""

    @login_required
    @accepts(schema=UserMutableFieldsSchema, api=api)
    # NOTE: should we have response schema be a UserSchema as in groups?
    @responds(schema=IdStatusResponseSchema, api=api)
    def put(self):
        """Modifies the Current User"""
        ...


@api.route("/<int:id>/password")
@api.param("id", "ID for the User resource.")
class UserIdPasswordEndpoint(Resource):

    @login_required
    @accepts(schema=UserPasswordSchema, api=api)
    @responds(schema=IdStatusResponseSchema, api=api)
    def post(self, id: int):
        """Updates the User's password with a given ID."""


@api.route("/current/password")
class UserCurrentPasswordEndpoint(Resource):

    @login_required
    @accepts(schema=UserPasswordSchema, api=api)
    @responds(schema=IdStatusResponseSchema, api=api)
    def post(self):
        """Updates the Current User's password."""


# TODO: Return list of users (see doc)
