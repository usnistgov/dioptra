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

.. _how-to-adding-certificates:

Add Custom CA Certificates
==========================

This guide explains how to add custom Certificate Authority (CA) certificates to your Dioptra deployment. This is necessary when operating in environments with internal certificate authorities or when connecting to services that use certificates signed by non-public CAs.

Prerequisites
-------------

* :ref:`how-to-prepare-deployment` - A configured Dioptra deployment (before running ``init-deployment.sh``)
* CA certificate file(s) in PEM format

Adding Certificates
-------------------

.. rst-class:: header-on-a-card header-steps

Step 1: Prepare Certificate Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ensure your CA certificate files meet the following requirements:

- **PEM format**: Each certificate must be encoded using base64 and stored in a plain text file between ``-----BEGIN CERTIFICATE-----`` and ``-----END CERTIFICATE-----`` lines.

- **One certificate per file**: Each file should contain only one CA certificate. Do not bundle multiple CA certificates together.

- **File extension**: Each file **must** have the ``.crt`` extension (e.g., ``ca-root.crt``). If your certificate has a different extension (such as ``.pem``), rename it to ``.crt``.

.. rst-class:: header-on-a-card header-steps

Step 2: Copy Certificates to the Deployment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Copy your CA certificate files into the ``ssl/ca-certificates/`` folder in your deployment directory:

.. code:: sh

   cp /path/to/your/ca-certificate.crt ./ssl/ca-certificates/

You can add multiple CA certificates by copying additional files:

.. code:: sh

   cp /path/to/another-ca.crt ./ssl/ca-certificates/

.. rst-class:: header-on-a-card header-steps

Step 3: Run the Initialization Script
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The deployment initialization scripts will automatically look for extra CA certificates in the ``ssl/ca-certificates/`` folder and copy and bundle them into named volumes so they are available at runtime.

Run the initialization script:

.. code:: sh

   ./init-deployment.sh --branch <branch-name>

.. note::

   Replace ``<branch-name>`` with the Dioptra branch that matches your container images (e.g., ``main`` for releases, ``dev`` for development builds).

The script will process all ``.crt`` files in the ``ssl/ca-certificates/`` folder and make them available to all containers.

.. admonition:: Learn More

   See the ``README.md`` file in the ``ssl/ca-certificates/`` folder for additional details.

.. rst-class:: header-on-a-card header-seealso

See Also
--------

* :ref:`how-to-enabling-ssl-tls` - Enable SSL/TLS for NGINX and Postgres
* :ref:`how-to-prepare-deployment` - Full deployment customization
