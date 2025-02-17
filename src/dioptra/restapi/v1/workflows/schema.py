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

from marshmallow import Schema, fields


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
