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

.. _reference-queues:

Queues
=================


.. contents:: Contents
   :local:
   :depth: 2

.. _reference-queues-definition:

Queue Definition
---------------------

A **Queue** in Dioptra represents a logical job queue, which workers can accept jobs from.


.. _reference-queues-attributes:

Queue Attributes
----------------

This section describes the attributes that define a Queue.


.. _reference-queues-required-attributes:

Required Attributes
~~~~~~~~~~~~~~~~~~~

* **Name**: (string) The name of the queue. 
* **Group**: (integer ID) The Group that owns this Queue and controls access permissions.
* **Description**: (string) A description of the queue.


.. _reference-queues-system-managed-state:

System-Managed State
~~~~~~~~~~~~~~~~~~~~

The following attributes are automatically assigned by the system and cannot be set directly by the user.

- **ID**: Unique identifier assigned upon creation.
- **Created On**: Timestamp indicating when the Experiment was created.
- **Last Modified On**: Timestamp indicating when the Experiment was last modified.

.. _reference-queues-registration-interfaces:

Registration Interfaces
-----------------------

Queues can be created programmatically via the Python Client or the REST API.
They can also be :ref:`created through the web interface <how-to-create-queues>`.

.. _reference-queues-python-client:

Using Python Client
~~~~~~~~~~~~~~~~~~~

**Create a Queue**

    .. automethod:: dioptra.client.queues.QueuesCollectionClient.create


.. _reference-queues-rest-api:

Using REST API
~~~~~~~~~~~~~~

Queues can be created directly via the HTTP API.

**Create Queues**

See the :http:post:`POST /api/v1/queues </api/v1/queues/>` endpoint documentation for payload requirements.


.. rst-class:: fancy-header header-seealso

See Also
---------

* :ref:`How To Create Queues <how-to-create-queues>`
* :ref:`Queues Explanation <explanation-queues-and-workers>`
* :ref:`Entrypoints Reference <reference-entrypoints>`
