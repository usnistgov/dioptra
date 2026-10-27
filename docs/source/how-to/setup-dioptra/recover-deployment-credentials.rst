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

.. _how-to-recover-deployment-credentials:

Recover Deployment Credentials
==============================

Use this guide when initialization reports an incomplete or empty credential set, or when interrupted credential generation leaves files that prevent a rerun.
Work from the deployment directory as the user who owns its files.

.. rst-class:: header-on-a-card header-steps

Step 1: Stop Services and Inspect the Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If services are running, stop them before changing credential files:

.. code:: sh

   docker compose down

Stop any other running initializers, then inspect the paths listed in :ref:`reference-init-deployment-credentials` for missing or empty files and the path or permission problems reported by the initializer.
Do not print credential contents in terminal output or logs.

.. rst-class:: header-on-a-card header-steps

Step 2: Restore or Regenerate the Complete Set
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Choose a path based on whether any service has used these credentials to initialize its accounts.

Option A: Recover Credentials Already Used by Services
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use this path if any service has initialized its accounts with these credentials, even if the deployment is currently stopped.
Do not regenerate the credentials.

1. Locate a protected backup containing the complete, matching credential set.
   If no backup is available, stop here and recover the original credentials before proceeding.
2. Restore all three credential files from that backup.
   Preserve deployment-specific settings in ``.env`` and owner-only permissions (``0600``) on the restored files.

Option B: Discard Credentials Not Yet Used by Services
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use this path only if no service has initialized its accounts with these credentials.

Remove all remaining credential files listed in :ref:`reference-init-deployment-credentials`.
Leave all three destinations absent so that rerunning initialization in Step 4 generates a complete fresh set.

.. warning::

   Do not use this procedure to rotate secrets.
   Deleting and regenerating credential files does not change the credentials stored by existing services; the new values will fail to authenticate against those services.
   If you discard the original credentials without a backup, you can be locked out.

.. rst-class:: header-on-a-card header-steps

Step 3: Remove Abandoned Temporary Files (Optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

List hidden files in the deployment directory and its ``secrets/`` directory without displaying their contents:

.. code:: sh

   ls -la . secrets

Look for these temporary-file names, where ``<token>`` is a randomly generated string of 32 hexadecimal characters:

* ``..env.<token>.tmp``
* ``secrets/.postgres-passwd.env.<token>.tmp``
* ``secrets/.<deployment-slug>-rustfs-accounts.env.<token>.tmp``

If any of these files remain:

1. Inspect them and confirm which files belong to an abandoned initialization attempt.
   Do not identify files for deletion solely by their names.
2. Remove only the confirmed abandoned temporary files.

.. rst-class:: header-on-a-card header-steps

Step 4: Rerun Initialization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Rerun ``init-deployment.sh`` with the branch and configuration flags used for the deployment.
For an existing deployment, follow :ref:`how-to-update-deployment`; for a new deployment, resume :ref:`how-to-prepare-deployment`.
Restart services only after initialization succeeds.
