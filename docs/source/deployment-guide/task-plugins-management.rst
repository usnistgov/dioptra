.. NOTICE
..
.. This software (or technical data) was produced for the U. S. Government under
.. contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
.. 52.227-14, Alt. IV (DEC 2007)
..
.. © 2021 The MITRE Corporation.

.. _deployment-guide-task-plugins-management:

Task Plugins Management
=======================

There are two tasks associated with managing the task plugins on a Testbed deployment, which are reviewed in the sections below.

Initial Configuration
---------------------

.. note::

   We assume that, for the purposes of this section, you have already provisioned and configured the rest of Testbed environment.
   Readers that have not are referred to the :doc:`Single Machine Deployment guide <single-machine-deployment>`.

Configuring the task plugins system is a two part process,

#. Create an S3 bucket for the plugins and sync them to it
#. Set the ``AI_PLUGINS_S3_URI`` variable for all the Testbed Workers to match the location of the freshly synchronized plugins.

For the purposes of this guide, let's assume the following,

- We want to sync the plugins to an S3 bucket named `plugins`
- The latest version of the ``securingai_builtins`` task plugins are available at the directory ``/path/to/task-plugins``
- The ``docker-compose.yml`` file we are using to manage our deployment is in the directory ``/etc/securing-ai/lab_deployment``
- We need root access in order to interact with Docker

With these assumptions, we run ``sudo -s`` to become root and navigate to the ``/etc/securing-ai/lab_deployment`` directory.
We now use a `securing-ai/restapi` container to create the `plugins` bucket and upload the task plugins,

.. code-block:: sh

   # Start a bash shell in a restapi container
   # NOTE: REPLACE /path/to/task-plugins WITH ABSOLUTE PATH TO THE TESTBED REPO'S task-plugins DIRECTORY
   docker-compose run --rm --entrypoint "/bin/bash" -u $(id -u):$(id -g) \
     -v /path/to/task-plugins:/task-plugins restapi

   # Run inside the container
   s3-mb.sh --endpoint-url ${MLFLOW_S3_ENDPOINT_URL} plugins
   s3-sync.sh --endpoint-url ${MLFLOW_S3_ENDPOINT_URL} --delete \
     /task-plugins/securingai_builtins s3://plugins/securingai_builtins

   # Exit the container
   exit

   # Teardown
   docker-compose down

To set the ``AI_PLUGINS_S3_URI`` environment variable for the Testbed Workers, open your ``docker-compose.yml`` file and add ``AI_PLUGINS_S3_URI: s3://plugins/securingai_builtins`` to each Worker's ``environment:`` block,

.. code-block:: yaml

   tfcpu-01:
     image: securing-ai/tensorflow2-cpu:latest
     # ...Truncated...
     environment:
       AI_PLUGINS_S3_URI: s3://plugins/securingai_builtins
       AI_RESTAPI_DATABASE_URI: sqlite:////work/data/securingai.db
       AI_RESTAPI_ENV: prod
     # ...Truncated...


Updating the Collection
-----------------------

To update the task plugins collection, all you need to do is synchronize the latest versions of the task plugins to the S3 bucket where they're stored.
Like before, we assume that,

- Our task plugins collection is stored in the folder ``s3://plugins/securingai_builtins``
- The newer versions of these plugins are in the directory ``/path/to/task-plugins/securingai_builtins``
- The ``docker-compose.yml`` file we are using to manage our deployment is in the directory ``/etc/securing-ai/lab_deployment``
- We need root access in order to interact with Docker

So, just as before, we run ``sudo -s`` to become root, navigate to the ``/etc/securing-ai/lab_deployment``, and perform the task plugins update,

.. code-block:: sh

   # NOTE: REPLACE /path/to/task-plugins WITH ABSOLUTE PATH TO THE TESTBED REPO'S task-plugins DIRECTORY
   docker-compose run --rm --entrypoint "/bin/bash" -u $(id -u):$(id -g) \
     -v /path/to/task-plugins:/task-plugins restapi -c '/usr/local/bin/s3-sync.sh \
     --endpoint-url ${MLFLOW_S3_ENDPOINT_URL} --delete \
     /task-plugins/securingai_builtins s3://plugins/securingai_builtins'

   # Teardown
   docker-compose down
