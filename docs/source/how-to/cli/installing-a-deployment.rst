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

.. _how-to-cli-install-deployment:

Install a Deployment
====================

This guide shows how to install a new Dioptra deployment using the ``dioptra-platform`` CLI.

Prerequisites
-------------

- Docker must be installed and running.
- ``cosign`` must be installed for container image signature verification. If it is not installed, verification will be skipped.

Install With a Default Name
---------------------------

If no deployments currently exist, you can omit the deployment name and a default is used:

.. code-block:: console

    $ dioptra-platform install

The deployment is named ``default``.

Install With a Specific Name
----------------------------

Alternatively, you can install a deployment with a given name:

.. code-block:: console

    $ dioptra-platform install my-deployment

Choose the Container Images to Install
----------------------------------------

By default, the deployment will use container images that match the installed ``dioptra-platform`` version. To install a specific image version, use ``--image-tag``:

.. code-block:: console

    $ dioptra-platform install my-deployment --image-tag 1.1.0-2

Overwrite an Existing Deployment
--------------------------------

To reinstall over an existing deployment for a clean start, ``--force`` is required and the data volumes will be deleted. This is a destructive action and requires you to accept the prompt.

.. code-block:: console

    $ dioptra-platform install my-deployment --force

The confirmation prompt can be skipped by adding ``--yes``.

.. note::

    ``--force`` deletes deployment user data. A deployment's containers can be updated while preserving user data with :doc:`upgrade <updating-a-deployment>`.

Install a CA Certificate
------------------------

To add a CA certificate to a deployment's trust stores, add the ``--cert`` flag with a cert path when installing:

.. code-block:: console

    $ dioptra-platform install my-deployment --cert /path/to/cert.crt

The certificate must be a single cert PEM-format file.