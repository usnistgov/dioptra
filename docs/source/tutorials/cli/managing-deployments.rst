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

.. _tutorial-installing-with-cli:

Deploying With the CLI
======================

This tutorial walks through installing, running, and uninstalling a Dioptra deployment from start to finish. 

This is meant as an introductory approach to deployment management using the ``dioptra-platform`` CLI. See the :doc:`How-To Guides </how-to/cli/index>` for more information on the actions performed here.

Prerequisites
-------------

Make sure Docker is installed and running. Check Docker availability with:

.. code-block:: console

    $ docker info

Step 1: Confirm No Deployments
------------------------------

After having installed Dioptra, no deployments exist yet.

.. code-block:: console

    $ dioptra-platform list
    No deployments found.

Step 2: Install a Deployment
----------------------------

Since no deployments exist, Dioptra will create a default deployment after running:

.. code-block:: console

    $ dioptra-platform install

Dioptra will:

1. Create the deployment configuration.
2. Verify Dioptra container image signatures.
3. Pull all necessary container images.
4. Run deployment initialization.

This may take several minutes or longer since Dioptra needs to download the container images. A success message will appear when the install is complete.

Step 3: See the New Deployment
------------------------------

List the deployments again:

.. code-block:: console

    $ dioptra-platform list

The new deployment named ``default`` with a ``stopped`` status should be displayed. This means the deployment is installed, but not yet running.

Step 4: Start the Deployment
----------------------------

.. code-block:: console

    $ dioptra-platform start

Since there is only one deployment, ``start`` can be run without specifying a deployment name.

Step 5: Check the Status
------------------------

.. code-block:: console

    $ dioptra-platform status --verbose

The status should now be ``running``. Adding the ``--verbose`` option here shows a detailed display about the deployment, including its volumes, networks, and images and their digests.

Step 6: Stop the Deployment
---------------------------

When finished, stop the deployment:

.. code-block:: console

    $ dioptra-platform stop

Data is preserved while stopped. After restarting a deployment, everything will remain the same as before running ``stop``.

Step 7: Uninstall the Deployment
--------------------------------

.. code-block:: console

    $ dioptra-platform uninstall

.. warning::

    Uninstalling a deployment deletes all data associated with it.

Enter ``y`` when prompted to confirm the uninstall.

Listing again will confirm that the uninstall was successful:

.. code-block:: console

    $ dioptra-platform list
    No deployments found.

See Also
--------

**How-To Guides:**

* The :doc:`How-To Guides </how-to/cli/index>` show how to install specific versions, update deployments, and manage multiple deployments.

**Reference Documentation:**

* The :doc:`CLI Reference </reference/cli-reference>` documents all available commands and options.