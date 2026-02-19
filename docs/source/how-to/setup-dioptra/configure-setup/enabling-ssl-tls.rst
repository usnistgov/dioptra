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

.. _how-to-enabling-ssl-tls:

Enable SSL/TLS in NGINX and Postgres
====================================

This guide explains how to enable SSL/TLS encryption for the NGINX reverse proxy and PostgreSQL database services in your Dioptra deployment.

Prerequisites
-------------

* :ref:`how-to-prepare-deployment` - A configured Dioptra deployment (before running ``init-deployment.sh``)
* :ref:`how-to-using-docker-compose-overrides` - Override file created
* SSL certificate and private key files for each service you want to secure
* (Optional) :ref:`how-to-adding-certificates` - If using an internal CA

SSL/TLS Configuration
---------------------

.. rst-class:: header-on-a-card header-steps

Step 1: Obtain Certificate Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You will need a server certificate (``server.crt``) and private key (``server.key``) for each service.
These can be:

- Obtained from a certificate authority (CA)
- Generated using Let's Encrypt
- Self-signed certificates (for testing only)

.. rst-class:: header-on-a-card header-steps

Step 2: Copy Certificates to the Deployment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The certificate and key files **must** be named ``server.crt`` and ``server.key`` when copying them to the deployment directories.

**For NGINX:**

.. code:: sh

   cp /path/to/your/nginx-certificate.crt ./ssl/nginx/server.crt
   cp /path/to/your/nginx-private-key.key ./ssl/nginx/server.key

**For Postgres:**

.. code:: sh

   cp /path/to/your/db-certificate.crt ./ssl/db/server.crt
   cp /path/to/your/db-private-key.key ./ssl/db/server.key

You can use different certificate-key pairs for each service.

.. rst-class:: header-on-a-card header-steps

Step 3: Configure NGINX for SSL/TLS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you are enabling SSL/TLS in NGINX, add the SSL port and update the health check in ``docker-compose.override.yml``.

Open ``docker-compose.override.yml`` and add the following configuration for the NGINX service:

.. code:: yaml

   services:
     <deployment-name>-nginx:
       healthcheck:
         test:
           [
             "CMD",
             "/usr/local/bin/healthcheck.sh",
             "http://localhost:30080",
             "https://localhost:30443",
             "https://localhost:35000",
             "https://localhost:35050/login",
             "https://localhost:39000",
             "https://localhost:39001",
           ]
       ports:
         - "127.0.0.1:443:30443/tcp"

.. note::

   Replace ``<deployment-name>`` with your deployment's slugified name (default: ``dioptra-deployment``).

.. note::

   The ``ports:`` list in the override file **appends** to the existing ports in ``docker-compose.yml``.
   You only need to specify the new HTTPS port (443:30443).
   The ``healthcheck:`` configuration **replaces** the existing health check to use HTTPS endpoints.

.. rst-class:: header-on-a-card header-steps

Step 4: Run the Initialization Script with SSL Flags
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Run the initialization script with the appropriate SSL flags:

**Enable NGINX SSL only:**

.. code:: sh

   ./init-deployment.sh --branch <branch-name> --enable-nginx-ssl

**Enable Postgres SSL only:**

.. code:: sh

   ./init-deployment.sh --branch <branch-name> --enable-postgres-ssl

**Enable both NGINX and Postgres SSL:**

.. code:: sh

   ./init-deployment.sh --branch <branch-name> --enable-nginx-ssl --enable-postgres-ssl

.. important::

   You must specify the ``--enable-nginx-ssl`` and ``--enable-postgres-ssl`` options **each time** you run the ``init-deployment.sh`` script.
   If you omit them on a subsequent run, SSL/TLS will be disabled for the services.

.. note::

   Replace ``<branch-name>`` with the Dioptra branch that matches your container images (e.g., ``main`` for releases, ``dev`` for development builds).

.. admonition:: Learn More

   See the ``README.md`` files in the ``ssl/db/`` and ``ssl/nginx/`` folders for additional details about certificate requirements.

.. rst-class:: header-on-a-card header-seealso

See Also
--------

* :ref:`how-to-using-docker-compose-overrides` - Docker Compose override file basics
* :ref:`how-to-adding-certificates` - Add custom CA certificates
* :ref:`how-to-prepare-deployment` - Full deployment customization
