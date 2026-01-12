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

.. _reference-deployment-commands:

Deployment Commands Reference
=============================

This reference provides quick lookup for common commands used to manage a running Dioptra deployment.

.. note::

   All commands should be run from within your deployment directory (e.g., ``dioptra-deployment/``).

.. seealso::

   :ref:`how-to-update-deployment` - Step-by-step guide for updating your deployment configuration.

Starting Dioptra
----------------

.. tab-set::

   .. tab-item:: Docker Compose

      Start all services in detached mode:

      .. code:: sh

         docker compose up -d

   .. tab-item:: systemd

      Install and start the systemd service (Linux only):

      .. code:: sh

         sudo cp ./systemd/dioptra.service /etc/systemd/system
         sudo systemctl start dioptra
         sudo systemctl enable dioptra  # Start on boot

Once started, access the frontend at ``http://localhost/`` (or ``https://localhost/`` if SSL/TLS is enabled).

Stopping Dioptra
----------------

.. tab-set::

   .. tab-item:: Docker Compose

      Stop all services (preserves data):

      .. code:: sh

         docker compose down

      Stop and delete all data:

      .. code:: sh

         docker compose down -v

      .. warning::

         The ``-v`` flag deletes all named volumes, including your database and stored artifacts.

   .. tab-item:: systemd

      Stop the service:

      .. code:: sh

         sudo systemctl stop dioptra

      Disable start on boot:

      .. code:: sh

         sudo systemctl disable dioptra

Checking Service Status
-----------------------

View status of all containers:

.. code:: sh

   docker compose ps

This shows running containers, health status, and exposed ports.

Viewing Logs
------------

**All services:**

.. code:: sh

   docker compose logs

**Specific service** (e.g., REST API):

.. code:: sh

   docker compose logs <deployment-name>-restapi

**Follow logs in real-time:**

.. code:: sh

   docker compose logs -f

Press :kbd:`Ctrl+C` to stop following.

**Limit to recent entries:**

.. code:: sh

   docker compose logs --tail=100

**Available service names:**

Service names are prefixed with your deployment name.
For example, if your deployment name is ``dioptra-deployment``, the REST API service would be ``dioptra-deployment-restapi``.

- ``<deployment-name>-restapi`` - Dioptra REST API
- ``<deployment-name>-nginx`` - NGINX reverse proxy
- ``<deployment-name>-db`` - PostgreSQL database
- ``<deployment-name>-dbadmin`` - pgAdmin4 database administration
- ``<deployment-name>-redis`` - Redis queue
- ``<deployment-name>-minio`` - Minio S3 storage
- ``<deployment-name>-mlflow-tracking`` - MLflow tracking server
- ``<deployment-name>-tfcpu-*``, ``<deployment-name>-tfgpu-*`` - TensorFlow workers
- ``<deployment-name>-pytorchcpu-*``, ``<deployment-name>-pytorchgpu-*`` - PyTorch workers

.. note::

   Replace ``<deployment-name>`` with the slugified version of your deployment name (e.g., ``dioptra-deployment`` for the default).
   Run ``docker compose ps`` to see the exact service names for your deployment.

Restarting Services
-------------------

.. tab-set::

   .. tab-item:: Docker Compose

      Restart all services:

      .. code:: sh

         docker compose restart

      Restart a specific service:

      .. code:: sh

         docker compose restart <deployment-name>-restapi

   .. tab-item:: systemd

      Restart all services:

      .. code:: sh

         sudo systemctl restart dioptra

.. seealso::

   * :ref:`how-to-update-deployment` - Apply configuration changes
   * :ref:`reference-init-deployment-script` - Initialization script options
   * `Docker Compose CLI reference <https://docs.docker.com/compose/reference/>`__ - Full command documentation
