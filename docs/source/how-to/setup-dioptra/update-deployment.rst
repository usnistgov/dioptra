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

.. _how-to-update-deployment:

Update Your Deployment
======================

This guide shows you how to apply configuration changes to your Dioptra deployment, whether from upstream template updates or local override file modifications.

Prerequisites
-------------

* :ref:`how-to-prepare-deployment` - An initialized Dioptra deployment
* Python 3.11+ virtual environment with the ``cruft`` package installed (``pip install cruft``)
* Terminal access to the deployment directory

.. seealso::

   For basic commands (start, stop, logs, restart), see :ref:`reference-deployment-commands`.

Overview
--------

Choose the appropriate option based on what you need to update:

**Option A: Apply Template Updates** - Use this when:

* A new version of the Dioptra deployment template is available
* You need to change template variables (e.g., number of workers, datasets directory)
* You want to pull in upstream fixes or improvements

**Option B: Apply Override File Changes** - Use this when:

* You only modified ``docker-compose.override.yml``
* No template updates are needed
* You're making local customizations (data mounts, GPU settings, custom containers)

Option A: Apply Template Updates
--------------------------------

Use this workflow when you need to fetch updates from the upstream Dioptra template or change template variables.

.. rst-class:: header-on-a-card header-steps

Step A1: Stop the Running Services
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before updating, stop your running Dioptra services:

.. code:: sh

   docker compose down

.. rst-class:: header-on-a-card header-steps

Step A2: Fetch Template Updates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use ``cruft update`` to fetch the latest changes from the Dioptra deployment template:

.. code:: sh

   cruft update --checkout <branch-name>

This compares your local deployment against the upstream template and applies any updates.

**To update specific template variables at the same time:**

.. code:: sh

   cruft update --checkout <branch-name> \
     --variables-to-update '{ "datasets_directory": "/path/to/dioptra/data" }'

.. note::

   Replace ``<branch-name>`` with the Dioptra branch that matches your container images (e.g., ``main`` for releases, ``dev`` for development builds).

.. note::

   If there are conflicts between your local changes and template updates, cruft will prompt you to resolve them.

.. rst-class:: header-on-a-card header-steps

Step A3: Rerun the Initialization Script
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After updating the template, rerun ``init-deployment.sh`` to apply the changes:

.. code:: sh

   ./init-deployment.sh --branch <branch-name>

.. note::

   Replace ``<branch-name>`` with the Dioptra branch that matches your container images (e.g., ``main`` for releases, ``dev`` for development builds).

When rerunning the script on an already-initialized deployment, it will freeze during the Minio setup step because those configurations have already been applied.
Use the ``--skip-minio-setup`` option to skip this step:

.. code:: sh

   ./init-deployment.sh --branch <branch-name> --skip-minio-setup

.. important::

   If you previously enabled SSL/TLS, include those flags again:

   .. code:: sh

      ./init-deployment.sh --branch <branch-name> --enable-nginx-ssl --enable-postgres-ssl --skip-minio-setup

.. rst-class:: header-on-a-card header-steps

Step A4: Restart the Services
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Start the services to apply the updates:

.. code:: sh

   docker compose up -d

Verify all services are running:

.. code:: sh

   docker compose ps

Option B: Apply Override File Changes
-------------------------------------

Use this simpler workflow when you only modified the ``docker-compose.override.yml`` file and don't need to run ``cruft update``.

.. rst-class:: header-on-a-card header-steps

Step B1: Stop the Running Services
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Stop the current deployment:

.. code:: sh

   docker compose down

.. rst-class:: header-on-a-card header-steps

Step B2: Restart the Services
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Start the services again to pick up the new configuration:

.. code:: sh

   docker compose up -d

Docker Compose automatically merges your override file with the main ``docker-compose.yml`` on startup.

.. note::

   Some changes (like adding new volumes or changing environment variables) require a full stop/start cycle.
   A simple ``docker compose restart`` may not pick up all changes.

.. rst-class:: header-on-a-card header-seealso

See Also
--------

* :ref:`reference-deployment-commands` - Quick reference for start, stop, logs, and restart commands
* :ref:`reference-init-deployment-script` - Complete init-deployment.sh options
* :ref:`how-to-using-docker-compose-overrides` - Working with override files
* :ref:`reference-deployment-template` - Template variable descriptions
