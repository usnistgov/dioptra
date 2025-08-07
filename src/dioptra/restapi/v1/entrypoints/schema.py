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

from marshmallow import Schema, fields, validate

from dioptra.restapi.v1.plugins.schema import (
    ALLOWED_PLUGIN_TASK_PARAMETER_REGEX,
    PluginTaskContainerSchema,
    PluginTaskParameterSchema,
)
from dioptra.restapi.v1.queues.schema import QueueRefSchema
from dioptra.restapi.v1.schemas import (
    BasePageSchema,
    GroupIdQueryParametersSchema,
    PagingQueryParametersSchema,
    SearchQueryParametersSchema,
    SortByGetQueryParametersSchema,
    generate_base_resource_ref_schema,
    generate_base_resource_schema,
)


class EntrypointPluginFileSchema(Schema):
    """The schema for the data stored in a Entrypoint PluginFile snapshot."""

    id = fields.Integer(
        attribute="id",
        metadata={"description": "ID for the PluginFile resource."},
    )
    filename = fields.String(
        attribute="filename",
        metadata={"description": "Filename of the PluginFile resource."},
    )
    snapshotId = fields.Integer(
        attribute="snapshot_id",
        metadata={"description": "Snapshot ID for the PluginFile resource."},
    )
    url = fields.Url(
        attribute="url",
        metadata={"description": "URL for accessing the full PluginFile snapshot."},
        relative=True,
    )
    tasks = fields.Nested(
        PluginTaskContainerSchema,
        attribute="tasks",
        metadata={"description": "Tasks associated with the PluginFile resource."},
        many=False,
    )


class EntrypointPluginSchema(Schema):
    """The schema for the data stored in a Entrypoint Plugin snapshot."""

    id = fields.Integer(
        attribute="id",
        metadata={"description": "ID for the Plugin resource."},
    )
    name = fields.String(
        attribute="name",
        metadata={"description": "Name of the Plugin resource."},
    )
    snapshotId = fields.Integer(
        attribute="snapshot_id",
        metadata={"description": "Snapshot ID for the Plugin resource."},
    )
    latestSnapshot = fields.Boolean(
        attribute="latest_snapshot",
        metadata={"description": "Whether or not the Plugin is the latest version."},
    )
    url = fields.Url(
        attribute="url",
        metadata={"description": "URL for accessing the full Plugin snapshot."},
        relative=True,
    )
    files = fields.Nested(
        EntrypointPluginFileSchema,
        attribute="files",
        many=True,
        metadata={"description": "List of parameters for the entrypoint."},
    )


class EntrypointParameterSchema(Schema):
    """The schema for the data stored in a Entrypoint parameter resource."""

    name = fields.String(
        attribute="name",
        metadata={"description": "Name of the Entrypoint parameter resource."},
        required=True,
    )
    defaultValue = fields.String(
        attribute="default_value",
        metadata={"description": "Default value of the Entrypoint parameter."},
        load_default=None,
    )
    parameterType = fields.String(
        attribute="parameter_type",
        metadata={"description": "Data type of the Entrypoint parameter."},
        required=True,
        validate=validate.OneOf(
            ["string", "float", "integer", "boolean", "list", "mapping"]
        ),
    )


class ArtifactOutputParameterSchema(PluginTaskParameterSchema):
    """The schema for the data stored in a ArtifactOutputParameterSchema"""


class EntrypointArtifactSchema(Schema):
    """The schema for the data stored in a Entrypoint artifact resource."""

    name = fields.String(
        attribute="name",
        metadata={"description": "Name of the Entrypoint artifact resource."},
        required=True,
        validate=validate.Regexp(
            ALLOWED_PLUGIN_TASK_PARAMETER_REGEX,
            error=(
                "'{input}' is not a compatible name for a Python function "
                "parameter. A Python function parameter must start with a letter or "
                "underscore, followed by letters, numbers, or underscores. In "
                "addition, '_' is not a valid Python function parameter."
            ),
        ),
    )
    outputParams = fields.Nested(
        ArtifactOutputParameterSchema,
        attribute="output_params",
        many=True,
        metadata={
            "description": "List of output ArtifactOutputParameters that the artifact is"
            "expected to produce."
        },
    )


EntrypointRefBaseSchema = generate_base_resource_ref_schema("Entrypoint")
EntrypointSnapshotRefBaseSchema = generate_base_resource_ref_schema(
    "Entrypoint", keep_snapshot_id=True
)


class EntrypointRefSchema(EntrypointRefBaseSchema):  # type: ignore
    """The reference schema for the data stored in a Entrypoint resource."""

    name = fields.String(
        attribute="name",
        metadata={"description": "Name of the Entrypoint resource."},
    )


