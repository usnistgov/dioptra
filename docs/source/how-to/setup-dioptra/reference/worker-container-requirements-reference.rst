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

.. _reference-worker-container-requirements:

Worker Container Requirements Reference
=======================================

This reference describes the minimal requirements for integrating a custom worker container into a Dioptra deployment using Docker Compose.
These are the requirements you must satisfy regardless of whether you use the Dioptra templates or build a worker container from scratch.

.. contents:: Table of Contents
   :local:
   :depth: 1

Environment Variables
---------------------

The worker container must provide all environment variables required by the ``dioptra-worker-v1`` process (see :ref:`reference-dioptra-worker-v1`) as well as credentials for S3-compatible artifact storage.

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Variable
     - Description
   * - ``MLFLOW_TRACKING_URI``
     - MLflow tracking server URL (consumed natively by MLflow).
   * - ``MLFLOW_S3_ENDPOINT_URL``
     - S3-compatible endpoint URL for artifact storage (consumed natively by MLflow).
   * - ``DIOPTRA_API``
     - Dioptra REST API base URL.
   * - ``DIOPTRA_WORKER_USERNAME``
     - Username for worker authentication with the REST API.
   * - ``DIOPTRA_WORKER_PASSWORD``
     - Password for worker authentication with the REST API.
   * - ``AWS_ACCESS_KEY_ID``
     - S3/MinIO access key (consumed by boto3/MLflow).
   * - ``AWS_SECRET_ACCESS_KEY``
     - S3/MinIO secret key (consumed by boto3/MLflow).

The first five variables are checked by ``dioptra-worker-v1`` at startup; the process exits immediately if any are missing.
``AWS_ACCESS_KEY_ID`` and ``AWS_SECRET_ACCESS_KEY`` are consumed by underlying libraries (boto3/MLflow) and must be present for artifact storage operations to succeed.

.. note::

   The Dioptra deployment template supplies these variables through a combination of env files and the ``docker-compose.yml`` ``environment:`` block.
   See :ref:`reference-deployment-template` and :ref:`reference-deployment-folder`.

Worker Process
--------------

The container must run the ``dioptra-worker-v1`` command, which is provided by the ``dioptra-platform`` Python package.
This can be done in one of two ways:

- **Directly in the Dockerfile** ``ENTRYPOINT`` **or** ``CMD``: invoke ``dioptra-worker-v1`` with the required ``--url`` and queue name arguments.
- **Via an entrypoint script**: create a shell script that handles service startup ordering and then invokes ``dioptra-worker-v1``.

The minimal invocation is:

.. code:: sh

   dioptra-worker-v1 --url <redis-uri> <queue-name>

See :ref:`reference-dioptra-worker-v1` for the full command-line reference.

The Dioptra provided workers and the :ref:`custom worker cookiecutter template <reference-custom-worker-template>` both use an entrypoint script that reads the Redis URI from the ``RQ_REDIS_URI`` environment variable, waits for dependent services to become reachable, and then starts the worker.
Queue names are passed as positional arguments through the ``command:`` section in docker-compose.

Network
-------

The worker container must join the ``dioptra`` Docker network to communicate with other Dioptra services (Redis, MinIO, REST API, MLflow Tracking).

.. code:: yaml

   services:
     custom-worker:
       # ...
       networks:
         - dioptra

.. rst-class:: header-on-a-card header-seealso

See Also
--------

* :ref:`reference-dioptra-worker-v1` -- ``dioptra-worker-v1`` process environment variables and arguments
* :ref:`how-to-integrating-custom-containers` -- Add the custom worker to your deployment
* :ref:`how-to-creating-custom-workers` -- Build a custom worker image
* :ref:`reference-custom-worker-template` -- Template files, entrypoint script, and health check details
* :ref:`reference-deployment-template` -- Deployment template configuration
* :ref:`reference-deployment-folder` -- Generated deployment files and env file descriptions
