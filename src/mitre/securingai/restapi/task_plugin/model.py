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
