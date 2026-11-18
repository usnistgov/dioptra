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

.. _reference-dioptra-ssl:

dioptra-ssl Command Reference
=============================

``dioptra-ssl`` creates certificate authorities, issues server certificates and validates certificate files.
It is supplied by the ``dioptra-platform`` Python package and can be used without a Dioptra deployment.

.. seealso::

   For Docker deployment initialization and certificate replacement, see :ref:`reference-init-deployment-script` and :ref:`reference-manage-ssl`.

   For interrupted standalone certificate creation, see :ref:`how-to-recover-certificate-creation`.

Syntax
------

.. code:: text

   dioptra-ssl COMMAND [OPTIONS]

See :ref:`reference-dioptra-ssl-argument-values` for shared path, date, DNS-name and IP-address rules.

Command Summary
---------------

.. list-table:: Commands
   :header-rows: 1
   :widths: 25 75

   * - Command
     - Purpose
   * - :ref:`create-ca <reference-dioptra-ssl-create-ca>`
     - Create a private CA key and self-signed CA certificate.
   * - :ref:`issue <reference-dioptra-ssl-issue>`
     - Create a server key and certificate signed by an explicitly selected CA.
   * - :ref:`validate <reference-dioptra-ssl-validate>`
     - Check existing certificates and, optionally, their private keys without modifying them.

.. _reference-dioptra-ssl-common-options:

Common Options
--------------

These options are available after any command name.

.. program:: dioptra-ssl

.. option:: --format <text|json>

   Select the output format.
   ``text`` produces human-readable output and is the default.
   ``json`` produces structured JSON.

.. option:: --help

   Display help for the command and exit.

.. _reference-dioptra-ssl-create-ca:

create-ca
---------

Creates an RSA private key and a self-signed CA certificate using SHA-256.
Use this CA to issue server certificates with the :ref:`issue <reference-dioptra-ssl-issue>` command.

Syntax
~~~~~~

.. code:: text

   dioptra-ssl create-ca --key-out PATH --cert-out PATH --common-name TEXT
                         [--rsa-bits N] [--valid-days N]
                         [--not-after-limit UTC] [--format text|json]

Options
~~~~~~~

.. program:: dioptra-ssl create-ca

.. option:: --key-out <path>

   Required destination for the new CA private key.
   The destination must not exist.

.. option:: --cert-out <path>

   Required destination for the new CA certificate.
   The destination must not exist.

.. option:: --common-name <text>

   Required name for the CA, such as ``Example Service CA``.
   This name is stored in the certificate's Common Name (CN) field.

.. option:: --rsa-bits <n>

   RSA key size in bits.
   The default is ``3072``.
   The minimum is ``2048``.

.. option:: --valid-days <n>

   Requested certificate lifetime in days.
   The value must be a positive integer.
   The default is ``1825``.

.. option:: --not-after-limit <utc>

   Optional expiration deadline in UTC.
   If the lifetime requested with ``--valid-days`` would extend past this date, the command shortens it and reports the change.
   Creation fails if no valid lifetime remains.

See :ref:`reference-dioptra-ssl-common-options` for ``--format`` and ``--help``.

Examples
~~~~~~~~

Create a CA named ``Example Service CA``, saving its key and certificate in an existing private directory named ``pki``:

.. code:: sh

   dioptra-ssl create-ca --key-out pki/ca.key --cert-out pki/ca.crt \
     --common-name "Example Service CA"

.. _reference-dioptra-ssl-issue:

issue
-----

Creates an RSA private key and a server certificate signed by the CA you specify.
It signs the certificate with SHA-256 using the CA's RSA or ECDSA private key.
The certificate includes the DNS names and IP addresses supplied with ``--dns`` and ``--ip``.

Syntax
~~~~~~

.. code:: text

   dioptra-ssl issue --ca-cert PATH --ca-key PATH --key-out PATH --cert-out PATH
                     [--dns NAME]... [--ip ADDRESS]... [--ca-chain PATH]
                     [--rsa-bits N] [--valid-days N] [--not-after-limit UTC]
                     [--issuance-log PATH] [--format text|json]

