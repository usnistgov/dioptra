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
"""The schemas for serializing/deserializing Model resources."""
from marshmallow import Schema, fields

from dioptra.restapi.v1.artifacts.schema import ArtifactRefSchema
from dioptra.restapi.v1.schemas import (
    BasePageSchema,
    GroupIdQueryParametersSchema,
    PagingQueryParametersSchema,
    SearchQueryParametersSchema,
    generate_base_resource_ref_schema,
    generate_base_resource_schema,
)

ModelBaseRefSchema = generate_base_resource_ref_schema("Model")


class ModelRefSchema(ModelBaseRefSchema):  # type: ignore
    """The reference schema for the data stored in a Model resource."""

    name = fields.String(
        attribute="name",
        metadata=dict(description="Name of the Model resource."),
        required=True,
    )


class ModelVersionRefSchema(Schema):
    """The reference schema for the data stored in a Model Version."""

    versionNumber = fields.Integer(
        attribute="version_number",
        metadata=dict(description="The version number of the Model."),
        dump_only=True,
    )
    url = fields.Url(
        attribute="url",
        metadata=dict(description="URL for accessing the full Model Version."),
        relative=True,
    )


class ModelVersionMutableFieldsSchema(Schema):
    description = fields.String(
        attribute="description",
        metadata=dict(description="Description of the Model Version."),
        load_default=None,
    )


class ModelVersionSchema(ModelVersionMutableFieldsSchema):
    """The schema for the data stored in a ModelVersion resource."""

    model = fields.Nested(
        ModelRefSchema,
        attribute="model",
        metadata=dict(description="The Model resource."),
        dump_only=True,
    )
    artifactId = fields.Integer(
        attribute="artifact_id",
        data_key="artifact",
        metadata=dict(description="The artifact representing the Model Version."),
        load_only=True,
        required=True,
    )
    artifact = fields.Nested(
        ArtifactRefSchema,
        attribute="artifact",
        metadata=dict(description="The artifact representing the Model Version."),
        dump_only=True,
    )
    versionNumber = fields.Integer(
        attribute="version_number",
        metadata=dict(description="The version number of the Model."),
        dump_only=True,
    )
    createdOn = fields.DateTime(
        attribute="created_on",
        metadata=dict(description="Timestamp when the Model Version was created."),
        dump_only=True,
    )


class ModelMutableFieldsSchema(Schema):
    """The fields schema for the mutable data in a Model resource."""

    name = fields.String(
        attribute="name",
        metadata=dict(description="Name of the Model resource."),
        required=True,
    )
    description = fields.String(
        attribute="description",
        metadata=dict(description="Description of the Model resource."),
        load_default=None,
    )


ModelBaseSchema = generate_base_resource_schema("Model", snapshot=True)


class ModelSchema(ModelMutableFieldsSchema, ModelBaseSchema):  # type: ignore
    """The schema for the data stored in a Model resource."""

    versions = fields.Nested(
        ModelVersionRefSchema,
        many=True,
        attribute="versions",
        metadata=dict(description="The details of this model version."),
        dump_only=True,
    )
    latestVersion = fields.Nested(
        ModelVersionSchema,
        attribute="latest_version",
        metadata=dict(description="The details of latest version of this model."),
        dump_only=True,
    )


class ModelPageSchema(BasePageSchema):
    """The paged schema for the data stored in a Model resource."""

    data = fields.Nested(
        ModelSchema,
        many=True,
        metadata=dict(description="List of Model resources in the current page."),
    )


class ModelVersionPageSchema(BasePageSchema):
    """The paged schema for the data stored in a Model resource."""

    data = fields.Nested(
        ModelVersionSchema,
        many=True,
        metadata=dict(description="List of Model resources in the current page."),
    )


class ModelGetQueryParameters(
    PagingQueryParametersSchema,
    GroupIdQueryParametersSchema,
    SearchQueryParametersSchema,
):
    """The query parameters for the GET method of the /models endpoint."""


class ModelVersionGetQueryParameters(
    PagingQueryParametersSchema,
    SearchQueryParametersSchema,
):
    """The query parameters for the GET method of the /models/{id}/versions endpoint."""
