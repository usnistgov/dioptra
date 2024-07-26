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
"""The schemas for serializing/deserializing Plugin resources."""
import re

from marshmallow import Schema, fields, validate

from dioptra.restapi.v1.plugin_parameter_types.schema import (
    PluginParameterTypeRefSchema,
)
from dioptra.restapi.v1.schemas import (
    BasePageSchema,
    GroupIdQueryParametersSchema,
    PagingQueryParametersSchema,
    SearchQueryParametersSchema,
    generate_base_resource_ref_schema,
    generate_base_resource_schema,
)

ALLOWED_PLUGIN_NAME_REGEX = re.compile(r"^([A-Z]|[A-Z_][A-Z0-9_]+)$", flags=re.IGNORECASE)  # noqa: B950; fmt: skip
ALLOWED_PLUGIN_FILENAME_REGEX = re.compile(r"^([A-Za-z]|[A-Za-z_][A-Za-z0-9_]+)\.py$")
ALLOWED_PLUGIN_TASK_REGEX = re.compile(r"^([A-Z]|[A-Z_][A-Z0-9_]+)$", flags=re.IGNORECASE)  # noqa: B950; fmt: skip
ALLOWED_PLUGIN_TASK_PARAMETER_REGEX = re.compile(r"^([A-Z]|[A-Z_][A-Z0-9_]+)$", flags=re.IGNORECASE)  # noqa: B950; fmt: skip


PluginRefBaseSchema = generate_base_resource_ref_schema("Plugin")
PluginSnapshotRefBaseSchema = generate_base_resource_ref_schema(
    "Plugin", keep_snapshot_id=True
)


class PluginRefSchema(PluginRefBaseSchema):  # type: ignore
    """The reference schema for the data stored in a Plugin resource."""

    name = fields.String(
        attribute="name",
        metadata=dict(description="Name of the Plugin resource."),
    )


class PluginSnapshotRefSchema(PluginSnapshotRefBaseSchema):  # type: ignore
    """The snapshot reference schema for the data stored in a Plugin resource."""

    name = fields.String(
        attribute="name",
        metadata=dict(description="Name of the Plugin resource."),
    )


PluginFileRefBaseSchema = generate_base_resource_ref_schema("PluginFile")


class PluginFileRefSchema(PluginFileRefBaseSchema):  # type: ignore
    """The reference schema for the data stored in a PluginFile."""

    pluginId = fields.Int(
        attribute="plugin_id",
        data_key="plugin",
        metadata=dict(description="ID for the Plugin resource this file belongs to."),
    )
    filename = fields.String(
        attribute="filename",
        metadata=dict(description="Filename of the PluginFile resource."),
    )


