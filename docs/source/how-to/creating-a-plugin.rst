
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

.. _how_to_create_a_plugin:

Create Plugins
========================

This how-to explains how to build Plugins in Dioptra. 

You will learn how to build two types of Plugins:

- :ref:`Plugin function tasks <Create Plugin Function Tasks>` 
- :ref:`Plugin artifact tasks <Create Plugin Artifact Tasks>` 

You will learn how to build both of these Plugin types in the GUI, the Rest API, and through the Python Client. 

.. seealso::
   
   * :ref:`Overview of Experiments <experiment-overview-explanation>` - understand how plugins fit into experiments
   * :ref:`What are plugins? <plugins-explanation>` - learn about how plugins work


Prerequisites
-------------
Before proceeding with the how-to, ensure Dioptra has been set up correctly.
   
* :ref:`getting-started-running-dioptra` - You need access to a Dioptra deployment
* :ref:`Guided User Interface Setup [ADD REF] <fix_missing_ref_placeholder>` - You need to have access to the GUI

.. _Create Plugin Function Tasks:

Create Plugin Function Tasks
----------------------------

**Steps:**

1. Write Python functions 
2. Register Python functions as function tasks within a Dioptra Plugin

First: Annotate custom Python functions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Before creating a plugin function task, you need Python functions you want to register as Plugin function tasks.

.. admonition:: Define plugin function tasks in Python code

   1. **Create one or more Python files with function definitions**. These files will be bundled into a Dioptra Plugin

      .. note:: 

         - Functions *must* be decorated with the ``@Pyplugs.register`` decorator to be used in entrypoint task graphs. More at :ref:`Reference - Plugins Syntax [ADD REF] <fix_missing_ref_placeholder>`
         - Type annotations help with automatic task registration and are recommended 

      **Example Python file with one Plugin function task**

      .. admonition:: Plugin Function Task 
         :class: code-panel python

         .. code-block:: python

            # plugin_file_1.py

            from dioptra import pyplugs

            # Helper function
            def sqr(a: float) -> float:
               return a*a

            # Plugin function task
            @pyplugs.register # Required for task registration
            def my_plugin_function_task(b: float) -> str:
               return f"{b} squared is {sqr(b)}"

Once you've created a set of properly annotated Python functions, you can register them within a Dioptra Plugin.

Second: Register Plugin Function Tasks through User Interface
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. admonition:: Register plugin function tasks in Dioptra plugin (GUI)

   1. **Create the Plugin Container:**
      
      In the GUI, go to the **Plugins tab**. Click **create a new plugin**. Add a *name* and *description*.

      .. figure:: /images/plugin.png
         :alt: Figure depicting the Dioptra Plugins page
         :figclass: border-image
      
         Dioptra Plugins page

      .. figure:: /images/plugin-create.png
         :alt: Figure depicting the Dioptra plugin creation page
         :figclass: border-image
      
         Dioptra plugin creation page

   2. **Add a file:**
      
      Navigate into your newly created plugin. Click **"Add a file"** and open it.

      .. figure:: /images/plugin-manage-files.png
         :alt: Figure depicting the location of the Manage Plugin Files button on the Dioptra Plugins page
         :figclass: border-image

         Manage Plugin Files button

   3. **Customize the file:**
      
      **Edit the metadata**. Add a *filename* and optionally a *description*.

      .. figure:: /images/plugin-file-create.png
         :alt: Figure depicting the Dioptra Plugin File Creation page
         :figclass: border-image

         Dioptra plugin file creation page

   4. **Add Python Code and Register Tasks:**
      
      Upload your Python code or copy/paste it into the editor. Then, register the tasks:
      
      - **Option 1:** Click **"Import Function Tasks"** to auto detect function tasks.
      - **Option 2:** **Manually register each task**. The Plugin function task Name must match the Python function name exactly. 

      .. figure:: /images/plugin-task-create.png
         :alt: Figure depicting the Dioptra Plugin Task Form with created input and output parameters
         :figclass: border-image

         Dioptra Plugin Task Form with created input and output parameters

      .. seealso::
         Refer to the  :ref:`How to create plugin param types [ADD REF] <fix_missing_ref_placeholder>` guide to learn how to register new **Plugin Parameter Types** for your 
         Plugin function tasks outside of the built-in types (``any``, ``string``, ``integer``, etc.).

   5. **Confirm Creation:**

      Once added, the task will appear in the plugin function tasks list. **Save** your file.

      .. figure:: /images/plugin-task-created.png
         :alt: Figure depicting the Dioptra Plugin File Creation page with tasks registered for the file
         :figclass: border-image
         
         Dioptra Plugin File Creation page with tasks registered for the file

