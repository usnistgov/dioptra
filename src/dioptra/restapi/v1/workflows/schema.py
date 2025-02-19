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
from marshmallow import Schema, ValidationError, fields, validates_schema

from dioptra.restapi.custom_schema_fields import FileUpload, MultiFileUpload


class FileTypes(Enum):
    TAR_GZ = "tar_gz"
    ZIP = "zip"


class JobFilesDownloadQueryParametersSchema(Schema):
    """The query parameters for making a jobFilesDownload workflow request."""

    jobId = fields.String(
        attribute="job_id",
        metadata=dict(description="A job's unique identifier."),
    )
    fileType = fields.Enum(
        FileTypes,
        attribute="file_type",
        metadata=dict(
            description="The type of file to download: tar_gz or zip.",
        ),
        by_value=True,
        default=FileTypes.TAR_GZ.value,
    )


class SignatureAnalysisSchema(Schema):

    pythonCode = fields.String(
        attribute="python_code",
        metadata=dict(description="The contents of the python file"),
    )


class SignatureAnalysisSignatureParamSchema(Schema):
    name = fields.String(
        attribute="name", metadata=dict(description="The name of the parameter")
    )
    type = fields.String(
        attribute="type", metadata=dict(description="The type of the parameter")
    )


class SignatureAnalysisSignatureInputSchema(SignatureAnalysisSignatureParamSchema):
    required = fields.Boolean(
        attribute="required",
        metadata=dict(description="Whether this is a required parameter"),
    )


class SignatureAnalysisSignatureOutputSchema(SignatureAnalysisSignatureParamSchema):
    pass


class SignatureAnalysisSuggestedTypes(Schema):

    # add proposed_type in next iteration

    name = fields.String(
        attribute="name",
        metadata=dict(description="A suggestion for the name of the type"),
    )

    description = fields.String(
        attribute="description",
        metadata=dict(
            description="The annotation the suggestion is attempting to represent"
        ),
    )


class SignatureAnalysisSignatureSchema(Schema):
    name = fields.String(
        attribute="name", metadata=dict(description="The name of the function")
    )
    inputs = fields.Nested(
        SignatureAnalysisSignatureInputSchema,
        metadata=dict(description="A list of objects describing the input parameters."),
        many=True,
    )
    outputs = fields.Nested(
        SignatureAnalysisSignatureOutputSchema,
        metadata=dict(
            description="A list of objects describing the output parameters."
        ),
        many=True,
    )
    missing_types = fields.Nested(
        SignatureAnalysisSuggestedTypes,
        metadata=dict(
            description="A list of missing types for non-primitives defined by the file"
        ),
        many=True,
    )


class SignatureAnalysisOutputSchema(Schema):
    tasks = fields.Nested(
        SignatureAnalysisSignatureSchema,
        metadata=dict(
            description="A list of signature analyses for the plugin tasks "
            "provided in the input file"
        ),
        many=True,
    )


class ResourceImportSourceTypes(Enum):
    GIT = "git"
    UPLOAD_ARCHIVE = "upload_archive"
    UPLOAD_FILES = "upload_files"


class ResourceImportResolveNameConflictsStrategy(Enum):
    FAIL = "fail"
    OVERWRITE = "overwrite"


class ResourceImportSchema(Schema):
    """The request schema for importing resources"""

    groupId = fields.Integer(
        attribute="group_id",
        data_key="group",
        metadata=dict(
            description="ID of the Group that will own the imported resources."
        ),
        required=True,
    )
    sourceType = fields.Enum(
        ResourceImportSourceTypes,
        attribute="source_type",
        metadata=dict(
            description="The source of the resources to import"
            "('upload_archive', 'upload_files', or 'git'."
        ),
        by_value=True,
        required=True,
    )
    gitUrl = fields.String(
        attribute="git_url",
        metadata=dict(
            description="The URL of the git repository containing resources to import. "
            "A git branch can optionally be specified by appending #BRANCH_NAME. "
            "Used when sourceType is 'git'."
        ),
        required=False,
    )
    archiveFile = FileUpload(
        attribute="archive_file",
        metadata=dict(
            type="file",
            format="binary",
            description="The archive file containing resources to import (.tar.gz). "
            "Used when sourceType is 'upload_archive'.",
        ),
        required=False,
    )
    files = MultiFileUpload(
        attribute="files",
        metadata=dict(
            type="file",
            format="binary",
            description="The files containing the resources to import."
            "Used when sourceType is 'upload_files'.",
        ),
        required=False,
    )
    configPath = fields.String(
        attribute="config_path",
        metdata=dict(description="The path to the toml configuration file."),
        load_default="dioptra.toml",
    )
    resolveNameConflictsStrategy = fields.Enum(
        ResourceImportResolveNameConflictsStrategy,
        attribute="resolve_name_conflicts_strategy",
        metadata=dict(
            description="Strategy for resolving resource name conflicts. "
            "Available options are 'fail' or 'overwrite'"
        ),
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
