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
"""The schemas for serializing/deserializing Artifact resources."""

from __future__ import annotations

from marshmallow import fields

from dioptra.restapi.v1.schemas import (
    BasePageSchema,
    PagingQueryParametersSchema,
    SearchQueryParametersSchema,
    generate_base_resource_ref_schema,
    generate_base_resource_schema,
)

ArtifactRefBaseSchema = generate_base_resource_ref_schema("Artifact")


class ArtifactRefSchema(ArtifactRefBaseSchema):  # type: ignore
    """The reference schema for the data stored in a Artifact resource."""

    artifactUri = fields.URL(
        attribute="artifact_uri",
        metadata=dict(
            description="URL pointing to the location of the Artifact resource."
        ),
        relative=True,
    )


ArtifactBaseSchema = generate_base_resource_schema("Artifact", snapshot=False)


class ArtifactSchema(ArtifactBaseSchema):  # type: ignore
    """The schema for the data stored in an Artifact resource."""

    jobId = fields.Int(
        attribute="job_id",
        metadata=dict(description="id of the job that produced this Artifact"),
    )
    mlflowRunId = fields.Int(
        attribute="mlflow_run_id",
        metadata=dict(description="id of the tracking MLflow run"),
    )
    artifactUri = fields.URL(
        attribute="artifact_uri",
        metadata=dict(description="URL pointing to the location of the Artifact."),
        relative=True,
    )


class ArtifactPageSchema(BasePageSchema):
    """The paged schema for the data stored in an Artifact resource."""

    data = fields.Nested(
        ArtifactSchema,
        many=True,
        metadata=dict(description="List of Artifact resources in the current page."),
    )


class ArtifactGetQueryParameters(
    PagingQueryParametersSchema,
    SearchQueryParametersSchema,
):
    """The query parameters for the GET method of the /artifacts endpoint."""