Alternatively: Register Plugin Function Tasks - REST API
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It is possible to register plugins programmatically, though it is outside the scope of this guide.

.. admonition:: REST API Info
   :class: code-panel console

   You can create plugins by sending ``POST`` requests to the ``/api/v1/plugins`` endpoint.
   
   .. seealso::
      See the :ref:`REST API Reference [ADD REF] <fix_missing_ref_placeholder>` for payload definitions and authentication requirements.

----

.. _Create Plugin Artifact Tasks:

Create Plugin Artifact Tasks
----------------------------


**Steps:**

1. Define Python classes which overwrite artifact handler methods
2. Register class(es) as artifact tasks within a Dioptra Plugin

.. seealso::
   
   * :ref:`Explanation - Artifacts [ADD REF] <fix_missing_ref_placeholder>` to learn about artifacts

First: Create Artifact Classes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


.. admonition:: Define plugin artifact tasks in Python code

   1. **Create a Python file**.
   2. **Import dependencies**: You must import ``ArtifactTaskInterface`` from ``dioptra.sdk.api.artifact``.
   3. **Define the class**: Create a class that inherits from ``ArtifactTaskInterface``.
   4. **Implement required methods**:
      
      - ``serialize``: Logic to convert an in-memory object (e.g., a NumPy array) into a file on disk.
      - ``deserialize``: Logic to read the file back into an object.
      
      .. note::
         You may optionally define a ``validation`` method to validate the argument types for these methods.
         Learn more about Artifact classes methods :ref:`Reference - Plugins <ref-plugin-artifact-tasks>`

   **Example Artifact Plugin File**

   .. admonition:: Artifact Plugin Example - NumPy Array Handler 
      :class: code-panel python

      .. code-block:: python

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

Second: Register Plugin Artifact Tasks through User Interface
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once your class is defined, you can register it in Dioptra using the GUI.

**NOTE: images are placeholder and are not accurate**

.. admonition:: Register plugin artifact tasks in Dioptra plugin (GUI)

   1. **Create the Plugin Container:**
      
      Navigate to the **Plugins** tab and click **Create**. Enter a name (e.g., "artifact_plugin") and description, then click **Confirm**.

      .. figure:: /images/plugin-create.png
         :alt: Figure depicting the Dioptra plugin creation page
         :figclass: border-image
      
         Dioptra plugin creation page

   2. **Add the Python File:**
      
      Click the **Manage Plugin Files** button next to your new plugin. Click **Create**, enter a filename, and paste the Artifact Class code (from the step above) into the editor.

      .. figure:: /images/plugin-file-create.png
         :alt: Figure depicting the Dioptra Plugin File Creation page
         :figclass: border-image

         Dioptra plugin file creation page

   3. **Register the Artifact Task:**
      
      On the right-hand side of the file creation page, locate the **Task Form**. You must manually register the artifact task.

      - **Task Name:** Must match the **Class Name** exactly (e.g., ``NumpyArrayArtifactTask``).
      - **Task Type:** Ensure you select "Artifact"
      - **Output Params:** For an Artifact Task, the "Output Parameter" is the **Type** of object produced by the ``deserialize`` method (e.g., ``NumpyArray``).

      .. figure:: /images/plugin-task-params.png
         :alt: Figure depicting the Dioptra Plugin Task Form
         :figclass: border-image

         Dioptra Plugin Task Form. Ensure the Task Name matches your Python Class name.

      - Click **Add Task**
   4. **Save:**
      
      Register any additional artifact tasks, then click **Save File** to finalize the changes.


Use in entrypoints
^^^^^^^^^^^^^^^^^^

* Use **Plugin function tasks** in the entrypoint task graph
* Use **Plugin artifact tasks** in the entrypoint artifact output graph AND when utilizing artifact input parameters 

.. seealso::
   
   * :ref:`Building Blocks Tutorial - Part 4 - Saving Artifacts <tutorial-1-part-4>` to see how artifacts can be used in a basic data science workflow
   * :ref:`How to create an entrypoint [ADD REF] <fix_missing_ref_placeholder>` to learn how to use plugin function tasks and artifact plugin tasks in entrypoints


.. _fix_missing_ref_placeholder:

Missing References Placeholder
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is an empty section to serve as a destination link for any references that don't exist yet. 