At least one ``--dns`` or ``--ip`` is required.
These names and addresses are stored in the certificate's Subject Alternative Name (SAN) extension.

Options
~~~~~~~

.. program:: dioptra-ssl issue

.. option:: --ca-cert <path>

   Required PEM certificate for the signing CA.
   The certificate must be valid and permit certificate signing.

.. option:: --ca-key <path>

   Required private key for the signing CA.
   The key must match the certificate supplied with ``--ca-cert``.

.. option:: --ca-chain <path>

   Optional PEM file containing intermediate CA certificates needed to complete the certificate chain.
   Omit this option when using a CA created by :ref:`create-ca <reference-dioptra-ssl-create-ca>`.

.. option:: --key-out <path>

   Required destination for the new server private key.
   The destination must not exist.

.. option:: --cert-out <path>

   Required destination for the new server certificate.
   The destination must not exist.

.. option:: --dns <name>

   Add a DNS name clients use to connect to the server.
   Repeat this option for additional names.

.. option:: --ip <address>

   Add an IPv4 or IPv6 address clients use to connect to the server.
   Repeat this option for additional addresses.

.. option:: --rsa-bits <n>

   New server key size in bits.
   The default is ``3072``.
   The minimum is ``2048``.

.. option:: --valid-days <n>

   Requested certificate lifetime in days.
   The value must be a positive integer.
   The default is ``365``.

   The command shortens the lifetime if necessary so the certificate expires no later than the CA certificate or the deadline set by ``--not-after-limit``.
   It reports any shortening and fails if no valid lifetime remains.

.. option:: --not-after-limit <utc>

   Optional expiration deadline in UTC.

.. option:: --issuance-log <path>

   Optional path to a log of certificates signed by this command.
   No log is written by default.
   See :ref:`reference-dioptra-ssl-issuance-history` for the file format and logging behavior.

See :ref:`reference-dioptra-ssl-common-options` for ``--format`` and ``--help``.

Examples
~~~~~~~~

Issue a certificate for ``service.example.org`` and ``192.0.2.20`` using the CA in the existing ``pki`` directory:

.. code:: sh

   dioptra-ssl issue --ca-cert pki/ca.crt --ca-key pki/ca.key \
     --key-out pki/service.key --cert-out pki/service.crt \
     --dns service.example.org --ip 192.0.2.20

.. _reference-dioptra-ssl-validate:

validate
--------

Checks local certificate files without changing them.

For server certificates, it verifies the certificate chain against root CA certificates you supply and checks the requested DNS names and IP addresses.
With ``--kind ca``, it checks whether a CA certificate can sign other certificates.

If you supply a private key, it also checks that the key matches the certificate.

The command does not connect to a running server or check whether certificates have been revoked.
See :ref:`reference-certificate-algorithms` for supported certificate keys and signature algorithms.

Syntax
~~~~~~

.. code:: text

   dioptra-ssl validate --cert PATH [--key PATH] [--kind server|ca|outbound-ca]
                        [--trust PATH]... [--dns NAME]... [--ip ADDRESS]...
                        [--max-not-after UTC] [--warn-ca-not-after UTC]
                        [--format text|json]

By default, the command validates a server certificate.
This requires ``--trust`` and at least one ``--dns`` or ``--ip``.

Options
~~~~~~~

.. program:: dioptra-ssl validate

.. option:: --cert <path>

   Required path to a PEM certificate file.
   For server validation, this single file must contain the server certificate first, followed by any required intermediate certificates.
   Supply root CA certificates separately with ``--trust``.

.. option:: --key <path>

   Optional path to a private key file.
   The command checks that this key matches the certificate.