class EntrypointSnapshotRefSchema(EntrypointSnapshotRefBaseSchema):  # type: ignore
    """The snapshot reference schema for the data stored in a Entrypoint resource."""

    name = fields.String(
        attribute="name",
        metadata={"description": "Name of the Entrypoint resource."},
    )


class EntrypointMutableFieldsSchema(Schema):
    """The fields schema for the mutable data in a Entrypoint resource."""

    name = fields.String(
        attribute="name",
        metadata={"description": "Name of the Entrypoint resource."},
        required=True,
    )
    description = fields.String(
        attribute="description",
        metadata={"description": "Description of the Entrypoint resource."},
        load_default=None,
    )
    taskGraph = fields.String(
        attribute="task_graph",
        metadata={"description": "Task graph of the Entrypoint resource."},
        required=True,
    )
    artifactGraph = fields.String(
        attribute="artifact_graph",
        metadata={"description": "Artifact graph of the Entrypoint resource."},
    )
    parameters = fields.Nested(
        EntrypointParameterSchema,
        attribute="parameters",
        many=True,
        metadata={"description": "List of parameters for the entrypoint."},
        load_default=list,
    )
    artifactParameters = fields.Nested(
        EntrypointArtifactSchema,
        attribute="artifact_parameters",
        many=True,
        metadata={"description": "List of artifacts for the entrypoint."},
        load_default=list,
    )
    queueIds = fields.List(
        fields.Integer(),
        attribute="queue_ids",
        data_key="queues",
        metadata={"description": "The queue for the entrypoint."},
        load_only=True,
        load_default=list,
    )


class EntrypointPluginMutableFieldsSchema(Schema):
    pluginIds = fields.List(
        fields.Integer(),
        attribute="plugin_ids",
        data_key="plugins",
        metadata={"description": "List of plugin files for the entrypoint."},
        load_only=True,
        load_default=list,
    )


class EntrypointArtifactPluginMutableFieldsSchema(Schema):
    artifactPluginIds = fields.List(
        fields.Integer(),
        attribute="artifact_plugin_ids",
        data_key="artifactPlugins",
        metadata={"description": "List of artifact_plugin files for the entrypoint."},
        load_only=True,
    )


EntrypointBaseSchema = generate_base_resource_schema("Entrypoint", snapshot=True)


class EntrypointSchema(
    EntrypointArtifactPluginMutableFieldsSchema,
    EntrypointPluginMutableFieldsSchema,
    EntrypointMutableFieldsSchema,
    EntrypointBaseSchema,  # type: ignore
):
    """The schema for the data stored in a Entrypoint resource."""

    plugins = fields.Nested(
        EntrypointPluginSchema,
        attribute="plugins",
        many=True,
        metadata={"description": "List of plugins for the entrypoint."},
        dump_only=True,
    )
    artifactPlugins = fields.Nested(
        EntrypointPluginSchema,
        attribute="artifact_plugins",
        many=True,
        metadata={"description": "List of artifact plugins for the entrypoint."},
        dump_only=True,
    )
    queues = fields.Nested(
        QueueRefSchema,
        attribute="queues",
        many=True,
        metadata={"description": "The queue for the entrypoint."},
        dump_only=True,
    )


class EntrypointDraftSchema(
    EntrypointArtifactPluginMutableFieldsSchema,
    EntrypointPluginMutableFieldsSchema,
    EntrypointMutableFieldsSchema,
    EntrypointBaseSchema,  # type: ignore
):
    """The schema for the data stored in a Entrypoint resource."""

    pluginIds = fields.List(
        fields.Integer(),
        attribute="plugin_ids",
        data_key="plugins",
        metadata={"description": "List of plugin files for the entrypoint."},
    )

    artifactPluginIds = fields.List(
        fields.Integer(),
        attribute="artifact_plugin_ids",
        data_key="artifactPlugins",
        metadata={"description": "List of artifact plugin files for the entrypoint."},
    )

    queueIds = fields.List(
        fields.Integer(),
        attribute="queue_ids",
        data_key="queues",
        metadata={"description": "The queue for the entrypoint."},
    )


class EntrypointPageSchema(BasePageSchema):
    """The paged schema for the data stored in a Entrypoint resource."""

    data = fields.Nested(
        EntrypointSchema,
        many=True,
        metadata={"description": "List of Entrypoint resources in the current page."},
    )


class EntrypointGetQueryParameters(
    PagingQueryParametersSchema,
    GroupIdQueryParametersSchema,
    SearchQueryParametersSchema,
    SortByGetQueryParametersSchema,
):
    """The query parameters for the GET method of the /entrypoints endpoint."""
