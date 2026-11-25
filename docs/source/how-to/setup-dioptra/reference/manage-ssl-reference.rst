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

.. _reference-manage-ssl:

manage_ssl.py Command Reference
===============================

``scripts/manage_ssl.py`` initializes, validates, replaces, and recovers deployment certificates.
It uses the settings in :ref:`config/ssl.toml <reference-ssl-toml>`.

.. seealso::

   For step-by-step instructions, see:

   * :ref:`how-to-prepare-deployment` for deployment initialization.
   * :ref:`how-to-replace-deployment-certificates` for server certificate replacement.
   * :ref:`how-to-replace-deployment-ca` for CA replacement.
   * :ref:`how-to-recover-certificate-operation` for interrupted operations.

Syntax
------

.. code:: text

   python3 scripts/manage_ssl.py COMMAND [OPTIONS]

``COMMAND`` is one of the commands in the :ref:`reference-manage-ssl-command-summary`.
Square brackets indicate optional arguments.
Braces with vertical bars, such as ``{resume|rollback}``, indicate a required choice.

Requirements
------------

The command requires:

* Python 3.11 or newer.
* Docker with Docker Compose.
* The Dioptra container images configured for the deployment.

Run the command as the user who owns the deployment files and has permission to use Docker.
No additional Python packages are required on the host.

.. _reference-manage-ssl-command-summary:

Command Summary
---------------

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Command
     - Description
   * - :ref:`init <reference-manage-ssl-init>`
     - Initialize deployment certificates or check an existing installation.
   * - :ref:`validate <reference-manage-ssl-validate>`
     - Check deployment certificates without changing them.
   * - :ref:`replace <reference-manage-ssl-replace>`
     - Replace selected server certificates using the existing CA or supplied files.
   * - :ref:`replace-ca <reference-manage-ssl-replace-ca>`
     - Replace the deployment CA and the server certificates it issues.
   * - :ref:`recover <reference-manage-ssl-recover>`
     - Finish an interrupted operation or restore the previous certificates.

.. _reference-manage-ssl-common-options:

Common Options
--------------

The following option is available after any command name.

.. program:: scripts/manage_ssl.py

.. option:: --deployment-root <path>

   Optional deployment directory.
   Defaults to the root of the deployment containing this script.
   Relative paths in ``config/ssl.toml`` resolve from this directory, regardless of the shell's working directory.

.. _reference-manage-ssl-init:

init
----

Initializes deployment certificates using ``config/ssl.toml``.
It creates missing certificates configured with ``source = "generated"``, validates supplied certificates, and installs the certificates and trusted CAs needed by the services.
``init-deployment.sh`` calls this command during deployment initialization.

Normal deployment services must be stopped before running ``init``.
Stopped containers may remain.
The command uses temporary utility containers to validate and install files, and leaves normal services stopped.
Success confirms validated installation.
Live HTTPS is checked separately by :ref:`validate <reference-manage-ssl-validate>` after normal services start.

Syntax
~~~~~~

.. code:: text

   python3 scripts/manage_ssl.py init [--deployment-root PATH]

See :ref:`reference-manage-ssl-common-options` for ``--deployment-root``.

Examples
~~~~~~~~

Initialize certificates from the deployment directory:

.. code:: sh

   python3 scripts/manage_ssl.py init

For the full initialization procedure, see :ref:`how-to-prepare-deployment`.

Rerunning Initialization
~~~~~~~~~~~~~~~~~~~~~~~~

Rerunning ``init`` preserves valid existing certificates and private keys, including the deployment CA.
It corrects file permissions when ownership and paths are safe, and reports each changed path with its old and new permissions.
Unsafe paths, incorrect ownership, or invalid certificates stop initialization.
See :ref:`reference-certificate-permissions` for the file requirements.

Changes to supplied certificate files or the ``source`` setting require :ref:`replace <reference-manage-ssl-replace>`.
If an earlier operation was interrupted, ``init`` reports its operation ID and the applicable recovery command.

.. _reference-manage-ssl-validate:

validate
--------

Checks the configuration, file ownership and permissions, server names and IP addresses, certificate chains, matching private keys, and certificate validity.
It also checks installed certificates and verifies live HTTPS using the expected certificates.
It leaves deployment files, permissions, installation records, and running services unchanged.

Syntax
~~~~~~

.. code:: text

   python3 scripts/manage_ssl.py validate [--deployment-root PATH]

See :ref:`reference-manage-ssl-common-options` for ``--deployment-root``.

Examples
~~~~~~~~

Check certificates from the deployment directory:

.. code:: sh

   python3 scripts/manage_ssl.py validate

Validation Results
~~~~~~~~~~~~~~~~~~

The command reports the result of each check, including any checks that could not run.
It returns zero only when all required checks pass.
Failed or incomplete checks return a nonzero exit status, including when Docker, a required container image, or a required HTTPS endpoint is unavailable.

.. _reference-manage-ssl-replace:

replace
-------

Replaces the selected server certificates and preserves the deployment CA.
It validates the replacement certificates before stopping affected services, installs them, restarts the services, and verifies HTTPS using the expected certificates.
Replacement requires a brief service interruption.
The previous certificates and keys remain available for recovery after success.

