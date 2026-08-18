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

.. _how-to-cli-uninstall-clean-deployments:

Uninstall and Clean Up
======================

This guide shows how to remove deployments and how to clean up resources from previous or incomplete installs.

Uninstall a Deployment
----------------------

.. code-block:: console

    $ dioptra-platform uninstall my-deployment

This stops the deployment and removes its containers (if running), deletes its data volumes and on disk directory, and unregisters it. By default, container images remain on disk so future installs are faster.

Add ``--yes`` to skip the confirmation prompt.

.. warning::

    Uninstalling permanently deletes a deployment's user data volumes.

Uninstall and Remove Images
---------------------------

To also remove images when uninstalling a deployment:

.. code-block:: console

    $ dioptra-platform uninstall my-deployment --remove-images

To additionally remove third-party images (PostgreSQL, Redis, and MinIO):

.. code-block:: console

    $ dioptra-platform uninstall my-deployment --remove-images --include-external

.. warning::

    Third party images may be shared with other tools that Dioptra doesn't know about. Removal may affect their operation.

Clean Up Orphaned Resources
---------------------------

If a deployment's installation directory is manually deleted, associated Docker resources (volumes, images, networks) are left behind. Such a deployment will show as ``missing`` in the listing:

.. code-block:: console

    $ dioptra-platform list

To find and remove these orphaned resources:

.. code-block:: console

    $ dioptra-platform clean

Clean compares known Dioptra resources against those claimed by any installed deployment(s). A resource not claimed by any deployment is considered orphaned and a candidate for removal. Clean prints a list of all such resources and prompts for confirmation before removal.

To additionally remove orphaned third-party images:

.. code-block:: console

    $ dioptra-platform clean --include-external

.. warning::

    Third party images may be shared with other tools that Dioptra doesn't know about. Removal may affect their operation.