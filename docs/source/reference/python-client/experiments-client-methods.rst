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

.. _reference-experiments-client-methods:

Experiments Client Methods
=================

This page lists all relevant methods for Dioptra :ref:`Experiments <explanation-experiments-and-jobs>` that are available via the Python Client. 

.. contents:: Contents
   :local:
   :depth: 2


Requirements
-------------

- :ref:`explanation-install-dioptra` - an installation and deployment of Dioptra must be available
- :ref:`how-to-set-up-the-python-client` - the Python client must be configured and initialized


.. _reference-experiments-client-methods-crud-methods:

Experiments - CRUD Methods
--------------------------

After :ref:`importing and initializing the client <how-to-set-up-the-python-client>`, these methods for creating, reading updating and deleting (CRUD) experiments can be executed via ``client.experiments.METHOD_NAME()``. 


Create Experiment
~~~~~~~~~~~~~~~~~
      
    .. automethod:: dioptra.client.experiments.ExperimentsCollectionClient.create

Get Experiments
~~~~~~~~~~~~~~~
      
    .. automethod:: dioptra.client.experiments.ExperimentsCollectionClient.get

Modify Experiment
~~~~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.experiments.ExperimentsCollectionClient.modify_by_id

Delete Experiment
~~~~~~~~~~~~~~~~~
      
    .. automethod:: dioptra.client.experiments.ExperimentsCollectionClient.delete_by_id


.. _reference-experiments-client-methods-other-methods:

Experiments - Other Methods
---------------------------

Get Metrics for Jobs in Experiment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.experiments.ExperimentsCollectionClient.get_metrics_by_id


.. _reference-experiments-client-methods-attached-entrypoints-methods:


Entrypoint Attachment - Methods
-------------------------------

These methods exist within the class ``ExperimentEntrypointsSubCollectionClient``, and can are accessed via the ``entrypoints`` property of the Experiment Client (which points to ``ExperimentEntrypointsSubCollectionClient``)

**Example - Attach Entrypoints to Experiment**

.. admonition:: Attach Entrypoints to Experiment
   :class: code-panel python

   .. code-block:: python

        client.experiments.entrypoints.create(experiment_id=1, entrypoint_ids=[2,3])


Add Entrypoint to Experiment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
      
    .. automethod:: dioptra.client.experiments.ExperimentEntrypointsSubCollectionClient.create

Get Entrypoints for Experiment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
      
    .. automethod:: dioptra.client.experiments.ExperimentEntrypointsSubCollectionClient.get

Replace Attached Entrypoints
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.experiments.ExperimentEntrypointsSubCollectionClient.modify_by_id

Delete All Attached Entrypoints
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
      
    .. automethod:: dioptra.client.experiments.ExperimentEntrypointsSubCollectionClient.delete

Delete One Entrypoint by ID
~~~~~~~~~~~~~~~~~~~~~~~~~~~
      
    .. automethod:: dioptra.client.experiments.ExperimentEntrypointsSubCollectionClient.delete_by_id


.. _reference-experiments-client-methods-executed-jobs-methods:


Job Execution - Methods
-----------------------

These methods exist within the class ``ExperimentJobsSubCollectionClient``, and can are accessed via the ``jobs`` property of the Experiment Client (which points to ``ExperimentJobsSubCollectionClient``)

**Example - Run an Entrypoint as a Job within an Experiment**

.. admonition:: Run Entrypoint as a Job
   :class: code-panel python

   .. code-block:: python

        client.experiments.jobs.create(experiment_id=1, entrypoint_id=[2], queue_id=10,)



Get All Jobs
~~~~~~~~~~~~
      
    .. automethod:: dioptra.client.experiments.ExperimentJobsSubCollectionClient.get

Get One Job by ID
~~~~~~~~~~~~~~~~~
      
    .. automethod:: dioptra.client.experiments.ExperimentJobsSubCollectionClient.get_by_id

Get Job Status by ID
~~~~~~~~~~~~~~~~~~~~
      
    .. automethod:: dioptra.client.experiments.ExperimentJobsSubCollectionClient.get_status

Create a Job
~~~~~~~~~~~~

    .. automethod:: dioptra.client.experiments.ExperimentJobsSubCollectionClient.create

Set Job Status by ID
~~~~~~~~~~~~~~~~~~~~
      
    .. automethod:: dioptra.client.experiments.ExperimentJobsSubCollectionClient.set_status
        

Delete a Job by ID
~~~~~~~~~~~~~~~~~~
      
    .. automethod:: dioptra.client.experiments.ExperimentJobsSubCollectionClient.delete_by_id






Tags Attached to Experiment - Methods
-------------------------------------

Methods belonging to the ``TagsSubCollectionClient`` can are accessed via the ``tags`` property of the Experiment Client (which points to ``TagsSubCollectionClient``)

**Example - Get Tags for an Experiment**

.. admonition:: Get Tags for Experiment
   :class: code-panel python

   .. code-block:: python

        client.experiments.tags.get(1)


See **available methods** for the ``TagsSubCollectionClient``: 

* :ref:`reference-tags-client-methods`




Snapshots of Experiment - Methods
---------------------------------

Methods belonging to the  ``SnapshotsSubCollectionClient`` can are accessed via the ``snapshots`` property of the Experiment Client (which points to ``SnapshotsSubCollectionClient``)

**Example - Get Snapshots for an Experiment**

.. admonition:: Get Snapshots for Experiment
   :class: code-panel python

   .. code-block:: python

        client.experiments.snapshots.get(1)


See **available methods** for the ``SnapshotsSubCollectionClient``:

* :ref:`reference-snapshots-client-methods`


.. rst-class:: fancy-header header-seealso

See Also
---------

* :ref:`Experiments reference <reference-experiments>`
* :ref:`Experiments and Jobs explanation <explanation-experiments-and-jobs>`
* :ref:`How to create Experiments <how-to-create-experiments>`
