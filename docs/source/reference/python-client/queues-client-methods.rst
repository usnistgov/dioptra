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

.. _reference-queues-client-methods:

Queues Client Methods
=====================

This page lists all relevant methods for Dioptra :ref:`Queues <explanation-queues>` that are available via the Python Client.

.. contents:: Contents
   :local:
   :depth: 2


Requirements
------------

- :ref:`explanation-install-dioptra` - an installation and deployment of Dioptra must be available
- :ref:`how-to-set-up-the-python-client` - the Python client must be configured and initialized



.. _reference-queues-client-methods-crud-methods:

Queues - CRUD methods
---------------------

After :ref:`importing and initializing the client <how-to-set-up-the-python-client>`, these methods for creating, reading, updating, and deleting (CRUD) Queues can be executed via ``client.queues.METHOD_NAME()``. 


Create Queue
~~~~~~~~~~~~
      
    .. automethod:: dioptra.client.queues.QueuesCollectionClient.create

Get Queues
~~~~~~~~~~
      
    .. automethod:: dioptra.client.queues.QueuesCollectionClient.get

Get Queue by ID
~~~~~~~~~~~~~~~
      
    .. automethod:: dioptra.client.queues.QueuesCollectionClient.get_by_id

Modify Queue
~~~~~~~~~~~~

    .. automethod:: dioptra.client.queues.QueuesCollectionClient.modify_by_id

Delete Queue
~~~~~~~~~~~~
      
    .. automethod:: dioptra.client.queues.QueuesCollectionClient.delete_by_id



Tags Attached to Queue - Methods
--------------------------------

Methods belonging to the ``TagsSubCollectionClient`` can are accessed via the ``tags`` property of the Queues Client (which points to ``TagsSubCollectionClient``)

**Example - Get tags for a Queue**

.. admonition:: Get tags for a Queue
   :class: code-panel python

   .. code-block:: python

        client.queues.tags.get(1)

See **available methods** for the ``TagsSubCollectionClient``: 

* :ref:`reference-tags-client-methods`


Snapshots of Queue - Methods
----------------------------

Methods belonging to the  ``SnapshotsSubCollectionClient`` can are accessed via the ``snapshots`` property of the Queues Client (which points to ``SnapshotsSubCollectionClient``)

**Example - Get snapshots for a Queue**

.. admonition:: Get snapshots for a Queue
   :class: code-panel python

   .. code-block:: python

        client.queues.snapshots.get(1)

See **available methods** for the ``SnapshotsSubCollectionClient``:

* :ref:`reference-snapshots-client-methods`


.. rst-class:: fancy-header header-seealso

See Also
--------

* :ref:`Queues reference <reference-queues>`
* :ref:`Queues explanation <explanation-queues-and-workers>`
* :ref:`How to create Queues <how-to-create-queues>`

