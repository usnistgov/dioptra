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

.. _reference-jobs-client-methods:

Jobs Client Methods
===================


This page lists all relevant methods for Dioptra :ref:`Jobs <explanation-experiments-and-jobs>` that are available via the Python Client. 

.. contents:: Contents
    :local:
    :depth: 2

Requirements
------------

* :ref:`explanation-install-dioptra` - an installation and deployment of Dioptra must be available
* :ref:`how-to-set-up-the-python-client` - the Python client must be configured and initialized

.. _reference-jobs-client-methods-crud-methods:

Jobs - CRUD methods
-------------------

After :ref:`importing and initializing the client <how-to-set-up-the-python-client>`,these methods for creating, reading, updating, and deleting (CRUD) jobs can be executed via ``client.jobs.METHOD_NAME()``. 

Get Jobs
~~~~~~~~

      
    .. automethod:: dioptra.client.jobs.JobsCollectionClient.get

Get Job by ID
~~~~~~~~~~~~~



    .. automethod:: dioptra.client.jobs.JobsCollectionClient.get_by_id



Delete Job by ID
~~~~~~~~~~~~~~~~

      
    .. automethod:: dioptra.client.jobs.JobsCollectionClient.delete_by_id


.. _reference-jobs-client-methods-status-mlflow:

Jobs - Other Methods
--------------------

Get Job Status
~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.jobs.JobsCollectionClient.get_status


Get Job Parameters
~~~~~~~~~~~~~~~~~~

      
    .. automethod:: dioptra.client.jobs.JobsCollectionClient.get_parameters

Get Artifact Parameters
~~~~~~~~~~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.jobs.JobsCollectionClient.get_artifact_parameters



Get Latest Metrics for Job
~~~~~~~~~~~~~~~~~~~~~~~~~~

      
    .. automethod:: dioptra.client.jobs.JobsCollectionClient.get_metrics_by_id


Append Metric to Job
~~~~~~~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.jobs.JobsCollectionClient.append_metric_by_id



Get Metric History (Snapshots)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    .. automethod:: dioptra.client.jobs.JobsCollectionClient.get_metrics_snapshots_by_id



Get Logs
~~~~~~~~

    .. automethod:: dioptra.client.jobs.JobsCollectionClient.get_logs_by_id



Append Logs
~~~~~~~~~~~

    .. automethod:: dioptra.client.jobs.JobsCollectionClient.append_logs_by_id


Tags Attached to Job - Methods
------------------------------

Methods belonging to the ``TagsSubCollectionClient`` can are accessed via the ``tags`` property of the Jobs Client (which points to ``TagsSubCollectionClient``)

**Example - Get Tags for a Job**

.. admonition:: Get Tags for a Job
   :class: code-panel python

   .. code-block:: python

        client.jobs.tags.get(1)

See **available methods** for the ``TagsSubCollectionClient``: 

* :ref:`reference-tags-client-methods`


Snapshots of Job - Methods
--------------------------

Methods belonging to the  ``SnapshotsSubCollectionClient`` can are accessed via the ``snapshots`` property of the Jobs Client (which points to ``SnapshotsSubCollectionClient``)

**Example - Get snapshots for a Job**

.. admonition:: Get snapshots for a Job
   :class: code-panel python

   .. code-block:: python

        client.jobs.snapshots.get(1)

See **available methods** for the ``SnapshotsSubCollectionClient``:

* :ref:`reference-snapshots-client-methods`


See Also
--------

* :ref:`Jobs reference <reference-jobs>`
* :ref:`Experiments and Jobs explanation <explanation-experiments-and-jobs>`
* :ref:`How to create Experiments <how-to-create-experiments>`

