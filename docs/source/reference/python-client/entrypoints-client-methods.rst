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

.. _reference-entrypoint-client-methods:

Entrypoint Client Methods
=========================


This page lists all relevant methods for Dioptra :ref:`Entrypoints <explanation-entrypoints>` that are available via the Python Client.

.. contents:: Contents
    :local:
    :depth: 2

Requirements
------------

* :ref:`explanation-install-dioptra` - an installation and deployment of Dioptra must be available
* :ref:`how-to-set-up-the-python-client` - the Python client must be configured and initialized

.. _reference-entrypoints-client-methods-crud-methods:

Entrypoints - CRUD methods
--------------------------

After :ref:`importing and initializing the client <how-to-set-up-the-python-client>`, these methods for creating, reading, updating, and deleting (CRUD) entrypoints can be executed via ``client.entrypoints.METHOD_NAME()``. 
Create Entrypoint
~~~~~~~~~~~~~~~~~
      
    .. automethod:: dioptra.client.entrypoints.EntrypointsCollectionClient.create

Get Entrypoints
~~~~~~~~~~~~~~~
      
    .. automethod:: dioptra.client.entrypoints.EntrypointsCollectionClient.get

Get One Entrypoint
~~~~~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.entrypoints.EntrypointsCollectionClient.get_by_id



Modify Entrypoint
~~~~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.entrypoints.EntrypointsCollectionClient.modify_by_id

Delete Entrypoint
~~~~~~~~~~~~~~~~~


    .. automethod:: dioptra.client.entrypoints.EntrypointsCollectionClient.delete_by_id



.. _reference-entrypoints-client-methods-plugins-methods:

Entrypoint Plugins - Methods
----------------------------

These methods exist within the class ``EntrypointPluginsSubCollectionClient``, and are accessed via the ``plugins`` property of the Entrypoint Client (which points to ``EntrypointPluginsSubCollectionClient``).

**Example - Attach Plugins to Entrypoint**

.. admonition:: Attach Plugins to an Entrypoint
   :class: code-panel python

   .. code-block:: python

        client.entrypoints.plugins.create(entrypoint_id=1, plugin_ids=[2,3])

Add Plugin to Entrypoint
~~~~~~~~~~~~~~~~~~~~~~~~
      
    .. automethod:: dioptra.client.entrypoints.EntrypointPluginsSubCollectionClient.create

Get Plugins for Entrypoint
~~~~~~~~~~~~~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.entrypoints.EntrypointPluginsSubCollectionClient.get



Get One Plugin by ID
~~~~~~~~~~~~~~~~~~~~
      
    .. automethod:: dioptra.client.entrypoints.EntrypointPluginsSubCollectionClient.get_by_id

Delete One Plugin by ID
~~~~~~~~~~~~~~~~~~~~~~~


    .. automethod:: dioptra.client.entrypoints.EntrypointPluginsSubCollectionClient.delete_by_id



.. _reference-entrypoints-client-methods-artifact-plugins-methods:

Entrypoint Artifact Plugins - Methods
-------------------------------------

These methods exist within the class ``EntrypointArtifactPluginsSubCollectionClient``, and are accessed via the ``artifact_plugins`` property of the Entrypoint Client.

**Example - Attach Artifact Plugins to Entrypoint**

``client.entrypoints.artifact_plugins.create(entrypoint_id=1, artifact_plugin_ids=[5])``

Add Artifact Plugin to Entrypoint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
      
    .. automethod:: dioptra.client.entrypoints.EntrypointArtifactPluginsSubCollectionClient.create

Get Artifact Plugins for Entrypoint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


    .. automethod:: dioptra.client.entrypoints.EntrypointArtifactPluginsSubCollectionClient.get


Get One Artifact Plugin by ID
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
      
    .. automethod:: dioptra.client.entrypoints.EntrypointArtifactPluginsSubCollectionClient.get_by_id

Delete One Artifact Plugin by ID
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


    .. automethod:: dioptra.client.entrypoints.EntrypointArtifactPluginsSubCollectionClient.delete_by_id


.. _reference-entrypoints-client-methods-queues-methods:

Entrypoint Queues - Methods
---------------------------

These methods exist within the class ``EntrypointQueuesSubCollectionClient``, and are accessed via the ``queues`` property of the Entrypoint Client.

**Example - Attach Queues to Entrypoint**

``client.entrypoints.queues.create(entrypoint_id=1, queue_ids=[10])``

Add Queue to Entrypoint
~~~~~~~~~~~~~~~~~~~~~~~
      
    .. automethod:: dioptra.client.entrypoints.EntrypointQueuesSubCollectionClient.create

Get Queues for Entrypoint
~~~~~~~~~~~~~~~~~~~~~~~~~


    .. automethod:: dioptra.client.entrypoints.EntrypointQueuesSubCollectionClient.get


Replace Attached Queues
~~~~~~~~~~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.entrypoints.EntrypointQueuesSubCollectionClient.modify_by_id

Delete All Attached Queues
~~~~~~~~~~~~~~~~~~~~~~~~~~


    .. automethod:: dioptra.client.entrypoints.EntrypointQueuesSubCollectionClient.delete
        

Delete One Queue by ID
~~~~~~~~~~~~~~~~~~~~~~
      
    .. automethod:: dioptra.client.entrypoints.EntrypointQueuesSubCollectionClient.delete_by_id


Tags Attached to Entrypoint - Methods
-------------------------------------

Methods belonging to the ``TagsSubCollectionClient`` are accessed via the ``tags`` property of the Entrypoint Client (which points to ``TagsSubCollectionClient``).

**Example - Get tags for an Entrypoint**

``client.entrypoints.tags.get(1)``

See **available methods** for the ``TagsSubCollectionClient``: 

* :ref:`reference-tags-client-methods`


Snapshots of Entrypoint - Methods
---------------------------------

Methods belonging to the `EntrypointsSnapshotCollectionClient` are accessed via the `snapshots` property of the Entrypoint Client.

**Example - Get snapshots for an Entrypoint**

.. admonition:: Get snapshots for an Entrypoint
   :class: code-panel python

   .. code-block:: python

        client.entrypoints.snapshots.get(1)

See **available methods** for the ``SnapshotsSubCollectionClient``:

* :ref:`reference-snapshots-client-methods`


.. rst-class:: fancy-header header-seealso

See Also
--------

* :ref:`Entrypoints reference <reference-entrypoints>`
* :ref:`Entrypoints explanation <explanation-entrypoints>`
* :ref:`How to create Entrypoints <how-to-create-entrypoints>`

