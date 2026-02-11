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

.. _reference-dioptra-components:

Dioptra Components
===================

Reference material for the various components and resources that comprise experiment workflows in Dioptra.

Quick Definitions
-------------------

Plugins
~~~~~~~~

- ``Plugin``: A collection of Python files which contain registered ``Plugin Tasks`` and/or ``Artifact Plugin Tasks`` 
- ``Plugin Task``: A single Python function within a ``Plugin`` file, used in ``Entrypoints``
- ``Plugin Task Input``: An input into a ``Plugin Task`` (i.e. a Python argument)
- ``Plugin Task Output``: The output of a ``Plugin Task``. A ``Plugin Task Output`` can be fed in as a ``Plugin Task Input`` via the ``Entrypoint Task Graph``, or saved as an ``Artifact`` via the ``Artifact Output Graph``
- ``Plugin Parameter Type``: Either a built-in or user-defined type, used for Entrypoint task graph ``type validation`` 


Artifacts
~~~~~~~~~~~~

- ``Artifact Plugin``: A type of ``Plugin`` container that specifically contains Artifact Plugin Tasks. 
- ``Artifact``: The output of a Plugin Task that has been saved to disk via the serialize method of an ``Artifact Task``
- ``Artifact Handler``: A subclass of ArtifactTaskInterface, defining serialization / deserialization / validation logic for artifacts
- ``Artifact Task``: The serialize method for an ``Artifact Handler``, used in the ``Artifact Output Graph`` to save ``Plugin Task Outputs`` to ``Artifacts`` 
- ``Artifact Task Output Parameter``: An object that is returned by the deserialize method of an ``Artifact Handler``
- ``Artifact Task Output Parameter Type``: The ``Parameter Type`` for the object that is returned by an ``Artifact Task``

Entrypoints
~~~~~~~~~~~~~~~~~~~

- ``Entrypoint``: Define parameterizable workflows, which can be reused across multiple ``Experiments``
- ``Entrypoint Parameter``: An input used for the ``Entrypoint Task Graph`` (and the ``Artifact Output Graph``) - can be customized during a ``Job`` run and have an optional default value
- ``Entrypoint Artifact Parameter``: A kind of ``Entrypoint Parameter``, where the value is read in from a ``Snapshot`` of an ``Artifact`` during ``Job`` execution. Can contain multiple objects (object is accessed with the dot notation)
- ``Entrypoint Task Graph``: The sequence of ``Plugin Tasks`` that an ``Entrypoint`` executes, written in YAML. A directed, acyclic graph (DAG)
- ``Entrypoint Task Graph Step``: A single step in the ``Entrypoint Task Graph``, which must have a name. Can have positional and keyword arguments as well.
- ``Entrypoint Artifact Output Graph``: The logic dictating which ``Plugin Task Outputs`` are saved to ``Artifacts`` and how (i.e. which ``Artifact Tasks`` are invoked and their inputs)

Experiments/Jobs
~~~~~~~~~~~~~~~~~~~

- ``Experiment``: A container that holds ``Entrypoints`` and ``Job`` runs 
- ``Job``: A parameterized run of an ``Entrypoint`` 

Other
~~~~~~~~~~~~~~~~~~~

- ``Metric``: A numeric value that is associated with a specific step of a ``job`` (i.e. training accuracy at a given epoch for the "train" ``plugin task``)
- ``Snapshot`` (Artifact, Plugin, Entrypoint): A specific version of a resource in time 
- ``Queue``: A queue manager for ``jobs`` - manages job execution for a specific ``worker`` environment
- ``Worker``: Contains the resources for executing a ``job``. Default worker containers are available for GPU and CPU hardware. Custom workers can be developed.
- ``User``: A user profile with login credentials and permissions. Belongs to one or more ``groups``
- ``Groups``: A set of ``users`` and permission rules for resource access. Currently, each resource can only belong to a single ``group``
- ``Tags``: String values that are associated in many to many relationships with various Dioptra resources. Used for filtering tables, etc.

Detailed Reference Pages
--------------------------------

.. container:: wide-lightly-shaded

   .. toctree::
      :maxdepth: 1
      :caption: Table of Contents

      dioptra-component-glossary
      users-reference
      groups-reference
      queues-reference
      param-types-reference
      plugin-reference
      entrypoints-reference
      experiments-reference
      jobs-reference
      artifacts-reference
      metrics-reference
      workers-reference
      task-graph-reference
      artifact-graph-reference

.. rst-class:: fancy-header header-seealso

See Also 
---------

* :ref:`how-to-running-experiments` - How to guides for creating resources with the Dioptra GUI / Python Client
* :ref:`Dioptra components explainers <explanation-dioptra-components>` - Explanation on Dioptra components
