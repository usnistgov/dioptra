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

.. _reference-dioptra-worker-v1:

dioptra-worker-v1 Reference
===========================

``dioptra-worker-v1`` is the command that starts a Dioptra worker process.
It is provided by the ``dioptra-platform`` Python package and wraps the `RQ worker CLI <https://python-rq.org/docs/workers/>`__.
The process polls a Redis queue for jobs submitted through the Dioptra REST API and executes them.

.. contents:: Table of Contents
   :local:
   :depth: 1

Environment Variables
---------------------

Required
~~~~~~~~

The process checks for these variables at startup and exits immediately if any are missing.

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

Optional
~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Variable
     - Description
   * - ``DIOPTRA_RQ_WORKER_LOG_AS_JSON``
     - Enable JSON-formatted log output. Unset by default (disabled).
   * - ``DIOPTRA_RQ_WORKER_LOG_LEVEL``
     - Logging level (``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``). Defaults to ``INFO``.

Command-Line Arguments
----------------------

``dioptra-worker-v1`` accepts the same arguments as the ``rq worker`` command.
The two relevant arguments for starting a worker are:

``-u, --url <redis-uri>``
   URL describing the Redis connection (e.g., ``redis://localhost:6379/0``).
   Defaults to ``redis://localhost:6379/0`` if not provided.

``QUEUES``
   One or more queue names to poll, passed as positional arguments.
   At least one queue name is required.

Usage
-----

.. code:: sh

   dioptra-worker-v1 --url redis://localhost:6379/0 tensorflow_cpu

.. rst-class:: header-on-a-card header-seealso

See Also
--------

* :ref:`reference-worker-container-requirements` -- Container-level requirements for deploying a worker
* :ref:`reference-custom-worker-template` -- Cookiecutter template that wraps this command in an entrypoint script
