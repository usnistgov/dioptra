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
"""The schemas for serializing/deserializing Group resource."""
from __future__ import annotations

from typing import Union

from marshmallow import Schema, fields, missing

from dioptra.restapi.v1.schemas import (
    BasePageSchema,
    PagingQueryParametersSchema,
    SearchQueryParametersSchema,
)


class GroupRefSchema(Schema):
    """The reference schema for the data stored in a Group resource."""

    id = fields.Integer(
        attribute="id",
        metadata=dict(description="ID for the Group resource."),
    )
    name = fields.String(
        attribute="name", metadata=dict(description="Name of the Group resource.")
    )
    url = fields.Url(
        attribute="url",
        metadata=dict(description="URL for accessing the full Group resource."),
        relative=True,
    )


def generate_group_permissions_schema(
    is_response: bool, use_defaults: bool
) -> type[Schema]:
    schema: dict[str, Union[fields.Field, type]] = {
        "read": fields.Boolean(
            attribute="read",
            metadata=dict(description="Permission for member to read Group."),
            dump_only=is_response,
            load_only=not is_response,
            load_default=(False if use_defaults else missing),
        ),
        "write": fields.Boolean(
            attribute="write",
            metadata=dict(description="Permission for member to modify Group."),
            dump_only=is_response,
            load_only=not is_response,
            load_default=(False if use_defaults else missing),
        ),
        "shareRead": fields.Boolean(
            attribute="share_read",
            metadata=dict(
                description="Permission for member to share read-only Group."
            ),
            dump_only=is_response,
            load_only=not is_response,
            load_default=(False if use_defaults else missing),
        ),
        "shareWrite": fields.Boolean(
            attribute="share_write",
            metadata=dict(
                description="Permission for member to share read+write Group."
            ),
            dump_only=is_response,
            load_only=not is_response,
            load_default=(False if use_defaults else missing),
        ),
        "owner": fields.Boolean(
            attribute="owner",
            metadata=dict(description="Flag for if the member is a Group owner."),
            dump_only=is_response,
            load_only=not is_response,
            load_default=(False if use_defaults else missing),
        ),
        "admin": fields.Boolean(
            attribute="admin",
            metadata=dict(description="Flag for if the member is a Group admin."),
            dump_only=is_response,
            load_only=not is_response,
            load_default=(False if use_defaults else missing),
        ),
    }

    return Schema.from_dict(schema)


GroupMemberCreateFieldsSchema = generate_group_permissions_schema(
    is_response=False, use_defaults=True
)

GroupMemberMutableFieldsSchema = generate_group_permissions_schema(
    is_response=False, use_defaults=False
)

GroupPermissionsResponseSchema = generate_group_permissions_schema(
    is_response=True, use_defaults=False
)


class GroupMemberBaseSchema(Schema):
    """The base schema of a Group Member."""

    from dioptra.restapi.v1.users.schema import UserRefSchema

    userId = fields.Integer(
        attribute="user_id",
        data_key="user",
        metadata=dict(
            description="Unique identifier for the User that is a member of the Group."
        ),
        load_only=True,
        required=True,
    )
    user = fields.Nested(
        UserRefSchema,
        attribute="user",
        metadata=dict(description="User that is a member of the Group."),
        dump_only=True,
    )
    group = fields.Nested(
        GroupRefSchema,
        attribute="group",
        metadata=dict(description="The Group of which the User is a member."),
        dump_only=True,
    )
    permissions = fields.Nested(
        GroupPermissionsResponseSchema,
        attribute="permissions",
        metadata=dict(description="The Group Permissions for this User."),
        dump_only=True,
    )


class GroupMemberSchema(GroupMemberCreateFieldsSchema, GroupMemberBaseSchema):  # type: ignore
    """The schema for a Group Member"""


class GroupMutableFieldsSchema(Schema):
    """The schema for the mutable data by GroupMembers in a Group."""

    name = fields.String(
        attribute="name", metadata=dict(description="Name of the Group."), required=True
    )


class GroupSchema(GroupMutableFieldsSchema):
    """The schema for the data stored in a Group resource."""

    from dioptra.restapi.v1.users.schema import UserRefSchema

    id = fields.Integer(
        attribute="id",
        metadata=dict(description="ID for the Group resource."),
        dump_only=True,
    )
    user = fields.Nested(
        UserRefSchema,
        attribute="user",
        metadata=dict(description="User that created the Group resource."),
        dump_only=True,
    )
    members = fields.Nested(
        GroupMemberSchema,
        attribute="members",
        many=True,
        metadata=dict(description="A list of GroupMembers in a Group."),
        dump_only=True,
    )
    createdOn = fields.DateTime(
        attribute="created_on",
        metadata=dict(description="Timestamp when the Group resource was created."),
        dump_only=True,
    )
    lastModifiedOn = fields.DateTime(
        attribute="last_modified_on",
        metadata=dict(
            description="Timestamp when the Group resource was last modified."
        ),
        dump_only=True,
    )


class GroupPageSchema(BasePageSchema):
    """The paged schema for the data stored in a Group resource."""

    data = fields.Nested(
        GroupSchema,
        many=True,
        metadata=dict(description="List of Group resources in the current page."),
    )


class GroupGetQueryParameters(
    PagingQueryParametersSchema,
    SearchQueryParametersSchema,
):
    """The query parameters for the GET method of the /groups endpoint."""
