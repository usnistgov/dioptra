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

.. _how-to-integrating-custom-containers:

Integrate Custom Containers
===========================

This guide explains how to integrate custom Docker containers into your Dioptra deployment, enabling the use of specialized worker images or additional services.

Prerequisites
-------------

* :ref:`how-to-prepare-deployment` - A configured Dioptra deployment
* :ref:`how-to-using-docker-compose-overrides` - Override file created
* Custom container image built and available locally or in a registry
* Understanding of Docker Compose file structure

Integration Steps
-----------------

.. rst-class:: header-on-a-card header-steps

Step 1: Prepare Your Custom Container
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ensure your custom container image is built and available. You can verify it with:

.. code:: sh

   docker images | grep custom-container

If your container is in a remote registry, ensure Docker has access to pull it.

.. rst-class:: header-on-a-card header-steps

Step 2: Add the Container Service Definition
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Open ``docker-compose.override.yml`` and add your custom container definition in the ``services:`` section.

Below is a template for a custom worker container that integrates with Dioptra's services:

.. code:: yaml

   services:
     custom-container:
       # Container image name and tag
       image: custom-container:dev

       # Restart policy
       restart: always

       # Hostname for internal DNS resolution
       hostname: custom-container

       # Health check configuration
       healthcheck:
         test:
           - CMD
           - /usr/local/bin/healthcheck.sh
         interval: 30s
         timeout: 60s
         retries: 5
         start_period: 80s

       # Environment variables for Dioptra integration
       environment:
         AWS_ACCESS_KEY_ID: ${WORKER_AWS_ACCESS_KEY_ID}
         AWS_SECRET_ACCESS_KEY: ${WORKER_AWS_SECRET_ACCESS_KEY}
         DIOPTRA_WORKER_USERNAME: ${DIOPTRA_WORKER_USERNAME}
         DIOPTRA_WORKER_PASSWORD: ${DIOPTRA_WORKER_PASSWORD}

       # Wait for dependent services before starting
       command:
         - --wait-for
         - <deployment-name>-redis:6379
         - --wait-for
         - <deployment-name>-minio:9001
         - --wait-for
         - <deployment-name>-db:5432
         - --wait-for
         - <deployment-name>-mlflow-tracking:5000
         - --wait-for
         - <deployment-name>-restapi:5000
         - tensorflow-cpu

       # Environment files to load
       env_file:
         - ./envs/ca-certificates.env
         - ./envs/<deployment-name>-worker.env
         - ./envs/<deployment-name>-worker-cpu.env

       # Network to join
       networks:
         - dioptra

       # Volume mounts
       volumes:
         - "worker-ca-certificates:/usr/local/share/ca-certificates:rw"
         - "worker-etc-ssl:/etc/ssl:rw"
         - "<host-data-path>:/dioptra/data:ro"

.. note::

   Replace ``<deployment-name>`` with your deployment's slugified name (default: ``dioptra-deployment``) and ``<host-data-path>`` with the absolute path to your data directory.

.. seealso::

   See :ref:`reference-worker-container-requirements` for the complete list of required environment variables, process invocation, and network configuration for custom worker containers.

.. rst-class:: header-on-a-card header-steps

Step 3: Configure Environment and Volumes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Customize the container definition for your needs:

**Environment Variables:**
Add any additional environment variables your container needs in the ``environment:`` section.

**Volume Mounts:**
Add volume mounts to provide access to data or configuration files. See :ref:`how-to-data-mounts` for more details.

**GPU Support:**
If your container needs GPU access, add the GPU configuration. See :ref:`how-to-gpu-enabled-workers` for details.

.. rst-class:: header-on-a-card header-steps

Step 4: Start the Deployment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Apply your changes by starting or restarting the deployment:

.. code:: sh

   docker compose up -d

Verify your custom container is running:

.. code:: sh

   docker compose ps

Check the logs if needed:

.. code:: sh

   docker compose logs custom-container

.. rst-class:: header-on-a-card header-seealso

See Also
--------

* :ref:`reference-worker-container-requirements` - Worker container environment variables, process invocation, and network requirements
* :ref:`how-to-using-docker-compose-overrides` - Docker Compose override file basics
* :ref:`how-to-prepare-deployment` - Full deployment customization
* :ref:`how-to-data-mounts` - Mount data volumes into containers
* :ref:`how-to-gpu-enabled-workers` - Configure GPU support
* `Docker Compose specification <https://docs.docker.com/compose/compose-file/>`__ - Full reference for compose files
