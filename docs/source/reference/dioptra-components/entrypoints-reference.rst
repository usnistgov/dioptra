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

.. _reference-entrypoints:

Entrypoints
=================


.. contents:: Contents
   :local:
   :depth: 2

.. _reference-entrypoints-definition:

Entrypoint Definition
---------------------

An **Entrypoint** in Dioptra is a repeatable workflow that can be executed as a Job. Entrypoints execute the function tasks defined in the task graph upon job submission. 
Entrypoint parameters and Artifact Input Parameters can optionally be attached to entrypoints and then used in the Task Graph. The outputs from Function Tasks 
can be saved as Artifacts, and the logic for this is defined in the Artifact Task Graph. 

.. _reference-experiments-attributes:


Entrypoint Attributes
---------------------

This section describes the attributes that define an Entrypoint.

.. _reference-entrypoints-required-attributes:

Required Attributes
~~~~~~~~~~~~~~~~~~~

.. _reference-entrypoints-optional-attributes:

- **Name**: (string) The display name for the Entrypoint. 
- **Group**: (integer ID) The Group that owns this Experiment and controls access permissions.
- **Task Graph**: (YAML string) The task graph for entrypoint, which as a YAML-formatted string that defines the core workflow (technically, a Directed Acyclical Graph). Composed of function task invocations and their input arguments. 


Optional Attributes
~~~~~~~~~~~~~~~~~~~

- **Description**: (string, optional) A text description of the Entrypoint's purpose or scope. Defaults to empty.
- **Plugins**: (list of Plugin IDs, optional) A list of Plugin containers to attach to the entrypoint - the associated Plugin Function Tasks are then made available to the Entrypoint Task Graph. Defaults to empty.
- **Artifact Plugins**:  (list of Plugin IDs, optional) A list of Plugin containers to attach to the entrypoint - the associated Plugin Artifact Tasks are then made available to the Artifact Output Task Graph. Defaults to empty.
- **Parameters**: (list of Dicts, optional) Global parameters that can be used in the Entrypoint Task Graph and Artifact Task Graph. Each Parameter has a type and can optionally have a default value. Parameter values are set at Job runtime. Defaults to empty.
- **Artifact Parameters**: (list of Dicts, optional) Global objects, loaded from disk at Job execution, can be used in the Entrypoint Task Graph and Artifact Task Graph. User selects which specific artifact snapshot to load into the Artifact Parameter at Job Runtime. Defaults to empty.
- **Artifact Task Graph**: (YAML string, optional) The artifact task graph for entrypoint, which as a YAML-formatted string that defines the artifact serialization logic. Artifact Tasks are called once the main Task Graph execution is completed. Defaults to empty.
- **Queues**: (list of integer IDs, optional) A list of the queues that can pick up Job submissions of this entrypoint and carry out their execution. Job will not be runnable without at least one attached Queue. Defaults to empty.

.. _reference-entrypoints-system-generated-attributes:

System-Generated Attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **ID**: Unique identifier assigned upon creation.
- **Created On**: Timestamp indicating when the Entrypoint was created.
- **Last Modified On**: Timestamp indicating when the Entrypoint was last modified.

- Snapshot? 
- Jobs?

.. _reference-entrypoints-task-graph-syntax:

Task Graph Syntax
~~~~~~~~~~~~~~~~~

.. _reference-entrypoints-artifact-output-graph-syntax:

Artifact Output Graph Syntax
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. _reference-entrypoints-registration-interfaces:

Registration Interfaces
-----------------------

.. _reference-entrypoints-python-client:

Using Python Client
~~~~~~~~~~~~~~~~~~~

**Create an Entrypoint**

    .. automethod:: dioptra.client.entrypoints.EntrypointsCollectionClient.create

.. _reference-entrypoints-rest-api:

Using REST API
~~~~~~~~~~~~~~

.. rst-class:: fancy-header header-seealso

See Also
---------
