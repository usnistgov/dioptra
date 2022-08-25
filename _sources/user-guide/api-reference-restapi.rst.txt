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

.. _user-guide-api-reference-restapi:

Testbed REST API Reference
==========================

.. include:: /_glossary_note.rst

This page documents the endpoints and available :term:`HTTP` methods for the Dioptra :term:`REST` :term:`API`.
In addition to using this page, it is highly recommended that Testbed users also use the Swagger documentation that the :term:`REST` :term:`API` service automatically generates at runtime, which presents all of this page's information in an interactive format.
To access the Swagger documentation, just navigate to the web URL for the Testbed :term:`REST` :term:`API` service (omit the ``/api`` part at the end of the web address).

.. figure:: ../images/swagger-docs-testbed-rest-api.gif
   :figwidth: 100%
   :alt: An animation clicking and scrolling through the contents of the Dioptra :term:`REST` :term:`API` Swagger documentation.

   An animated tour of the automatically generated Swagger documentation for the Dioptra :term:`REST` :term:`API`.
   Several of the Testbed demos that you can run on a personal computer publish the :term:`REST` :term:`API` service at the address http://localhost:30080.

Experiment
----------

Experiment registration operations.

Endpoints
^^^^^^^^^

The following is the list of endpoints under the ``/api/experiment/`` namespace.

.. http:get:: /api/experiment/

   **Gets a list of all registered experiments**

   :status 200: Success
   :reqheader X-Fields: An optional fields mask
   :>json string [].createdOn: The date and time the experiment was created.
   :>json integer [].experimentId: An integer identifying a registered experiment.
   :>json string [].lastModified: The date and time the experiment was last modified.
   :>json string [].name: The name of the experiment.

.. http:post:: /api/experiment/

   **Creates a new experiment via an experiment registration form**

   :status 200: Success
   :reqheader X-Fields: An optional fields mask
   :form name: *(required)* The name to register as a new experiment.
   :>json string createdOn: The date and time the experiment was created.
   :>json integer experimentId: An integer identifying a registered experiment.
   :>json string lastModified: The date and time the experiment was last modified.
   :>json string name: The name of the experiment.

