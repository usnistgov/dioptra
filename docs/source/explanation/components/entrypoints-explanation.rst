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

.. _explanation-entrypoints:

Entrypoints
================


Summary: What is an Entrypoint?
---------------------------------

An **entrypoint** is the declarative workflow. It specifies which tasks to run, how data flows between them, and what inputs are required to start the process.

Whether interacting with Dioptra via the Graphical User Interface (GUI) or programmatically via the API, the entrypoint serves as the template. It allows the same logic to run repeatedly with different settings.

An entrypoint is comprised of six distinct components:

1. **Parameters**: The variable inputs set at execution time.

2. **Artifact Parameters**: Inputs that accept files from previous jobs.

3. **Attached Plugins**: The definition of which function and artifact tasks are available to this entrypoint.

4. **The Task Graph**: The logic defining the main computational workflow.

5. **The Artifact Task Graph**: The logic defining how data is persisted in storage.

6. **The Attached Queue**: The associated queue / worker that executes job runs of the entrypoint.

Parameters (Job Inputs)
------------------------

Parameters define the "knobs" that a user can turn when executing an entrypoint. These are global variables that can be passed into any task within the task graph or artifact task graph. 
They are determined when an entrypoint is executed as a job. 

**Standard Parameters**: These are either basic built-in data types (strings, integers, booleans, etc.) or custom types (dictionaries, nested objects, etc.) used to configure the entrypoint (e.g., setting a learning_rate or a dataset_name). They are set by the user during job execution. Standard parameters can also have default values. 

**Artifact Parameters**: These allow an entrypoint to accept complex objects or files produced by previous Dioptra jobs. This is how entrypoints can be chained together (e.g., passing a "trained model" artifact from a training job into a testing job).

Attached Plugins
-----------------
An entrypoint must declare attached plugins before it can use their associated tasks.

**Function Plugins**: Provide the computational tasks (the "verbs" of a workflow) used in the main task graph.

**Artifact Plugins**: Provide the serialization logic (the "savers" and "loaders") used to handle loading artifact parameters at the beginning of jobs and saving artifacts at the end of the jobs (defined in the artifact task graph)

By attaching plugins, the entrypoint imports the input/output signatures of those tasks. This allows Dioptra to validate that the tasks are compatible with one another.

The Task Graph
-----------------

The task graph is the core of the entrypoint. It defines the execution order and parameterization of the function tasks.

In Dioptra, a task graph is defined in YAML. Dioptra uses a Directed Acyclic Graph (DAG) structure to manage these dependencies. If Task B requires the output of Task A, the engine automatically ensures Task A completes successfully before Task B begins.

.. admonition:: Learn more

    For a deep dive on graph syntax, dependency management, and invocation styles, see :ref:`Task Graphs explanation <explanation-task-graph>` and :ref:`Entrypoints reference <reference-entrypoints>`.

The Artifact Task Graph
------------------------

While the main task graph handles in-memory computation, the artifact task graph handles storage (I/O).

This graph defines which in-memory objects from the main workflow should be saved to disk and which artifact plugin should be used to save them. This separation ensures that computational logic remains clean and decoupled from storage details.

Type Validation
~~~~~~~~~~~~~~~~

Dioptra performs static type validation on entrypoints. Because every parameter and plugin task has a defined type (e.g., Pandas DataFrame, integer, PyTorch model), the engine can verify that a graph is valid before running it.

For example, if a string parameter is provided to a task expecting a DataFrame, Dioptra will flag the mismatch.

The Attached Queue(s)
------------------------

Executing an entrypoint as a job requires a worker. 
By linking queues to entrypoints, workers can be assigned jobs to process the associated task graph logic.


.. rst-class:: fancy-header header-seealso

See Also 
----------

* :ref:`Entrypoints: reference <reference-entrypoints>` - Complete YAML syntax guide for entrypoint files and task graphs
* :ref:`Task Graphs: explanation <explanation-task-graph>` - Detailed explanation of workflow logic
* :ref:`Plugins: explanation <explanation-plugins>` - Explanation of Plugins, Function Tasks and Artifact Tasks

