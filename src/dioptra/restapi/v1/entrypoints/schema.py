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

from typing import Any

from marshmallow import Schema, fields, pre_dump, validate, validates
from marshmallow.exceptions import ValidationError

from dioptra.restapi.errors import InputParameterNotUniqueError
from dioptra.restapi.utils import find_non_unique
from dioptra.restapi.v1.plugins.schema import (
    ALLOWED_PLUGIN_TASK_PARAMETER_REGEX,
    PluginSnapshotRefSchema,
    PluginTaskContainerSchema,
    PluginTaskParameterSchema,
)
from dioptra.restapi.v1.queues.schema import QueueRefSchema
from dioptra.restapi.v1.schemas import (
    BasePageSchema,
    GroupIdQueryParametersSchema,
    PagingQueryParametersSchema,
    SearchQueryParametersSchema,
    ShowDeletedQueryParametersSchema,
    SortByGetQueryParametersSchema,
    generate_base_resource_ref_schema,
    generate_base_resource_schema,
)
from dioptra.task_engine.issues import ValidationIssue


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

    @validates("parameters")
    def validate_parameters(self, parameters: list[dict[str, Any]]):
        duplicates = find_non_unique("name", parameters)
        if len(duplicates) > 0:
            raise InputParameterNotUniqueError("Entrypoint", duplicates=duplicates)

    @validates("artifactParameters")
    def validate_artifact_parameters(self, parameters: list[dict[str, Any]]):
        duplicates = find_non_unique("name", parameters)
        if len(duplicates) > 0:
            raise InputParameterNotUniqueError(
                "Entrypoint Artifact", duplicates=duplicates
            )
        for parameter in parameters:
            duplicates = find_non_unique("name", parameter["output_params"])
            if len(duplicates) > 0:
                raise InputParameterNotUniqueError(
                    "Entrypoint Artifact Output",
                    artifact_name=parameter["name"],
                    duplicates=duplicates,
                )


class ValidateOnlySchema(Schema):
    validateOnly = fields.Bool(
        attribute="validate_only",
        data_key="validateOnly",
        load_default=False,
        metadata={
            "description": "Flag indicating whether to perform a full validation and save the entrypoint, or perform a lighter validation and not save the entrypoint."
        },
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
    ShowDeletedQueryParametersSchema,
):
    """The query parameters for the GET method of the /entrypoints endpoint."""


class DelimitedKeyValuePairs(fields.Field):
    def __init__(
        self,
        *,
        delimiter: str = ",",
        equality: str = ":",
        **additional_metadata,
    ) -> None:
        super().__init__(**additional_metadata)
        self.delimiter = delimiter
        self.equality = equality

    def _deserialize(self, value, attr, data, **kwargs) -> dict[str, str]:
        try:
            if value == "":
                return {}
            return {
                str(pair.split(self.equality)[0]): str(pair.split(self.equality)[1])
                for pair in value.split(self.delimiter)
            }
        except Exception as e:
            raise ValidationError(
                f"{attr} is not a delimited list {value}. List format should be key{self.equality}value{self.delimiter}key2{self.equality}value2{self.delimiter}key3{self.equality}value3."
            ) from e


class SwapChoiceRequestSchema(Schema):
    swaps = DelimitedKeyValuePairs(
        attribute="swaps",
        data_key="swaps",
        metadata={
            "description": (
                "A list of swap choices to be applied to the entrypoint task graph."
            )
        },
    )


class DynamicGlobalParametersResponseSchema(Schema):
    globalParameters = fields.List(
        fields.String(),
        attribute="entrypoint_params",
        data_key="entrypointParams",
        metadata={
            "description": (
                "A list of global parameters used in the entrypoint task graph."
            )
        },
    )
    topologicalSort = fields.List(
        fields.String(),
        attribute="topological_sort",
        data_key="topologicalSort",
        metadata={
            "description": ("A list of task names topologically sorted by dependency.")
        },
    )
    activePlugins = fields.Nested(
        PluginSnapshotRefSchema,
        attribute="active_plugins",
        data_key="activePlugins",
        metadata={"description": ("A list of plugin objects used in the entrypoint.")},
        many=True,
    )


class SwapInfoSchema(Schema):
    """Schema representing a single swap option (SwapInfo)."""

    swapName = fields.String(
        attribute="swap_name",
        metadata={"description": "The name of the swap this definition belongs to."},
        required=True,
    )
    taskAlias = fields.String(
        attribute="task_alias",
        metadata={"description": "Alias for the task definition."},
        required=True,
    )
    taskName = fields.String(
        attribute="task_name",
        metadata={"description": "Name of the task that can be swapped in."},
        required=True,
    )
    entrypointKeywordArgs = fields.List(
        fields.String(),
        attribute="entrypoint_keyword_args",
        metadata={
            "description": "A list of the keyword arguments that need to be specified for this task."
        },
        required=True,
    )
    pluginFileResourceSnapshotId = fields.Integer(
        attribute="plugin_file_resource_snapshot_id",
        metadata={
            "description": "Resource snapshot ID of the plugin file containing the task."
        },
        required=True,
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


class EntrypointConfigSchema(Schema):
    types = fields.Dict(
        keys=fields.String(),
        values=fields.Raw(),
        attribute="types",
        allow_none=True,
        metadata={
            "description": "A dictionary of types defined for this experiment.",
        },
        load_default=dict,
    )
    parameters = fields.Dict(
        keys=fields.String(),
        values=fields.Raw(),
        attribute="parameters",
        allow_none=True,
        metadata={
            "description": "A dictionary of parameters defined for this experiment.",
        },
        load_default=dict,
    )
    tasks = fields.Dict(
        keys=fields.String(),
        values=fields.Raw(),
        attribute="tasks",
        allow_none=True,
        metadata={
            "description": "A dictionary of tasks defined for this experiment.",
        },
        load_default=dict,
    )
    graph = fields.Dict(
        keys=fields.String(),
        values=fields.Raw(),
        attribute="graph",
        allow_none=True,
        metadata={
            "description": "A dictionary representing the task graph for this experiment.",
        },
        load_default=dict,
    )
    artifact_outputs = fields.Dict(
        keys=fields.String(),
        values=fields.Raw(),
        attribute="artifact_outputs",
        allow_none=True,
        metadata={
            "description": "A dictionary representing the artifact outputs for this experiment.",
        },
        load_default=dict,
    )
    artifact_inputs = fields.Dict(
        keys=fields.String(),
        values=fields.Raw(),
        attribute="artifact_inputs",
        allow_none=True,
        metadata={
            "description": "A dictionary representing the artifact inputs for this experiment.",
        },
        load_default=dict,
    )
