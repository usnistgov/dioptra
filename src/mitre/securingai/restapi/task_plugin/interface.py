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
