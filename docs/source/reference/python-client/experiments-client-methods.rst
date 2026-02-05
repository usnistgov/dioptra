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

This page lists all relevant properties and methods for Dioptra :ref:`Experiments <explanation-experiments-and-jobs>` that are available via the Python Client. 

.. contents:: Contents
   :local:
   :depth: 2


Requirements
-------------

- :ref:`how-to-install-dioptra` - an installation and deployment of Dioptra must be available
- :ref:`how-to-set-up-the-python-client` - the Python client must be configured and initialized


.. _reference-experiments-client-methods-experiment-properties:

Experiment Properties
---------------------
These properties can be accessed via ``client.experiments.{property_name}``. 


Attached Entrypoints
~~~~~~~~~

    .. autoattribute:: dioptra.client.experiments.ExperimentsCollectionClient.entrypoints

See available methods for this client subcollection: :ref:`reference-experiments-client-methods-attached-entrypoints-methods`

Executed Jobs
~~~~~~~~~

    .. autoattribute:: dioptra.client.experiments.ExperimentsCollectionClient.jobs

See available methods for this client subcollection: :ref:`reference-experiments-client-methods-executed-jobs-methods`

Attached Tags
~~~~~~~~~

    .. autoattribute:: dioptra.client.experiments.ExperimentsCollectionClient.tags

See available methods for this client subcollection: :ref:`reference-tags-client-methods`


Experiment Snapshots
~~~~~~~~~

    .. autoattribute:: dioptra.client.experiments.ExperimentsCollectionClient.snapshots

See available methods for this client subcollection: :ref:`reference-snapshots-client-methods`


.. _reference-experiments-client-methods-crud-methods:

Experiments - CRUD methods
---------------------

These methods can be executed via ``client.experiments.METHOD_NAME()``. 



Create
~~~~~~~~~
      
    .. automethod:: dioptra.client.experiments.ExperimentsCollectionClient.create

Get
~~~~~~~~~
      
    .. automethod:: dioptra.client.experiments.ExperimentsCollectionClient.get

Modify
~~~~~~~~~

    .. automethod:: dioptra.client.experiments.ExperimentsCollectionClient.modify_by_id

Delete
~~~~~~~~~
      
    .. automethod:: dioptra.client.experiments.ExperimentsCollectionClient.delete_by_id


.. _reference-experiments-client-methods-other-methods:

Experiments - Other Methods
---------------------

Get Metrics 
~~~~~~~~~~~~

    .. automethod:: dioptra.client.experiments.ExperimentsCollectionClient.get_metrics_by_id


.. _reference-experiments-client-methods-attached-entrypoints-methods:


Attached Entrypoints - Methods
--------------------------------------------

These methods exist within the class ``ExperimentEntrypointsSubCollectionClient``, and can be executed after retrieving a specific experiment via the class property ``RETRIEVED_EXPERIMENT.entrypoints``

.. admonition:: Access ExperimentEntrypointsSubCollectionClient
    :class: code-panel python

    .. code-block:: python 

        # Assumes authenticated Python client instance
        experiments = client.experiments.get()
        first_experiment = experiments[0]
        attached_entrypoints = first_experiment.entrypoints.get() # See below for other available methods

Add Entrypoint to Experiment
~~~~~~~~~
      
    .. automethod:: dioptra.client.experiments.ExperimentEntrypointsSubCollectionClient.create

Get Entrypoints for Experiment
~~~~~~~~~
      
    .. automethod:: dioptra.client.experiments.ExperimentEntrypointsSubCollectionClient.get

Replace Attached Entrypoints
~~~~~~~~~

    .. automethod:: dioptra.client.experiments.ExperimentEntrypointsSubCollectionClient.modify_by_id

Delete All Attached Entrypoints
~~~~~~~~~
      
    .. automethod:: dioptra.client.experiments.ExperimentEntrypointsSubCollectionClient.delete

Delete One Entrypoint by ID
~~~~~~~~~
      
    .. automethod:: dioptra.client.experiments.ExperimentEntrypointsSubCollectionClient.delete_by_id


.. _reference-experiments-client-methods-executed-jobs-methods:


Executed Jobs - Methods
--------------------------------------------

These methods exist within the class ``ExperimentJobsSubCollectionClient``, and can be executed after retrieving a specific experiment via the class property ``RETRIEVED_EXPERIMENT.jobs``


.. admonition:: Access ExperimentJobsSubCollectionClient
    :class: code-panel python
        
    .. code-block:: python 

        # Assumes authenticated Python client instance
        experiments = client.experiments.get()
        first_experiment = experiments[0]
        executed_jobs = first_experiment.jobs.get() # See below for other available methods

Get All Jobs
~~~~~~~~~
      
    .. automethod:: dioptra.client.experiments.ExperimentJobsSubCollectionClient.get

Get One Job by ID
~~~~~~~~~
      
    .. automethod:: dioptra.client.experiments.ExperimentJobsSubCollectionClient.get_by_id

Get Job Status by ID
~~~~~~~~~
      
    .. automethod:: dioptra.client.experiments.ExperimentJobsSubCollectionClient.get_status

Create a Job
~~~~~~~~~

    .. automethod:: dioptra.client.experiments.ExperimentJobsSubCollectionClient.create

Set Job Status by ID
~~~~~~~~~
      
    .. automethod:: dioptra.client.experiments.ExperimentJobsSubCollectionClient.set_status
        

Delete a Job by ID
~~~~~~~~~
      
    .. automethod:: dioptra.client.experiments.ExperimentJobsSubCollectionClient.delete_by_id



Create a Job Artifact (do we want this?)
~~~~~~~~~
      
    .. automethod:: dioptra.client.experiments.ExperimentJobsSubCollectionClient.create_artifact

Get MLFlow Run ID (do we want this?)
~~~~~~~~~
      
    .. automethod:: dioptra.client.experiments.ExperimentJobsSubCollectionClient.get_mlflow_run_id

Set MLFlow Run ID  (do we want this?)
~~~~~~~~~
      
    .. automethod:: dioptra.client.experiments.ExperimentJobsSubCollectionClient.set_mlflow_run_id


.. rst-class:: fancy-header header-seealso

See Also
---------

* :ref:`Experiments reference <reference-experiments>`
* :ref:`Experiments and Jobs explanation <explanation-experiments-and-jobs>`
* :ref:`How to create Experiments <how-to-create-experiments>`
