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
"""The schemas for serializing/deserializing the task plugin endpoint objects.

.. |TaskPlugin| replace:: :py:class:`~.model.TaskPlugin`
.. |TaskPluginUploadForm| replace:: :py:class:`~.model.TaskPluginUploadForm`
.. |TaskPluginUploadFormData| replace:: :py:class:`~.model.TaskPluginUploadFormData`
"""
from __future__ import annotations

from typing import Any, Dict

from marshmallow import Schema, fields, post_dump, post_load, pre_dump
from werkzeug.datastructures import FileStorage

from .model import TaskPlugin, TaskPluginUploadForm, TaskPluginUploadFormData


class TaskPluginSchema(Schema):
    """The schema for the data stored in a |TaskPlugin| object.

    Attributes:
        taskPluginName: A unique string identifying a task plugin package within a
            collection.
        collection: The collection that contains the task plugin module, for example,
            the "securingai_builtins" collection.
        modules: The available modules (Python files) in the task plugin package.
    """

    __model__ = TaskPlugin

    taskPluginName = fields.String(
        attribute="task_plugin_name",
        metadata=dict(
            description="A unique string identifying a task plugin package within a "
            "collection."
        ),
    )
    collection = fields.String(
        attribute="collection",
        metadata=dict(
            description="The collection that contains the task plugin module, for "
            'example, the "builtins" collection.',
        ),
    )
    modules = fields.List(
        fields.String(),
        attribute="modules",
        metadata=dict(
            description="The available modules (Python files) in the task plugin "
            "package."
        ),
    )

    @post_load
    def deserialize_object(
        self, data: Dict[str, Any], many: bool, **kwargs
    ) -> TaskPlugin:
        """Creates a |TaskPlugin| object from the validated data."""
        return self.__model__(**data)


class TaskPluginUploadFormSchema(Schema):
    """The schema for the task plugin uploading form.

    Attributes:
        task_plugin_name: A unique string identifying a task plugin package within a
            collection.
        task_plugin_file: A tarball archive or zip file containing a single task plugin
            package.
        collection: The collection where the task plugin package should be stored.
    """

    task_plugin_name = fields.String(
        attribute="task_plugin_name",
        metadata=dict(
            description="A unique string identifying a task plugin package within a "
            "collection."
        ),
    )
    task_plugin_file = fields.Raw(
        metadata=dict(
            description="A tarball archive or zip file containing a single task plugin "
            "package.",
        ),
    )
    collection = fields.String(
        attribute="collection",
        metadata=dict(
            description="The collection where the task plugin should be stored."
        ),
    )

    @pre_dump
    def extract_data_from_form(
        self, data: TaskPluginUploadForm, many: bool, **kwargs
    ) -> Dict[str, Any]:
        """Extracts data from the |TaskPluginUploadForm| for validation."""

        return {
            "task_plugin_name": data.task_plugin_name.data,
            "task_plugin_file": data.task_plugin_file.data,
            "collection": data.collection.data,
        }

    @post_dump
    def serialize_object(
        self, data: Dict[str, Any], many: bool, **kwargs
    ) -> TaskPluginUploadFormData:
        """Creates a |TaskPluginUploadFormData| object from the validated data."""
        return TaskPluginUploadFormData(**data)  # type: ignore


TaskPluginUploadSchema = [
    dict(
        name="task_plugin_name",
        type=str,
        location="form",
        required=True,
        help="A unique string identifying a task plugin package within a collection.",
    ),
    dict(
        name="task_plugin_file",
        type=FileStorage,
        location="files",
        required=True,
        help="A tarball archive or zip file containing a single task plugin "
        "package.",
    ),
    dict(
        name="collection",
        type=str,
        location="form",
        required=True,
        help="The collection where the task plugin should be stored.",
    ),
]
