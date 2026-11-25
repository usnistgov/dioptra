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

.. _reference-certificate-policy:

Certificate Policy Reference
============================

This page describes the certificate requirements for a Dioptra deployment.

.. seealso::

   * :ref:`reference-ssl-toml` for certificate settings.
   * :ref:`reference-manage-ssl` for certificate maintenance commands.

Ownership and Renewal
---------------------

The ``source`` setting in :ref:`config/ssl.toml <reference-ssl-toml>` selects generated or supplied certificates separately for the API and nginx.
Both default to ``generated``.
You can use either source for each service.
A deployment with supplied certificates for both services does not need a local certificate authority (CA).

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Certificate source
     - Responsibility
   * - ``generated``
     - Dioptra creates the deployment CA and separate server certificates and private keys. You protect the CA's private key and replace certificates before they expire.
   * - ``supplied``
     - You provide the server certificate bundle, matching private key, and root CA certificate. You obtain and install replacements before the certificates expire.

Dioptra does not renew certificates automatically.

Rerunning deployment initialization preserves valid existing certificates and private keys.
To install new supplied certificates or change a service's ``source`` setting, follow :ref:`how-to-replace-deployment-certificates`.

.. _reference-certificate-algorithms:

Algorithms
----------

Dioptra uses the following algorithms for generated certificates and accepts the listed algorithms for supplied certificates:

.. list-table:: Supported certificate profiles
   :header-rows: 1
   :widths: 25 35 40

   * - Property
     - Generated Certificates
     - Supplied Certificates
   * - Public keys
     - Separate RSA-3072 keys for the CA, API and nginx.
     - RSA of at least 2048 bits, or ECDSA on P-256, P-384 or P-521.
   * - Certificate signatures
     - SHA-256 with RSA.
     - RSA PKCS#1 v1.5, RSA-PSS or ECDSA with SHA-256, SHA-384 or SHA-512 and valid parameters.
   * - Chains
     - Deployment-local CA and separate server certificates.
     - Mixed RSA/ECDSA chains compatible with the participating server and client runtimes.

Dioptra rejects unsupported keys and algorithms, including MD5 or SHA-1 signatures on server and intermediate CA certificates.

A trusted root CA certificate may use an older hash algorithm for the signature on its own certificate.
Its public key and the signatures it creates on other certificates must still meet the requirements in the table.

This exception does not apply to a CA certificate signed by another CA and used as an intermediate certificate.

CA certificates used to secure the API and nginx require a critical Basic Constraints extension with ``CA:TRUE`` and a Key Usage extension permitting ``keyCertSign`` (certificate signing).

The :ref:`dioptra-ssl validate <reference-dioptra-ssl-validate>` command applies these requirements with ``--kind server`` or ``--kind ca``.
Standalone ``dioptra-ssl`` creates RSA keys and can issue through a supported RSA or ECDSA CA.

Validity and Expiration
-----------------------

These expiration limits support migration away from RSA and ECDSA certificate authentication, following `NIST's post-quantum transition timetable (NIST IR 8547) <https://csrc.nist.gov/pubs/ir/8547/final>`_.
Dioptra applies an earlier deadline to certificates it generates and a later deadline to supplied server certificates.

The limits apply to the algorithms identified in the table.
Post-quantum certificate authentication is not currently supported.

CA and server certificates used to secure the API and nginx must not be expired or used before their validity period begins.
Server certificates must have a valid certificate chain to a trusted root CA.

.. list-table:: Deployment expiration requirements
   :header-rows: 1
   :widths: 35 65

   * - Certificate type
     - Expiration requirement
   * - Generated RSA CA and server certificates
     - Must expire by December 31, 2030, at 23:59:59 UTC.
   * - Supplied RSA/ECDSA server certificates
     - Must expire by December 31, 2035, at 23:59:59 UTC.
   * - Supplied RSA/ECDSA root and intermediate CA certificates
     - Expiration after December 31, 2035, at 23:59:59 UTC produces a warning identifying the certificate. The certificate must still pass validity and chain checks.

Generated server certificates normally last 365 days.
Dioptra shortens that period when necessary so they expire no later than their issuing CA or the deployment expiration limit.
It reports the expiration date and any shortening.
Certificate generation fails if no valid period remains.

