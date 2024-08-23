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
"""The schemas for serializing/deserializing Tags."""
from __future__ import annotations

from marshmallow import Schema, fields

from dioptra.restapi.v1.groups.schema import GroupRefSchema
from dioptra.restapi.v1.schemas import (
    BasePageSchema,
    GroupIdQueryParametersSchema,
    PagingQueryParametersSchema,
    ResourceTypeQueryParametersSchema,
    SearchQueryParametersSchema,
)
from dioptra.restapi.v1.users.schema import UserRefSchema


class TagRefSchema(Schema):
    """The reference schema for the data stored in a Tag."""

    id = fields.Integer(
        attribute="id",
        metadata=dict(description="ID for the Tag."),
        dump_only=True,
    )
    name = fields.String(
        attribute="name", metadata=dict(description="Name of the Tag.")
    )
    group = fields.Nested(
        GroupRefSchema,
        attribute="group",
        metadata=dict(description="Owner of the Tag."),
    )
    url = fields.Url(
        attribute="url",
        metadata=dict(description="URL for accessing the full Tag."),
        relative=True,
    )


class TagMutableFieldsSchema(Schema):
    """The fields schema for the mutable data in a Tag resource."""

    name = fields.String(
        attribute="name", metadata=dict(description="Name of the Tag resource.")
    )


class TagBaseSchema(Schema):
    """The reference schema for the data stored in a Tag."""

    id = fields.Integer(
        attribute="id",
        metadata=dict(description="ID for the Tag."),
        dump_only=True,
    )
    groupId = fields.Integer(
        attribute="group_id",
        data_key="group",
        metadata=dict(description="Group that owns the Tag."),
        load_only=True,
    )
    group = fields.Nested(
        GroupRefSchema,
        attribute="group",
        metadata=dict(description="Group that owns the Tag."),
        dump_only=True,
    )
    user = fields.Nested(
        UserRefSchema,
        attribute="user",
        metadata=dict(description="User that created the Tag."),
        dump_only=True,
    )
    createdOn = fields.DateTime(
        attribute="created_on",
        metadata=dict(description="Timestamp when the Tag resource was created."),
        dump_only=True,
    )
    lastModifiedOn = fields.DateTime(
        attribute="last_modified_on",
        metadata=dict(description="Timestamp when the Tag resource was last modified."),
        dump_only=True,
    )


class TagSchema(TagMutableFieldsSchema, TagBaseSchema):
    """The schema for the data stored in a Tag resource."""


class TagPageSchema(BasePageSchema):
    """The paged schema for the data stored in a Tag resource."""

    data = fields.Nested(
        TagSchema,
        many=True,
        metadata=dict(description="List of Tags in the current page."),
    )


class TagGetQueryParameters(
    PagingQueryParametersSchema,
    GroupIdQueryParametersSchema,
    SearchQueryParametersSchema,
):
    """The query parameters for the GET method of the /tags endpoint."""


class TagResourceQueryParameters(
    PagingQueryParametersSchema, ResourceTypeQueryParametersSchema
):
    """The query parameters for the GET method of the /tags/resources/ endpoint."""
