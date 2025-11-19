.. This Software (Dioptra) is being made available as a public service by the
.. National Institute of Standards and Technology (NIST), an Agency of the United
.. States Department of Commerce. This software was developed in part by employees of
.. NIST and in part by NIST contractors. Copyright in portions of this software that
.. were developed by NIST contractors has been licensed or assigned to NIST. Pursuant
.. to Title 17 United States Code Section 105, works of NIST employees are not
.. subject to copyright protection in the United States. However, NIST may hold
.. international copyright in software created by its employees and domestic
.. copyright (or licensing rights) in portions of software that were assigned or
.. licensed to NIST. To the extent that NIST holds copyright in this software, it is
.. being made available under the Creative Commons Attribution 4.0 International
.. license (CC BY 4.0). The disclaimers of the CC BY 4.0 license apply to all parts
.. of the software developed or licensed by NIST.
..
.. ACCESS THE FULL CC BY 4.0 LICENSE HERE:
.. https://creativecommons.org/licenses/by/4.0/legalcode

.. _plugins-explanation:

Plugins
================

Summary: What is a Plugin?
--------------------------

A **Plugin** is a logical container used to organize Python code within Dioptra. 



Plugins hold the Python files that define the logic for your experiments. Within these files, you define **Tasks**—the individual units of work that the Dioptra engine executes. There are two distinct types of tasks within a plugin:

1. **Plugin Function Tasks:** These act as the computational steps in a workflow.
   
   * *Example:* A task that accepts a training dataset and returns a trained ML model.

2. **Plugin Artifact Tasks:** These handle the interface between memory and disk storage (I/O).
   
   * *Example:* A task that takes a trained model object from memory and saves it as a ``.pt`` (PyTorch) file.

.. seealso::
   
   * :ref:`Dioptra experiment overview <experiment-overview-explanation>` - How plugins fit into Dioptra experiments
   * :ref:`how_to_create_a_plugin` - Step-by-step guide on building plugins
   * :ref:`Reference - Plugins <plugins-reference>` - Detailed syntax for decorators and type annotations

Plugin Function Tasks
---------------------

Plugin Function Tasks are Python functions that have been registered with Dioptra. They serve as the fundamental "verbs" or actions in your entrypoint workflow graphs. 

These tasks perform specific units of work, such as training a model, calculating a metric, or transforming data. Like standard Python functions, they accept inputs (arguments) and produce return values.

**Example of a Plugin file with a single Plugin Function Task**:

.. admonition:: Python file defining plugin function task
    :class: code-panel python

    .. code-block:: python

        # plugin_file_1.py

        from dioptra import pyplugs

        # Helper function (not registered, internal use only)
        def sqr(a: float) -> float:
            return a*a

        # Plugin function task (registered for use in Dioptra)
        @pyplugs.register 
        def my_plugin_task(b: float) -> str:
            return f"{b} squared is {sqr(b)}"



**Data Flow and Chaining**

When chained together in an entrypoint, the output of one function task can flow automatically into the input of other function tasks. These tasks operate primarily on in-memory objects (such as DataFrames, integers, or model objects).

Note that while Function Tasks process data, they generally do not save it to disk. To persist results, you must pass the output of a Function Task to an Artifact Task.

.. seealso::
    
    * :ref:`Explanation - Entrypoints [ADD REF] <fix_missing_ref_placeholder>` - Learn how tasks are chained and how default parameter values are set.

Function Task Registration
-----------------

Writing the Python code is only the first step; function tasks must be **Registered** to be visible to the Dioptra engine.

Registration defines:

* **The Function Task Name:** Always equal to the function name in Python - this is the identifier used to reference the task in entrypoint graphs.
* **Input/Output Names:** This is how input arguments are set in entrypoints and how output objects are referenced
* **Input/Output Types:** Defining the plugin parameter types for each input/output allows for entrypoint task graph validity

When creating Python plugins, users manually register each function task. This can be done in the user interface or through the REST API. 



.. note::
    
   In order for a Python function to be registrable, it must use the ``@pyplugs.register`` decorator. 
   View :ref:`Reference - Plugins <plugins-reference>` to learn about the ``@pyplugs.register`` syntax for function plugin tasks.


Plugin Artifact Tasks
---------------------

Plugin Artifact Tasks manage data persistence. Because complex Python objects (like machine learning models or large arrays) cannot be plainly written to a text file, they require specific serialization logic.

Artifact tasks encapsulate this logic, allowing Dioptra to:

1. **Serialize:** Convert an in-memory object into a format suitable for storage on disk.
2. **Deserialize:** Load a file from disk and reconstruct the in-memory object.

By isolating I/O logic in Artifact Tasks, the main computational workflow (Function Tasks) remains decoupled from file system operations, making your code cleaner and more portable.


**Plugin artifact task example:**

.. admonition:: Python file defining plugin artifact task - NumPy Array Handler 
    :class: code-panel python

    .. code-block:: python

        # my_artifact_plugins.py

        from __future__ import annotations
        from pathlib import Path
        from typing import Any
        import numpy as np
        from dioptra.sdk.api.artifact import ArtifactTaskInterface

        # Defining serialize and deserialize methods for ArtifactTask
        # Method is required
        class NumpyArrayArtifactTask(ArtifactTaskInterface):
            @staticmethod
            def serialize(working_dir: Path, name: str, contents: np.ndarray, **kwargs) -> Path:
                path = (working_dir / name).with_suffix(".npy")
                np.save(path, contents, allow_pickle=False)
                return path

            @staticmethod
            def deserialize(working_dir: Path, path: str, **kwargs) -> np.ndarray:
                return np.load(working_dir / path)

            @staticmethod
            def validation() -> dict[str, Any] | None:
                return None

    
Artifact tasks can optionally define a **validate** method to ensure argument types are valid for the **serialize** and **deserialize** methods. 


.. note::
   
   Artifact task plugins are Python classes and must inherit from the parent class ``ArtifactTaskInterface``.
   See :ref:`Reference - Plugins <plugins-reference>` to learn about the syntax for creating artifact tasks. 



Artifact Task Registration
-----------------

Artifact tasks are registered similarly to function tasks. 

When an artifact task is registered, the user defines:

* **The Artifact Task Name:** Always equal to the name of the Python class that defines the serialize and deserialize methods
* **Output Parameters:** The name and the type of the return object from the **deserialize** method 


Using Plugins in Entrypoints
----------------------------

Plugins create the "vocabulary" of tasks available to an experiment. To utilize these tasks, you must attach the relevant Plugin to an **Entrypoint**.

Function tasks are used in the entrypoint task graph, and artifact tasks are used in the artifact output graph and the artifact input parameters. 
Entrypoints utilize the types that are declared in function tasks inputs / outputs to ensure the workflow is valid. 

.. seealso::
   
   * :ref:`Explanation - Entrypoints [ADD REF] <fix_missing_ref_placeholder>` - Learn how plugins are used in entrypoints

.. _fix_missing_ref_placeholder:

Missing References Placeholder
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is an empty section to serve as a destination link for any references that don't exist yet.