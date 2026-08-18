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

.. _how-to-cli-update-deployment:

Update a Deployment
===================

Dioptra distinguishes between two kinds of updates:

- **Container updates** - newer container images (security/dependency updates) running on the same Dioptra version. Applied with ``upgrade``, preserving your user data.
- **CLI and client updates** - a newer ``dioptra-platform`` package. Applied through ``pip``.

Check for Updates
-----------------

.. code-block:: console 

    $ dioptra-platform update my-deployment

This checks to see if newer container images or CLI/client package is available, without making any changes.

Apply a Container Update
------------------------

.. code-block:: console

    $ dioptra-platform upgrade my-deployment

This pulls down the newer images and recreates the containers. Your data volumes are preserved. If the deployment was stopped, it will use the new images the next time it is started. If it was previously running, the new images are immediately available for use in the updated deployment. If the pull fails, the deployment is rolled back to the previous state.

Use ``--yes`` to skip the confirmation prompt.

Update the CLI + Client
-----------------------

Container updates do not update the ``dioptra-platform`` installation. When ``update`` reports a newer package version, update ``dioptra-platform`` with:

.. code-block:: console

    $ pip install --upgrade dioptra-platform

Updating the CLI affects CLI behavior and future installs. Existing deployments will continue to run with their respective image versions.