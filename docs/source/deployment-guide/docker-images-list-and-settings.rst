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

.. _deployment-guide-docker-images-list-and-settings:

Docker Images List and Settings
===============================

.. include:: /_glossary_note.rst

Nginx
-----

Nginx is an open-source web server that serves as a reverse proxy in the Testbed architecture.
It receives :term:`HTTP` requests originating from outside the Testbed network and routes the traffic to the appropriate service.

Command
~~~~~~~

.. code-block:: none

   Usage: docker run --rm -it IMAGE [OPTIONS]

.. rubric:: Options

--ai-lab-host            AI Lab Service host (default: ``'restapi'``)
--ai-lab-port            AI Lab Service port (default: ``'5000'``)
--mlflow-tracking-host   AI Lab Service host (default: ``'mlflow-tracking'``)
--mlflow-tracking-port   AI Lab Service port (default: ``'5000'``)
--nginx-lab-port         Nginx listening port (default: ``'30080'``)
--nginx-mlflow-port      Nginx listening port (default: ``'35000'``)

MLFlow Tracking
---------------

The MLFlow Tracking service is an :term:`API` and UI for logging and querying parameters, metrics, and output files when running your experiments.

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

:kbd:`AWS_ACCESS_KEY_ID`

The username for accessing S3 storage.
Must match ``MINIO_ROOT_USER`` set for the Minio image.

:kbd:`AWS_SECRET_ACCESS_KEY`

The password for accessing S3 storage.
Must match ``MINIO_ROOT_PASSWORD`` set for the Minio image.

:kbd:`MLFLOW_S3_ENDPOINT_URL`

The URL endpoint for accessing the S3 storage.

Command
~~~~~~~

.. code-block:: none

   Usage: docker run --rm -it IMAGE [OPTIONS]

.. rubric:: Options

--conda-env               Conda environment (default: ``'dioptra'``)
--backend-store-uri       |URI| to which to persist experiment and run data. Acceptable |URI|\s are SQLAlchemy-compatible database connection strings (e.g. 'sqlite:///path/to/file.db') or local filesystem |URI|\s (e.g. ``'file:///absolute/path/to/directory'``). (default: ``'sqlite:////work/mlruns/mlflow-tracking.db'``)
--default-artifact-root   Local or S3 |URI| to store artifacts, for new experiments. Note that this flag does not impact already-created experiments. Default: Within file store, if a ``file:/`` |URI| is provided. If a sql backend is used, then this option is required. (default: ``'file:///work/artifacts'``)
--gunicorn-opts           Additional command line options forwarded to gunicorn processes. (no default)
--host                    The network address to listen on. Use 0.0.0.0 to bind to all addresses if you want to access the tracking server from other machines. (default: ``'0.0.0.0'``)
--port                    The port to listen on. (default: ``'5000'``)
--workers                 Number of gunicorn worker processes to handle requests. (default: ``'4'``)

REST API
--------

The :term:`REST` :term:`API` service is an :term:`API` for registering experiments and submitting jobs to the Testbed.

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

:kbd:`DIOPTRA_RESTAPI_DATABASE_URI`

The |URI| to use to connect to the :term:`REST` :term:`API` database.
(default: ``'$(pwd)/dioptra.db'``)

:kbd:`DIOPTRA_RESTAPI_ENV`

Selects a set of configurations for the Flask app to use.
Must be 'prod', 'dev', or 'test'.
(default: ``'prod'``)

:kbd:`DIOPTRA_DEPLOY_SECRET_KEY`

Secret key used by Flask to sign cookies.
While cookies are not used when accessing the :term:`REST` :term:`API`, per best practices this should still be changed to a long, random value.
(default: ``'deploy123'``)

:kbd:`AWS_ACCESS_KEY_ID`

The username for accessing S3 storage.
Must match ``MINIO_ROOT_USER`` set for the Minio image.

:kbd:`AWS_SECRET_ACCESS_KEY`

The password for accessing S3 storage.
Must match ``MINIO_ROOT_PASSWORD`` set for the Minio image.

:kbd:`MLFLOW_TRACKING_URI`

