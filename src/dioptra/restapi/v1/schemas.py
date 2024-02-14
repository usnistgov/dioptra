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
from __future__ import annotations

from marshmallow import Schema, fields


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
    first = fields.String(
        attribute="first",
        metadata=dict(description="URL to first page in results set."),
    )
    next = fields.String(
        attribute="next",
        metadata=dict(description="URL to next page in results set."),
    )
    prev = fields.String(
        attribute="prev",
        metadata=dict(description="URL to last page in results set."),
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
    )


class GroupIdQueryParametersSchema(Schema):
    """A schema for adding group_id query parameters to a resource endpoint."""

    groupId = fields.String(
        attribute="group_id",
        metadata=dict(description="Filter results by the Group ID."),
    )


class SearchQueryParametersSchema(Schema):
    """A schema for adding search query parameters to a resource endpoint."""

    query = fields.String(
        attribute="query",
        metadata=dict(description="Search terms for the query (* and ? wildcards)."),
    )
    field = fields.Integer(
        attribute="field",
        metadata=dict(description="Name of the resource field to search."),
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
