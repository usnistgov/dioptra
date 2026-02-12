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

.. _reference-parameter-types-client-methods:

Parameter Types Client Methods
==========================

This page lists all relevant methods for Dioptra :ref:`Plugin Parameter Types <reference-plugin-parameter-types>` that are available via the Python Client. 

.. contents:: Contents
    :local:
    :depth: 2

Requirements
----------------

* :ref:`explanation-install-dioptra` - an installation and deployment of Dioptra must be available
* :ref:`how-to-set-up-the-python-client` - the Python client must be configured and initialized

.. _reference-plugin-parameter-types-client-methods-crud-methods:

Plugin Parameter Types - CRUD methods
----------------

After :ref:`importing and initializing the client <how-to-set-up-the-python-client>`, these methods can be executed via ``client.plugin_parameter_types.METHOD_NAME()``. 

Create Plugin Parameter Type
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.plugin_parameter_types.PluginParameterTypesCollectionClient.create

Get Plugin Parameter Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.plugin_parameter_types.PluginParameterTypesCollectionClient.get



Get Plugin Parameter Type by ID
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.plugin_parameter_types.PluginParameterTypesCollectionClient.get_by_id

Modify Plugin Parameter Type
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.plugin_parameter_types.PluginParameterTypesCollectionClient.modify_by_id


Delete Plugin Parameter Type
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.plugin_parameter_types.PluginParameterTypesCollectionClient.delete_by_id




Tags Attached to Plugin Parameter Type
-------------------

Methods belonging to the ``TagsSubCollectionClient`` can are accessed via the ``tags`` property of the Plugin Parameter Types Client (which points to ``TagsSubCollectionClient``)

**Example - Get tags for a Plugin Parameter Type**

``client.plugin_parameter_types.tags.get(1)``

Methods - Tags
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


See **available methods for the TagsSubCollectionClient**: :ref:`reference-tags-client-methods`



Snapshots of Plugin Parameter Type
-----------------------------------

Methods belonging to the  ``SnapshotsSubCollectionClient`` can are accessed via the ``snapshots`` property of the Plugin Parameter Types Client (which points to ``SnapshotsSubCollectionClient``)

**Example - Get snapshots for a Plugin Parameter Type**

``client.plugin_parameter_types.snapshots.get(1)``

Methods - Snapshots
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


See **available methods for the SnapshotsSubCollectionClient**: :ref:`reference-snapshots-client-methods`


.. rst-class:: fancy-header header-seealso

See Also
---------

* :ref:`Plugin Parameter Types reference <reference-parameter-types>`
* :ref:`How to create Plugin Parameter Types <how-to-create-parameter-types>`

