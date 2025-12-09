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

.. _reference-dioptra-components-glossary:

Dioptra Components Glossary
=================
An enumeration of Dioptra components and their definitions. 


Plugins
~~~~~~~~

- ``Plugin``: A collection of Python files which contain ``Plugin Tasks`` and/or ``Artifact Plugin Tasks`` 
- ``Plugin Task``: A single Python function within a ``Plugin`` file, used in ``Entrypoints``
- ``Plugin Task Input``: An input into a ``Plugin Task`` (i.e. a Python argument)
- ``Plugin Task Output``: The output of a ``Plugin Task``. A ``Plugin Task Output`` can be fed in as a ``Plugin Task Input`` via the ``Entrypoint Task Graph``, or saved as an ``Artifact`` via the ``Artifact Output Graph``
- ``Plugin Parameter Type``: Either a built-in or user-defined type, used for Entrypoint type validation 


Artifacts
~~~~~~~~~~~~

- ``Artifact Plugin``: A type of ``Plugin`` container that specifically contains Artifact Plugin Tasks. 
- ``Artifact``: The output of a Plugin Task that has been saved to disk 
- ``Artifact Handler``: A subclass of ArtifactTaskInterface, defining serialization / deserialization / validation logic for artifacts
- ``Artifact Task``: The serialize method for an ``Artifact Handler``, used in the ``Artifact Output Graph`` to save ``Plugin Task Outputs`` to ``Artifacts`` 
- ``Artifact Task Output Parameter``: This is the ``Parameter Type`` for the object that is returned by ``Artifact Task``

Entrypoints
~~~~~~~~~~~~~~~~~~~

- ``Entrypoint``: Define parameterizable workflows to be reused across multiple ``Experiments``
- ``Entrypoint Parameter``: An input used for the ``Entrypoint Task Graph`` and the ``Artifact Output Graph`` that can be customized during a ``Job`` run 
- ``Entrypoint Artifact Parameter``: A kind of ``Entrypoint Parameter`` that is read in from a ``Snapshot`` of an ``Artifact``
- ``Entrypoint Task Graph``: The sequence of ``Plugin Tasks`` that an ``Entrypoint`` executes, written in YAML. A directed, acyclic graph (DAG)
- ``Entrypoint Task Graph Step``: A single step in the ``Entrypoint Task Graph``, which must have a name
- ``Entrypoint Artifact Output Graph``: The logic dictating which ``Plugin Task Outputs`` are saved to ``Artifacts`` and how (i.e. which ``Artifact Tasks`` are invoked and how)

Experiments/Jobs
~~~~~~~~~~~~~~~~~~~

- ``Experiment``: A container that holds ``Entrypoints`` and ``Job`` runs 
- ``Job``: A parameterized run of an ``Entrypoint`` 

Other
~~~~~~~~~~~~~~~~~~~

- ``Metric``: *TBD*
- ``Snapshot`` (Artifact, Plugin, Entrypoint?): A specific version of an item in time 
- ``Queue``: *TBD* 
- ``Worker``: *TBD* 
- ``User``: *TBD* 
- ``Groups``: *TBD* 
- ``Models``: *TBD* 
- ``Tags``: *TBD* 
