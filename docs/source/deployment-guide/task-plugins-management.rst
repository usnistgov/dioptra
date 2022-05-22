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

.. _deployment-guide-task-plugins-management:

Task Plugins Management
=======================

.. include:: /_glossary_note.rst

There are two tasks associated with managing the task plugins on a Testbed deployment, which are reviewed in the sections below.

Initial Configuration
---------------------

.. note::

   We assume that, for the purposes of this section, you have already provisioned and configured the rest of the Testbed environment.
   Readers that have not are referred to the :doc:`Single Machine Deployment guide <single-machine-deployment>`.

Configuring the task plugins system is a two part process,

#. Create an S3 bucket for the plugins and sync them to it
#. Set the ``DIOPTRA_PLUGINS_S3_URI`` variable for all the Testbed Workers to match the location of the freshly synchronized plugins.

For the purposes of this guide, let's assume the following,

- We want to sync the plugins to an S3 bucket named `plugins`
- The latest version of the ``dioptra_builtins`` task plugins are available at the directory ``/path/to/task-plugins``
- The ``docker-compose.yml`` file we are using to manage our deployment is in the directory ``/etc/dioptra/lab_deployment``
- We need root access in order to interact with Docker

With these assumptions, we run ``sudo -s`` to become root and navigate to the ``/etc/dioptra/lab_deployment`` directory.
We now use a `dioptra/restapi` container to create the `plugins` bucket and upload the task plugins,

.. code-block:: sh

   # Start a bash shell in a restapi container
   # NOTE: REPLACE /path/to/task-plugins WITH ABSOLUTE PATH TO THE TESTBED REPO'S task-plugins DIRECTORY
   docker-compose run --rm --entrypoint "/bin/bash" -u $(id -u):$(id -g) \
     -v /path/to/task-plugins:/task-plugins restapi

   # Run inside the container
   s3-mb.sh --endpoint-url ${MLFLOW_S3_ENDPOINT_URL} plugins
   s3-sync.sh --endpoint-url ${MLFLOW_S3_ENDPOINT_URL} --delete \
     /task-plugins/dioptra_builtins s3://plugins/dioptra_builtins

   # Exit the container
   exit

   # Teardown
   docker-compose down

To set the ``DIOPTRA_PLUGINS_S3_URI`` environment variable for the Testbed Workers, open your ``docker-compose.yml`` file and add ``DIOPTRA_PLUGINS_S3_URI: s3://plugins/dioptra_builtins`` to each Worker's ``environment:`` block,

.. code-block:: yaml

   tfcpu-01:
     image: dioptra/tensorflow2-cpu:latest
     # ...Truncated...
     environment:
       DIOPTRA_PLUGINS_S3_URI: s3://plugins/dioptra_builtins
       DIOPTRA_RESTAPI_DATABASE_URI: sqlite:////work/data/dioptra.db
       DIOPTRA_RESTAPI_ENV: prod
     # ...Truncated...


Updating the Collection
-----------------------

To update the task plugins collection, all you need to do is synchronize the latest versions of the task plugins to the S3 bucket where they're stored.
Like before, we assume that,

- Our task plugins collection is stored in the folder ``s3://plugins/dioptra_builtins``
- The newer versions of these plugins are in the directory ``/path/to/task-plugins/dioptra_builtins``
- The ``docker-compose.yml`` file we are using to manage our deployment is in the directory ``/etc/dioptra/lab_deployment``
- We need root access in order to interact with Docker

So, just as before, we run ``sudo -s`` to become root, navigate to the ``/etc/dioptra/lab_deployment``, and perform the task plugins update,

.. code-block:: sh

   # NOTE: REPLACE /path/to/task-plugins WITH ABSOLUTE PATH TO THE TESTBED REPO'S task-plugins DIRECTORY
   docker-compose run --rm --entrypoint "/bin/bash" -u $(id -u):$(id -g) \
     -v /path/to/task-plugins:/task-plugins restapi -c '/usr/local/bin/s3-sync.sh \
     --endpoint-url ${MLFLOW_S3_ENDPOINT_URL} --delete \
     /task-plugins/dioptra_builtins s3://plugins/dioptra_builtins'

   # Teardown
   docker-compose down
