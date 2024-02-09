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
"""
from __future__ import annotations

from marshmallow import Schema, fields

from dioptra.restapi.utils import FileUpload


class TaskPluginSchema(Schema):
    """The schema for the data stored in a |TaskPlugin| object."""

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
        dump_only=True,
    )
    taskPluginFile = FileUpload(
        metadata=dict(
            description="A tarball archive or zip file containing a single task plugin "
            "package.",
        ),
        load_only=True,
    )


class NameStatusResponseSchema(Schema):
    """A simple response for reporting a status for one or more objects."""

    status = fields.String(
        attribute="status",
        metadata=dict(description="The status of the request."),
    )
    collection = fields.String(
        attribute="collection",
        metadata=dict(description="The collection where the task plugin was deleted."),
    )
    taskPluginName = fields.List(
        fields.String(),
        attribute="task_plugin_name",
        metadata=dict(
            description="A list of names identifying the affected object(s)."
        ),
    )
