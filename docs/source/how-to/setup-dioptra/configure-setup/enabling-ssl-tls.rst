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

Configure SSL/TLS Certificates
==============================

Dioptra generates certificates automatically during :ref:`deployment setup <how-to-prepare-deployment>`.
Use this guide to provide your own certificates for the API, nginx, or both before initializing the deployment.
For an already initialized deployment, follow :ref:`how-to-replace-deployment-certificates`.

Prerequisites
-------------

* A deployment directory created by following :ref:`how-to-prepare-deployment`, before running ``init-deployment.sh``.
* OpenSSL for inspecting certificate names and expiration dates.

Have these files ready for each service whose certificate you will provide:

* A PEM file containing your server certificate and any required intermediate certificates. Look for a download described as a **full certificate chain**, such as ``fullchain.pem``.
* The private key associated with that server certificate.
* The root certificate from your certificate authority (CA), which Dioptra uses to verify the server certificate.

See :ref:`reference-certificate-policy` for certificate requirements.

Certificate Setup
--------------------------

Run commands from the deployment root.

.. rst-class:: header-on-a-card header-steps

Step 1: Choose Which Certificates to Provide
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Open ``config/ssl.toml``.
Set ``source = "supplied"`` in ``[restapi]``, ``[nginx]``, or both, depending on which certificates you will provide.
List the corresponding root CA certificate in ``trust_files``.

For example, to let Dioptra generate the API certificate while you provide the nginx certificate, update these fields in the existing sections:

.. code:: toml

   [restapi]
   source = "generated"
   trust_files = []

   [nginx]
   source = "supplied"
   trust_files = ["ssl/ca-certificates/root-ca.crt"]

Leave ``source = "generated"`` for services whose certificates Dioptra will generate.
Keep the other settings unchanged.
See :ref:`reference-ssl-toml` for field definitions and path rules.

.. rst-class:: header-on-a-card header-steps

Step 2: Combine Separate Certificate Files (Optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you already have a full-chain PEM file, continue to :ref:`Step 3 <how-to-check-initial-certificate-files>`.

If your provider supplies the server certificate and intermediate certificates separately, combine them into one PEM file with the server certificate first:

.. code:: sh

   cat "SERVER_CERT_PATH" "INTERMEDIATE_CERTS_PATH" > server-chain.pem

Replace ``SERVER_CERT_PATH`` with the server certificate file and ``INTERMEDIATE_CERTS_PATH`` with the intermediate certificate file supplied by your provider.
Use the resulting ``server-chain.pem`` as ``CHAIN_PATH`` in the following steps.
If both services need combined files, use a different output filename for each, such as ``restapi-chain.pem`` and ``nginx-chain.pem``.

.. _how-to-check-initial-certificate-files:

.. rst-class:: header-on-a-card header-steps

Step 3: Check Certificate Names and Expiration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For each certificate you will provide, display the server certificate's names and expiration date:

.. code:: sh

   openssl x509 -in "CHAIN_PATH" -noout -subject -issuer -dates \
     -ext subjectAltName

Replace ``CHAIN_PATH`` with the path to your full-chain PEM file.
Check the Subject Alternative Name (SAN) entries for the service:

* For the API, check for its internal DNS name, ``<deployment-slug>-restapi``, such as ``dioptra-deployment-restapi``.
* For nginx, check for the DNS name or IP address in ``public.host`` in ``config/ssl.toml``. Confirm that this is the address you will use in your browser URL.

Also check for any additional names or addresses listed in the service's ``dns_sans`` and ``ip_sans`` settings.
DNS names must appear as DNS entries and IP addresses as IP address entries.
Check that the certificate's expiration date meets the :ref:`certificate requirements <reference-certificate-policy>`.

.. rst-class:: header-on-a-card header-steps

Step 4: Copy the Certificate Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Copy the files into the deployment directory.
For nginx, run:

.. code:: sh

   install -m 0644 "CHAIN_PATH" ssl/nginx/server.crt
   install -m 0600 "KEY_PATH" ssl/nginx/server.key
   install -m 0644 "ROOT_CA_PATH" ssl/ca-certificates/root-ca.crt

Replace ``CHAIN_PATH``, ``KEY_PATH`` and ``ROOT_CA_PATH`` with the paths to your full certificate chain, private key and root CA certificate.
The ``install`` command copies each file with the specified permissions, including owner-only access for the private key.
For the API, use ``ssl/restapi/server.crt`` and ``ssl/restapi/server.key`` as the first two destinations.
Use separate private keys for the API and nginx.

If the API and nginx use different root certificates, give each root certificate a separate filename in ``ssl/ca-certificates/``.
Check that each service's ``trust_files`` setting names its root certificate's destination, relative to the deployment directory.

.. rst-class:: header-on-a-card header-steps

Step 5: Prepare PostgreSQL Certificates (Optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you do not want TLS for PostgreSQL, skip this step and continue to :ref:`Step 6 <how-to-initialize-with-supplied-certificates>`.

Copy the PostgreSQL server certificate and its matching private key into the deployment directory:

.. code:: sh

   install -m 0644 "DB_CERT_PATH" ssl/db/server.crt
   install -m 0600 "DB_KEY_PATH" ssl/db/server.key

Replace ``DB_CERT_PATH`` with the path to the server certificate file, including any required intermediate certificates, and ``DB_KEY_PATH`` with the path to its private key.
See ``ssl/db/README.md`` in the deployment directory for certificate file requirements.

.. _how-to-initialize-with-supplied-certificates:

.. rst-class:: header-on-a-card header-steps

Step 6: Initialize the Deployment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Run the initializer.
If you provided PostgreSQL certificates in Step 5, add ``--enable-postgres-ssl`` to the following command.
Otherwise, omit that option.

.. code:: sh

   ./init-deployment.sh --branch BRANCH_NAME

Replace ``BRANCH_NAME`` with the Dioptra branch matching your container images.
If you enabled PostgreSQL TLS, include ``--enable-postgres-ssl`` each time you rerun the initializer.

Wait for initialization to report success before continuing.
If it reports an interrupted certificate operation, follow :ref:`how-to-recover-certificate-operation`.

.. rst-class:: header-on-a-card header-steps

Step 7: Check the Installed Certificates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Check the installed certificates:

.. code:: sh

   python3 scripts/manage_ssl.py validate

Confirm that validation succeeds with no unavailable checks.
Note the reported expiration dates so you can replace the certificates before they expire.

.. rst-class:: header-on-a-card header-steps

Step 8: Start the Services
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Start the deployment services:

.. code:: sh

   docker compose up -d

.. rst-class:: header-on-a-card header-steps

Step 9: Configure Client Trust (Optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If your browser or Python client does not already trust the CA that issued the server certificate, follow the :ref:`workstation <how-to-trust-public-issuer>` or :ref:`Python client <how-to-configure-python-trust>` instructions to verify its fingerprint and configure trust.

.. rst-class:: header-on-a-card header-steps

Step 10: Verify Access
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Open the deployment's HTTPS address and confirm that the frontend loads without certificate warnings.
If you already have an account, log in to check authenticated access.
For external Python clients, follow the :ref:`client connection and login checks <how-to-set-up-the-python-client>`.

.. rst-class:: fancy-header header-seealso

See Also
--------

* :ref:`reference-certificate-policy` lists certificate requirements.
* :ref:`reference-init-deployment-script` describes initialization and reruns.
* :ref:`how-to-replace-deployment-certificates` covers replacing certificates after initialization.