.. option:: --kind <server|ca|outbound-ca>

   Certificate type to validate.
   The default is ``server``.

   ``server``
      Check a server certificate's chain and the requested DNS names and IP addresses.

   ``ca``
      Check whether a CA certificate is valid for signing other certificates.
      No DNS name or IP address is required.

   ``outbound-ca``
      Inspect one CA certificate used to access external websites, reporting policy problems as warnings.
      Use ``--cert`` to supply the certificate; ``--warn-ca-not-after`` and ``--format`` are optional.

.. option:: --trust <path>

   Path to a PEM file containing a root CA certificate to trust for this check.
   Required for server certificate validation.
   Repeat this option to supply additional root CA files.

.. option:: --dns <name>

   Check that the server certificate is valid for the specified DNS name.
   Repeat this option to check additional names.

.. option:: --ip <address>

   Check that the server certificate is valid for the specified IPv4 or IPv6 address.
   Repeat this option to check additional addresses.

.. option:: --max-not-after <utc>

   Optional expiration deadline in UTC for the certificate supplied with ``--cert``.
   Validation fails if that certificate expires after this date.

.. option:: --warn-ca-not-after <utc>

   Optional expiration threshold in UTC for CA certificates in the chain.
   A CA certificate that expires after this date produces a warning.
   The warning alone does not cause validation to fail.

With ``--kind server`` or ``--kind ca``, certificates must be within their validity period and use supported algorithms, whether or not these options are supplied.

See :ref:`reference-dioptra-ssl-common-options` for ``--format`` and ``--help``.

Examples
~~~~~~~~

Validate a server certificate for ``service.example.org`` and check its private key, using ``root-ca.crt`` as the trusted root CA:

.. code:: sh

   dioptra-ssl validate --cert server-chain.pem --key server.key \
     --trust root-ca.crt --dns service.example.org

Validate a CA certificate and check that its private key matches:

.. code:: sh

   dioptra-ssl validate --kind ca --cert pki/ca.crt --key pki/ca.key

Output and Exit Status
----------------------

Results report certificate details, checks and warnings as applicable to the command.
JSON output also includes a schema version and the command name.

Successful commands return exit status ``0``.
Errors identify the affected file or certificate and the failed operation or check.
File-access and storage errors include the operating-system reason.
Errors are written to standard error and return a nonzero exit status.
In JSON mode, an error is reported as a single structured JSON object.

.. _reference-dioptra-ssl-argument-values:

Argument Values
---------------

* Relative file paths are resolved from the directory where you run the command.
* Dates and times use UTC in RFC 3339 format, ending in ``Z``, for example ``2030-12-31T23:59:59Z``.
* DNS names and IP addresses must not include a URL scheme or port number.
  For example, use ``dioptra.example.org``, not ``https://dioptra.example.org:443``.

.. _reference-dioptra-ssl-files-permissions:

Files and Permissions
---------------------

.. list-table::
   :header-rows: 1
   :widths: 25 50 25

   * - Created file
     - Format
     - Permissions
   * - Certificate
     - PEM
     - ``0644``
   * - Private key
     - Unencrypted PKCS#8 PEM
     - ``0600``

Create output files in directories you own.
Store private keys and their backups in directories only you can access, outside source control.

.. _reference-dioptra-ssl-publication:

Creation Failures and Retained Files
------------------------------------

``create-ca`` and ``issue`` fail if either output file already exists.
If a command fails while writing the files, it reports which files were written and the paths to the saved certificate and private key.
If issuance logging was requested, it also reports whether the issuance record was saved successfully.
Keep these saved files until recovery is complete.
Follow :ref:`how-to-recover-certificate-creation` to restore an intact pair or generate replacements.
If a requested issuance record cannot be confirmed, you can recover a validated pair while accepting that the issuance might not be recorded.
If you require a complete record, generate a new pair with working logging.

For certificates managed by a Dioptra deployment, see :ref:`how-to-recover-certificate-operation`.

.. _reference-dioptra-ssl-recovery-problems:

Recovery Problems
-----------------

