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

.. _reference-plugin-client-methods:

Plugin Client Methods
=================


This page lists all relevant methods for Dioptra :ref:`Plugins <explanation-plugins>` that are available via the Python Client.

.. contents:: Contents
    :local:
    :depth: 2

Requirements
-----------

* :ref:`explanation-install-dioptra` - an installation and deployment of Dioptra must be available
* :ref:`how-to-set-up-the-python-client` - the Python client must be configured and initialized

.. _reference-plugins-client-methods-crud-methods:

Plugins - CRUD methods
----------------------

After :ref:`importing and initializing the client <how-to-set-up-the-python-client>`, these methods can be executed via ``client.plugins.METHOD_NAME()``.

Create Plugin
~~~~~~~~~~~~~~~~~~~~~~

      
    .. automethod:: dioptra.client.plugins.PluginsCollectionClient.create

Get Plugins
~~~~~~~~~~~
      
    .. automethod:: dioptra.client.plugins.PluginsCollectionClient.get

Get Plugin by ID
~~~~~~~~~~~~~~~~~~~~~~



    .. automethod:: dioptra.client.plugins.PluginsCollectionClient.get_by_id



Modify Plugin
~~~~~~~~~~~~~~~~~~~~~~


    .. automethod:: dioptra.client.plugins.PluginsCollectionClient.modify_by_id

Delete Plugin
~~~~~~~~~~~~~~~~~~~~~~



    .. automethod:: dioptra.client.plugins.PluginsCollectionClient.delete_by_id



.. _reference-plugins-client-methods-files-methods:

Plugin Files - Methods
---------------------------------

These methods exist within the class ``PluginFilesSubCollectionClient``, and are accessed via the ``files`` property of the Plugins Client (which points to ``PluginFilesSubCollectionClient``).

**Example - Create a file within a Plugin**

``client.plugins.files.create(plugin_id=1, filename="script.py", contents="print('hello')")``

Create Plugin File
~~~~~~~~~~~~~~~~~~~~~~

      
    .. automethod:: dioptra.client.plugins.PluginFilesSubCollectionClient.create

Get Files for Plugin
~~~~~~~~~~~~~~~~~~~~~~



    .. automethod:: dioptra.client.plugins.PluginFilesSubCollectionClient.get



Get Plugin File by ID
~~~~~~~~~~~~~~~~~~~~~~

      
    .. automethod:: dioptra.client.plugins.PluginFilesSubCollectionClient.get_by_id

Modify Plugin File
~~~~~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.plugins.PluginFilesSubCollectionClient.modify_by_id

Delete Plugin File
~~~~~~~~~~~~~~~~~~
      
    .. automethod:: dioptra.client.plugins.PluginFilesSubCollectionClient.delete_by_id

Delete All Files in Plugin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~



    .. automethod:: dioptra.client.plugins.PluginFilesSubCollectionClient.delete_all



Tags Attached to Plugin
---------------------------------

Methods belonging to the ``TagsSubCollectionClient`` are accessed via the ``tags`` property of the Plugins Client (which points to ``TagsSubCollectionClient``).

**Example - Get tags for a Plugin**

``client.plugins.tags.get(1)``

Methods - Tags
~~~~~~~~~~~~~~~~~~~~~~


See **available methods for the TagsSubCollectionClient**: :ref:`reference-tags-client-methods`


Snapshots of Plugin
-------------------

Methods belonging to the ``PluginsSnapshotCollectionClient`` are accessed via the ``snapshots`` property of the Plugins Client (which points to ``PluginsSnapshotCollectionClient``).

**Example - Get snapshots for a Plugin**

``client.plugins.snapshots.get(1)``

Methods - Snapshots
~~~~~~~~~~~~~~~~~~~~~~


See **available methods for the SnapshotsSubCollectionClient**: :ref:`reference-snapshots-client-methods`

Methods - Plugin Specific Snapshots
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


The following methods are specific to Plugin snapshots and are not available on other resources.

Download Files Bundle
~~~~~~~~~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.plugins.PluginsSnapshotCollectionClient.get_files_bundle


.. rst-class:: fancy-header header-seealso

See Also
---------

* :ref:`Plugins reference <reference-plugins>`
* :ref:`Plugins explanation <explanation-plugins>`
* :ref:`How to create Plugins <how-to-create-plugins>`

