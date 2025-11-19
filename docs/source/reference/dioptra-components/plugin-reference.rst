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

.. seealso::
   
   * :ref:`What are Plugins? <plugins-explanation>` 
   * :ref:`How to create a plugin <how_to_create_a_plugin>`

.. contents:: Table of Contents
   :local:
   :depth: 2

Module Requirements
-------------------

**Plugin Package**

* **Naming:** Valid Python module name (alphanumeric, underscores). Unique.
* **Structure:** Directory containing ``.py`` files. ``__init__.py`` not required.

**Plugin Files**

* **Extension:** ``.py``
* **Naming:** Valid Python module name.
* **Content:** Function Task definitions OR Artifact Task definitions.

.. _ref-plugin-function-tasks:

Plugin Function Tasks
---------------------

**Syntax**

.. code-block:: python

    from dioptra import pyplugs

    @pyplugs.register
    def task_name(param_1: type, param_2: type) -> return_type:
        ...

**Requirements**

* **Decorator:** ``@pyplugs.register`` required.
* **Type Hints:** Recommended for auto-detection of parameters.

**Registration Schema**

* **Task Name:** String. Must match Python function name.
* **Input Parameters:**
    * **Name:** String. Matches argument name.
    * **Type:** Plugin Parameter Type (e.g., ``float``).

* **Output Parameters:**
    * **Name:** String.
    * **Type:** Dioptra Type.

.. _ref-plugin-artifact-tasks:

Plugin Artifact Tasks
---------------------

**Syntax**

.. code-block:: python

    from typing import Any
    from pathlib import Path
    from dioptra.sdk.api.artifact import ArtifactTaskInterface

    class MyArtifactTask(ArtifactTaskInterface):
        @staticmethod
        def serialize(working_dir: Path, name: str, contents: Any, **kwargs) -> Path:
            ...
        
        @staticmethod
        def deserialize(working_dir: Path, path: str, **kwargs) -> Any:
            ...

**Requirements**

* **Inheritance:** Must inherit from ``dioptra.sdk.api.artifact.ArtifactTaskInterface``.
* **Methods:** ``serialize`` and ``deserialize`` are required static methods.

**Method Signatures**

* **serialize**
    
    .. code-block:: python

       (working_dir: Path, name: str, contents: Any, **kwargs) -> Path

* **deserialize**
    
    .. code-block:: python

       (working_dir: Path, path: str, **kwargs) -> Any

* **validation** (Optional)
    
    .. code-block:: python

       () -> dict[str, Any] | None

**Registration Schema**

* **Task Name:** String. Must match Python Class name.
* **Output Parameters:**
    * **Name:** String.
    * **Type:** Dioptra Type (Matches ``deserialize`` return type).