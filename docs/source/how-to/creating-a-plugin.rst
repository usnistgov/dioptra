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

This how-to explains how to build Plugins in Dioptra. You will learn how to create a plugin container, add code to it, and register tasks.

This guide covers the two main types of Plugins:

- **Function tasks:** Standard Python functions decorated for Dioptra.
- **Artifact tasks:** Python classes that handle file serialization/deserialization.

Learn about what Plugins are in our :ref:`Plugin Explainer documentation <plugins-explanation>`.

Prerequisites
-------------

* :ref:`getting-started-running-dioptra` - You need access to a Dioptra deployment.
* :ref:`Guided User Interface Setup [ADD REF] <fix_missing_ref_placeholder>` - You need access to the GUI.

.. _create_plugin_recipe:

Plugin Creation Workflow
------------------------

Follow these steps to create and register a new plugin.

.. admonition:: Step 1: Prepare your Python Code

   Write your Python functions or Artifact classes in a local file. Ensure you have applied the necessary decorators or class inheritance.
   
   * For standard functions, see :ref:`Code Example: Function Tasks <plugin_function_code>`.
   * For artifact handlers, see :ref:`Code Example: Artifact Tasks <plugin_artifact_code>`.

.. admonition:: Step 2: Create the Plugin Container

   In the Dioptra GUI, navigate to the **Plugins tab**. Click **Create a new plugin**. Enter a *name* and *description*, then confirm.

.. admonition:: Step 3: Create a Plugin File

   Click into your newly created Plugin. Within the Plugin container, click the **"Create"** button in the Plugin Files window. In the Plugin file editor, provide a filename, a description, and paste or upload your Python code (from Step 1) into the code editor.

.. admonition:: Step 4: Register Tasks

   You must register the specific tasks defined in your code so Dioptra can see them. Use the **Task Form** on the right side of the file editor:

   * **For Functions:** Click **"Import Function Tasks"** to auto-detect and register decorated functions (requires type annotations in Python code). Alternatively, register tasks manually:
     
     * **Task Name:** Must match the Python *Function Name* exactly.
     * **Input Params:** Add parameters matching your function arguments exactly.
     * **Output Params:** Define names for the returned values. See :ref:`Multiple Outputs <multiple_outputs_ref>` below for details on handling iterables.

   * **For Artifacts:** You must **manually register** the task. 
     
     * **Task Name:** Must match the Python *Class Name* exactly.
     * **Output Params:** Select the **Parameter Type** that corresponds to the object produced by the ``deserialize`` method.


   All inputs and outputs require a **Parameter Type** for validation. See :ref:`Plugin Parameter Types <plugin_param_types_ref>` below.

.. admonition:: Step 5: Save and Confirm

   Once the tasks appear in the list, click **Save File**. Your plugin is now ready for use in experiments.

----

.. _plugin_param_types_ref:

More info
----------

Plugin Parameter Types
~~~~~~~~~~~~~~~~~~~~~~

Dioptra uses parameter types to validate data passing between tasks.

* **Function Tasks:** You must assign types to all **Input** arguments and **Output** returns.
* **Artifact Tasks:** You must assign a type to the **Output Parameter**.

You may use built-in types (e.g., ``any``, ``string``, ``integer``, ``boolean``, ``float``) or define your own.

   More info: 

   * :ref:`How to create plugin param types [ADD REF] <fix_missing_ref_placeholder>`
   * :ref:`Explanation - Parameter Types [ADD REF] <fix_missing_ref_placeholder>`

.. _multiple_outputs_ref:

Multiple Outputs of Function Tasks
~~~~~~~~~~~~~~~~~~~~~~

A task may produce zero, one, or multiple outputs. These outputs must be named and typed so they can be referenced by subsequent tasks in a graph.

If your function returns a single value, you map it to a single output parameter. If your function returns an **iterable** (e.g., a list or tuple), Dioptra extracts values from the iterable and assigns them to your defined output parameters in order.

   See :ref:`Plugins - Reference <plugins-reference-return-values>` for more. 

Register with REST API
----------------------

Using Python Client
~~~~~~~~~~~~~~~~~~~~~~

You can register plugins programmatically using the **Dioptra Python client**. This is essential for automated deployment pipelines.

   .. automethod:: dioptra.client.plugins.PluginFilesSubCollectionClient.create
      :no-docstring:

See :ref:`Plugins - Reference <plugin-reference-python-client-registration>` for full code examples and workflow.

With HTTP Requests
~~~~~~~~~~~~~~~~~~~~~~

Plugins can also be created and registered directly using **HTTP POST** requests.

See the :http:post:`POST /api/v1/plugins </api/v1/plugins/>` endpoint documentation for payload requirements.

----

.. _plugin_function_code:


Example Plugin Code
-----------------------------

Function Tasks
~~~~~~~~~~~~~~

Use this pattern when creating standard processing tasks.

.. admonition:: Plugin Function Task Example
   :class: code-panel python

   .. code-block:: python

      # plugin_file_1.py

      from dioptra import pyplugs

      # Helper function (internal use only)
      def sqr(a: float) -> float:
         return a*a

      # Plugin function task (registered)
      @pyplugs.register
      def my_plugin_function_task(b: float) -> str:
         return f"{b} squared is {sqr(b)}"

.. note::
   Functions must be decorated with ``@Pyplugs.register`` to be used in entrypoint task graphs. Type annotations are recommended.
   See :ref:`Plugins - Reference <plugins-reference>` for more. 


----

.. _plugin_artifact_code:

Artifact Handlers
~~~~~~~~~~~~~~~~~~

Use this pattern when defining how to save (serialize) or load (deserialize) specific data types.

.. admonition:: Artifact Plugin Example - NumPy Array Handler
   :class: code-panel python

   .. code-block:: python

      from __future__ import annotations
      from pathlib import Path
      from typing import Any
      import numpy as np
      from dioptra.sdk.api.artifact import ArtifactTaskInterface

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

.. note::
   Classes must inherit from ``ArtifactTaskInterface``. You must implement ``serialize`` and ``deserialize``.
   See :ref:`Plugins - Reference <plugins-reference>` for more. 


----

.. seealso::

   * :ref:`Overview of Experiments <experiment-overview-explanation>` - Understand how plugins fit into experiments.
   * :ref:`Explanation - Artifacts [ADD REF] <fix_missing_ref_placeholder>` - Learn about artifacts.
   * :ref:`Building Blocks Tutorial - Part 4 <tutorial-1-part-4>` - See artifacts used in a data science workflow.

.. _fix_missing_ref_placeholder:

Missing References Placeholder
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This is an empty section to serve as a destination link for any references that don't exist yet.