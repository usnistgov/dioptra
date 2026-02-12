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

.. _reference-tags-client-methods:

Tags Client Methods
===================


This page lists all relevant methods for Dioptra Tags that are available via the Python Client. 

.. contents:: Contents
   :local:
   :depth: 2


Requirements
------------

- :ref:`explanation-install-dioptra` - an installation and deployment of Dioptra must be available
- :ref:`how-to-set-up-the-python-client` - the Python client must be configured and initialized



.. _reference-tags-client-methods-crud-methods:

Tags - CRUD methods
-------------------

After :ref:`importing and initializing the client <how-to-set-up-the-python-client>`, these methods can be executed via ``client.tags.METHOD_NAME()``. 



Create Tag
~~~~~~~~~~
      
    .. automethod:: dioptra.client.tags.TagsCollectionClient.create

Get Tags
~~~~~~~~
      
    .. automethod:: dioptra.client.tags.TagsCollectionClient.get

Get Tag by ID
~~~~~~~~~~~~~
      
    .. automethod:: dioptra.client.tags.TagsCollectionClient.get_by_id

Modify Tag
~~~~~~~~~~

    .. automethod:: dioptra.client.tags.TagsCollectionClient.modify_by_id

Delete Tag
~~~~~~~~~~
      
    .. automethod:: dioptra.client.tags.TagsCollectionClient.delete_by_id


.. _reference-tags-client-methods-other-methods:

Tags - Other Methods
--------------------

Get Dioptra Resources for Tag
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.tags.TagsCollectionClient.get_resources_for_tag


.. _reference-tags-client-methods-attached-tags-methods:


Attached Tags - Methods
-----------------------

These methods exist within the class ``TagsSubCollectionClient``. In other resource clients (like Experiments or Jobs), they are typically accessed via a ``tags`` property.

**Example - Get Tags for an Experiment**

.. admonition:: Get Tags for an Experiment
   :class: code-panel python

   .. code-block:: python

        client.experiments.tags.get(1)


Get Attached Tags
~~~~~~~~~~~~~~~~~
      
    .. automethod:: dioptra.client.tags.TagsSubCollectionClient.get

Replace All Attached Tags
~~~~~~~~~~~~~~~~~~~~~~~~~
      
    .. automethod:: dioptra.client.tags.TagsSubCollectionClient.modify

Append Tags to Resource
~~~~~~~~~~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.tags.TagsSubCollectionClient.append

Remove One Tag from Resource
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
      
    .. automethod:: dioptra.client.tags.TagsSubCollectionClient.remove

Remove All Tags from Resource
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
      
    .. automethod:: dioptra.client.tags.TagsSubCollectionClient.remove_all

