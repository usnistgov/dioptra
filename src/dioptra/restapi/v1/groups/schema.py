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
"""The schemas for serializing/deserializing Group resources."""
from __future__ import annotations

from marshmallow import Schema, fields

from dioptra.restapi.v1.tags.schema import TagRefSchema
from dioptra.restapi.v1.users.schema import UserRefSchema


class GroupRefSchema(Schema):
    """The reference schema for the data stored in a Group resource."""

    id = fields.Integer(
        attribute="id",
        metadata=dict(description="ID for the Group resource."),
        dump_only=True,
    )
    name = fields.String(
        attribute="name", metadata=dict(description="Name of the Group resource.")
    )
    url = fields.Url(
        attribute="url",
        metadata=dict(description="URL for accessing the full Group resource."),
        relative=True,
    )


class MemberMutableFieldsSchema(Schema):
    """The fields schema of mutable data of a Group Member."""

    read = fields.Boolean(
        attribute="read",
        metadata=dict(description="Permission for member to read Group Resources."),
    )
    write = fields.Boolean(
        attribute="write",
        metadata=dict(description="Permission for member to modify Group Resources."),
    )
    shareRead = fields.Boolean(
        attribute="share_read",
        metadata=dict(
            description="Permission for member to share read-only Group Resources."
        ),
    )


class MemberSchema(MemberMutableFieldsSchema):
    """The fields schema of a Group Member."""

    user = fields.Nested(
        UserRefSchema,
        attribute="user",
        metadata=dict(description="User that is a memebr of the Group resource."),
    )
    group = fields.Nested(
        GroupRefSchema,
        attribute="group",
        metadata=dict(description="The Group Resource of which the User is a member."),
    )


class ManagerMutableFieldsSchema(Schema):
    """The fields schema of mutable data of a Group Manager."""

    owner = fields.Boolean(
        attribute="owner",
        metadata=dict(description="Flag for if the Manager is a Group owner."),
    )
    admin = fields.Boolean(
        attribute="admin",
        metadata=dict(description="Flag for if the Maanger is a Group admin."),
    )


class ManagerSchema(MemberSchema, ManagerMutableFieldsSchema):
    """The fields schema of a Group Manager."""


class GroupMemberMutableFieldsSchema(Schema):
    """The fields schema for the mutable data by Members in a Group resource."""

    members = fields.List(
        fields.Nested(MemberSchema),
        attribute="members",
        metadata=dict(description="A list of Members in a Group."),
    )


class GroupMangerMutableFieldsSchema(Schema):
    """The fields schema for the mutable data by Managers in a Group resource."""

    name = fields.String(
        attribute="name", metadata=dict(description="Name of the Group resource.")
    )
    managers = fields.List(
        fields.Nested(ManagerSchema),
        attribute="managers",
        metadata=dict(description="A list of Managers in a Group."),
    )


class GroupSchema(GroupMemberMutableFieldsSchema, GroupMangerMutableFieldsSchema):  # type: ignore
    """The schema for the data stored in a Group resource."""

    id = fields.Integer(
        attribute="id",
        metadata=dict(description="ID for the Group resource."),
        dump_only=True,
    )
    user = fields.Nested(
        UserRefSchema,
        attribute="user",
        metadata=dict(description="User that created the Group resource."),
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
    tags = fields.Nested(
        TagRefSchema,
        attribute="tags",
        metadata=dict(description="Tags associated with the Group resource."),
        many=True,
        dump_only=True,
    )
