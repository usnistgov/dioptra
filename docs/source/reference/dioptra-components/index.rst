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
==================

Reference material for the various components and resources that comprise experiment workflows in Dioptra.

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

Quick Definitions
-----------------

Plugins
~~~~~~~

- ``Plugin``: A collection of Python files which contain registered ``Function Tasks`` and/or ``Artifact Tasks``.
- ``Plugin Parameter Type``: Either a built-in or user-defined type, used for type validation. ``Function Task Inputs``, ``Function Task Outputs``, ``Artifact Task Outputs``, ``Entrypoint Parameters`` and the outputs from ``Entrypoint Artifact Parameters`` all have associated ``Plugin Parameter Types``.

Plugin Function Tasks 
~~~~~~~~~~~~~~~~

- ``Function Task``: A registered Python function within a ``Plugin`` file that defines some computational task, used in the ``Task Graph`` in ``Entrypoints``.
- ``Function Task Input``: An input into a ``Function Task`` registered as part of the task definition.  Has an associated ``Plugin Parameter Type`` for type validation.
- ``Function Task Output``: The output of a ``Function Task`` registered as part of the task definition.  Has an associated ``Plugin Parameter Type`` for type validation. A ``Function Task Output`` can be fed in as a ``Function Task Input`` via the ``Task Graph``, or saved as an ``Artifact`` via the ``Artifact Output Graph``.

Plugin Artifact Tasks and Artifacts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ``Artifact``: The output of a ``Function Task`` that has been saved to disk via the serialize method of an ``Artifact Task``.
- ``Artifact Task``: A registered subclass of *ArtifactTaskInterface* that defines serialization, deserialization, and validation logic for an ``Artifact`` type. Used to save ``Artifacts`` in the ``Artifact Output Graph`` in ``Entrypoints``, and also to load saved ``Artifacts`` as ``Entrypoint Artifact Parameters`` at ``Job`` runtime.
- ``Artifact Task Output``: An object that is returned by the deserialize method of an ``Artifact Task``.  Has an associated ``Plugin Parameter Type`` for type validation.

Entrypoints
~~~~~~~~~~~

- ``Entrypoint``: Define parameterizable workflows, which can be reused across multiple ``Experiments``.
- ``Entrypoint Parameter``: An input used for the ``Task Graph`` and the ``Artifact Output Graph``. Can be customized during a ``Job`` run and have an optional default value. Has an associated ``Plugin Parameter Type`` for type validation.
- ``Entrypoint Artifact Parameter``: A kind of ``Entrypoint Parameter``, where the value is read in from a ``Snapshot`` of an ``Artifact`` during ``Job`` execution. Can contain multiple objects, each of which has an associated ``Plugin Parameter Type`` for type validation.
- ``Task Graph``: The sequence of ``Function Tasks`` that an ``Entrypoint`` executes, written in YAML. A directed, acyclic graph (DAG).
- ``Task Graph Step``: A single step in the ``Task Graph``, which must have a name. Can have positional and keyword arguments as well.
- ``Artifact Output Graph``: The logic dictating which ``Function Task Outputs`` are saved to ``Artifacts`` and how (i.e. which ``Artifact Tasks`` are invoked and their inputs). Written in YAML.

Experiments/Jobs
~~~~~~~~~~~~~~~~

- ``Experiment``: A logical container that holds ``Entrypoints`` and ``Job`` runs.
- ``Job``: A parameterized run of an ``Entrypoint``.
- ``Queue``: A queue manager for ``Jobs``. Manages ``Job`` execution for a specific ``worker`` environment.
- ``Worker``: Contains the resources for executing a ``Job``. Default worker containers are available for GPU and CPU hardware. Custom workers can be developed.
- ``Metric``: A numeric value that is associated with a specific step of a ``Job`` (i.e. training accuracy at a given epoch for the "train" ``Function Task``).

Other
~~~~~

- ``User``: A user profile with login credentials and permissions. Belongs to one or more ``Groups``.
- ``Group``: A set of ``Users`` and permission rules for resource access. Currently, there is only a single "public" ``Group``.
- ``Snapshot``: A specific version of a Resource (e.g. Experiment, Plugin, Entrypoint, Artifact) in time.
- ``Tag``: String values that are associated in many to many relationships with various Dioptra resources. Used for filtering tables, etc.

.. rst-class:: fancy-header header-seealso

See Also
--------

* :ref:`how-to-running-experiments` - How to guides for creating resources with the Dioptra GUI / Python Client
* :ref:`Dioptra components explainers <explanation-dioptra-components>` - Explanation on Dioptra components