These deployment limits cannot be overridden in ``ssl.toml``.

A supplied CA certificate expiring in 2040 can still be used with an otherwise valid server certificate expiring in 2034.
Dioptra reports a warning for the CA certificate.

When you run ``dioptra-ssl`` directly, you can set expiration limits through its command-line options.
See :ref:`dioptra-ssl validate <reference-dioptra-ssl-validate>` for those options.

Identities, Chains and Trust
----------------------------

Each server certificate must include the required DNS names or IP addresses in its Subject Alternative Name (SAN) extension.

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Service
     - Required DNS name or IP address
   * - API
     - ``<deployment-slug>-restapi``, the API's internal DNS name.
   * - nginx
     - The DNS name or IP address specified by ``public.host`` in :ref:`config/ssl.toml <reference-ssl-toml>`.

Use ``dns_sans`` or ``ip_sans`` when clients connect to a service using additional DNS names or IP addresses beyond those listed in the table.
Each certificate must include those additional names and addresses.
If clients use only the values in the table, leave both settings empty.

Use the hostname or IP address from the client's connection URL.
For example, connecting to ``https://dioptra.example.org`` requires that DNS name in the certificate; it does not require an IP entry merely because the name resolves to an IP address.

.. note::

   Dioptra includes these names and addresses automatically when it generates deployment certificates.
   When obtaining supplied certificates, request the required names and addresses from your certificate provider.

DNS names must appear as DNS entries in the SAN extension, and IP addresses must appear as IP address entries.
A name in the certificate's Common Name field alone does not satisfy this requirement.
Generated certificates use explicit identities without unrestricted wildcards.

For supplied certificates, ``server.crt`` must contain the server certificate followed by any required intermediate CA certificates.
Your certificate provider may supply these together as a full-chain bundle.
List the root CA certificate files separately in ``trust_files`` and provide the matching private key in ``server.key``.

For additional CA certificates in ``ssl/ca-certificates/`` used only to access external websites, Dioptra reports policy problems as warnings.
The requirements above apply when a CA certificate is listed in a service's ``trust_files``.

See :ref:`how-to-replace-deployment-certificates` for preparing and installing these files.

.. _reference-certificate-permissions:

Files and Permissions
---------------------

The paths below are relative to the deployment directory.
On the host, these files and directories must belong to the user who owns the deployment.
Installed server certificates and private keys must belong to the account that runs the service.

.. list-table:: Required file permissions
   :header-rows: 1
   :widths: 70 30

   * - File or directory
     - Required permissions
   * - ``.ssl-private/`` and every subdirectory
     - ``0700``
   * - ``ssl/restapi/`` and ``ssl/nginx/``
     - ``0700``
   * - Private keys, installation records, and private files saved for recovery
     - ``0600``
   * - Public certificate files
     - ``0644``
   * - ``ssl/ca-certificates/``
     - ``0755``
   * - ``envs/tls.env``
     - ``0640``

During initialization, Dioptra corrects permissions when it can safely verify file ownership and paths.
It reports each changed path with its previous and new permissions.
File contents and ownership remain unchanged.

Initialization stops if a private path is a link or an unexpected file type, ownership is incorrect, or permissions cannot be corrected safely.
The ``validate`` command reports permission problems without changing files.

Backups and Client Trust
------------------------

Keep a protected backup of ``.ssl-private/ca/ca.key`` and ``.ssl-private/ca/ca.crt``.
Dioptra needs the private key to issue new certificates using that CA.

Back up the server certificates, private keys, configuration, and files needed for recovery.
Restrict access to backups containing private keys.
See :ref:`reference-deployment-certificate-backups` for the complete file list.

``ssl/ca-certificates/dioptra-local-ca.crt`` contains the public CA certificate to share with people who connect to your deployment.
Keep private keys out of this directory and client trust stores.

:ref:`how-to-adding-certificates` explains how to verify the CA certificate's fingerprint and configure browser or Python-client trust.
After :ref:`replacing the deployment CA <how-to-replace-deployment-ca>`, clients that trusted the previous CA need the new public CA certificate.
