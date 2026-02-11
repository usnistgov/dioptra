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

.. _reference-artifacts-client-methods:

Artifacts Client Methods
========================

This page lists all relevant methods for Dioptra :ref:`Artifacts <explanation-artifacts>` that are available via the Python Client.

.. contents:: Contents
   :local:
   :depth: 2


Requirements
------------

- :ref:`explanation-install-dioptra` - an installation and deployment of Dioptra must be available
- :ref:`how-to-set-up-the-python-client` - the Python client must be configured and initialized


.. _reference-artifacts-client-methods-crud-methods:

Artifacts - CRUD methods
------------------------

After :ref:`importing and initializing the client <how-to-set-up-the-python-client>`, these methods for creating, reading, updating, and deleting (CRUD) artifacts can be executed via ``client.artifacts.METHOD_NAME()``. 

Create Artifact
~~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.artifacts.ArtifactsCollectionClient.create

Get Artifacts
~~~~~~~~~~~~~

    .. automethod:: dioptra.client.artifacts.ArtifactsCollectionClient.get

Get One Artifact by ID
~~~~~~~~~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.artifacts.ArtifactsCollectionClient.get_by_id

Modify Artifact
~~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.artifacts.ArtifactsCollectionClient.modify_by_id


.. _reference-artifacts-client-methods-other-methods:

Artifacts - Other Methods
-------------------------

Get File Listing
~~~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.artifacts.ArtifactsCollectionClient.get_files

Download Artifact Contents
~~~~~~~~~~~~~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.artifacts.ArtifactsCollectionClient.get_contents


.. _reference-artifacts-client-methods-snapshots:


Snapshots of Artifacts - Methods
--------------------------------

Methods belonging to the ``ArtifactsSnapshotCollectionClient`` are accessed via the ``snapshots`` property of the Artifacts Client (which points to ``ArtifactsSnapshotCollectionClient``).

**Example - Get Snapshots for an Artifact**

.. admonition:: Get Snapshots for an Artifact
   :class: code-panel python

   .. code-block:: python
            
        client.artifacts.snapshots.get(artifact_id=1)


See **available methods** for the ``SnapshotsSubCollectionClient``:

* :ref:`reference-snapshots-client-methods`


In addition to the standard snapshot methods, the Artifacts client includes specific methods for downloading snapshot content:

Download Snapshot Contents
^^^^^^^^^^^^^^^^^^^^^^^^^^

    .. automethod:: dioptra.client.artifacts.ArtifactsSnapshotCollectionClient.get_contents


.. rst-class:: fancy-header header-seealso

See Also
---------

* :ref:`Artifacts reference <reference-artifacts>`
* :ref:`Artifacts explanation <explanation-artifacts>`