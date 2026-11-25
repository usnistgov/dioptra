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

Configure Certificate Trust
===========================

Use this guide to configure trusted certificate authorities (CAs) for deployment services, your browser or an external Python client.
Repeat the relevant procedure if the deployment's CA changes.

Overview
-----------

Follow one or more procedures for the systems you configure:

* :ref:`Option A: Deployment Services <how-to-deployment-service-trust>` is for the deployment owner.
* :ref:`Option B: Your Workstation <how-to-trust-public-issuer>` configures browser trust.
* :ref:`Option C: Your Python Client <how-to-configure-python-trust>` configures trust for scripts and notebooks.

.. _how-to-deployment-service-trust:

Option A: Deployment Services
----------------------------------

Prerequisites
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* A deployment directory created by following :ref:`how-to-prepare-deployment`.
* Terminal access as the user who owns the deployment files.
* Docker with Docker Compose.
* Public root CA certificates for any additional certificate authorities the services need to trust, obtained from the certificate administrator.

Run the commands in this procedure from the deployment directory.

.. rst-class:: header-on-a-card header-steps

Step A1: Copy the CA Certificates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Copy each public root CA certificate into ``ssl/ca-certificates/``.
Use PEM format, one certificate per file, and a ``.crt`` filename extension.

.. code:: sh

   install -m 0644 "ROOT_CA_PATH" ssl/ca-certificates/root-ca.crt

Replace ``ROOT_CA_PATH`` with the path to your public root CA certificate.
If you add more than one certificate, give each a different destination filename.

Warnings about CA certificates used only to access external websites do not stop initialization.
CA certificates used to secure the API or nginx must meet the :ref:`certificate policy <reference-certificate-policy>`.

To configure API or nginx server certificates that you provide, follow :ref:`how-to-enabling-ssl-tls`.

.. rst-class:: header-on-a-card header-steps

Step A2: Initialize the Deployment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you are changing an existing API or nginx server certificate, follow :ref:`how-to-replace-deployment-certificates`.

Run the initializer.
If PostgreSQL TLS is enabled, include ``--enable-postgres-ssl`` in the following command:

.. code:: sh

   ./init-deployment.sh --branch BRANCH_NAME

Replace ``BRANCH_NAME`` with the Dioptra branch matching your container images.
Wait for initialization to report success before continuing.

.. rst-class:: header-on-a-card header-steps

Step A3: Start the Services
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Start the services:

.. code:: sh

   docker compose up -d
   docker compose ps

Confirm that the deployment services are running.

.. _how-to-trust-public-issuer:

Option B: Your Workstation
----------------------------------

Prerequisites
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* The deployment's HTTPS address.
* Permission to change your browser's or operating system's certificate trust settings.
* OpenSSL for displaying certificate fingerprints.

.. rst-class:: header-on-a-card header-steps

Step B1: Obtain the CA Certificate
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If your browser already trusts the CA, continue to :ref:`Step B4 <how-to-check-browser-certificate-trust>`.

Obtain the deployment's public root CA certificate and its SHA-256 fingerprint from the deployment owner or certificate administrator.
Save the certificate file on your workstation.

If you own the deployment, use the public root CA certificate for nginx and its fingerprint recorded during initialization or replacement.

.. _how-to-verify-ca-fingerprint:

.. rst-class:: header-on-a-card header-steps

Step B2: Verify the Certificate Fingerprint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Display the SHA-256 fingerprint of the certificate file on your workstation:

.. code:: sh

   openssl x509 -in "CA_CERT_PATH" -noout -fingerprint -sha256

Replace ``CA_CERT_PATH`` with the path to the public CA certificate file you received.
Compare the result with the fingerprint recorded during initialization or replacement, or supplied by the deployment administrator in a message you can verify came from them.
Compare the hexadecimal fingerprint values, ignoring differences in capitalization or colon separators.
The fingerprints must match before you trust the certificate.

If the values differ, do not import the certificate.
Ask the deployment owner or certificate administrator to confirm the fingerprint and resend the certificate, then repeat this check.

.. rst-class:: header-on-a-card header-steps

Step B3: Import the CA Certificate
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Import the verified public root CA certificate using your browser's or operating system's certificate settings.
If prompted to choose a purpose, allow the CA to verify websites or HTTPS servers.

.. _how-to-check-browser-certificate-trust:

.. rst-class:: header-on-a-card header-steps

Step B4: Check Browser Access
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Open the deployment's HTTPS address, including its port if needed.
Confirm that the page loads without a certificate warning before entering credentials.

If a certificate warning appears, do not bypass it.
Send the warning message to the deployment owner for help.

.. _how-to-configure-python-trust:

Option C: Your Python Client
----------------------------------

Prerequisites
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* The deployment's HTTPS address.
* A Python environment containing the Dioptra client and its ``requests`` dependency.
* OpenSSL for displaying certificate fingerprints.

.. rst-class:: header-on-a-card header-steps

Step C1: Activate the Client Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Activate the Python environment containing the Dioptra client and its ``requests`` dependency.

.. _how-to-obtain-python-ca-certificate:

.. rst-class:: header-on-a-card header-steps

Step C2: Obtain and Verify the CA Certificate (Optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If Requests already trusts the deployment's CA, continue to :ref:`Step C5 <how-to-check-python-certificate-trust>`.

Obtain the public root CA certificate and its SHA-256 fingerprint from the deployment owner or certificate administrator.
Save the certificate on the computer where you run the Python client, then follow the instructions in :ref:`Verify the Certificate Fingerprint <how-to-verify-ca-fingerprint>`.

.. rst-class:: header-on-a-card header-steps

Step C3: Create the CA Bundle
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the terminal where you activated the Python environment, combine Requests' default CA bundle with the verified deployment CA certificate:

.. code:: sh

   cat "$(python -c 'import requests; print(requests.certs.where())')" \
       "CA_CERT_PATH" > dioptra-ca-bundle.pem

Replace ``CA_CERT_PATH`` with the path to the PEM certificate you verified in :ref:`Step C2 <how-to-obtain-python-ca-certificate>`.
The command creates ``dioptra-ca-bundle.pem`` in the current directory and leaves the installed CA bundle unchanged.
Recreate this file after updating ``certifi`` or replacing the deployment CA.

.. rst-class:: header-on-a-card header-steps

Step C4: Configure Certificate Trust
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

From the same directory, set ``REQUESTS_CA_BUNDLE`` to the combined bundle:

.. code:: sh

   export REQUESTS_CA_BUNDLE="$PWD/dioptra-ca-bundle.pem"

Start Python or your notebook from this terminal so it uses this setting.

.. _how-to-check-python-certificate-trust:

.. rst-class:: header-on-a-card header-steps

Step C5: Check the HTTPS Connection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the same terminal, check the HTTPS connection:

.. code:: sh

   python - <<'PY'
   import requests

   response = requests.get("https://localhost/")
   print(response.status_code)
   PY

Replace the URL with the deployment's HTTPS address, including its port if needed.
A successful request to the frontend prints ``200``.

If you receive a certificate verification error, send the error message to the deployment owner for help.

Follow :ref:`how-to-set-up-the-python-client` to select the API address and log in.

.. rst-class:: fancy-header header-seealso

See Also
--------

* :ref:`how-to-enabling-ssl-tls` explains how to use your own server certificates.
* :ref:`reference-certificate-policy` lists certificate and trust requirements.
* :ref:`how-to-replace-deployment-ca` covers replacement of Dioptra's CA.
