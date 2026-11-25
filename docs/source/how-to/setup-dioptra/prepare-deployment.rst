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

This guide explains how to create, configure, and start a Dioptra deployment.

Prerequisites
-------------

* Python 3.11+ virtual environment with the ``cruft`` package installed (``pip install cruft``)
* `Docker Engine <https://docs.docker.com/engine/install/>`__ and `Docker Compose <https://docs.docker.com/compose/install/>`__ installed
* Dioptra container images, downloaded or built following :ref:`how-to-get-container-images`.
* Permission to create and manage the deployment directory.
* A POSIX deployment environment with the :ref:`required filesystem support <reference-init-deployment-requirements>`

Deployment Setup
----------------

.. rst-class:: header-on-a-card header-steps

Step 1: Create the Deployment Directory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create the directory where you plan to keep your deployment and change into it:

.. code:: sh

   mkdir -p "DEPLOYMENTS_DIRECTORY"
   cd "DEPLOYMENTS_DIRECTORY"

Replace ``DEPLOYMENTS_DIRECTORY`` with the path to your deployment parent directory.

.. rst-class:: header-on-a-card header-steps

Step 2: Apply the Template
~~~~~~~~~~~~~~~~~~~~~~~~~~

Run cruft to apply the Dioptra Deployment template. There are four different methods for configuring the deployment:

**Method 1: Interactive prompts for each variable**

.. code:: sh

   cruft create https://github.com/usnistgov/dioptra --checkout BRANCH_NAME \
     --directory cookiecutter-templates/cookiecutter-dioptra-deployment

**Method 2: Use all default template values**

.. code:: sh

   cruft create https://github.com/usnistgov/dioptra --checkout BRANCH_NAME \
     --directory cookiecutter-templates/cookiecutter-dioptra-deployment --no-input

**Method 3: Use defaults except for specific values**

.. code:: sh

   cruft create https://github.com/usnistgov/dioptra --checkout BRANCH_NAME \
     --directory cookiecutter-templates/cookiecutter-dioptra-deployment --no-input \
     --extra-context '{"datasets_directory": "~/datasets"}'

**Method 4: Use values from a config file**

.. code:: sh

   cruft create https://github.com/usnistgov/dioptra --checkout BRANCH_NAME \
     --directory cookiecutter-templates/cookiecutter-dioptra-deployment --no-input \
     --extra-context-file overrides.json

.. note::

   Replace ``BRANCH_NAME`` with the Dioptra branch that matches your container images (for example, ``main`` for releases or ``dev`` for development builds).

.. tip::

   If you make a mistake, press :kbd:`Ctrl+C` to interrupt cruft, remove any created folder, and start over.

.. rst-class:: header-on-a-card header-steps

Step 3: Configure Template Variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you selected Method 1, enter the configuration variables at the prompts.
You can accept the defaults when they fit your environment.

Key variables include:

- **deployment_name:** A name to associate with the deployment (default: ``Dioptra deployment``)
- **container_registry:** Registry prefix for Dioptra container images. Leave as default for downloaded images, or set to empty for locally built images. See :ref:`how-to-get-container-images-registry-prefix` for details. (default: ``ghcr.io/usnistgov``)
- **container_tag:** Should match the tags of your Dioptra container images (default: ``1.2.4``)
- **nginx_server_name:** Hostname or IP address used to access Dioptra (default: ``localhost``). Change it if you will use a different hostname or IP address.
- **num_tensorflow_cpu_workers / num_pytorch_cpu_workers:** Number of CPU workers (default: ``1`` each)
- **datasets_directory:** Host directory to mount at ``/dioptra/data`` in workers (default: *empty*)

.. admonition:: Learn More

   See :ref:`reference-deployment-template` for complete descriptions of all template variables, including interactive prompt examples and non-interactive configuration methods.

.. rst-class:: header-on-a-card header-steps

Step 4: Initialize the Deployment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Change into the rendered deployment directory, using its actual name:

.. code:: sh

   cd dioptra-deployment

If you want to use your own server certificates, follow :ref:`how-to-enabling-ssl-tls` before initialization.

If you are rerunning initialization, tear down the existing deployment first:

.. code:: sh

   docker compose down

Keep the named volumes by omitting ``--volumes``.
Stopped containers must also be removed before initialization.

.. note::

   When running initialization inside a developer container, HTTPS verification may fail because the SSL manager cannot reach nginx at the default address.
   See :ref:`Reaching nginx from a developer container <how-to-compose-overrides-nginx-connection>` to configure the connection address.

Run the initializer as the user who owns the deployment files, using the branch that matches your container images:

.. code:: sh

   ./init-deployment.sh --branch BRANCH_NAME

.. note::

   Replace ``BRANCH_NAME`` with the Dioptra branch that matches your container images (for example, ``main`` for releases or ``dev`` for development builds).

.. admonition:: Learn More

   See :ref:`reference-init-deployment-script` for complete command-line options and detailed examples.

.. rst-class:: header-on-a-card header-steps

Step 5: Save Certificate Details and Configure Trust
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Wait for initialization to finish successfully.
The initializer starts services for HTTPS verification and worker registration, then tears them down while retaining deployment data.
Save the reported HTTPS address, public CA certificate path, and SHA-256 fingerprint for configuring browser trust.

If initialization reports an incomplete or empty credential set, follow :ref:`how-to-recover-deployment-credentials` before continuing.
If it reports an interrupted certificate operation, follow :ref:`how-to-recover-certificate-operation`.

Retain a protected backup of the :ref:`certificate files and installation state <reference-deployment-certificate-backups>`.

If your browser does not already trust the deployment's CA, complete Steps B1–B3 in the :ref:`workstation instructions <how-to-trust-public-issuer>` to obtain, verify, and import the CA certificate.

.. rst-class:: header-on-a-card header-steps

Step 6: Start Dioptra
~~~~~~~~~~~~~~~~~~~~~

Start all Dioptra services:

.. code:: sh

   docker compose up -d

Open the HTTPS address reported by initialization, such as ``https://localhost/``.

Verify all services are running:

.. code:: sh

   docker compose ps

.. admonition:: Learn More

   See :ref:`reference-deployment-commands` for the full suite of commands to manage your deployment (stop, restart, view logs, etc.).

Next Steps
------------

To test that Dioptra is working, consider progressing through the :ref:`Hello World Tutorial<tutorial-hello-world-in-dioptra>`.


.. rst-class:: header-on-a-card header-seealso

See Also
--------

**How-To Guides:**

* :ref:`how-to-update-deployment` - Update your deployment when new template versions are available
* :ref:`how-to-replace-deployment-certificates` - Replace certificates before expiry

**Reference Documentation:**

* :ref:`reference-deployment-template` - Complete template variable descriptions
* :ref:`reference-deployment-folder` - Deployment folder structure and file descriptions
* :ref:`reference-init-deployment-script` - Initialization script options

**Optional Customizations:**

* :ref:`how-to-using-docker-compose-overrides` - Use override files for customizations
* :ref:`how-to-data-mounts` - Mount data volumes into worker containers
* :ref:`how-to-gpu-enabled-workers` - Configure GPU workers
* :ref:`how-to-adding-certificates` - Configure deployment and workstation certificate trust
* :ref:`how-to-enabling-ssl-tls` - Supply API or nginx certificates
* :ref:`how-to-integrating-custom-containers` - Add custom containers
