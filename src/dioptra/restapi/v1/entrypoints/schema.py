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
"""The schemas for serializing/deserializing Entrypoint resources."""
from __future__ import annotations

from marshmallow import Schema, fields

from dioptra.restapi.v1.schemas import (
    BasePageSchema,
    GroupIdQueryParametersSchema,
    PagingQueryParametersSchema,
    SearchQueryParametersSchema,
    generate_base_resource_ref_schema,
    generate_base_resource_schema,
)


class EntrypointParameterSchema(Schema):
    """The schema for the data stored in a Entrypoint parameter resource."""

    entrypointId = fields.Integer(
        attribute="entrypoint_id",
        data_key="entrypoint",
        metadata=dict(description="ID for the associated entrypoint."),
    )
    parameterNumber = fields.Integer(
        attribute="parameter_number",
        metadata=dict(description="Index of the Entrypoint parameter."),
    )
    name = fields.String(
        attribute="name",
        metadata=dict(description="Name of the Entrypoint parameter resource."),
    )
    defaultValue = fields.String(
        attribute="default_value",
        metadata=dict(description="Default value of the Entrypoint parameter."),
    )
    parameterType = fields.String(
        attribute="parameter_type",
        metadata=dict(description="Data type of the Entrypoint parameter."),
    )


EntrypointRefBaseSchema = generate_base_resource_ref_schema("Entrypoint")


class EntrypointRefSchema(EntrypointRefBaseSchema):  # type: ignore
    """The reference schema for the data stored in a Entrypoint resource."""

    name = fields.String(
        attribute="name",
        metadata=dict(description="Name of the Entrypoint resource."),
    )


class EntrypointMutableFieldsSchema(Schema):
    """The fields schema for the mutable data in a Entrypoint resource."""

    name = fields.String(
        attribute="name",
        metadata=dict(description="Name of the Entrypoint resource."),
    )
    taskGraph = fields.String(
        attribute="task_graph",
        metadata=dict(description="Task graph of the Entrypoint resource."),
    )
    parameters = fields.Nested(
        EntrypointParameterSchema,
        many=True,
        metadata=dict(description="List of parameters for the entrypoint."),
    )


EntrypointBaseSchema = generate_base_resource_schema("Entrypoint", snapshot=True)


class EntrypointSchema(EntrypointMutableFieldsSchema, EntrypointBaseSchema):  # type: ignore
    """The schema for the data stored in a Entrypoint resource."""


class EntrypointPageSchema(BasePageSchema):
    """The paged schema for the data stored in a Entrypoint resource."""

    data = fields.Nested(
        EntrypointSchema,
        many=True,
        metadata=dict(description="List of Entrypoint resources in the current page."),
    )


class EntrypointGetQueryParameters(
    PagingQueryParametersSchema,
    GroupIdQueryParametersSchema,
    SearchQueryParametersSchema,
):
    """The query parameters for the GET method of the /entrypoints endpoint."""
