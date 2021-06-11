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
"""The data models for the task plugin endpoint objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from typing_extensions import TypedDict
from werkzeug.datastructures import FileStorage
from wtforms.fields import SelectField, StringField
from wtforms.validators import InputRequired


@dataclass
class TaskPlugin(object):
    """The task plugin data class.

    Attributes:
        task_plugin_name: A unique string identifying a task plugin package within a
            collection.
        collection: The collection that contains the task plugin module, for example,
            the "securingai_builtins" collection.
        modules: The available modules (Python files) in the task plugin package.
    """

    task_plugin_name: str
    collection: str
    modules: List[str]

    def __eq__(self, other):
        if not isinstance(other, TaskPlugin):
            return NotImplemented

        return (
            self.task_plugin_name == other.task_plugin_name
            and self.collection == other.collection
            and set(self.modules) == set(other.modules)
        )


class TaskPluginUploadForm(FlaskForm):
    """The task plugin upload form.

    Attributes:
        task_plugin_name: A unique string identifying a task plugin package within a
            collection.
        task_plugin_file: A tarball archive or zip file containing a single task plugin
            package.
        collection: The collection where the task plugin package should be stored.
    """

    task_plugin_name = StringField(
        "Task Plugin Name",
        validators=[InputRequired()],
        description="A unique string identifying a task plugin package within a "
        "collection.",
    )
    task_plugin_file = FileField(
        validators=[
            FileRequired(),
            FileAllowed(["tar", "tgz", "bz2", "gz", "xz", "zip"]),
        ],
        description="A tarball archive or zip file containing a single task plugin "
        "package.",
    )
    collection = SelectField(
        "Task Plugin Collection",
        choices=[("securingai_custom", "Custom Task Plugins Collection")],
        validators=[InputRequired()],
        description="The collection where the task plugin package should be stored.",
    )


class TaskPluginUploadFormData(TypedDict, total=False):
    """The data extracted from the task plugin upload form.

    Attributes:
        task_plugin_name: A unique string identifying a task plugin package within a
            collection.
        task_plugin_file: A tarball archive or zip file containing a single task plugin
            package.
        collection: The collection where the task plugin package should be stored.
    """

    task_plugin_name: str
    task_plugin_file: FileStorage
    collection: str
