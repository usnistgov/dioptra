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

.. _how-to-uninstall-dioptra:

Uninstall Dioptra
=================

This guide explains how to remove a Dioptra deployment by hand, without
using the ``dioptra-platform`` CLI. Use this if the CLI is unavailable or if
a deployment was created outside the CLI.

If the CLI is available, prefer :ref:`how-to-cli-uninstall-clean-deployments`, which performs
these steps for you.

.. warning::

   These steps permanently delete deployment data, including databases and
   artifacts. Make sure you have backed up anything you need before proceeding.

Overview
--------

A Dioptra deployment consists of:

- A **deployment directory** containing ``docker-compose.yml``, an
  ``.env`` file, and supporting configuration.
- Running **containers** defined by that compose file.
- Docker **volumes** holding persistent data.
- A Docker **network** connecting the services.
- Container **images** pulled from the registry.
- An entry in the CLI's **deployment registry** (only if installed via the
  CLI).

Removing a deployment by hand means tearing down each of these.

Step 1: Locate the deployment directory
---------------------------------------

Deployments created by the CLI live under::

   ~/.config/dioptra-platform/deployments/<deployment-name>

If you installed to a custom location, use that path instead. The rest of
this guide assumes you run commands from inside the deployment directory:

.. code-block:: console

   $ cd ~/.config/dioptra-platform/deployments/<deployment-name>

Step 2: Stop and remove the containers
--------------------------------------

From the deployment directory, bring down the stack. This stops and
removes the containers and the deployment's network:

.. code-block:: console

   $ docker compose down --remove-orphans

If your environment uses the legacy standalone Compose, substitute
``docker-compose`` for ``docker compose``.

To also remove the deployment's volumes in the same step, add ``-v``:

.. code-block:: console

   $ docker compose down --remove-orphans -v

If you use ``-v`` here, you can skip Step 4.

.. note::

   ``docker compose down`` only works if ``docker-compose.yml`` is still
   present and valid. If the deployment directory was already deleted, skip
   to Step 4 to remove resources directly.

Step 3: Remove the deployment directory
---------------------------------------

.. code-block:: console

   $ cd ~
   $ rm -rf ~/.config/dioptra-platform/deployments/<deployment-name>

Step 4: Remove leftover volumes
-------------------------------

If you did not use ``-v`` in Step 2, or if the compose file was already
gone, remove the volumes directly.

First, list the deployment's volumes. Deployment volumes are prefixed with
the deployment's directory name:

.. code-block:: console

   $ docker volume ls --filter "name=<deployment-name>"

Review the list, then remove them:

.. code-block:: console

   $ docker volume rm <volume-name> [<volume-name> ...]

To remove all volumes matching the deployment name at once:

.. code-block:: console

   $ docker volume ls --filter "name=<deployment-name>" -q | xargs docker volume rm

.. warning::

   Check the list before removing. The name filter matches substrings, so
   confirm every listed volume belongs to the deployment you intend to
   remove.

Step 5: Remove the network
--------------------------

If ``docker compose down`` in Step 2 did not remove the network (for
example, because the compose file was missing), remove it directly:

.. code-block:: console

   $ docker network ls --filter "name=<deployment-name>"
   $ docker network rm <network-name>

Step 6: Remove the images (optional)
------------------------------------

Images are shared across deployments and are not deleted by default, so
that reinstalls are fast. Remove them only if you are sure no other
deployment needs them.

List the Dioptra images:

.. code-block:: console

   $ docker images "ghcr.io/usnistgov/dioptra/*"

Remove specific images:

.. code-block:: console

   $ docker image rm <image> [<image> ...]

Third-party images used by Dioptra (such as PostgreSQL, Redis, and MinIO) may 
be shared with other tools on your host. Remove these only if you are certain 
they are not needed elsewhere.

Step 7: Remove the registry entry (CLI installs only)
-----------------------------------------------------

If the deployment was installed with the CLI, an entry remains in the
deployment registry even after the directory is deleted. The registry is a
YAML file at::

   ~/.config/dioptra-platform/deployments.yml

Open it in a text editor and remove the block under ``deployments:`` that
matches your deployment name. For example, to remove ``my-deployment``,
delete its entry:

.. code-block:: yaml

   deployments:
     my-deployment:          # delete this key and everything indented under it
       path: ...
       image_tag: ...
       ...
     other-deployment:       # leave other deployments untouched
       ...

Save the file. If this was your only deployment, the file should contain:

.. code-block:: yaml

   deployments: {}

.. note::

   If you have the CLI available, ``dioptra-platform clean`` removes
   orphaned registry entries and their resources automatically, which is
   safer than editing the registry by hand.

Verify removal
--------------

Confirm nothing is left behind:

.. code-block:: console

   $ docker ps -a --filter "name=<deployment-name>"      # no containers
   $ docker volume ls --filter "name=<deployment-name>"  # no volumes
   $ docker network ls --filter "name=<deployment-name>" # no network
   $ ls ~/.config/dioptra-platform/deployments/          # directory gone

If all of these come back empty, the deployment is fully removed.