The following cases cover validation and file errors during standalone recovery.
For the restart procedure, follow :ref:`Start Again <how-to-recover-certificate-creation-restart>` in the :ref:`certificate recovery how-to <how-to-recover-certificate-creation>`.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Problem
     - Action
   * - A file cannot be read or written, or its permissions cannot be set.
     - Check the reported path, that its parent directory exists, and that you own the output directory and have the required access. Correct the path or use a private directory you own. For a read-only filesystem, use a writable location.
   * - Storage is full or a filesystem operation fails.
     - Free space or use a working filesystem with sufficient space, then start again with unused output paths. A failed write may leave a partial file.
   * - A certificate or key is malformed, missing, or does not match its partner.
     - Check that both saved files belong to the same attempt. If they remain unusable, start again. Restore damaged externally supplied files from a known-good copy or obtain replacements from their provider; a lost private key can require a new certificate.
   * - The server certificate's chain cannot be verified.
     - Check the root CA supplied with ``--trust`` and the intermediate certificates in the certificate file. If the correct inputs still fail validation, start again using a valid signing CA and its matching key.
   * - A DNS name or IP address does not match.
     - Check the validation argument against the original issuance request. If the certificate lacks a name you need, issue a new certificate with that name.
   * - A certificate is outside its validity period or exceeds the requested deadline.
     - Check the system clock and compare any ``--max-not-after`` argument with the original request. If the saved certificate still fails the validity check, generate a replacement using a valid CA.
   * - An algorithm is unsupported or a CA cannot be used for signing.
     - Check that you selected the intended certificate. If so, use a CA and certificate that meet the :ref:`supported requirements <reference-certificate-algorithms>`.
   * - An existing output's checksum differs from its saved copy.
     - Check the selected paths. If they are correct, leave both files unchanged and start again with unused output paths.

Keep saved files and existing outputs when starting again.
A failed server-certificate operation does not require replacing a healthy CA.

.. _reference-dioptra-ssl-issuance-history:

Optional Issuance History
-------------------------

Use ``issue --issuance-log PATH`` to record certificate signing in the specified file.
The file uses UTF-8 JSON Lines format, with one JSON object per line, and permissions ``0600``.
Each record contains:

* A schema version and unique issuance ID.
* The signing time in UTC.
* SHA-256 fingerprints of the signing CA certificate and the issued certificate.
* The issued certificate's serial number, DNS names, IP addresses and validity dates.
* The public-key and signature algorithms.

The issued certificate's fingerprint and issuance ID identify its log record.
The log covers only signing performed by this command with logging enabled.
An interruption between signing and writing the log can leave a signed certificate without a log record.

.. list-table:: Logging failures
   :header-rows: 1
   :widths: 35 65

   * - Condition
     - Result
   * - The log cannot be written.
     - The command fails and saves the generated certificate and private key for recovery.
   * - The log is written, but writing the certificate or key output fails.
     - The log record remains. It confirms signing, but does not confirm that both output files were written successfully.
   * - The log contains an invalid or incomplete record.
     - The command stops before signing another certificate. Keep the log unchanged and select a new log path when starting a fresh issuance.

For subsequent issuance, you can reuse a valid, writable log.
If the log is damaged or its condition is uncertain, select a new, unused path with ``--issuance-log`` and retain the old log.
The new log records subsequent issuance; it does not record a recovered certificate retrospectively or complete the old history.
Missing or damaged records are not reconstructed as part of recovery.
A complete record remains part of the signing history even if its certificate will not be used.

To start a fresh issuance, follow :ref:`Start Again <how-to-recover-certificate-creation-restart>` in the :ref:`certificate recovery how-to <how-to-recover-certificate-creation>`.
See :ref:`reference-dioptra-ssl-publication` for failure reporting.

.. rst-class:: fancy-header header-seealso

See Also
--------

* :ref:`reference-certificate-policy` lists certificate requirements enforced by deployment tools.
* :ref:`dioptra-api prod <reference-dioptra-api-prod>` describes running the API with HTTPS from an installed Python package.
