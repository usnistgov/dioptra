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
"""Common schemas for serializing/deserializing resources."""

from marshmallow import Schema, fields

from dioptra.restapi.v1.schemas import (
    BasePageSchema,
    DraftTypeQueryParametersSchema,
    GroupIdQueryParametersSchema,
    PagingQueryParametersSchema,
)


class DraftRefSchema(Schema):
    """The reference schema for the data stored in a Draft."""

    id = fields.Integer(
        attribute="id",
        metadata=dict(description="ID for the Draft."),
        dump_only=True,
    )
    resourceType = fields.String(
        attribute="resource_type",
        metadata=dict(description="The resource type of the Draft."),
    )
    url = fields.Url(
        attribute="url",
        metadata=dict(description="URL for accessing the full Draft."),
        relative=True,
    )


class DraftSchema(Schema):
    """A base schema for a draft of a resource."""

    from dioptra.restapi.v1.groups.schema import GroupRefSchema
    from dioptra.restapi.v1.users.schema import UserRefSchema

    id = fields.Integer(
        attribute="id",
        metadata=dict(description="ID of the Draft."),
        dump_only=True,
    )
    group = fields.Nested(
        GroupRefSchema,
        attribute="group",
        metadata=dict(description="Group that owns the draft resource."),
        dump_only=True,
    )
    user = fields.Nested(
        UserRefSchema,
        attribute="user",
        metadata=dict(description="User that created the draft resource."),
        dump_only=True,
    )
    payload = fields.Dict(
        attribute="payload",
        metadata=dict(description="The contents of the draft resource."),
        dump_only=True,
    )
    createdOn = fields.DateTime(
        attribute="created_on",
        metadata=dict(description="Timestamp when the draft resource was created."),
        dump_only=True,
    )
    lastModifiedOn = fields.DateTime(
        attribute="last_modified_on",
        metadata=dict(
            description="Timestamp when the draft resource was last modified."
        ),
        dump_only=True,
    )
    resourceType = fields.String(
        attribute="resource_type",
        metadata=dict(description="The type of resource of this draft."),
        dump_only=True,
    )
    resource = fields.Integer(
        attribute="resource_id",
        metadata=dict(description="ID of the resource this draft modifies."),
        dump_only=True,
    )
    resourceSnapshot = fields.Integer(
        attribute="resource_snapshot_id",
        metadata=dict(description="ID of the resource snapshot this draft modifies."),
        dump_only=True,
        allow_none=True,
    )
    metadata = fields.Dict(
        attribute="metadata",
        metadata=dict(description="Additional metadata about the draft"),
        dump_only=True,
    )


class DraftPageSchema(BasePageSchema):
    """The paged schema for the data stored in a Draft."""

    data = fields.Nested(
        DraftSchema,
        many=True,
        metadata=dict(description="List of Drafts in the current page."),
    )


class DraftGetQueryParameters(
    PagingQueryParametersSchema,
    GroupIdQueryParametersSchema,
    DraftTypeQueryParametersSchema,
):
    """The query parameters for the GET method of the /<resource>/drafts endpoint."""
