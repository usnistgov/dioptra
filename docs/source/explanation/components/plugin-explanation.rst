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

.. _explanation-plugins:

Plugins
================

Summary: What is a Plugin?
--------------------------

A **Plugin** is a logical container used to organize Python code within Dioptra.


Plugins hold the Python files that define the experiment logic. These files define **Tasks**—the individual units of work that the Dioptra engine executes. There are two distinct types of tasks within a plugin:

1. **Plugin Function Tasks:** These act as the computational steps in a workflow.

   * *Example:* A task that accepts a training dataset and returns a trained ML model.

2. **Plugin Artifact Tasks:** These handle the interface between memory and disk storage (I/O).

   * *Example:* A task that serializes a trained model object to a .pt (PyTorch) file and handles the subsequent deserialization back into memory for potential downstream tasks.

Plugin Function Tasks
---------------------

Plugin Function Tasks are Python functions that have been registered with Dioptra. They serve as the fundamental "verbs" or actions in entrypoint workflow graphs.

These tasks perform specific units of work, such as training a model, calculating a metric, or transforming data. Like standard Python functions, they accept inputs (arguments) and produce return values.


**Data Flow and Chaining**

When chained together in an entrypoint, the output of one function task can flow automatically into the input of other function tasks. These tasks operate primarily on in-memory objects (such as DataFrames, integers, or model objects).

Note that while Function Tasks process data, they generally do not save it to disk. To persist results, the output of a function task must be passed into the artifact task graph to dictate which artifact task will save it to disk.

    See :ref:`Entrypoints Explanation <explanation-entrypoints>` to learn how tasks are chained and how default parameter values are set.

Function Task Registration
-----------------

Writing the Python code is only the first step; function tasks must be **registered** to be visible to the Dioptra engine.

Registration defines:

* **The Function Task Name:** Always equal to the function name in Python - this is the identifier used to reference the task in entrypoint graphs
* **Input/Output Names:** This is how input arguments are set in entrypoints and how output objects are referenced
* **Input/Output Types:** Defining the plugin parameter types for each input/output allows for entrypoint task graph validity

When creating Python plugins, users manually register each function task. This can be done in the user interface or through the REST API. See detailed steps in :ref:`How To Create Plugins <how-to-create-plugins>`


.. note::

   In order for a Python function to be registrable, it must use the ``@pyplugs.register`` decorator.
   View :ref:`Plugins Reference <reference-plugins>`  to learn about the ``@pyplugs.register`` syntax for function plugin tasks.


Plugin Artifact Tasks
---------------------

Plugin Artifact Tasks manage data persistence. Because complex Python objects (like machine learning models or large arrays) cannot be plainly written to a text file, they require specific serialization logic.

By isolating I/O logic in Artifact Tasks, the main computational workflow (Function Tasks) remains decoupled from file system operations, making code cleaner and more portable.


Artifact Handlers are Python classes that define certain methods for I/O logic.


.. note::

    Artifact Handler classes must inherit from the parent class ``ArtifactTaskInterface``. See :ref:`Plugins Reference <reference-plugins>` to learn about the syntax for creating artifact tasks.


Artifact Task Registration
-----------------

Artifact tasks are registered similarly to function tasks.

When an artifact task is registered, the user defines:

* **The Artifact Task Name:** Always equal to the name of the Python class that defines the artifact handling logic
* **Output Parameters:** The name and the type of the return object from the **deserialize** method


Using Function Tasks and Artifact Tasks
----------------------------

Plugins create the "vocabulary" of tasks available to an experiment. To utilize these tasks, a relevant plugin must be attached to an **Entrypoint**.

Function tasks are used in the entrypoint task graph. Artifact tasks are used in the artifact output graph to save artifacts, and in the artifact input parameters to make saved artifacts available to an entrypoint task graph.

Entrypoints utilize the types that are declared in function tasks inputs / outputs to ensure the workflow is valid.

    See :ref:`Entrypoints Explanation <explanation-entrypoints>` to learn how plugins are used in entrypoints


.. rst-class:: fancy-header header-seealso

See Also
---------

* :ref:`Workflow Architecture Explanation <explanation-workflow-architecture>` - How plugins fit into Dioptra's workflow architecture
* :ref:`how-to-create-plugins` - Step-by-step guide on building plugins
* :ref:`Plugins Reference <reference-plugins>` - Detailed syntax for decorators and type annotations
