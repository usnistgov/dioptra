# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
"""The interfaces for creating and updating |TaskPlugin| objects.

.. |TaskPlugin| replace:: :py:class:`~.model.TaskPlugin`
"""

from typing import List

from typing_extensions import TypedDict


class TaskPluginInterface(TypedDict, total=False):
    """The interface for constructing a new |TaskPlugin| object.

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
