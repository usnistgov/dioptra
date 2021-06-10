.. NOTICE
..
.. This software (or technical data) was produced for the U. S. Government under
.. contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
.. 52.227-14, Alt. IV (DEC 2007)
..
.. © 2021 The MITRE Corporation.

.. _user-guide-api-reference-restapi:

Testbed REST API Reference
==========================

This page documents the endpoints and available HTTP methods for the Dioptra REST API.
In addition to using this page, it is highly recommended that Testbed users also use the Swagger documentation that the REST API service automatically generates at runtime, which presents all of this page's information in an interactive format.
To access the Swagger documentation, just navigate to the web URL for the Testbed REST API service (omit the ``/api`` part at the end of the web address).

.. figure:: ../images/swagger-docs-testbed-rest-api.gif
   :figwidth: 100%
   :alt: An animation clicking and scrolling through the contents of the Dioptra REST API Swagger documentation.

   An animated tour of the automatically generated Swagger documentation for the Dioptra REST API.
   Several of the Testbed demos that you can run on a personal computer publish the REST API service at the address http://localhost:30080.

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

.. autoexception:: mitre.securingai.restapi.experiment.errors.ExperimentAlreadyExistsError

.. autoexception:: mitre.securingai.restapi.experiment.errors.ExperimentMLFlowTrackingAlreadyExistsError

.. autoexception:: mitre.securingai.restapi.experiment.errors.ExperimentDoesNotExistError

.. autoexception:: mitre.securingai.restapi.experiment.errors.ExperimentMLFlowTrackingDoesNotExistError

.. autoexception:: mitre.securingai.restapi.experiment.errors.ExperimentMLFlowTrackingRegistrationError

.. autoexception:: mitre.securingai.restapi.experiment.errors.ExperimentRegistrationError

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
   :>json string [].dependsOn: A UUID for a previously submitted job to set as a dependency for the current job.
   :>json string [].entryPoint: The name of the entry point in the MLproject file to run.
   :>json string [].entryPointKwargs: A string listing parameter values to pass to the entry point for the job. The list of parameters is specified using the following format: `"-P param1=value1 -P param2=value2"`.
   :>json integer [].experimentId: An integer identifying a registered experiment.
   :>json string [].jobId: A UUID that identifies the job.
   :>json string [].lastModified: The date and time the job was last modified.
   :>json string [].mlflowRunId: A UUID that identifies the MLFLow run associated with the job.
   :>json integer [].queueId: An integer identifying a registered queue.
   :>json string [].status: The current status of the job. The allowed values are: queued, started, deferred, finished, failed.
   :>json string [].timeout: The maximum alloted time for a job before it times out and is stopped.
   :>json string [].workflowUri: The URI pointing to the tarball archive or zip file uploaded with the job.

.. http:post:: /api/job/

   **Creates a new job via a job submission form with an attached file**

   :status 200: Success
   :reqheader X-Fields: An optional fields mask
   :form experiment_name: *(required)* The name of a registered experiment.
   :form queue: *(required)* The name of an active queue.
   :form timeout: The maximum alloted time for a job before it times out and is stopped. If omitted, the job timeout will default to 24 hours.
   :form entry_point: *(required)* The name of the entry point in the MLproject file to run.
   :form entry_point_kwargs: A list of entry point parameter values to use for the job. The list is a string with the following format: `"-P param1=value1 -P param2=value2"`. If omitted, the default values in the MLproject file will be used.
   :form depends_on: A job UUID to set as a dependency for this new job. The new job will not run until this job completes successfully. If omitted, then the new job will start as soon as computing resources are available.
   :form workflow: *(required)* A tarball archive or zip file containing, at a minimum, a MLproject file and its associated entry point scripts.
   :>json string createdOn: The date and time the job was created.
   :>json string dependsOn: A UUID for a previously submitted job to set as a dependency for the current job.
   :>json string entryPoint: The name of the entry point in the MLproject file to run.
   :>json string entryPointKwargs: A string listing parameter values to pass to the entry point for the job. The list of parameters is specified using the following format: `"-P param1=value1 -P param2=value2"`.
   :>json integer experimentId: An integer identifying a registered experiment.
   :>json string jobId: A UUID that identifies the job.
   :>json string lastModified: The date and time the job was last modified.
   :>json string mlflowRunId: A UUID that identifies the MLFLow run associated with the job.
   :>json integer queueId: An integer identifying a registered queue.
   :>json string status: The current status of the job. The allowed values are: queued, started, deferred, finished, failed.
   :>json string timeout: The maximum alloted time for a job before it times out and is stopped.
   :>json string workflowUri: The URI pointing to the tarball archive or zip file uploaded with the job.

.. openapi:: api-restapi/openapi.yml
   :include:
     /api/job/{.*

Error Messages
^^^^^^^^^^^^^^

The following error handlers are registered to the job endpoints.

.. autoexception:: mitre.securingai.restapi.job.errors.JobDoesNotExistError

.. autoexception:: mitre.securingai.restapi.job.errors.JobSubmissionError

.. autoexception:: mitre.securingai.restapi.job.errors.JobWorkflowUploadError

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

.. autoexception:: mitre.securingai.restapi.queue.errors.QueueAlreadyExistsError

.. autoexception:: mitre.securingai.restapi.queue.errors.QueueDoesNotExistError

.. autoexception:: mitre.securingai.restapi.queue.errors.QueueRegistrationError
