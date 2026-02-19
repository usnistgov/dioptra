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

.. _reference-workers:

Workers
=======

.. contents:: Contents
   :local:
   :depth: 2

.. _reference-workers-definition:

Worker Definition
-----------------

A :ref:`Worker <explanation-queues-and-workers>` in Dioptra is an execution environment for running Jobs. It should contain all of the requirements needed for a given entrypoint, such as any local files, python packages, or executables needed as part of the job.

A worker must run the dioptra-worker-v1 executable, which will watch a named :ref:`Queue <explanation-queues-and-workers>` in the Dioptra REST API for jobs.
When a new job is added to the queue being watched by the worker, the worker will take the job from the queue and attempt to execute it. Upon finishing the job, the worker will update the job status in the REST API.

.. _reference-workers-configuration:

Worker Configuration
--------------------

A Worker must be able to communicate with the REST API for job status updates.
Dioptra Workers are configured primarily through environment variables, which are required to be set and accessible in the worker environment.

.. _reference-workers-required-configuration:

Required Configuration
~~~~~~~~~~~~~~~~~~~~~~

The following variables must be set for the worker to successfully register and process jobs:

* **DIOPTRA_WORKER_USERNAME**: (string) The username for a registered user within the Dioptra application. The worker operates under these credentials.
* **DIOPTRA_WORKER_PASSWORD**: (string) The password corresponding to the ``DIOPTRA_WORKER_USERNAME``.
* **DIOPTRA_API**: (string) The base URL of the Dioptra API service (e.g., ``http://localhost:5000``).
* **RQ_REDIS_URI**: (string, URI) The connection string for the Redis instance used by RQ (Redis Queue) to manage job distribution (e.g., ``redis://localhost:6379/0``).
* **MLFLOW_TRACKING_URI**: (string, URI) The URI for the MLflow Tracking server.
* **MLFLOW_S3_ENDPOINT_URL**: (string, URL) The endpoint for S3-compatible storage (e.g. MinIO) used by MLflow to store large artifacts.

.. _reference-workers-optional-configuration:

Optional Configuration
~~~~~~~~~~~~~~~~~~~~~~

* **OBJC_DISABLE_INITIALIZE_FORK_SAFETY**: (macOS Only) Set to ``YES`` to resolve stability issues with the Python ``fork()`` safety check when running RQ workers on Darwin kernels.

Pre-Configured Workers
-----------------------

There are four workers that are available as standalone Docker containers:

   * **tensorflow-cpu** - for systems with _no_ GPU present, contains Tensorflow and ART as dependencies
   * **tensorflow-gpu** - for GPU equipped systems, contains Tensorflow and ART as dependencies
   * **pytorch-cpu** - for systems with _no_ GPU present, contains PyTorch and ART as dependencies
   * **pytorch-gpu** - for GPU equipped systems, contains PyTorch and ART as dependencies

Creating queues with these names (case sensitive) will allow jobs to be run in these worker containers, as long as the corresponding worker is enabled.
Additionally, custom workers can be created which watch queues of other names and provide different environments for the jobs to run in, allowing for additional requirements and packages to be included.

.. admonition:: Learn More

   See :ref:`how-to-download-container-images` to learn more about downloading these workers as pre-built containers.

.. rst-class:: fancy-header header-seealso

See Also
--------
* :ref:`how-to-creating-custom-workers` - Instructions on creating custom workers
* :ref:`explanation-queues-and-workers` - Explanation on Queues and Workers