Syntax
~~~~~~

.. code:: text

   python3 scripts/manage_ssl.py replace --target {restapi|nginx|all}
                                        [--deployment-root PATH]

Options
~~~~~~~

.. program:: scripts/manage_ssl.py replace

.. option:: --target <restapi|nginx|all>

   Required service selection.
   ``restapi`` selects the API, ``nginx`` selects the browser-facing service, and ``all`` selects both.

See :ref:`reference-manage-ssl-common-options` for ``--deployment-root``.

Examples
~~~~~~~~

Replace the API certificate from the deployment directory:

.. code:: sh

   python3 scripts/manage_ssl.py replace --target restapi

Replacement Certificates
~~~~~~~~~~~~~~~~~~~~~~~~

The service's ``source`` setting in :ref:`config/ssl.toml <reference-ssl-toml>` determines which replacement certificates the command uses.

* When ``source = "generated"``, it creates certificates using the existing deployment CA.
* When ``source = "supplied"``, it uses the replacement certificate and private key at ``ssl/<service>/server.crt`` and ``ssl/<service>/server.key``, where ``<service>`` is ``restapi`` or ``nginx``.
  It validates the certificate using the CA certificates listed in that service's ``trust_files`` setting.

See :ref:`how-to-replace-deployment-certificates` for preparing the files and configuration.

.. _reference-manage-ssl-replace-ca:

replace-ca
----------

Replaces the deployment certificate authority (CA) and every server certificate configured with ``source = "generated"``.
Supplied server certificates remain unchanged.
If no services use generated certificates, the command reports an error and leaves the deployment unchanged.

Syntax
~~~~~~

.. code:: text

   python3 scripts/manage_ssl.py replace-ca [--deployment-root PATH]

See :ref:`reference-manage-ssl-common-options` for ``--deployment-root``.

Examples
~~~~~~~~

Replace the deployment CA from the deployment directory:

.. code:: sh

   python3 scripts/manage_ssl.py replace-ca

Service Interruption and Client Trust
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The command validates the new CA and server certificates before stopping affected services.
It installs the replacements, restarts the services, and verifies HTTPS using the expected certificates.
The previous certificates and keys remain available for recovery after success.

Replacement requires a brief service interruption.
Browsers and Python clients that trust the previous deployment CA need to trust the new CA before reconnecting.
See :ref:`how-to-replace-deployment-ca` for the replacement and client trust procedure.

.. _reference-manage-ssl-recover:

recover
-------

Finishes an interrupted certificate installation or restores the previous certificates, private keys, and trusted CAs.
Recovery stops with an error if required files are missing or have changed unexpectedly, or if the recorded operation does not match the installed certificates.

Syntax
~~~~~~

.. code:: text

   python3 scripts/manage_ssl.py recover --operation OPERATION_ID
                                        --action {resume|rollback}
                                        [--deployment-root PATH]

Options
~~~~~~~

.. program:: scripts/manage_ssl.py recover

.. option:: --operation <id>

   Required operation ID reported by the interrupted command or a later initialization attempt.
   Identifies the saved files for that operation under ``.ssl-private/operations/``.

.. option:: --action <resume|rollback>

   Required recovery action. Accepted values are:

   ``resume``
      Revalidates the saved replacement certificates and completes their installation.
      It does not generate new certificates or a different CA.

   ``rollback``
      Restores the previous certificates, private keys, and trusted CAs only if they still pass validation.
      Rollback is unavailable when there is no previous installation or its certificates are expired or otherwise invalid.

Recovery follows the service requirements of the interrupted command:

.. list-table:: Recovery service behavior
   :header-rows: 1
   :widths: 25 75

   * - Interrupted command
     - Requirement and result
   * - ``init``
     - Normal services must be stopped. Recovery validates and installs certificates offline and leaves services stopped.
   * - ``replace`` or ``replace-ca``
     - Backend services must be available. Recovery coordinates affected services and requires live HTTPS verification before success.

See :ref:`reference-manage-ssl-common-options` for ``--deployment-root``.

Examples
~~~~~~~~

Resume an interrupted operation from the deployment directory:

.. code:: sh

   python3 scripts/manage_ssl.py recover --operation OPERATION_ID --action resume

Replace ``OPERATION_ID`` with the ID reported by the interrupted command.
See :ref:`how-to-recover-certificate-operation` for choosing a recovery action and checking the result.

Output and Exit Status
----------------------

Successful initialization, replacement, or recovery reports the selected HTTPS endpoints, public CA certificate locations and fingerprints, and certificate expiration dates.
Successful commands return zero.
Validation failures and incomplete operations return a nonzero exit status.

For an interrupted operation, keep the reported operation ID and follow :ref:`how-to-recover-certificate-operation`.

See :ref:`reference-certificate-policy` for certificate requirements and :ref:`reference-deployment-folder` for backup locations.

Nginx Verification Connection
-----------------------------

The optional ``x-dioptra.nginx-connect-host`` Compose setting selects the hostname or IP address the manager uses to connect to nginx.
The default empty string selects the address automatically.

See :ref:`how-to-using-docker-compose-overrides` for an example.
