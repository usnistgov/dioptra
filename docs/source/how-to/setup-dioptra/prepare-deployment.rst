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

.. _how-to-prepare-deployment:

Prepare Your Deployment
=======================

This guide explains how to create and configure a Dioptra deployment using the cruft template system.
After completing these steps, you will have a deployment folder ready to start.

Prerequisites
-------------

* Python 3.11+ virtual environment with the ``cruft`` package installed (``pip install cruft``)
* `Docker Engine <https://docs.docker.com/engine/install/>`__ and `Docker Compose <https://docs.docker.com/compose/install/>`__ installed
* :ref:`how-to-get-container-images` - Container images available (downloaded or built)
* A terminal with access to the deployment target directory

Deployment Setup
----------------

.. rst-class:: header-on-a-card header-steps

Step 1: Create the Deployment Directory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create the folder where you plan to keep your deployment and change into it so that it becomes your working directory.

.. code:: sh

   mkdir -p /path/to/deployments/folder
   cd /path/to/deployments/folder

.. rst-class:: header-on-a-card header-steps

Step 2: Apply the Template
~~~~~~~~~~~~~~~~~~~~~~~~~~

Run cruft to apply the Dioptra Deployment template. There are four different methods for configuring the deployment:

**Method 1: Interactive prompts for each variable**

.. code:: sh

   cruft create https://github.com/usnistgov/dioptra --checkout <branch-name> \
     --directory cookiecutter-templates/cookiecutter-dioptra-deployment

**Method 2: Use all default template values**

.. code:: sh

   cruft create https://github.com/usnistgov/dioptra --checkout <branch-name> \
     --directory cookiecutter-templates/cookiecutter-dioptra-deployment --no-input

**Method 3: Use defaults except for specific values**

.. code:: sh

   cruft create https://github.com/usnistgov/dioptra --checkout <branch-name> \
     --directory cookiecutter-templates/cookiecutter-dioptra-deployment --no-input \
     --extra-context '{"datasets_directory": "~/datasets"}'

**Method 4: Use defaults except for values in a config file**

.. code:: sh

   cruft create https://github.com/usnistgov/dioptra --checkout <branch-name> \
     --directory cookiecutter-templates/cookiecutter-dioptra-deployment --no-input \
     --extra-context-file overrides.json

.. note::

   Replace ``<branch-name>`` with the Dioptra branch that matches your container images (e.g., ``main`` for releases, ``dev`` for development builds).

.. tip::

   If you make a mistake, press :kbd:`Ctrl+C` to interrupt cruft, remove any created folder, and start over.

.. rst-class:: header-on-a-card header-steps

Step 3: Configure Template Variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you selected Method 1 (interactive prompts), you will be asked to set configuration variables.
In most cases, the default value is appropriate.

Key variables include:

- **deployment_name:** A name to associate with the deployment (default: ``Dioptra deployment``)
- **container_registry:** Set to ``ghcr.io/usnistgov`` if using downloaded images, or leave empty for locally built images. See :ref:`how-to-get-container-images-registry-prefix` for details. (default: *empty*)
- **container_tag:** Should match the tags of your Dioptra container images (default: ``dev``)
- **nginx_server_name:** Domain name, IP address, or ``_`` for local deployments (default: ``dioptra.example.org``)
- **num_tensorflow_cpu_workers / num_pytorch_cpu_workers:** Number of CPU workers (default: ``1`` each)
- **datasets_directory:** Host directory to mount at ``/dioptra/data`` in workers (default: *empty*)

.. admonition:: Learn More

   See :ref:`reference-deployment-template` for complete descriptions of all template variables, including interactive prompt examples and non-interactive configuration methods.

.. rst-class:: header-on-a-card header-steps

Step 4: Initialize the Deployment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Run the initialization script to generate passwords, copy configuration files, and prepare the named volumes.

.. code:: sh

   cd dioptra-deployment  # Or your deployment folder name
   ./init-deployment.sh --branch <branch-name>

.. note::

   Replace ``<branch-name>`` with the Dioptra branch that matches your container images (e.g., ``main`` for releases, ``dev`` for development builds).

The script automates password generation, certificate bundling, volume preparation, Minio account setup, and built-in plugin syncing.

.. admonition:: Learn More

   See :ref:`reference-init-deployment-script` for complete command-line options and detailed examples.

.. rst-class:: header-on-a-card header-steps

Step 5: Start Dioptra
~~~~~~~~~~~~~~~~~~~~~

Start all Dioptra services:

.. code:: sh

   docker compose up -d

Once the containers are running, open your web browser and navigate to ``http://localhost/`` (or ``https://localhost/`` if SSL/TLS is enabled).

Verify all services are running:

.. code:: sh

   docker compose ps

.. admonition:: Learn More

   See :ref:`reference-deployment-commands` for the full suite of commands to manage your deployment (stop, restart, view logs, etc.).

.. rst-class:: header-on-a-card header-seealso

See Also
--------

**How-To Guides:**

* :ref:`how-to-update-deployment` - Update your deployment when new template versions are available

**Reference Documentation:**

* :ref:`reference-deployment-template` - Complete template variable descriptions
* :ref:`reference-deployment-folder` - Deployment folder structure and file descriptions
* :ref:`reference-init-deployment-script` - Initialization script options

**Optional Customizations:**

* :ref:`how-to-using-docker-compose-overrides` - Use override files for customizations
* :ref:`how-to-data-mounts` - Mount data volumes into worker containers
* :ref:`how-to-gpu-enabled-workers` - Configure GPU workers
* :ref:`how-to-adding-certificates` - Add custom CA certificates
* :ref:`how-to-enabling-ssl-tls` - Enable SSL/TLS encryption
* :ref:`how-to-integrating-custom-containers` - Add custom containers
