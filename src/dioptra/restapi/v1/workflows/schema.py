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

from enum import Enum

from flask import request
from marshmallow import Schema, ValidationError, fields, pre_dump, validates_schema

from dioptra.restapi.custom_schema_fields import FileUpload, MultiFileUpload
from dioptra.restapi.v1.entrypoints.schema import (
    EntrypointArtifactSchema,
    EntrypointParameterSchema,
)
from dioptra.restapi.v1.schemas import FileDownloadParametersSchema
from dioptra.task_engine.issues import ValidationIssue


class JobFilesDownloadQueryParametersSchema(FileDownloadParametersSchema):
    """The query parameters for making a jobFilesDownload workflow request."""

    jobId = fields.String(
        attribute="job_id",
        metadata={"description": "A job's unique identifier."},
    )


class SignatureAnalysisSchema(Schema):
    pythonCode = fields.String(
        attribute="python_code",
        metadata={"description": "The contents of the python file"},
    )


class SignatureAnalysisSignatureParamSchema(Schema):
    name = fields.String(
        attribute="name", metadata={"description": "The name of the parameter"}
    )
    type = fields.String(
        attribute="type", metadata={"description": "The type of the parameter"}
    )


class SignatureAnalysisSignatureInputSchema(SignatureAnalysisSignatureParamSchema):
    required = fields.Boolean(
        attribute="required",
        metadata={"description": "Whether this is a required parameter"},
    )


class SignatureAnalysisSignatureOutputSchema(SignatureAnalysisSignatureParamSchema):
    pass


class SignatureAnalysisSuggestedTypes(Schema):
    # add proposed_type in next iteration

    name = fields.String(
        attribute="name",
        metadata={"description": "A suggestion for the name of the type"},
    )

    description = fields.String(
        attribute="description",
        metadata={
            "description": "The annotation the suggestion is attempting to represent"
        },
    )


class SignatureAnalysisSignatureSchema(Schema):
    name = fields.String(
        attribute="name", metadata={"description": "The name of the function"}
    )
    inputs = fields.Nested(
        SignatureAnalysisSignatureInputSchema,
        metadata={"description": "A list of objects describing the input parameters."},
        many=True,
    )
    outputs = fields.Nested(
        SignatureAnalysisSignatureOutputSchema,
        metadata={"description": "A list of objects describing the output parameters."},
        many=True,
    )
    missing_types = fields.Nested(
        SignatureAnalysisSuggestedTypes,
        metadata={
            "description": "A list of missing types for non-primitives defined by the file"
        },
        many=True,
    )


class SignatureAnalysisOutputSchema(Schema):
    tasks = fields.Nested(
        SignatureAnalysisSignatureSchema,
        metadata={
            "description": "A list of signature analyses for the plugin tasks "
            "provided in the input file"
        },
        many=True,
    )


class ResourceImportSourceTypes(Enum):
    GIT = "git"
    UPLOAD_ARCHIVE = "upload_archive"
    UPLOAD_FILES = "upload_files"


class ResourceImportResolveNameConflictsStrategy(Enum):
    FAIL = "fail"
    UPDATE = "update"
    OVERWRITE = "overwrite"


