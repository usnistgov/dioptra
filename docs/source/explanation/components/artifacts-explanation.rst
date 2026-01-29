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

.. _explanation-artifacts:

Artifacts
=========

Summary: What is an artifact?
-----------------------------

An **artifact** refers to the stored outputs of jobs. A job can produce multiple artifacts,
and artifacts produced by a job can be used as inputs to another job. How the artifact is used
is specified in the entrypoint associated with the job, but the artifact itself is provided at
runtime as an input to the job. 

Artifacts are used in entrypoints through ``Artifact Parameters``. When an artifact is designated as 
an input parameter, it can be referenced in the task graph in the exact same way any regular
entrypoint parameter or task output can be. The artifact is loaded into memory at the start of the
job execution and then is available for any tasks that reference it.


Artifact Tasks
--------------

**Artifact tasks** are a type of plugin task which detail the serialization
and deserialization of a given artifact type. When an output of a function task is designated to be 
saved as an artifact, it is passed to its corresponding serialization function within the artifact task.
Similarly, when an artifact is loaded, its deserialization function is used to load it as an object in memory.

Because the serialization input and deserialization output types must be the same, passing artifacts between
entrypoints is effectively transparent to the entrypoint - the entrypoint can handle those artifacts
as if they are an object loaded into memory, and ignore the details of reading/writing, as long as artifact
tasks for that type exist.

Note that when artifacts are created, they are associated with a snapshot of the artifact task that they were 
created with. Since the artifact task contains both serialization and deserialization, the same snapshot is used
for deserialization. 

.. rst-class:: fancy-header header-seealso

See Also
--------

* :ref:`Entrypoints: explanation <explanation-entrypoints>` - Explanation of Entrypoints, including the Artifact Task Graph.
* :ref:`Entrypoints: reference <reference-entrypoints>` - Complete YAML syntax guide for entrypoint files and task graphs.
* :ref:`Task Graphs: explanation <explanation-task-graph>` - Detailed explanation of workflow logic.
* :ref:`Plugins: explanation <explanation-plugins>` - Explanation of Plugins, Function Tasks and Artifact Tasks
