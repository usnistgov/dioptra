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

.. _how-to-recover-certificate-operation:

Recover an Interrupted Certificate Operation
============================================

Use this guide to finish an interrupted certificate installation or restore the certificates used before it started.
For routine maintenance, use :ref:`how-to-replace-deployment-certificates`.

Prerequisites
-------------

* The operation ID reported by the failed certificate command.
* Terminal access to the deployment directory as the user who owns its files.
* The Dioptra container images used by the deployment.
* Docker with Docker Compose.
* Python 3.11 or newer.

Recovery
--------

.. rst-class:: header-on-a-card header-steps

Step 1: Find the Operation ID
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Find the operation ID in the terminal output or saved log from the interrupted initialization or certificate replacement command.
In your terminal, run the following command to save the ID in a shell variable:

.. code:: sh

   operation_id='OPERATION_ID'

Replace ``OPERATION_ID`` with the reported operation ID.
This command produces no output.
Use the same terminal session for the recovery commands that follow.

.. rst-class:: header-on-a-card header-steps

Step 2: Choose the Recovery Action
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Choose the recovery action:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Action
     - Purpose
   * - ``resume``
     - Finish installing the certificates prepared by the interrupted operation.
   * - ``rollback``
     - Restore the certificates and trust settings used before the operation started.

To resume, keep the prepared certificate files and deployment configuration unchanged.
To roll back, the saved previous certificates must still be valid.
Rollback is unavailable during first-time initialization because there are no previous certificates to restore.

.. rst-class:: header-on-a-card header-steps

Step 3: Run the Selected Action
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For an interrupted ``init``, stop normal deployment services before recovery:

.. code:: sh

   docker compose stop

Recovery of ``init`` leaves normal services stopped.
For an interrupted replacement, keep backend services available so recovery can restart affected services and verify HTTPS.

If you selected ``resume``, run:

.. code:: sh

   python3 scripts/manage_ssl.py recover --operation "$operation_id" --action resume

If you selected ``rollback``, run:

.. code:: sh

   python3 scripts/manage_ssl.py recover --operation "$operation_id" --action rollback

Wait for the command to report success before continuing.
If it reports a problem, save the error message and resolve the reported file or configuration problem before running the command again.

.. rst-class:: header-on-a-card header-steps

Step 4: Check the Recovered Certificates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the failed certificate operation occurred during ``init-deployment.sh``, return to :ref:`Step 4 of deployment preparation <how-to-prepare-deployment>` and rerun the initializer with the same options to finish setup.
It preserves recovered certificates, verifies HTTPS, registers the worker account, and tears services down.

After full initialization, or after recovery of a standalone ``manage_ssl.py init``, start normal services:

.. code:: sh

   docker compose up -d

Check the recovered certificates:

.. code:: sh

   python3 scripts/manage_ssl.py validate

Confirm that validation succeeds with no unavailable checks.

.. rst-class:: header-on-a-card header-steps

Step 5: Update Certificate Trust (Optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If recovery changed the CA certificate, follow the :ref:`workstation <how-to-trust-public-issuer>` or :ref:`Python client <how-to-configure-python-trust>` instructions to verify its fingerprint and update trust.

.. rst-class:: header-on-a-card header-steps

Step 6: Verify Access
~~~~~~~~~~~~~~~~~~~~~

Open the deployment's HTTPS address in your browser and confirm that the frontend loads without certificate warnings.
If you have an account, log in to check authenticated access.
For external Python clients, repeat the :ref:`client connection and login checks <how-to-set-up-the-python-client>`.

Update your protected backup with the recovered CA and server certificates, their private keys and the recovery files.
See :ref:`reference-deployment-certificate-backups` for the files to retain.

.. rst-class:: header-on-a-card header-seealso

See Also
--------

* :ref:`reference-manage-ssl-recover` defines recovery options and failure behavior.
* :ref:`reference-certificate-policy` lists certificate requirements.
