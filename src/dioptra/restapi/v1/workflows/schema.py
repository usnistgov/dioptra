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

from dioptra.restapi.entrypoints import EntrypointParameterSchema


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


class EntrypointWorkflowSchema(Schema):
    """The YAML that represents the Entrypoint Workflow."""

    taskGraph = fields.String(
        attribute="task_graph",
        metadata=dict(description="Task graph of the Entrypoint resource."),
        required=True,
    )
    pluginIds = fields.List(
        fields.Integer(),
        attribute="plugin_ids",
        data_key="plugins",
        metadata=dict(description="List of plugin files for the entrypoint."),
        load_only=True,
    )
    parameters = fields.Nested(
        EntrypointParameterSchema,
        attribute="parameters",
        many=True,
        metadata=dict(description="List of parameters for the entrypoint."),
    )