.. openapi:: api-restapi/openapi.yml
   :include:
     /api/experiment/{.*

.. openapi:: api-restapi/openapi.yml
   :include:
     /api/experiment/name/.*

Error Messages
^^^^^^^^^^^^^^

The following error handlers are registered to the experiment endpoints.

.. autoexception:: dioptra.restapi.experiment.errors.ExperimentAlreadyExistsError

.. autoexception:: dioptra.restapi.experiment.errors.ExperimentMLFlowTrackingAlreadyExistsError

.. autoexception:: dioptra.restapi.experiment.errors.ExperimentDoesNotExistError

.. autoexception:: dioptra.restapi.experiment.errors.ExperimentMLFlowTrackingDoesNotExistError

.. autoexception:: dioptra.restapi.experiment.errors.ExperimentMLFlowTrackingRegistrationError

.. autoexception:: dioptra.restapi.experiment.errors.ExperimentRegistrationError

Job
---

Job submission and management operations.

Endpoints
^^^^^^^^^

The following is the list of endpoints under the ``/api/job/`` namespace.

.. http:get:: /api/job/

   **Gets a list of all submitted jobs**

   :status 200: Success
   :reqheader X-Fields: An optional fields mask
   :>json string [].createdOn: The date and time the job was created.
   :>json string [].dependsOn: A :term:`UUID` for a previously submitted job to set as a dependency for the current job.
   :>json string [].entryPoint: The name of the entry point in the MLproject file to run.
   :>json string [].entryPointKwargs: A string listing parameter values to pass to the entry point for the job. The list of parameters is specified using the following format: `"-P param1=value1 -P param2=value2"`.
   :>json integer [].experimentId: An integer identifying a registered experiment.
   :>json string [].jobId: A :term:`UUID` that identifies the job.
   :>json string [].lastModified: The date and time the job was last modified.
   :>json string [].mlflowRunId: A :term:`UUID` that identifies the MLFLow run associated with the job.
   :>json integer [].queueId: An integer identifying a registered queue.
   :>json string [].status: The current status of the job. The allowed values are: queued, started, deferred, finished, failed.
   :>json string [].timeout: The maximum alloted time for a job before it times out and is stopped.
   :>json string [].workflowUri: The :term:`URI` pointing to the tarball archive or zip file uploaded with the job.

.. http:post:: /api/job/

   **Creates a new job via a job submission form with an attached file**

   :status 200: Success
   :reqheader X-Fields: An optional fields mask
   :form experiment_name: *(required)* The name of a registered experiment.
   :form queue: *(required)* The name of an active queue.
   :form timeout: The maximum alloted time for a job before it times out and is stopped. If omitted, the job timeout will default to 24 hours.
   :form entry_point: *(required)* The name of the entry point in the MLproject file to run.
   :form entry_point_kwargs: A list of entry point parameter values to use for the job. The list is a string with the following format: `"-P param1=value1 -P param2=value2"`. If omitted, the default values in the MLproject file will be used.
   :form depends_on: A job :term:`UUID` to set as a dependency for this new job. The new job will not run until this job completes successfully. If omitted, then the new job will start as soon as computing resources are available.
   :form workflow: *(required)* A tarball archive or zip file containing, at a minimum, a MLproject file and its associated entry point scripts.
   :>json string createdOn: The date and time the job was created.
   :>json string dependsOn: A :term:`UUID` for a previously submitted job to set as a dependency for the current job.
   :>json string entryPoint: The name of the entry point in the MLproject file to run.
   :>json string entryPointKwargs: A string listing parameter values to pass to the entry point for the job. The list of parameters is specified using the following format: `"-P param1=value1 -P param2=value2"`.
   :>json integer experimentId: An integer identifying a registered experiment.
   :>json string jobId: A :term:`UUID` that identifies the job.
   :>json string lastModified: The date and time the job was last modified.
   :>json string mlflowRunId: A :term:`UUID` that identifies the MLFLow run associated with the job.
   :>json integer queueId: An integer identifying a registered queue.
   :>json string status: The current status of the job. The allowed values are: queued, started, deferred, finished, failed.
   :>json string timeout: The maximum alloted time for a job before it times out and is stopped.
   :>json string workflowUri: The :term:`URI` pointing to the tarball archive or zip file uploaded with the job.

.. openapi:: api-restapi/openapi.yml
   :include:
     /api/job/{.*

Error Messages
^^^^^^^^^^^^^^

The following error handlers are registered to the job endpoints.

.. autoexception:: dioptra.restapi.job.errors.JobDoesNotExistError

.. autoexception:: dioptra.restapi.job.errors.JobSubmissionError

.. autoexception:: dioptra.restapi.job.errors.JobWorkflowUploadError

Queue
-----

Queue registration operations.

Endpoints
^^^^^^^^^

The following is the list of endpoints under the ``/api/queue/`` namespace.

.. http:get:: /api/queue/

   **Gets a list of all registered queues**

   :status 200: Success
   :reqheader X-Fields: An optional fields mask
   :>json string [].createdOn: The date and time the queue was created.
   :>json string [].lastModified: The date and time the queue was last modified.
   :>json string [].name: The name of the queue.
   :>json integer [].queueId: An integer identifying a registered queue.

.. http:post:: /api/queue/

   **Creates a new queue via a queue registration form**

   :status 200: Success
   :reqheader X-Fields: An optional fields mask
   :form name: *(required)* The name to register as a new queue.
   :>json string createdOn: The date and time the queue was created.
   :>json string lastModified: The date and time the queue was last modified.
   :>json string name: The name of the queue.
   :>json integer queueId: An integer identifying a registered queue.

.. openapi:: api-restapi/openapi.yml
   :include:
     /api/queue/{.*

.. openapi:: api-restapi/openapi.yml
   :include:
     /api/queue/name/.*

Error Messages
^^^^^^^^^^^^^^

The following error handlers are registered to the queue endpoints.

.. autoexception:: dioptra.restapi.queue.errors.QueueAlreadyExistsError

.. autoexception:: dioptra.restapi.queue.errors.QueueDoesNotExistError

.. autoexception:: dioptra.restapi.queue.errors.QueueRegistrationError

Task Plugin
-----------

Task plugin registry operations.

Endpoints
^^^^^^^^^

The following is the list of endpoints under the ``/api/taskPlugin/`` namespace.

.. http:get:: /api/taskPlugin/

   **Gets a list of all registered task plugins**

   :status 200: Success
   :reqheader X-Fields: An optional fields mask
   :>json string [].collection: The collection that contains the task plugin module, for example, the "builtins" collection.
   :>json string [].modules[]: The available modules (Python files) in the task plugin package.
   :>json string [].taskPluginName: A unique string identifying a task plugin package within a collection.

.. http:post:: /api/taskPlugin/

   **Registers a new task plugin uploaded via the task plugin upload form**

   :status 200: Success
   :reqheader X-Fields: An optional fields mask
   :form task_plugin_name: *(required)* A unique string identifying a task plugin package within a collection.
   :form task_plugin_file: *(required)* A tarball archive or zip file containing a single task plugin package.
   :form collection: *(required)* The collection where the task plugin should be stored.
   :>json string collection: The collection that contains the task plugin module, for example, the "builtins" collection.
   :>json string modules[]: The available modules (Python files) in the task plugin package.
   :>json string taskPluginName: A unique string identifying a task plugin package within a collection.

.. openapi:: api-restapi/openapi.yml
   :include:
     /api/taskPlugin/{.*

.. openapi:: api-restapi/openapi.yml
   :include:
     /api/taskPlugin/dioptra_builtins/.*

.. openapi:: api-restapi/openapi.yml
   :include:
     /api/taskPlugin/dioptra_custom/.*

Error Messages
^^^^^^^^^^^^^^

The following error handlers are registered to the task plugin endpoints.

.. autoexception:: dioptra.restapi.task_plugin.errors.TaskPluginAlreadyExistsError

.. autoexception:: dioptra.restapi.task_plugin.errors.TaskPluginDoesNotExistError

.. autoexception:: dioptra.restapi.task_plugin.errors.TaskPluginUploadError
