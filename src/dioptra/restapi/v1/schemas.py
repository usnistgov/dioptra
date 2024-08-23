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

import enum

from marshmallow import Schema, fields


def generate_base_resource_schema(name: str, snapshot: bool) -> type[Schema]:
    """Generates the base schema for a Resource."""
    from dioptra.restapi.v1.groups.schema import GroupRefSchema
    from dioptra.restapi.v1.tags.schema import TagRefSchema
    from dioptra.restapi.v1.users.schema import UserRefSchema

    schema: dict[str, fields.Field | type] = {
        "id": fields.Integer(
            attribute="id",
            metadata=dict(description=f"ID for the {name} resource."),
            dump_only=True,
        ),
        "snapshotId": fields.Integer(
            attribute="snapshot_id",
            data_key="snapshot",
            metadata=dict(description=f"ID for the underlying {name} snapshot."),
            dump_only=True,
        ),
        "groupId": fields.Integer(
            attribute="group_id",
            data_key="group",
            metadata=dict(
                description=f"ID of the Group that will own the {name} resource."
            ),
            load_only=True,
            required=True,
        ),
        "group": fields.Nested(
            GroupRefSchema,
            attribute="group",
            metadata=dict(description=f"Group that owns the {name} resource."),
            dump_only=True,
        ),
        "user": fields.Nested(
            UserRefSchema,
            attribute="user",
            metadata=dict(description=f"User that created the {name} resource."),
            dump_only=True,
        ),
        "createdOn": fields.DateTime(
            attribute="created_on",
            metadata=dict(
                description=f"Timestamp when the {name} resource was created."
            ),
            dump_only=True,
        ),
        "lastModifiedOn": fields.DateTime(
            attribute="last_modified_on",
            metadata=dict(
                description=f"Timestamp when the {name} resource was last modified."
            ),
            dump_only=True,
        ),
        "latestSnapshot": fields.Bool(
            attribute="latest_snapshot",
            metadata=dict(
                description=f"Whether or not the {name} resource is the latest version."
            ),
            dump_only=True,
        ),
        "hasDraft": fields.Bool(
            attribute="has_draft",
            metadata=dict(
                description=f"Whether a draft exists for the {name} resource."
            ),
            dump_only=True,
        ),
        "tags": fields.Nested(
            TagRefSchema,
            attribute="tags",
            metadata=dict(description=f"Tags associated with the {name} resource."),
            many=True,
            dump_only=True,
        ),
    }

    if not snapshot:
        schema.pop("snapshotId")
        schema.pop("user")
        schema.pop("lastModifiedOn")
        schema.pop("latestSnapshot")

    return Schema.from_dict(schema, name=f"{name}BaseSchema")


def generate_base_resource_ref_schema(
    name: str, keep_snapshot_id: bool = False
) -> type[Schema]:
    """Generates the base schema for a ResourceRef."""
    from dioptra.restapi.v1.groups.schema import GroupRefSchema

    schema: dict[str, fields.Field | type] = {
        "id": fields.Integer(
            attribute="id",
            metadata=dict(description=f"ID for the {name} resource."),
        ),
        "snapshotId": fields.Integer(
            attribute="snapshot_id",
            metadata=dict(description=f"Snapshot ID for the {name} resource."),
        ),
        "group": fields.Nested(
            GroupRefSchema,
            attribute="group",
            metadata=dict(description=f"Group that owns the {name} resource."),
        ),
        "url": fields.Url(
            attribute="url",
            metadata=dict(description=f"URL for accessing the full {name} resource."),
            relative=True,
        ),
    }

    if keep_snapshot_id:
        schema.pop("id")
        return Schema.from_dict(schema, name=f"{name}SnapshotRefBaseSchema")
    else:
        schema.pop("snapshotId")
        return Schema.from_dict(schema, name=f"{name}RefBaseSchema")


class BasePageSchema(Schema):
    """The base schema for adding paging to a resource endpoint."""

    index = fields.Integer(
        attribute="index",
        metadata=dict(description="Index of the current page."),
    )
    isComplete = fields.Boolean(
        attribute="is_complete",
        metadata=dict(description="Boolean indicating if more data is available."),
    )
    totalNumResults = fields.Integer(
        attribute="total_num_results",
        metadata=dict(description="Total number of results."),
    )
    first = fields.Url(
        attribute="first",
        metadata=dict(description="URL to first page in results set."),
        relative=True,
    )
    next = fields.Url(
        attribute="next",
        metadata=dict(description="URL to next page in results set."),
        relative=True,
    )
    prev = fields.Url(
        attribute="prev",
        metadata=dict(description="URL to last page in results set."),
        relative=True,
    )


class PagingQueryParametersSchema(Schema):
    """A schema for adding paging query parameters to a resource endpoint."""

    index = fields.Integer(
        attribute="index",
        metadata=dict(description="Index of the current page."),
        load_default=0,
    )
    pageLength = fields.Integer(
        attribute="page_length",
        metadata=dict(description="Number of results to return per page."),
        load_default=10,
    )


class ResourceTypeQueryParametersSchema(Schema):
    """A schema for adding resource_type query parameters to a resource endpoint."""

    resourceType = fields.String(
        attribute="resource_type",
        metadata=dict(description="Filter results by the type of resource."),
        load_default=None,
    )


class GroupIdQueryParametersSchema(Schema):
    """A schema for adding group_id query parameters to a resource endpoint."""

    groupId = fields.Integer(
        attribute="group_id",
        metadata=dict(description="Filter results by the Group ID."),
        load_default=None,
    )


class DraftTypes(enum.Enum):
    ALL = "all"
    EXISTING = "existing"
    NEW = "new"


class DraftTypeQueryParametersSchema(Schema):
    """A schema for adding draft_type query parameters to a resource endpoint."""

    draftType = fields.Enum(
        DraftTypes,
        attribute="draft_type",
        metadata=dict(
            description="The type of drafts to return: all, existing, or new."
        ),
        by_value=True,
        load_default=DraftTypes.ALL,
    )


class SearchQueryParametersSchema(Schema):
    """A schema for adding search query parameters to a resource endpoint."""

    search = fields.String(
        attribute="search",
        metadata=dict(description="Search terms for the query (* and ? wildcards)."),
        load_default="",
    )


class ResourceGetQueryParameters(
    PagingQueryParametersSchema,
    SearchQueryParametersSchema,
):
    """The query parameters for the GET method of the resource endpoints."""


class IdListSchema(Schema):
    """The schema for a list of IDs."""

    ids = fields.List(
        fields.Integer(),
        attribute="ids",
        metadata=dict(description="List of identifiers for one or more objects."),
    )


class IdStatusResponseSchema(Schema):
    """A simple response for reporting a status for one or more resources."""

    id = fields.List(
        fields.Integer(),
        attribute="id",
        metadata=dict(
            description="A list of integers identifying the affected resource(s)."
        ),
    )
    status = fields.String(
        attribute="status",
        metadata=dict(description="The status of the request."),
    )


class ResourceUrlsPageSchema(BasePageSchema):
    """The paged schema for the Resource URLs."""

    data = fields.List(
        fields.String(),
        many=True,
        metadata=dict(description="List of Resource URLs in the current page."),
    )
