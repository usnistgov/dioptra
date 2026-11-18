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

.. _how-to-recover-certificate-creation:

Recover from Interrupted Certificate Creation
=============================================

Use this guide to recover the certificate and private key saved by a failed ``dioptra-ssl create-ca`` or ``dioptra-ssl issue`` command when it could not finish writing its output files.
For certificates managed by a Dioptra deployment, follow :ref:`how-to-recover-certificate-operation`.

Prerequisites
-------------

* The original command and its failure report, including the location of the saved files.
* Terminal access as the user who owns the saved files and output directories.
* ``dioptra-ssl`` and OpenSSL available in your terminal.
* For a server certificate, the root CA certificate needed to validate its chain.

Overview
-----------

Choose how to proceed after the failed command:

* **Option A: Recover the Saved Files.** Use this to check the saved certificate and key and restore missing outputs.
* **Option B: Start Again.** Use this if the saved files cannot be recovered or you prefer to generate a new pair.

.. _how-to-recover-certificate-creation-saved:

Option A: Recover the Saved Files
--------------------------------------

.. rst-class:: header-on-a-card header-steps

Step A1: Identify the Saved and Output Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Confirm that the failed command has stopped and that no other process is writing to these files.
Find the saved certificate and private key in the recovery directory identified by the failure report.
In your terminal, save their paths and the intended output paths in shell variables:

.. code:: sh

   saved_cert='SAVED_CERTIFICATE_PATH'
   saved_key='SAVED_PRIVATE_KEY_PATH'
   cert_out='OUTPUT_CERTIFICATE_PATH'
   key_out='OUTPUT_PRIVATE_KEY_PATH'

Replace the ``SAVED_`` placeholders with the paths to the saved files.
Replace the ``OUTPUT_`` placeholders with the original command's ``--cert-out`` and ``--key-out`` paths.
Use absolute paths to regular files, not directories or symbolic links; either output file may be missing.
These assignments produce no output.
Use the same terminal session for the remaining steps.

.. rst-class:: header-on-a-card header-steps

Step A2: Validate the Saved Certificate and Key
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the failed command was ``create-ca``, validate the saved CA certificate and key:

.. code:: sh

   dioptra-ssl validate --kind ca --cert "$saved_cert" --key "$saved_key"

If the failed command was ``issue``, validate the saved server certificate and key:

.. code:: sh

   dioptra-ssl validate --cert "$saved_cert" --key "$saved_key" \
     --trust 'ROOT_CA_FILE' --dns 'SERVER_DNS_NAME'

Replace ``ROOT_CA_FILE`` with the root CA certificate's path and ``SERVER_DNS_NAME`` with a DNS name from the original command.
Use ``--ip`` for an IP address, and repeat ``--dns`` or ``--ip`` to check every name and address from that command.
If the original command used ``--not-after-limit``, add ``--max-not-after`` with the same date.

Continue only if validation succeeds.
If it fails, use :ref:`reference-dioptra-ssl-recovery-problems` to check for an incorrect path, validation argument or file-access problem.
If the saved pair still cannot be validated, continue to :ref:`how-to-recover-certificate-creation-restart`.

.. rst-class:: header-on-a-card header-steps

Step A3: Check the Issuance Log (If Used)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the original ``issue`` command used ``--issuance-log``, check its failure report for confirmation that the issuance record was saved successfully.
If you did not use ``--issuance-log``, skip this step and continue to :ref:`how-to-recover-certificate-creation-compare`.

If the record was saved successfully, continue to :ref:`how-to-recover-certificate-creation-compare`.
If the log write failed or its completion could not be confirmed, keep the log unchanged and choose how to proceed:

* **Keep the generated pair.** If you accept that this issuance might not be recorded, continue to :ref:`how-to-recover-certificate-creation-compare`.
* **Require a complete issuance record.** Follow :ref:`how-to-recover-certificate-creation-restart` to generate a new pair with working logging.

For subsequent issuance, use a new log file if the old log is damaged or its condition is uncertain.
The new log records only future issuance; it does not record the certificate you recover here.

.. _how-to-recover-certificate-creation-compare:

