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

.. _how-to-replace-deployment-ca:

Replace the Deployment Certificate Authority
===============================================

Use this guide to replace the certificate authority (CA) created by Dioptra and all server certificates it issued for your deployment.
Replacement briefly stops affected services.
Browsers and external clients that trust the old CA must trust the new CA before they can reconnect.
Certificates you obtained from another provider remain unchanged.

For routine server certificate replacement using the existing CA, see :ref:`how-to-replace-deployment-certificates`.

Prerequisites
----------------

* An :ref:`initialized Dioptra deployment <how-to-prepare-deployment>` with a Dioptra-generated certificate for the API, nginx, or both.
* Python 3.11 or newer.
* Docker with Docker Compose.
* Terminal access to the deployment directory as the user who owns its files.
* A protected backup of the :ref:`certificate and recovery files <reference-deployment-certificate-backups>`.
* Permission to update certificate trust settings on affected workstations and external clients.

Replacement
--------------

.. rst-class:: header-on-a-card header-steps

Step 1: Replace the CA and Its Server Certificates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Run the replacement command:

.. code:: sh

   python3 scripts/manage_ssl.py replace-ca

Wait for the command to report successful replacement and HTTPS checks.
Record the reported location and fingerprint of the new public CA certificate.
If the command reports an interrupted operation, follow :ref:`how-to-recover-certificate-operation` using the reported operation ID.

.. rst-class:: header-on-a-card header-steps

Step 2: Check the Installed Certificates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Check the installed certificates:

.. code:: sh

   python3 scripts/manage_ssl.py validate

Confirm that validation succeeds with no unavailable checks.

.. rst-class:: header-on-a-card header-steps

Step 3: Update Trust on Your Workstations and Clients
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the new public CA certificate at ``ssl/ca-certificates/dioptra-local-ca.crt`` to update the browsers and Python clients you manage.

For browsers that access nginx with a Dioptra-generated certificate, follow :ref:`workstation trust setup <how-to-trust-public-issuer>`.
For Python clients that connect to a service using a Dioptra-generated certificate, follow :ref:`Python client trust setup <how-to-configure-python-trust>` with the new CA certificate.

.. rst-class:: header-on-a-card header-steps

Step 4: Send the CA Certificate to Other Users
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Send ``ssl/ca-certificates/dioptra-local-ca.crt`` to other users who need it, or to the administrators who manage their certificate trust settings.
Share the reported fingerprint in a message recipients can verify came from you, for example through your organization's authenticated messaging service.
Tell the recipients to follow the :ref:`workstation <how-to-trust-public-issuer>` or :ref:`Python client <how-to-configure-python-trust>` instructions to verify the received certificate's fingerprint and configure trust.

.. rst-class:: header-on-a-card header-steps

Step 5: Verify Access
~~~~~~~~~~~~~~~~~~~~~~~

Open the deployment's HTTPS address in your browser and confirm that the frontend loads without certificate warnings.
If you have an account, log in to check authenticated access.
For external Python clients, repeat the :ref:`client connection and login checks <how-to-set-up-the-python-client>`.

Update your protected backup with the new CA and server certificates, their private keys and the recovery files.
See :ref:`reference-deployment-certificate-backups` for the files to retain.

.. rst-class:: header-on-a-card header-seealso

See Also
-----------

* :ref:`reference-manage-ssl` describes the certificate management commands.
* :ref:`reference-certificate-policy` lists certificate requirements and validity limits.
* :ref:`how-to-recover-certificate-operation` covers resume and rollback.
