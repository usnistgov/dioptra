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

.. _reference-plugins:

Plugins
=================


.. contents:: Table of Contents
   :local:
   :depth: 2

.. _reference-plugins-plugin-definition:

Plugin Definition
-----------------

A **Plugin** in Dioptra acts as a logical container for code, functionally similar to a standard Python package.



**Requirements**

* **Naming:** Must be a valid Python module name (alphanumeric, underscores only). Must be unique within the Dioptra deployment.
* **Structure:** A flat directory containing ``.py`` files. 
* **Init File:** Unlike standard Python packages, an ``__init__.py`` file is **not** required.
* **Content:** Files may contain **Function Task** definitions or **Artifact Task** definitions.

.. _reference-plugins-plugin-function-tasks:

Plugin Function Tasks
---------------------

Function tasks are the primary computational units of an experiment.

Code Syntax
~~~~~~~~~~~

To define a function task, you must write a standard Python function and decorate it with ``@pyplugs.register``.

**Example Implementation**

.. admonition:: Function Task Example
   :class: code-panel python

    .. literalinclude:: ../../../../extra/plugins/hello_world/tasks.py
       :language: python
       :start-after: # [reference-task]
       :end-before: # [end-reference-task]


**Type Hints**
Type hints are strongly recommended. Dioptra uses them to automatically populate parameter types during registration imports.

Registration Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~

When registering a function task (via API or GUI), the configuration must match the code logic.

.. _reference-plugins-parameter-mapping:

Parameter Mapping
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* **Input Names:** The registered input parameter names must match the Python function argument names exactly.
* **Order:** [INSERT EXPLANATION ABOUT POSITIONAL VS KEYWORD ARGUMENTS HERE]
* **\*Args / \*\*Kwargs:** [INSERT EXPLANATION ABOUT HOW VARIABLE ARGUMENTS ARE HANDLED HERE]

.. _plugins-reference-return-values:

Return Values & Multiple Outputs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A function task may return a single value or multiple values (via a tuple or list).

* **Single Return:** Maps to a single registered Output Parameter.
* **Iterable Return (Tuple/List):** If the function returns an iterable, Dioptra maps the values to the registered Output Parameters in order (Index 0 to Output 1, Index 1 to Output 2).
* **Partial Mapping:** If fewer output parameters are registered than values returned, Dioptra discards the excess trailing values.

.. _reference-plugins-plugin-artifact-tasks:

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
    
.. admonition:: Artifact Handler Example 
   :class: code-panel python

    **Import Parent Class**

    .. literalinclude:: ../../../../extra/plugins/artifacts/tasks.py
       :language: python
       :start-after: # [artifact-task-imports]
       :end-before: # [end-artifact-task-imports]

    **Child Class Definition**

    .. literalinclude:: ../../../../extra/plugins/artifacts/tasks.py
       :language: python
       :start-after: # [example-artifact-task]
       :end-before: # [end-example-artifact-task]


.. _reference-plugins-registration-interfaces:

Registration Interfaces
-----------------------

Plugins can be created and tasks can be registered programmatically via the Python Client or the REST API.
They can also be registered manually through the :ref:`guided user interface <how-to-create-plugins-plugin-creation-workflow>`.

.. _plugin-reference-python-client-registration:

Using Python Client
~~~~~~~~~~~~~~~~~~~

**Create a Plugin Container**

    .. automethod:: dioptra.client.plugins.PluginsCollectionClient.create

**Add a Python file and register function tasks / artifact tasks**

    .. automethod:: dioptra.client.plugins.PluginFilesSubCollectionClient.create


Using REST API
~~~~~~~~~~~~~~

Plugins can be created and and tasks can be registered directly via the HTTP API.

**Create Plugins**

See the :http:post:`POST /api/v1/plugins </api/v1/plugins/>` endpoint documentation for payload requirements.

**Add Files**

See the :http:post:`/api/v1/plugins/{int:id}/files/` endpoint documentation for payload requirements.

.. rst-class:: fancy-header header-seealso

See Also 
---------
   
* :ref:`What are Plugins? <explanation-plugins>` 
* :ref:`How to create a plugin <how-to-create-plugins>`