class PluginTaskParameterSchema(Schema):
    """The schema for the data stored in a PluginTaskParameter"""

    name = fields.String(
        attribute="name",
        metadata=dict(description="Name of the PluginTaskParameter."),
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
    parameterTypeId = fields.Int(
        attribute="parameter_type_id",
        data_key="parameterType",
        metadata=dict(
            description="The ID of the assigned PluginParameterType resource"
        ),
        load_only=True,
        required=True,
    )
    parameterType = fields.Nested(
        PluginParameterTypeRefSchema,
        attribute="parameter_type",
        metadata=dict(description="The assigned PluginParameterType resource."),
        dump_only=True,
    )


class PluginTaskInputParameterSchema(PluginTaskParameterSchema):
    """The schema for the data stored in a PluginTaskInputParameter"""

    required = fields.Boolean(
        attribute="required",
        metadata=dict(
            description=(
                "Sets whether the input parameter is required (True) or optional "
                "(False). If True, then this parameter must be assigned a value in "
                "order to execute the PluginTask."
            ),
        ),
        load_default=True,
    )


class PluginTaskOutputParameterSchema(PluginTaskParameterSchema):
    """The schema for the data stored in a PluginTaskInputParameter"""


class PluginTaskSchema(Schema):
    """The schema for the data stored in a PluginTask."""

    name = fields.String(
        attribute="name",
        metadata=dict(description="Name of the PluginTask."),
        required=True,
        validate=validate.Regexp(
            ALLOWED_PLUGIN_TASK_REGEX,
            error=(
                "'{input}' is not a compatible name for a Python function. A Python "
                "function name must start with a letter or underscore, followed by "
                "letters, numbers, or underscores. In addition, '_' is not a valid "
                "Python function name."
            ),
        ),
    )
    inputParams = fields.Nested(
        PluginTaskInputParameterSchema,
        attribute="input_params",
        many=True,
        metadata=dict(
            description="List of input PluginTaskParameters in this PluginTask."
        ),
    )
    outputParams = fields.Nested(
        PluginTaskOutputParameterSchema,
        attribute="output_params",
        many=True,
        metadata=dict(
            description="List of output PluginTaskParameters in this PluginTask."
        ),
    )


PluginBaseSchema = generate_base_resource_schema("Plugin", snapshot=True)


class PluginMutableFieldsSchema(Schema):
    """The schema for the mutable data fields in a Plugin resource."""

    name = fields.String(
        attribute="name",
        metadata=dict(description="Name of the Plugin resource."),
        required=True,
        validate=validate.Regexp(
            ALLOWED_PLUGIN_NAME_REGEX,
            error=(
                "'{input}' is not a compatible name for Python module. A Python "
                "module must start with a letter or underscore, followed by letters, "
                "numbers, or underscores. In addition, a Python module name cannot "
                "be named '_' with no other characters."
            ),
        ),
    )
    description = fields.String(
        attribute="description",
        metadata=dict(description="Description of the Plugin resource."),
        load_default=None,
    )


class PluginSchema(PluginMutableFieldsSchema, PluginBaseSchema):  # type: ignore
    """The schema for the data stored in a Plugin resource."""

    files = fields.Nested(
        PluginFileRefSchema,
        attribute="files",
        metadata=dict(description="Files associated with the Plugin resource."),
        many=True,
        dump_only=True,
    )


class PluginPageSchema(BasePageSchema):
    """The paged schema for the data stored in a Plugin resource."""

    data = fields.Nested(
        PluginSchema,
        many=True,
        metadata=dict(description="List of Plugin resources in the current page."),
    )


class PluginGetQueryParameters(
    PagingQueryParametersSchema,
    GroupIdQueryParametersSchema,
    SearchQueryParametersSchema,
):
    """The query parameters for the GET method of the /plugins endpoint."""


PluginFileBaseSchema = generate_base_resource_schema("PluginFile", snapshot=True)


class PluginFileMutableFieldsSchema(Schema):
    """The schema for the mutable data fields in a PluginFile resource."""

    filename = fields.String(
        attribute="filename",
        metadata=dict(description="Name of the PluginFile resource."),
        required=True,
        validate=validate.Regexp(
            ALLOWED_PLUGIN_FILENAME_REGEX,
            error=(
                "'{input}' is not a compatible name for a Python file. A Python "
                "filename must start with a letter or underscore, followed by letters, "
                "numbers, or underscores, and ending with a lowercase '.py'. In "
                "addition, '_.py' is not a valid Python filename."
            ),
        ),
    )
    contents = fields.String(
        attribute="contents",
        metadata=dict(description="Contents of the file."),
        required=True,
    )
    tasks = fields.Nested(
        PluginTaskSchema,
        attribute="tasks",
        metadata=dict(description="Tasks associated with the PluginFile resource."),
        many=True,
    )
    description = fields.String(
        attribute="description",
        metadata=dict(description="Description of the PluginFile resource."),
        load_default=None,
    )


class PluginFileSchema(PluginFileMutableFieldsSchema, PluginFileBaseSchema):  # type: ignore
    """The schema for the data stored in a PluginFile resource."""

    plugin = fields.Nested(
        PluginRefSchema,
        attribute="plugin",
        metadata=dict(description="The Plugin resource this file belongs to."),
        dump_only=True,
    )


class PluginFilePageSchema(BasePageSchema):
    """The paged schema for the data stored in a PluginFile resource."""

    data = fields.Nested(
        PluginFileSchema,
        many=True,
        metadata=dict(description="List of PluginFile resources in the current page."),
    )


class PluginFileGetQueryParameters(
    PagingQueryParametersSchema,
    SearchQueryParametersSchema,
):
    """The query parameters for the GET method of the /plugins/{id}/files/ endpoint."""
