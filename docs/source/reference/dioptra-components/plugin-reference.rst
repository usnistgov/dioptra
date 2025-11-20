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

.. _plugins-reference:

Plugins Reference
=================


.. contents:: Table of Contents
   :local:
   :depth: 2

Plugin Definition
-----------------

A **Plugin** in Dioptra acts as a logical container for code, functionally similar to a standard Python package.



**Requirements**

* **Naming:** Must be a valid Python module name (alphanumeric, underscores only). Must be unique within the Dioptra deployment.
* **Structure:** A flat directory containing ``.py`` files. 
* **Init File:** Unlike standard Python packages, an ``__init__.py`` file is **not** required.
* **Content:** Files may contain **Function Task** definitions or **Artifact Task** definitions.

.. _ref-plugin-function-tasks:

Plugin Function Tasks
---------------------

Function tasks are the primary computational units of an experiment.

Code Syntax
~~~~~~~~~~~

To define a function task, you must write a standard Python function and decorate it with ``@pyplugs.register``.

.. code-block:: python

    from dioptra import pyplugs

    # The decorator is required for Dioptra to recognize the task
    @pyplugs.register
    def task_name(param_1: float, param_2: int = 10) -> float:
        return param_1 * param_2

**Type Hints**
Type hints are strongly recommended. Dioptra uses them to automatically populate parameter types during registration imports.

Registration Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~

When registering a function task (via API or GUI), the configuration must match the code logic.

**Parameter Mapping**

* **Input Names:** The registered input parameter names must match the Python function argument names exactly.
* **Order:** [INSERT EXPLANATION ABOUT POSITIONAL VS KEYWORD ARGUMENTS HERE]
* **\*Args / \*\*Kwargs:** [INSERT EXPLANATION ABOUT HOW VARIABLE ARGUMENTS ARE HANDLED HERE]

**Return Values & Multiple Outputs**
A function task may return a single value or multiple values (via a tuple or list).



* **Single Return:** Maps to a single registered Output Parameter.
* **Iterable Return (Tuple/List):** If the function returns an iterable, Dioptra maps the values to the registered Output Parameters in order (Index 0 to Output 1, Index 1 to Output 2).
* **Partial Mapping:** If fewer output parameters are registered than values returned, Dioptra discards the excess trailing values.

.. _ref-plugin-artifact-tasks:

Plugin Artifact Tasks
---------------------

Artifact tasks handle the serialization and deserialization of complex objects.

Code Syntax
~~~~~~~~~~~

Artifact tasks must be defined as classes that inherit from the ``ArtifactTaskInterface``.

**Parent Class Definition**

    .. autoclass:: dioptra.sdk.api.artifact.ArtifactTaskInterface
        :members:

**Example Implementation**
    
.. admonition:: Artifact Handler Class Definition Example 
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



Registration Interfaces
-----------------------

Plugins can be registered programmatically via the :ref:`guided user interface <how_to_create_a_plugin>`, the Python Client or the REST API.

Using Python Client
~~~~~~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.plugins.PluginFilesSubCollectionClient.create

**Example Payload**

.. code-block:: python

      # Assumes 'client' is authenticated and 'string_param_type_id' is defined
      plugin = client.plugins.create(GROUP_ID, "hello", "This is a Hello World Plugin")
      file = client.plugins.files.create(
          plugin_id=plugin["id"],
          filename="hello.py",
          content=PYTHON_CONTENTS,
          tasks=[{
              "name": "hello_world",
              "inputParams": [
                  {
                      "name": "greeting",
                      "parameterType": string_param_type_id,
                      "required": True
                  },
                  {
                      "name": "name",
                      "parameterType": string_param_type_id,
                      "required": True
                  }
              ],
              "outputParams": [
                  {
                      "name": "message",
                      "parameterType": string_param_type_id,
                  }
              ]
          }]
      )

Using REST API
~~~~~~~~~~~~~~

Plugins can be created and registered directly via the HTTP API.

See the :http:post:`POST /api/v1/plugins </api/v1/plugins/>` endpoint documentation for payload requirements.

.. seealso::
   
   * :ref:`What are Plugins? <plugins-explanation>` 
   * :ref:`How to create a plugin <how_to_create_a_plugin>`