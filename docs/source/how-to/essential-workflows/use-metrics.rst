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

.. _how-to-logging-metrics:

Logging Metrics
===============

This how-to explains how to log metrics in Dioptra. 

Prerequisites
-------------

.. tabs:: 

   .. group-tab:: Python Client

      * :ref:`how-to-prepare-deployment` -  A deployment of Dioptra is required.
      * :ref:`how-to-set-up-the-python-client` - Connect to the Python Client from within the job.

.. _how-to-create-users-user-creation-workflow:

Metric Logging Workflow
-----------------------

Metrics can be logged as part of a plugin, during the execution of a job,
by using the python client, and can be retrieved via the API or viewed 
through the Job details page.

.. note:: 
   This guide only explains how to log metrics through the client, and not how to incorporate metric
   logging into your custom plugin tasks.

.. rst-class:: header-on-a-card header-steps


Log a Metric to a Job
~~~~~~~~~~~~~~~~~~~~~

Log a metric as part of a job using the Python client.

.. tabs::

   .. group-tab:: Python Client

      **Client Method:**

      Use the client to create a metric.

      Note that from a job, you can use ``os.environ["__JOB_ID"]`` to get the current job's ID. 

      .. automethod:: dioptra.client.jobs.JobsCollectionClient.append_metric_by_id


.. rst-class:: header-on-a-card header-steps

Retrieving Metrics for Jobs
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Retrieve metrics from a job or view them in the GUI.

.. tabs::

   .. group-tab:: GUI

      In the Dioptra GUI, navigate to the **Jobs** tab. Click the row for a job. 
      Click the **Metrics** tab on the **Job Dashboard** page. A list of logged metrics
      will be displayed here.

   .. group-tab:: Python Client

      **Client Method:**

      Use the client to retrieve the latest metrics associated with the job.

      .. automethod:: dioptra.client.jobs.JobsCollectionClient.get_metrics_by_id

      Alternatively, you can retrieve the full metric history for a job.

      .. automethod:: dioptra.client.jobs.JobsCollectionClient.get_metrics_snapshots_by_id

      It is also possible to retrieve the metrics across all jobs in an experiment.

      .. automethod:: dioptra.client.experiments.ExperimentsCollectionClient.get_metrics_by_id
