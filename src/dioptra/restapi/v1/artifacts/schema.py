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

from marshmallow import Schema, fields

from dioptra.restapi.utils import validate_artifact_url
from dioptra.restapi.v1.file_types import FileTypes
from dioptra.restapi.v1.plugins.schema import ArtifactTaskSchema
from dioptra.restapi.v1.schemas import (
    BasePageSchema,
    GroupIdQueryParametersSchema,
    PagingQueryParametersSchema,
    SearchQueryParametersSchema,
    SortByGetQueryParametersSchema,
    generate_base_resource_ref_schema,
    generate_base_resource_schema,
)

ArtifactRefBaseSchema = generate_base_resource_ref_schema("Artifact")


class ArtifactRefSchema(ArtifactRefBaseSchema):  # type: ignore
    """The reference schema for the data stored in a Artifact resource."""

    url = fields.Url(
        attribute="url",
        metadata={"description": "URL for accessing the full Artifact Resource."},
        relative=True,
        dump_only=True,
    )


class ArtifactFileMetadataSchema(Schema):
    """The schema for the artifact file metadata."""

    isDir = fields.Bool(
        attribute="is_dir",
        metadata={"description": "Whether the file denotes a directory or not."},
        dump_only=True,
    )
    fileSize = fields.Integer(
        attribute="file_size",
        metadata={"description": "The size in bytes of the file."},
        dump_only=True,
    )
    fileUrl = fields.Url(
        attribute="file_url",
        metadata={"description": "URL for accessing the contents of the Artifact."},
        relative=True,
        dump_only=True,
    )


class ArtifactFileSchema(ArtifactFileMetadataSchema):
    """The schema for an artifact file."""

    relativePath = fields.String(
        attribute="relative_path",
        metadata={"description": "Relative path to the Artifact URI."},
        dump_only=True,
    )


class ArtifactMutableFieldsSchema(Schema):
    """The fields schema for the mutable data in a Artifact resource."""

    description = fields.String(
        attribute="description",
        metadata={"description": "Description of the Artifact resource."},
        load_default=None,
    )
    pluginSnapshotId = fields.Int(
        attribute="plugin_snapshot_id",
        metadata={
            "description": "The Snapshot ID of the plugin containing the plugin file that "
            "performs serializing/deserializing of this Artifact."
        },
        load_default=None,
        load_only=True,
    )
    taskId = fields.Int(
        attribute="task_id",
        metadata={
            "description": "The id of the plugin artifact task that performs the"
            "serializing/deserializing of this Artifact."
        },
        load_default=None,
        load_only=True,
    )


ArtifactBaseSchema = generate_base_resource_schema("Artifact", snapshot=True)


class ArtifactArtifactTaskSchema(ArtifactTaskSchema):
    pluginResourceId = fields.Int(
        attribute="plugin_resource_id",
        metadata={
            "description": ("resource id of the plugin containing the Artifact Task")
        },
        dump_only=True,
    )
    pluginResourceSnapshotId = fields.Int(
        attribute="plugin_resource_snapshot_id",
        metadata={
            "description": (
                "snapshot resource id of the plugin containing the Artifact Task"
            )
        },
        dump_only=True,
    )
    pluginFileResourceId = fields.Int(
        attribute="plugin_file_resource_id",
        metadata={
            "description": (
                "resource id of the plugin file containing the Artifact Task"
            )
        },
        dump_only=True,
    )
    pluginFileResourceSnapshotId = fields.Int(
        attribute="plugin_file_resource_snapshot_id",
        metadata={
            "description": (
                "snapshot resource id of the plugin file containing the Artifact Task"
            )
        },
        dump_only=True,
    )


class ArtifactSchema(
    ArtifactFileMetadataSchema,
    ArtifactMutableFieldsSchema,
    ArtifactBaseSchema,  # type: ignore
):
    """The schema for the data stored in an Artifact resource."""

    # Not URL since this version of validate_url allows mlflow specific schemes
    artifactUri = fields.String(
        attribute="artifact_uri",
        metadata={
            "description": "URL pointing to the location of the Artifact resource."
        },
        validate=validate_artifact_url,
    )
    jobId = fields.Int(
        attribute="job_id",
        data_key="job",
        metadata={"description": "id of the job that produced this Artifact"},
        required=True,
    )
    task = fields.Nested(
        ArtifactArtifactTaskSchema,
        attribute="task",
        metadata={"description": "The artifact task."},
        dump_only=True,
    )


class ArtifactPageSchema(BasePageSchema):
    """The paged schema for the data stored in an Artifact resource."""

    data = fields.Nested(
        ArtifactSchema,
        many=True,
        metadata={"description": "List of Artifact resources in the current page."},
    )


class ArtifactContentsGetQueryParameters(Schema):
    """A schema for adding artifact contents query parameters to a resource endpoint."""

    path = fields.String(
        attribute="path",
        metadata={
            "description": "Path of a specific artifact. Only valid if artifact"
            "is a directory."
        },
        load_default=None,
    )
    fileType = fields.Enum(
        FileTypes,
        attribute="file_type",
        metadata={
            "description": "Only valid if the artifact is a directory. The type of file to"
            "download: tar_gz or zip.",
        },
        by_value=True,
        load_default=None,
    )


class ArtifactGetQueryParameters(
    PagingQueryParametersSchema,
    GroupIdQueryParametersSchema,
    SearchQueryParametersSchema,
    SortByGetQueryParametersSchema,
):
    """The query parameters for the GET method of the /artifacts endpoint."""
