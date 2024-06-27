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
"""The schemas for serializing/deserializing Workflow resources."""
from marshmallow import Schema, fields

from dioptra.restapi.v1.schemas import (
    BasePageSchema,
    PagingQueryParametersSchema,
    SearchQueryParametersSchema,
    generate_base_resource_ref_schema,
    generate_base_resource_schema,
)

WorkflowRefBaseSchema = generate_base_resource_ref_schema("Workflow")


class WorkflowRefSchema(WorkflowRefBaseSchema):  # type: ignore
    """The reference schema for the data stored in a Workflow resource."""

    name = fields.String(
        attribute="name",
        metadata=dict(description="Name of the Workflow resource."),
    )


class WorkflowMutableFieldsSchema(Schema):
    """The fields schema for the mutable data in a Workflow resource."""

    name = fields.String(
        attribute="name",
        metadata=dict(description="Name of the Workflow resource."),
        required=True,
    )
    description = fields.String(
        attribute="description",
        metadata=dict(description="Description of the Workflow resource."),
        load_default=None,
    )


WorkflowBaseSchema = generate_base_resource_schema("Workflow", snapshot=True)


class WorkflowSchema(WorkflowMutableFieldsSchema, WorkflowBaseSchema):  # type: ignore
    """The schema for the data stored in a Workflow resource."""


class WorkflowPageSchema(BasePageSchema):
    """The paged schema for the data stored in a Workflow resource."""

    data = fields.Nested(
        WorkflowSchema,
        many=True,
        metadata=dict(description="List of Workflow resources in the current page."),
    )


class WorkflowGetQueryParameters(
    PagingQueryParametersSchema,
    SearchQueryParametersSchema,
):
    """The query parameters for the GET method of the /workflows endpoint."""