class ResourceImportSchema(Schema):
    """The request schema for importing resources"""

    groupId = fields.Integer(
        attribute="group_id",
        data_key="group",
        metadata={
            "description": "ID of the Group that will own the imported resources."
        },
        required=True,
    )
    sourceType = fields.Enum(
        ResourceImportSourceTypes,
        attribute="source_type",
        metadata={
            "description": "The source of the resources to import"
            "('upload_archive', 'upload_files', or 'git'."
        },
        by_value=True,
        required=True,
    )
    gitUrl = fields.String(
        attribute="git_url",
        metadata={
            "description": "The URL of the git repository containing resources to import. "
            "A git branch can optionally be specified by appending #BRANCH_NAME. "
            "Used when sourceType is 'git'."
        },
        required=False,
    )
    archiveFile = FileUpload(
        attribute="archive_file",
        metadata={
            "type": "file",
            "format": "binary",
            "description": "The archive file containing resources to import (.tar.gz). "
            "Used when sourceType is 'upload_archive'.",
        },
        required=False,
    )
    files = MultiFileUpload(
        attribute="files",
        metadata={
            "type": "file",
            "format": "binary",
            "description": "The files containing the resources to import."
            "Used when sourceType is 'upload_files'.",
        },
        required=False,
    )
    configPath = fields.String(
        attribute="config_path",
        metadata={"description": "The path to the toml configuration file."},
        load_default="dioptra.toml",
    )
    resolveNameConflictsStrategy = fields.Enum(
        ResourceImportResolveNameConflictsStrategy,
        attribute="resolve_name_conflicts_strategy",
        metadata={
            "description": "Strategy for resolving resource name conflicts. "
            "Available options are 'fail', 'update', or 'overwrite'"
        },
        by_value=True,
        load_default=ResourceImportResolveNameConflictsStrategy.FAIL.value,
    )

    @validates_schema
    def validate_source(self, data, **kwargs):
        num_provided_sources = sum(
            [
                "git_url" in data,
                "archiveFile" in request.files,
                "files" in request.files,
            ]
        )
        if num_provided_sources != 1:
            raise ValidationError(
                {
                    "sourceType": "Must only provide exactly one of "
                    "('gitUrl', 'archiveFile', 'files')."
                }
            )

        if (
            data["source_type"] == ResourceImportSourceTypes.GIT
            and "git_url" not in data
        ):
            raise ValidationError({"gitUrl": "field required when sourceType is 'git'"})

        if (
            data["source_type"] == ResourceImportSourceTypes.UPLOAD_ARCHIVE
            and "archiveFile" not in request.files
        ):
            raise ValidationError(
                {"archiveFile": "field required when sourceType is 'upload_archive'"}
            )

        if (
            data["source_type"] == ResourceImportSourceTypes.UPLOAD_FILES
            and "files" not in request.files
        ):
            raise ValidationError(
                {"files": "field required when sourceType is 'upload_files'"}
            )


class ValidateEntrypointRequestSchema(Schema):
    """The proposed inputs for an Entrypoint resource to be validated."""

    groupId = fields.Integer(
        attribute="group_id",
        data_key="group",
        metadata={"description": "ID of the Group validating the Entrypoint resource."},
        required=True,
    )
    taskGraph = fields.String(
        attribute="task_graph",
        metadata={"description": "Proposed task graph for the Entrypoint resource."},
        required=True,
    )
    artifactGraph = fields.String(
        attribute="artifact_graph",
        metadata={
            "description": "Proposed artifact graph for the Entrypoint resource."
        },
        required=False,
    )
    pluginSnapshotIds = fields.List(
        fields.Integer(),
        attribute="plugin_snapshot_ids",
        data_key="pluginSnapshots",
        metadata={
            "description": (
                "A list of IDs for the Plugin Snapshots that will be attached to the "
                "Entrypoint resource."
            )
        },
    )
    parameters = fields.Nested(
        EntrypointParameterSchema,
        attribute="parameters",
        many=True,
        metadata={"description": "Proposed parameters for the Entrypoint resource."},
    )
    artifacts = fields.Nested(
        EntrypointArtifactSchema,
        attribute="artifacts",
        many=True,
        metadata={
            "description": "Proposed artifact inputs for the Entrypoint resource."
        },
    )


class ValidateEntrypointIssueSchema(Schema):
    """The response for the validateEntrypoint endpoint."""

    type_ = fields.String(
        attribute="type",
        data_key="type",
        metadata={"description": "The validation issue type."},
    )
    severity = fields.String(
        attribute="severity",
        metadata={"description": "The severity of the validation issue."},
    )
    message = fields.String(
        attribute="message",
        metadata={"description": "A message describing the validation issue."},
    )

    @pre_dump
    def stringify_enums(self, data, **kwargs):
        if isinstance(data, ValidationIssue):
            return {
                "type": data.type.name,
                "severity": data.severity.name,
                "message": data.message,
            }

        return data


class ValidateEntrypointResponseSchema(Schema):
    """The response for the validateEntrypoint endpoint."""

    schemaValid = fields.Bool(
        attribute="schema_valid",
        metadata={
            "description": (
                "Indicates whether the proposed inputs for the Entrypoint resource "
                "are valid. If False, the schemaIssues field will contain a list of "
                "validation issues."
            ),
        },
    )
    schemaIssues = fields.Nested(
        ValidateEntrypointIssueSchema,
        attribute="schema_issues",
        metadata={"description": "A list of validation issues detected in the schema."},
        many=True,
    )
