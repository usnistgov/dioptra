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

.. _reference-jobs:

Jobs
====


.. contents:: Contents
   :local:
   :depth: 2

.. _reference-jobs-definition:

Job Definition
--------------

A **Job** in Dioptra is a parameterized execution of an :ref:`Entrypoint <reference-entrypoints>`. While an Experiment defines the scope and available workflows, a Job represents the actual run of a workflow.

When a Job is created, it is sent to a specific :ref:`Queue <reference-queues>`. A :ref:`Worker <reference-workers>` listening to that queue claims the Job and executes the entrypoint code using the provided parameters and artifact inputs.
Dioptra maintains a full history of every Job, including its logs, metrics, and any generated artifacts, creating a permanent record of the execution even if the underlying entrypoint or plugins are later modified.

.. _reference-jobs-attributes:

Job Attributes
--------------

This section describes the attributes used to define and track a Job.

.. _reference-jobs-required-attributes:

Required Attributes
~~~~~~~~~~~~~~~~~~~

- **Experiment**: (integer ID) The unique identifier of the Experiment that serves as the namespace for this Job.
- **Entrypoint**: (integer ID) The unique identifier of the Entrypoint resource defining the workflow to be executed. The Entrypoint must be associated with the selected Experiment.
- **Queue**: (integer ID) The unique identifier of the Queue where the Job will be submitted for execution.
- **Values**: (dictionary) A collection of parameter values (key-string pairs) passed to the Entrypoint to configure the workflow execution.
   - **Name**: (string) The input parameter name of the entrypoint parameter
   - **Value**: (any) The value for that entrypoint parameter

- **Artifact Values**: (dictionary) A collection of Artifact IDs and Snapshot IDs passed as input parameters to the workflow.
   - **Name**: (string) The name of the artifact parameter defined in the entrypoint
   - **Artifact ID**: (integer ID) The unique identifier of the Artifact, which was created by another Job execution
   - **Snapshot ID**: (integer ID) The unique identifier of the specific Snapshot to load for this Artifact.

.. _reference-jobs-optional-attributes:

Optional Attributes
~~~~~~~~~~~~~~~~~~~

- **Description**: (string, optional) A text description providing context for this specific Job run.
- **Timeout**: (string, optional) The maximum duration the Job is allowed to run before being automatically terminated by the system. Formatted using shorthand notation, i.e. ``24h``, ``1d``, ``120m``, etc.
- **Entrypoint Snapshot ID**: (integer ID, optional) The specific snapshot of the entrypoint to use. If not provided, the latest snapshot is used.

.. _reference-jobs-system-managed-state:

System-Managed State
~~~~~~~~~~~~~~~~~~~~

- **ID**: Unique identifier assigned to the Job upon registration.
- **Status**: The current state of the Job. Valid states include:
    * ``queued``: The Job is waiting in the queue for a worker.
    * ``started``: A worker has claimed the Job and execution is underway.
    * ``deferred``: The Job execution has been paused or delayed.
    * ``finished``: The Job completed successfully.
    * ``failed``: The Job encountered an error during execution.
- **Created On**: Timestamp indicating when the Job was submitted.
- **Last Modified On**: Timestamp indicating the last time the Job resource or status was updated.
- **Logs**: A collection of log entries (severity, message, and timestamp) generated during the Job's execution.
   - **Severity**: (string) The log level (e.g., INFO, ERROR, DEBUG).
   - **Logger Name**: (string) The name of the logger that produced the entry.
   - **Timestamp**: (timestamp) When the log was recorded
   - **Message**: (string) The actual log content
- **Metrics**: Key-value pairs (e.g., accuracy, loss) recorded by the workflow during execution.
   - **Name**: (string) The name of the metric (e.g., "accuracy").
   - **Step**: (integer) The execution step at which the metric was recorded.
   - **Value**: (float) The numerical value.
   - **Special Value**: (string, optional) Stores NaN, Infinity, or -Infinity if the metric value is non-finite.
   - **Timestamp**: (timestamp) When the metric was recorded.

- **Artifacts**: A list of new Artifact resources created and registered as a result of the Job.
- **MLflow Run ID**: The unique identifier for the associated MLflow run, used for tracking experiments and parameters.

.. _reference-jobs-registration-interfaces:

Registration Interfaces
-----------------------
Jobs are typically created within the context of an Experiment.

.. _reference-jobs-python-client:

Using Python Client
~~~~~~~~~~~~~~~~~~~

**Submit a Job through an Experiment**

    .. automethod:: dioptra.client.experiments.ExperimentJobsSubCollectionClient.create

.. _reference-jobs-rest-api:

Using REST API
~~~~~~~~~~~~~~

Jobs can be submitted directly via the HTTP API, usually via an experiment-specific endpoint.

**Create Job**

See the :http:post:`POST /api/v1/experiments/{experimentId}/jobs </api/v1/experiments/{id}/jobs/>` endpoint documentation for the required JSON payload, including parameters and artifact IDs.

.. rst-class:: fancy-header header-seealso

See Also
--------

Additional reference pages:

* :ref:`Experiments <reference-experiments>`
* :ref:`Entrypoints <reference-entrypoints>`
* :ref:`Queues <reference-queues>`
* :ref:`Metrics <reference-metrics>`