.. rst-class:: header-on-a-card header-steps

Step A4: Compare Any Existing Output Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the certificate output already exists, compare its SHA-256 checksum with the saved copy:

.. code:: sh

   openssl dgst -sha256 "$saved_cert" "$cert_out"

If the private key output already exists, compare its checksum with the saved copy:

.. code:: sh

   openssl dgst -sha256 "$saved_key" "$key_out"

Each comparison prints two checksums, one for each file.
The hexadecimal values must match.
Skip the comparison for any missing output file.
If a command cannot read a file, check its path and your read permissions, then repeat the comparison.
If the checksums differ, check that you selected files from the same failed operation.
If they still differ, leave the existing output unchanged and continue to :ref:`how-to-recover-certificate-creation-restart`.

.. rst-class:: header-on-a-card header-steps

Step A5: Restore the Missing Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the private key output is missing, copy it and set its permissions:

.. code:: sh

   cp -n "$saved_key" "$key_out" && chmod 600 "$key_out"

If the certificate output is missing, copy it and set its permissions:

.. code:: sh

   cp -n "$saved_cert" "$cert_out" && chmod 644 "$cert_out"

The ``-n`` option prevents ``cp`` from overwriting an existing file.
Leave existing files that matched their saved copies in place.
If copying or setting permissions fails, stop before using the output files.
Check :ref:`reference-dioptra-ssl-recovery-problems`, correct the reported file-access or storage problem, and continue to :ref:`how-to-recover-certificate-creation-restart`.
A failed copy may have left an incomplete output file.

.. rst-class:: header-on-a-card header-steps

Step A6: Verify the Recovered Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Compare both output files with the saved files you validated:

.. code:: sh

   openssl dgst -sha256 "$saved_cert" "$cert_out"
   openssl dgst -sha256 "$saved_key" "$key_out"

Confirm that the two certificate checksums match and that the two private-key checksums match.
Both output files must be present and identical to their saved copies before you use them.
If either comparison fails, continue to :ref:`how-to-recover-certificate-creation-restart`.

Keep a protected backup of the recovered certificate and private key.
Retain the saved recovery files and any issuance log until you have verified the recovered files and completed the backup.

.. _how-to-recover-certificate-creation-restart:

Option B: Start Again
--------------------------

.. rst-class:: header-on-a-card header-steps

Step B1: Prepare New Output Paths
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Keep the failed attempt's files and any issuance log in place.
Choose new filenames for ``--cert-out`` and ``--key-out`` in an existing directory you own and only you can access.
Neither output file may already exist.

Before retrying, correct any problem reported with the inputs, directory access or available storage.
See :ref:`reference-dioptra-ssl-recovery-problems` for the corresponding action.

.. rst-class:: header-on-a-card header-steps

Step B2: Repeat the Creation Command
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For ``issue``, reuse the same CA certificate and key if they remain valid and intact.
A failed server-certificate operation does not require replacing a healthy CA.

If you used ``--issuance-log``, keep using that log if it is valid and writable.
If it is damaged or you cannot determine its condition, supply a new, unused log filename and retain the old log unchanged.
The new log does not fill gaps in the old history.

Run the original :ref:`create-ca <reference-dioptra-ssl-create-ca>` or :ref:`issue <reference-dioptra-ssl-issue>` command with the new output paths and any corrected inputs.

.. note::

   If an already-used CA is damaged, restore it from a known-good backup where possible.
   Replacing it also requires replacing certificates that depend on it and updating affected clients to trust the new CA.

.. rst-class:: header-on-a-card header-steps

Step B3: Use the New Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Confirm that the command reports success and that both new output files exist.
Use these files for subsequent setup, and keep a protected backup of the certificate and private key.
Do not use the outputs from the abandoned attempt.
Retain its issuance log as part of the signing history, even if the certificate it records will not be used.

.. rst-class:: fancy-header header-seealso

See Also
--------

* :ref:`reference-dioptra-ssl-validate` describes certificate validation options.
* :ref:`reference-dioptra-ssl-files-permissions` lists certificate and private-key formats and permissions.
* :ref:`how-to-recover-certificate-operation` covers deployment certificate recovery.