The |URI| to use for connecting to the MLFlow Tracking service.

:kbd:`MLFLOW_S3_ENDPOINT_URL`

The URL endpoint for accessing the S3 storage.

:kbd:`RQ_REDIS_URI`

The ``redis://`` |URI| to the Redis queue.

Command
~~~~~~~

.. code-block:: none

   Usage: docker run --rm -it IMAGE [OPTIONS]

.. rubric:: Options

--app-module       Application module (default: ``'wsgi:app'``)
--backend          Server backend (default: ``'gunicorn'``)
--conda-env        Conda environment (default: ``'dioptra'``)
--gunicorn-module  Python module used to start Gunicorn WSGI server (default: ``'dioptra.restapi.cli.gunicorn'``)

Workers (PyTorch/Tensorflow)
----------------------------

A Testbed Worker is a managed process within a Docker container that watches one or more Redis Queues for new jobs to handle.
The Testbed Workers come in different flavors, with each one provisioned to support running jobs for different types of machine learning libraries.

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

:kbd:`DIOPTRA_PLUGIN_DIR`

Directory to use for syncing the task plugins.
(default: ``'/work/plugins'``)

:kbd:`DIOPTRA_PLUGINS_S3_URI`

The S3 |URI| to the directory containing the builtin plugins

:kbd:`DIOPTRA_RESTAPI_DATABASE_URI`

The |URI| to use to connect to the :term:`REST` :term:`API` database.
(default: ``'$(pwd)/dioptra.db'``)

:kbd:`AWS_ACCESS_KEY_ID`

The username for accessing S3 storage.
Must match ``MINIO_ROOT_USER`` set for the Minio image.

:kbd:`AWS_SECRET_ACCESS_KEY`

The password for accessing S3 storage.
Must match ``MINIO_ROOT_PASSWORD`` set for the Minio image.

:kbd:`MLFLOW_TRACKING_URI`

The |URI| to use for connecting to the MLFlow Tracking service.

:kbd:`MLFLOW_S3_ENDPOINT_URL`

The URL endpoint for accessing the S3 storage.

:kbd:`RQ_REDIS_URI`

The ``redis://`` |URI| to the Redis queue.

Command
~~~~~~~

.. code-block:: none

   Usage: docker run --rm -it IMAGE [OPTIONS] [ARGS]...

.. rubric:: Positional Arguments

:kbd:`...`

Queues to watch

.. rubric:: Options

--conda-env         Conda environment (default: ``'dioptra'``)
--results-ttl       Job results will be kept for this number of seconds (default: ``'500'``)
--rq-worker-module  Python module used to start the RQ Worker (default: ``'dioptra.rq.cli.rq'``)

Minio
-----

**Vendor image:** https://hub.docker.com/r/minio/minio/

The Minio service provides distributed, S3-compatible storage for the Testbed.

Command
~~~~~~~

.. code-block:: none

   Usage: docker run --rm -it IMAGE server [ARGS]...

.. rubric:: Positional Arguments

:kbd:`...`

A list of paths to data storage locations.
For a single machine deployment, the path should point to a bind mounted or docker volume directory, e.g. ``/data``.
For a distributed deployment, pass a list of URLs instead, e.g. ``http://minio{1...4}/data{1...2}``.
The ellipses syntax ``{1...4}`` expands into a list of URLs at runtime.

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

:kbd:`MINIO_ROOT_USER`

Sets the username for logging into the Minio deployment.

:kbd:`MINIO_ROOT_PASSWORD`

Sets the password for logging into the Minio deployment.

Redis
-----

**Vendor image:** https://hub.docker.com/_/redis

The Redis service is a fast in-memory database that is leveraged as a centralized queue to delegate jobs to the Testbed Workers.

Command
~~~~~~~

.. code-block:: none

   Usage: docker run --rm -it IMAGE redis-server [OPTIONS]

.. rubric:: Options

--appendonly       Persist data using an append only file. Accepts ``'yes'`` or ``'no'``. (default: ``'no'``)
--appendfilename   The name of the append only file. (default: ``'appendonly.aof'``)

.. Aliases

.. |URI| replace:: :term:`URI`
