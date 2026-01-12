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

An Entrypoint is the declarative workflow. It specifies which tasks to run, how data flows between them, and what inputs are required to start the process.

Whether interacting with Dioptra via the Graphical User Interface (GUI) or programmatically via the API, the Entrypoint serves as the template. It allows you to run the same logic repeatedly with different settings.

An Entrypoint is comprised of six distinct components:

1. **Parameters**: The variable inputs set at execution time.

2. **Artifact Parameters**: Inputs that accept files from previous jobs.

3. **Attached Plugins**: The definition of which function and artifact tasks are available to this entrypoint.

4. **The Task Graph**: The logic defining the main computational workflow.

5. **The Artifact Task Graph**: The logic defining how data is persisted to storage.

6. **The Attached Queue**: The associated queue / worker that executes job runs of the entrypoint.

Parameters (Job Inputs)
------------------------

Parameters defines the "knobs" that a user can turn when executing an entrypoint. These are global variables that can be passed into any task within the task graph or artifact task graph. 
They are determined when an entrypoint is executed as a job. 

**Standard Parameters**: These are either basic built-in data types (strings, integers, booleans, etc.) or custom types (dictionaries, nested objects, etc.) used to configure the entrypoint (e.g., setting a learning_rate or a dataset_name). They are 
set by the user during job execution. Standard parameters can also have default values. 

**Artifact Parameters**: These allow an entrypoint to accept complex objects or files resulting from previous Dioptra jobs. This is how you chain entrypoints together (e.g., passing a "trained model" artifact from a Training Job into a Testing Job).

Attached Plugins
-----------------
An entrypoint must declare attached Plugins before it can use their associated Tasks.

**Function Plugins**: Provide the computational tasks (the "verbs" of your workflow) used in the main Task Graph.

**Artifact Plugins**: Provide the serialization logic (the "savers" and "loaders") used to handle loading Artifact Parameters at the beggining of jobs and saving Artifacts at the end of the job (defined in the Artifact Task Graph)

By attaching plugins, the Entrypoint imports the input/output signatures of those tasks. This allows Dioptra to perform validation, ensuring that the tasks are compatible with one another.

The Task Graph
-----------------

The Task Graph is the core of the entrypoint. It defines the execution order and parameterization of the Function Tasks.

In Dioptra, the Task Graph is defined in YAML. Dioptra uses a Directed Acyclic Graph (DAG) structure to manage these dependencies. If Task B requires the output of Task A, the engine automatically ensures Task A completes successfully before Task B begins.

.. admonition:: Learn more

    For a deep dive on graph syntax, dependency management, and invocation styles, see :ref:`Task Graphs explanation <explanation-task-graph>` and :ref:`Entrypoints Reference <reference-entrypoints>`.

The Artifact Task Graph
------------------------

While the main Task Graph handles in-memory computation, the Artifact Task Graph handles storage (I/O).

This graph defines which in-memory objects from the main workflow should be saved to disk and which Artifact Plugin should be used to save them. This separation ensures that your computational logic remains clean and decoupled from storage details.

Type Validation
~~~~~~~~~~~~~~~~

Dioptra performs static type validation on your entrypoint. Because every Parameter and Plugin Task has a defined type (e.g., Pandas DataFrame, Integer, PyTorch Model), the engine can verify that your graph is valid before running it.

For example, if you attempt to pipe a String parameter into a task expecting a DataFrame, Dioptra will flag the mismatch.

The Attached Queue(s)
------------------------

Executing an entrypoint as a job requires a worker. 
By linking queues to entrypoints, you can choose which worker handles the job at runtime to process the associated task graph logic.


.. rst-class:: fancy-header header-seealso

See Also 
----------

* :ref:`Entrypoints: reference <reference-entrypoints>` - Complete YAML syntax guide for entrypoint files and task graphs.
* :ref:`Task Graphs: explanation <explanation-task-graph>` - Detailed explanation of workflow logic.
* :ref:`Plugins: explanation <explanation-plugins>` - Explanation of Plugins, Function Tasks and Artifact Tasks

