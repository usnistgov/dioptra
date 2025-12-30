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

.. _explanation-queues-and-workers:

Queues and Workers
================

Summary: What is a Worker?
--------------------------

A **worker** is an environment in which a job can be executed. A worker should contain all of the requirements needed for a given
entrypoint, such as any local files, python packages, or executables needed as part of the job.

A worker must run the ``dioptra-worker-v1`` executable, which will watch a named queue in the Dioptra RESTAPI for jobs. When a new
job is added to the queue being watched by the worker, the worker will take the job from the queue and attempt to execute it. Upon finishing
the job, the worker will update the job status in the RESTAPI.

In order to accomplish this the worker must be able to communicate with the RESTAPI and with MLFlow for experiment tracking and job status updates.
The following environment variables are required to be set and accessible in the worker environment.

.. code-block::
    
    MLFLOW_S3_ENDPOINT_URL=
    MLFLOW_TRACKING_URI=
    DIOPTRA_WORKER_USERNAME=
    DIOPTRA_WORKER_PASSWORD=
    DIOPTRA_API=

The username and password mentioned here must provide access to a valid account for the worker to interact with the Dioptra RESTAPI.

By default, Dioptra provides several default worker environments which can be enabled during setup:
    * tensorflow_cpu
    * tensorflow_gpu
    * pytorch_cpu
    * pytorch_gpu

Creating queues with these names, as long as the corresponding worker is enabled, will allow jobs to be run in these worker containers.

Additionally, custom workers can be created which watch queues of other names and provide different environments for the jobs to run in,
allowing for additional requirements and packages to be included.

See :ref:`how-to-using-custom-workers` for more information.

Summary: What is a Queue?
-------------------------

A **queue** is a resource in Dioptra which represents a logical job queue for workers watching that queue to take from. Entrypoints can
be assigned a number of queues they are compatible with, and at job creation, a specific queue is selected for the job to be added to.
Any workers watching that queue can take and execute the job.

.. rst-class:: fancy-header header-seealso

See Also 
---------
   
* :ref:`how-to-using-custom-workers` - Guide for creating custom workers
* :ref:`how-to-create-queues` - Step-by-step guide on creating queues



